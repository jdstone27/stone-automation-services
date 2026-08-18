"""The model is untrusted input. These tests pin down what we accept from it."""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.schemas import (
    MAX_ABS_AMOUNT,
    parse_amount,
    parse_currency,
    parse_document_date,
    parse_model_output,
)


class TestParseAmount:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("12.34", Decimal("12.34")),
            ("$12.34", Decimal("12.34")),
            ("  $1,234.56 ", Decimal("1234.56")),
            ("1.234,56", Decimal("1234.56")),   # European decimal comma
            ("1,234", Decimal("1234")),          # thousands separator
            ("12,34", Decimal("12.34")),         # lone decimal comma
            ("-45.00", Decimal("-45.00")),       # refund
            ("£99", Decimal("99.00")),
            (12.34, Decimal("12.34")),
            (12, Decimal("12.00")),
        ],
    )
    def test_coerces(self, raw, expected):
        amount, issue = parse_amount(raw)
        assert issue is None
        assert amount == expected

    def test_float_does_not_inherit_binary_error(self):
        amount, issue = parse_amount(0.1 + 0.2)
        assert issue is None
        assert amount == Decimal("0.30")

    @pytest.mark.parametrize("raw", [None, "", "   "])
    def test_absent_is_not_an_issue(self, raw):
        assert parse_amount(raw) == (None, None)

    @pytest.mark.parametrize("raw", ["about twenty quid", "N/A", "$$$", True, ["12.00"]])
    def test_unreadable_reports_issue(self, raw):
        amount, issue = parse_amount(raw)
        assert amount is None
        if raw is not True:
            assert issue is not None

    def test_rejects_implausible_magnitude(self):
        amount, issue = parse_amount(str(MAX_ABS_AMOUNT + Decimal("1")))
        assert amount is None
        assert "plausible maximum" in issue


class TestParseDate:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("2026-03-04", date(2026, 3, 4)),
            ("03/04/2026", date(2026, 3, 4)),   # US-first, documented
            ("04.03.2026", date(2026, 3, 4)),
            ("4 March 2026", date(2026, 3, 4)),
            ("March 4, 2026", date(2026, 3, 4)),
        ],
    )
    def test_formats(self, raw, expected):
        parsed, issue = parse_document_date(raw)
        assert issue is None
        assert parsed == expected

    def test_rejects_future(self):
        far = (datetime.now(timezone.utc).date() + timedelta(days=30)).isoformat()
        parsed, issue = parse_document_date(far)
        assert parsed is None
        assert "future" in issue

    def test_rejects_ancient(self):
        parsed, issue = parse_document_date("1887-01-01")
        assert parsed is None
        assert "implausibly old" in issue

    def test_unparseable(self):
        parsed, issue = parse_document_date("last Tuesday")
        assert parsed is None
        assert issue is not None


class TestParseCurrency:
    def test_uppercases(self):
        assert parse_currency("usd") == ("USD", None)

    def test_rejects_symbol(self):
        code, issue = parse_currency("$")
        assert code is None
        assert issue is not None


class TestParseModelOutput:
    def test_clean_receipt(self):
        result = parse_model_output(
            {
                "vendor": "  Ace   Hardware ",
                "date": "2026-03-04",
                "subtotal": "$90.00",
                "tax": "$7.20",
                "total": "$97.20",
                "currency": "usd",
                "category": "Supplies",
            }
        )
        assert result.issues == []
        assert result.needs_review is False
        assert result.fields.vendor == "Ace Hardware"
        assert result.fields.total == Decimal("97.20")
        assert result.fields.currency == "USD"

    def test_missing_total_needs_review(self):
        result = parse_model_output({"vendor": "Ace", "date": "2026-03-04"})
        assert result.needs_review is True
        assert any("total" in issue for issue in result.issues)

    def test_arithmetic_mismatch_flagged(self):
        result = parse_model_output(
            {"subtotal": "90.00", "tax": "7.20", "total": "1000.00"}
        )
        assert result.needs_review is True
        assert any("arithmetic" in issue for issue in result.issues)

    def test_rounding_slack_allowed(self):
        result = parse_model_output(
            {"subtotal": "90.00", "tax": "7.21", "total": "97.20"}
        )
        assert not any("arithmetic" in issue for issue in result.issues)

    def test_prose_response_is_not_fatal(self):
        result = parse_model_output("I could not read this receipt, sorry!")
        assert result.needs_review is True
        assert result.fields.total is None

    def test_placeholder_strings_become_null(self):
        result = parse_model_output({"vendor": "unknown", "total": "5.00"})
        assert result.fields.vendor is None
