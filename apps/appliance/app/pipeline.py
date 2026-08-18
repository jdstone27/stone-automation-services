"""Ingest and processing.

Two guarantees this module exists to keep:

1. Idempotency — a document is identified by the SHA-256 of its bytes. Dropping
   the same receipt twice, or renaming it first, records it once.
2. Nothing fatal — a corrupt PDF, an unreachable model, or a nonsense response
   sends the original to /review with a reason. It never takes the service down.
"""

from __future__ import annotations

import json
import logging
import mimetypes
import re
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.config import Settings
from app.extract import ExtractionError, extract_fields, render_to_images
from app.hashing import hash_bytes
from app.models import Document, DocumentStatus, Extraction
from app.schemas import parse_model_output

logger = logging.getLogger(__name__)

SUPPORTED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/tiff",
    "image/heic",
}

_UNSAFE_CHARS = re.compile(r"[^A-Za-z0-9._-]")


@dataclass
class IngestOutcome:
    document_id: int
    status: DocumentStatus
    duplicate: bool
    issues: list[str]


def guess_mime_type(filename: str) -> str:
    guessed, _ = mimetypes.guess_type(filename)
    return guessed or "application/octet-stream"


def safe_name(filename: str, *, max_length: int = 80) -> str:
    """Strip a filename down to something safe to place on disk."""
    stem = Path(filename).name
    cleaned = _UNSAFE_CHARS.sub("_", stem).lstrip(".")
    return (cleaned or "document")[:max_length]


def ingest_bytes(
    session: Session,
    *,
    payload: bytes,
    filename: str,
    settings: Settings,
    mime_type: str | None = None,
) -> IngestOutcome:
    """Accept a document, store it, and run extraction. Never raises on bad input."""
    settings.ensure_dirs()

    digest = hash_bytes(payload)
    resolved_mime = mime_type or guess_mime_type(filename)

    existing = session.scalar(select(Document).where(Document.sha256 == digest))
    if existing is not None:
        logger.info("duplicate document %s (sha256=%s); skipping", filename, digest[:12])
        return IngestOutcome(
            document_id=existing.id,
            status=existing.status,
            duplicate=True,
            issues=[],
        )

    document = Document(
        sha256=digest,
        original_filename=filename,
        mime_type=resolved_mime,
        byte_size=len(payload),
        status=DocumentStatus.processing,
    )
    session.add(document)
    try:
        session.flush()
    except IntegrityError:
        # Another worker claimed the same bytes between our check and insert.
        session.rollback()
        existing = session.scalar(select(Document).where(Document.sha256 == digest))
        if existing is None:
            raise
        return IngestOutcome(
            document_id=existing.id,
            status=existing.status,
            duplicate=True,
            issues=[],
        )

    if resolved_mime not in SUPPORTED_MIME_TYPES:
        return _send_to_review(
            session,
            document,
            payload,
            settings,
            issues=[f"unsupported file type {resolved_mime}"],
        )

    # Why: a real temp file, not a staging copy in /review — otherwise a
    # working file and a genuine review artefact can collide on the same name.
    suffix = Path(safe_name(filename)).suffix or ".bin"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as handle:
        handle.write(payload)
        working_path = Path(handle.name)

    try:
        images = render_to_images(working_path, resolved_mime)
        raw = extract_fields(
            images,
            model=settings.ollama_vision_model,
            ollama_url=settings.ollama_url,
            timeout_seconds=settings.ollama_timeout_seconds,
        )
    except ExtractionError as exc:
        logger.warning("extraction failed for %s: %s", filename, exc)
        working_path.unlink(missing_ok=True)
        return _send_to_review(session, document, payload, settings, issues=[str(exc)])
    except Exception as exc:  # noqa: BLE001 - a bad file must never kill the loop
        logger.exception("unexpected error processing %s", filename)
        working_path.unlink(missing_ok=True)
        return _send_to_review(
            session, document, payload, settings, issues=[f"unexpected error: {exc}"]
        )

    working_path.unlink(missing_ok=True)
    result = parse_model_output(raw)

    if result.needs_review:
        return _send_to_review(
            session, document, payload, settings, issues=result.issues, raw=raw
        )

    archive_path = _archive_path(settings, digest, filename)
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    archive_path.write_bytes(payload)

    session.add(
        Extraction(
            document_id=document.id,
            vendor=result.fields.vendor,
            document_date=result.fields.document_date,
            subtotal=result.fields.subtotal,
            tax=result.fields.tax,
            total=result.fields.total,
            currency=result.fields.currency,
            category=result.fields.category,
            model_name=settings.ollama_vision_model,
            raw_response=raw,
        )
    )
    document.status = DocumentStatus.extracted
    document.stored_path = str(archive_path)
    document.error_message = None
    document.processed_at = datetime.now(timezone.utc)
    session.flush()

    logger.info(
        "extracted %s: vendor=%s total=%s", filename, result.fields.vendor, result.fields.total
    )
    return IngestOutcome(
        document_id=document.id, status=document.status, duplicate=False, issues=[]
    )


def _send_to_review(
    session: Session,
    document: Document,
    payload: bytes,
    settings: Settings,
    *,
    issues: list[str],
    raw: dict | None = None,
) -> IngestOutcome:
    """Isolate a document that could not be processed, with a readable reason."""
    review_path = settings.review_dir / f"{document.sha256[:12]}-{safe_name(document.original_filename)}"
    review_path.write_bytes(payload)

    # Why: a sidecar so whoever opens /review can see why without the database.
    reason = {
        "document_id": document.id,
        "original_filename": document.original_filename,
        "sha256": document.sha256,
        "issues": issues,
        "model_response": raw,
        "at": datetime.now(timezone.utc).isoformat(),
    }
    review_path.with_suffix(review_path.suffix + ".reason.json").write_text(
        json.dumps(reason, indent=2, default=str)
    )

    document.status = DocumentStatus.review
    document.stored_path = str(review_path)
    document.error_message = "; ".join(issues)[:2000]
    document.processed_at = datetime.now(timezone.utc)
    session.flush()

    return IngestOutcome(
        document_id=document.id, status=document.status, duplicate=False, issues=issues
    )


def _archive_path(settings: Settings, digest: str, filename: str) -> Path:
    now = datetime.now(timezone.utc)
    return settings.archive_dir / f"{now:%Y}" / f"{now:%m}" / f"{digest[:12]}-{safe_name(filename)}"


def ingest_path(session: Session, path: Path, settings: Settings) -> IngestOutcome | None:
    """Ingest a file from the inbox, removing it once recorded."""
    try:
        payload = path.read_bytes()
    except OSError as exc:
        logger.warning("could not read %s: %s", path, exc)
        return None

    outcome = ingest_bytes(
        session, payload=payload, filename=path.name, settings=settings
    )
    try:
        path.unlink()
    except OSError as exc:
        logger.warning("processed %s but could not remove it from the inbox: %s", path, exc)
    return outcome
