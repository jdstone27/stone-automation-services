"""Pipeline behaviour against a real database.

The two properties that matter most are asserted here: the same bytes are only
ever recorded once, and nothing a bad document can do takes the service down.
"""

import json
from decimal import Decimal

import pytest
from sqlalchemy import func, select

from app.models import Document, DocumentStatus, Extraction
from app.pipeline import guess_mime_type, ingest_bytes, safe_name
from tests.conftest import requires_db

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"fake-image-data"

GOOD_RESPONSE = {
    "vendor": "Ace Hardware",
    "date": "2026-03-04",
    "subtotal": 90.00,
    "tax": 7.20,
    "total": 97.20,
    "currency": "USD",
    "category": "Supplies",
}


@pytest.fixture
def stub_model(monkeypatch):
    """Replace the vision call. The model itself is exercised on the Mini."""

    def _install(response=None, error=None):
        import app.pipeline as pipeline

        monkeypatch.setattr(pipeline, "render_to_images", lambda path, mime: [b"page"])

        def fake_extract(images, *, model, ollama_url, timeout_seconds):
            if error is not None:
                raise error
            return response

        monkeypatch.setattr(pipeline, "extract_fields", fake_extract)

    return _install


class TestPureHelpers:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("../../etc/passwd", "passwd"),  # traversal stripped by Path().name
            ("receipt 2026.pdf", "receipt_2026.pdf"),
            (".hidden", "hidden"),
            ("", "document"),
        ],
    )
    def test_safe_name(self, raw, expected):
        assert safe_name(raw) == expected

    def test_guess_mime_type(self):
        assert guess_mime_type("a.pdf") == "application/pdf"
        assert guess_mime_type("a.png") == "image/png"
        assert guess_mime_type("a.unknown") == "application/octet-stream"


@requires_db
class TestIngest:
    def test_happy_path_records_extraction(self, session, settings, stub_model):
        stub_model(response=GOOD_RESPONSE)

        outcome = ingest_bytes(
            session, payload=PNG_BYTES, filename="receipt.png", settings=settings
        )

        assert outcome.status is DocumentStatus.extracted
        assert outcome.duplicate is False
        assert outcome.issues == []

        document = session.get(Document, outcome.document_id)
        assert document.original_filename == "receipt.png"
        assert document.processed_at is not None

        extraction = session.scalar(
            select(Extraction).where(Extraction.document_id == document.id)
        )
        assert extraction.vendor == "Ace Hardware"
        assert extraction.total == Decimal("97.20")
        assert extraction.currency == "USD"
        assert extraction.model_name == "test-vision-model"

        # Original archived, nothing left in review.
        assert document.stored_path is not None
        archived = settings.archive_dir.rglob("*")
        assert any(path.is_file() for path in archived)
        assert list(settings.review_dir.glob("*")) == []

    def test_same_bytes_ingested_once(self, session, settings, stub_model):
        stub_model(response=GOOD_RESPONSE)

        first = ingest_bytes(
            session, payload=PNG_BYTES, filename="receipt.png", settings=settings
        )
        # Same bytes, different name — still the same document.
        second = ingest_bytes(
            session, payload=PNG_BYTES, filename="renamed-copy.png", settings=settings
        )

        assert second.duplicate is True
        assert second.document_id == first.document_id

        count = session.scalar(
            select(func.count()).select_from(Document).where(Document.sha256 == first_sha(session, first))
        )
        assert count == 1

    def test_model_failure_goes_to_review_not_crash(self, session, settings, stub_model):
        from app.extract import ExtractionError

        stub_model(error=ExtractionError("model timed out after 180s"))

        outcome = ingest_bytes(
            session, payload=PNG_BYTES, filename="blurry.png", settings=settings
        )

        assert outcome.status is DocumentStatus.review
        assert "timed out" in outcome.issues[0]

        review_files = sorted(path.name for path in settings.review_dir.iterdir())
        assert any(name.endswith(".png") for name in review_files)

        sidecar = next(settings.review_dir.glob("*.reason.json"))
        reason = json.loads(sidecar.read_text())
        assert reason["issues"] == outcome.issues
        assert reason["original_filename"] == "blurry.png"

    def test_unexpected_exception_is_contained(self, session, settings, stub_model):
        stub_model(error=ValueError("something nobody predicted"))

        outcome = ingest_bytes(
            session, payload=PNG_BYTES, filename="cursed.png", settings=settings
        )

        assert outcome.status is DocumentStatus.review
        assert "unexpected error" in outcome.issues[0]

    def test_missing_total_goes_to_review(self, session, settings, stub_model):
        stub_model(response={"vendor": "Ace", "date": "2026-03-04"})

        outcome = ingest_bytes(
            session, payload=PNG_BYTES, filename="partial.png", settings=settings
        )

        assert outcome.status is DocumentStatus.review
        assert any("total" in issue for issue in outcome.issues)
        # No extraction row for a document we could not read a total from.
        assert session.scalar(
            select(Extraction).where(Extraction.document_id == outcome.document_id)
        ) is None

    def test_prose_response_goes_to_review(self, session, settings, stub_model):
        stub_model(response="I'm sorry, I can't read that receipt.")

        outcome = ingest_bytes(
            session, payload=PNG_BYTES, filename="prose.png", settings=settings
        )
        assert outcome.status is DocumentStatus.review

    def test_unsupported_type_goes_to_review(self, session, settings, stub_model):
        stub_model(response=GOOD_RESPONSE)

        outcome = ingest_bytes(
            session, payload=b"MZ\x90\x00", filename="malware.exe", settings=settings
        )

        assert outcome.status is DocumentStatus.review
        assert "unsupported file type" in outcome.issues[0]


def first_sha(session, outcome):
    return session.get(Document, outcome.document_id).sha256
