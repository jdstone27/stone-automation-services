"""Parsing and validation of vision-model output.

The model's response is untrusted input. It may be missing keys, wrap numbers in
currency symbols, invent formats, or return prose. Nothing here raises on bad
input: every problem becomes an entry in `issues`, and the pipeline decides from
that whether a document is safe to record or belongs in /review.
"""

from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from pydantic import BaseModel

# Why: a receipt total in the millions is far more likely to be a misread than a
# real expense. Bound it so a hallucinated figure cannot land in the ledger.
MAX_ABS_AMOUNT = Decimal("1000000.00")

# Why: dated in the future means the model misread the year; allow a day of
# slack for timezone skew between the host and the document.
FUTURE_TOLERANCE = timedelta(days=1)
EARLIEST_PLAUSIBLE = date(1990, 1, 1)

_CURRENCY_CHARS = re.compile(r"[^\d,.\-]")
_CURRENCY_CODE = re.compile(r"^[A-Za-z]{3}$")

# Ambiguous slash dates are read US-first (MM/DD/YYYY). Stated rather than
# guessed, so a European receipt landing in /review has a documented reason.
_DATE_FORMATS = (
    "%Y-%m-%d",
    "%Y/%m/%d",
    "%m/%d/%Y",
    "%m-%d-%Y",
    "%d.%m.%Y",
    "%d %B %Y",
    "%d %b %Y",
    "%B %d, %Y",
    "%b %d, %Y",
)


class ExtractedFields(BaseModel):
    vendor: str | None = None
    document_date: date | None = None
    subtotal: Decimal | None = None
    tax: Decimal | None = None
    total: Decimal | None = None
    currency: str | None = None
    category: str | None = None


class ParseResult(BaseModel):
    fields: ExtractedFields
    issues: list[str] = []

    @property
    def needs_review(self) -> bool:
        """A record without a total is not a usable financial record."""
        return bool(self.issues) or self.fields.total is None


def _clean_text(value: Any, *, max_length: int = 200) -> str | None:
    if not isinstance(value, str):
        return None
    collapsed = " ".join(value.split())
    if not collapsed or collapsed.lower() in {"null", "none", "n/a", "unknown", "-"}:
        return None
    return collapsed[:max_length]


def parse_amount(value: Any) -> tuple[Decimal | None, str | None]:
    """Coerce a model-supplied amount to Decimal. Returns (amount, issue)."""
    if value is None or isinstance(value, bool):
        return None, None
    if isinstance(value, (int, float)):
        # Why: str() first — Decimal(float) carries the float's binary error.
        candidate = str(value)
    elif isinstance(value, str):
        candidate = value.strip()
        if not candidate:
            return None, None
    else:
        return None, f"amount had unexpected type {type(value).__name__}"

    stripped = _CURRENCY_CHARS.sub("", candidate)
    if not stripped or stripped in {"-", ".", ","}:
        return None, f"could not read an amount from {candidate!r}"

    # Both separators present: whichever comes last is the decimal point.
    if "," in stripped and "." in stripped:
        if stripped.rfind(",") > stripped.rfind("."):
            stripped = stripped.replace(".", "").replace(",", ".")
        else:
            stripped = stripped.replace(",", "")
    elif "," in stripped:
        parts = stripped.split(",")
        # A lone comma with exactly two trailing digits is a decimal comma;
        # anything else is a thousands separator.
        if len(parts) == 2 and len(parts[1]) == 2:
            stripped = stripped.replace(",", ".")
        else:
            stripped = stripped.replace(",", "")

    try:
        amount = Decimal(stripped)
    except InvalidOperation:
        return None, f"could not read an amount from {candidate!r}"

    if not amount.is_finite():
        return None, f"amount {candidate!r} was not a finite number"
    if abs(amount) > MAX_ABS_AMOUNT:
        return None, f"amount {amount} exceeds the plausible maximum {MAX_ABS_AMOUNT}"

    return amount.quantize(Decimal("0.01")), None


def parse_document_date(value: Any) -> tuple[date | None, str | None]:
    """Coerce a model-supplied date. Returns (date, issue)."""
    if value is None:
        return None, None
    if isinstance(value, date) and not isinstance(value, datetime):
        parsed = value
    elif isinstance(value, datetime):
        parsed = value.date()
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            return None, None
        parsed = None
        for fmt in _DATE_FORMATS:
            try:
                parsed = datetime.strptime(text, fmt).date()
                break
            except ValueError:
                continue
        if parsed is None:
            return None, f"could not read a date from {text!r}"
    else:
        return None, f"date had unexpected type {type(value).__name__}"

    today = datetime.now(timezone.utc).date()
    if parsed > today + FUTURE_TOLERANCE:
        return None, f"date {parsed.isoformat()} is in the future"
    if parsed < EARLIEST_PLAUSIBLE:
        return None, f"date {parsed.isoformat()} is implausibly old"
    return parsed, None


def parse_currency(value: Any) -> tuple[str | None, str | None]:
    text = _clean_text(value, max_length=8)
    if text is None:
        return None, None
    if not _CURRENCY_CODE.match(text):
        return None, f"currency {text!r} is not a three-letter code"
    return text.upper(), None


def parse_model_output(payload: Any) -> ParseResult:
    """Turn a decoded model response into validated fields plus a list of issues."""
    if not isinstance(payload, dict):
        return ParseResult(
            fields=ExtractedFields(),
            issues=[f"model returned {type(payload).__name__}, expected a JSON object"],
        )

    issues: list[str] = []

    total, issue = parse_amount(payload.get("total"))
    if issue:
        issues.append(f"total: {issue}")
    subtotal, issue = parse_amount(payload.get("subtotal"))
    if issue:
        issues.append(f"subtotal: {issue}")
    tax, issue = parse_amount(payload.get("tax"))
    if issue:
        issues.append(f"tax: {issue}")

    document_date, issue = parse_document_date(payload.get("date") or payload.get("document_date"))
    if issue:
        issues.append(f"date: {issue}")

    currency, issue = parse_currency(payload.get("currency"))
    if issue:
        issues.append(f"currency: {issue}")

    if total is None:
        issues.append("total: missing")

    # Arithmetic cross-check. A mismatch usually means one figure was misread,
    # so the document is worth a human glance even though every field parsed.
    if subtotal is not None and tax is not None and total is not None:
        if abs((subtotal + tax) - total) > Decimal("0.02"):
            issues.append(
                f"arithmetic: subtotal {subtotal} + tax {tax} != total {total}"
            )

    return ParseResult(
        fields=ExtractedFields(
            vendor=_clean_text(payload.get("vendor")),
            document_date=document_date,
            subtotal=subtotal,
            tax=tax,
            total=total,
            currency=currency,
            category=_clean_text(payload.get("category"), max_length=64),
        ),
        issues=issues,
    )
