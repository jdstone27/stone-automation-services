"""LocalLedger HTTP API.

Bound to loopback by compose. Nothing here reaches the network — the only
outbound call is to Ollama on this same machine.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import date, datetime
from decimal import Decimal

import httpx
from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import engine, get_session
from app.models import Document, DocumentStatus, Extraction
from app.pipeline import ingest_bytes
from app.watcher import InboxWatcher

settings = get_settings()
logging.basicConfig(
    level=settings.log_level.upper(),
    format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
)
logger = logging.getLogger("localledger")

_watcher = InboxWatcher(settings)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.ensure_dirs()
    if settings.watch_enabled:
        _watcher.start()
    else:
        logger.info("inbox watcher disabled by configuration")
    yield
    _watcher.stop()


app = FastAPI(
    title="LocalLedger",
    description="Self-hosted receipt and invoice extraction. Runs entirely on this machine.",
    version="0.1.0",
    lifespan=lifespan,
)


# ── Response models ────────────────────────────────────────────────────────

class ExtractionOut(BaseModel):
    vendor: str | None
    document_date: date | None
    subtotal: Decimal | None
    tax: Decimal | None
    total: Decimal | None
    currency: str | None
    category: str | None
    model_name: str

    model_config = {"from_attributes": True}


class DocumentOut(BaseModel):
    id: int
    sha256: str
    original_filename: str
    mime_type: str
    byte_size: int
    status: DocumentStatus
    error_message: str | None
    created_at: datetime
    processed_at: datetime | None
    extraction: ExtractionOut | None = None

    model_config = {"from_attributes": True}


class IngestResponse(BaseModel):
    document_id: int
    status: DocumentStatus
    duplicate: bool
    issues: list[str]


# ── Health ─────────────────────────────────────────────────────────────────

@app.get("/health/live", tags=["health"])
def live() -> dict[str, str]:
    """Process is up. Used by the container healthcheck."""
    return {"status": "ok"}


@app.get("/health/ready", tags=["health"])
def ready() -> dict[str, object]:
    """Dependencies are reachable: the database, and the model on the host."""
    checks: dict[str, object] = {}

    try:
        with engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")
        checks["database"] = "ok"
    except Exception as exc:  # noqa: BLE001
        checks["database"] = f"error: {exc}"

    try:
        response = httpx.get(settings.ollama_url.rstrip("/") + "/api/tags", timeout=5)
        response.raise_for_status()
        names = {model.get("name", "") for model in response.json().get("models", [])}
        wanted = settings.ollama_vision_model
        # Ollama reports tagged names; accept an untagged match too.
        if wanted in names or any(name.split(":")[0] == wanted.split(":")[0] for name in names):
            checks["ollama"] = "ok"
        else:
            checks["ollama"] = (
                f"reachable, but model {wanted!r} is not pulled. "
                f"Run: ollama pull {wanted}"
            )
    except Exception as exc:  # noqa: BLE001
        checks["ollama"] = f"error: {exc}"

    healthy = all(value == "ok" for value in checks.values())
    checks["status"] = "ok" if healthy else "degraded"
    return checks


# ── Documents ──────────────────────────────────────────────────────────────

@app.post("/documents", response_model=IngestResponse, tags=["documents"])
def upload_document(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
) -> IngestResponse:
    """Accept a receipt or invoice. Re-uploading the same bytes is a no-op."""
    payload = file.file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="uploaded file was empty")

    outcome = ingest_bytes(
        session,
        payload=payload,
        filename=file.filename or "upload",
        settings=settings,
        mime_type=file.content_type,
    )
    return IngestResponse(
        document_id=outcome.document_id,
        status=outcome.status,
        duplicate=outcome.duplicate,
        issues=outcome.issues,
    )


@app.get("/documents", response_model=list[DocumentOut], tags=["documents"])
def list_documents(
    status: DocumentStatus | None = None,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
) -> list[Document]:
    statement = select(Document).order_by(Document.created_at.desc())
    if status is not None:
        statement = statement.where(Document.status == status)
    return list(session.scalars(statement.limit(limit).offset(offset)))


@app.get("/documents/{document_id}", response_model=DocumentOut, tags=["documents"])
def get_document(document_id: int, session: Session = Depends(get_session)) -> Document:
    document = session.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="document not found")
    return document


@app.get("/stats", tags=["documents"])
def stats(session: Session = Depends(get_session)) -> dict[str, object]:
    """A quick read on what the appliance has processed."""
    counts = dict(
        session.execute(
            select(Document.status, func.count()).group_by(Document.status)
        ).all()
    )
    total_recorded = session.scalar(select(func.sum(Extraction.total))) or Decimal("0")
    return {
        "documents_by_status": {status.value: count for status, count in counts.items()},
        "extracted_total_value": str(total_recorded),
    }
