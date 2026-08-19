"""Vision extraction via a locally-hosted Ollama model.

Ollama runs natively on the host rather than in a container: on Apple Silicon a
containerised model cannot reach the Metal GPU and falls back to CPU. Nothing
here talks to anything outside this machine.
"""

from __future__ import annotations

import base64
import io
import json
import logging
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)

# Why: bound the work a single document can demand. A 200-page PDF dropped in
# the inbox should not occupy the model for an hour.
MAX_PAGES = 5
PDF_RENDER_SCALE = 2.0  # ~144 DPI; enough for small receipt type

EXTRACTION_PROMPT = """You are reading a receipt or invoice. Return ONLY a JSON object with exactly these keys:

{
  "vendor": string or null,
  "date": string or null,
  "subtotal": number or null,
  "tax": number or null,
  "total": number or null,
  "currency": string or null,
  "category": string or null
}

Rules:
- "date" must be ISO format: YYYY-MM-DD.
- Amounts must be plain numbers with no currency symbols or thousands separators.
- "currency" must be a three-letter code such as USD, EUR, GBP.
- "category" is a short expense category, for example: Supplies, Meals, Fuel, Software, Utilities.
- If a value is not clearly visible, use null. Do not guess.
- Return no explanation and no text outside the JSON object."""


class ExtractionError(RuntimeError):
    """Raised when the model could not be reached or produced nothing usable."""


def render_to_images(path: Path, mime_type: str) -> list[bytes]:
    """Return one image per page. Raster images pass through unchanged."""
    if mime_type == "application/pdf":
        return _render_pdf(path)
    return [path.read_bytes()]


def _render_pdf(path: Path) -> list[bytes]:
    try:
        import pypdfium2 as pdfium
    except ImportError as exc:  # pragma: no cover - dependency is in the image
        raise ExtractionError("pypdfium2 is not installed; cannot read PDFs") from exc

    try:
        document = pdfium.PdfDocument(path)
    except Exception as exc:
        raise ExtractionError(f"could not open PDF: {exc}") from exc

    images: list[bytes] = []
    try:
        for index in range(min(len(document), MAX_PAGES)):
            page = document[index]
            pil_image = page.render(scale=PDF_RENDER_SCALE).to_pil()
            buffer = io.BytesIO()
            pil_image.save(buffer, format="PNG")
            images.append(buffer.getvalue())
    except Exception as exc:
        raise ExtractionError(f"could not render PDF page: {exc}") from exc
    finally:
        document.close()

    if not images:
        raise ExtractionError("PDF contained no pages")
    return images


def extract_fields(
    images: list[bytes],
    *,
    model: str,
    ollama_url: str,
    timeout_seconds: float,
) -> dict:
    """Ask the local model to read the document. Returns the decoded JSON object.

    Raises ExtractionError if the model is unreachable or returns no JSON.
    """
    if not images:
        raise ExtractionError("no page images to send to the model")

    payload = {
        "model": model,
        "stream": False,
        "format": "json",
        "messages": [
            {
                "role": "user",
                "content": EXTRACTION_PROMPT,
                "images": [base64.b64encode(image).decode("ascii") for image in images],
            }
        ],
        # Why: deterministic reads. The same receipt should extract the same way
        # every time, which matters when reconciling a ledger.
        "options": {"temperature": 0},
    }

    url = ollama_url.rstrip("/") + "/api/chat"
    try:
        response = httpx.post(url, json=payload, timeout=timeout_seconds)
        response.raise_for_status()
    except httpx.TimeoutException as exc:
        raise ExtractionError(f"model timed out after {timeout_seconds}s") from exc
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text[:300]
        raise ExtractionError(f"model returned HTTP {exc.response.status_code}: {detail}") from exc
    except httpx.HTTPError as exc:
        raise ExtractionError(
            f"could not reach Ollama at {ollama_url}. Is it running on the host "
            f"(`brew services start ollama`)? Underlying error: {exc}"
        ) from exc

    try:
        body = response.json()
    except ValueError as exc:
        raise ExtractionError("Ollama response was not JSON") from exc

    content = (body.get("message") or {}).get("content")
    if not isinstance(content, str) or not content.strip():
        raise ExtractionError("model returned an empty response")

    return _decode_json_object(content)


def _decode_json_object(content: str) -> dict:
    """Decode the model's content, tolerating fenced or prose-wrapped JSON."""
    text = content.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
        text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Fall back to the outermost brace pair.
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass

    raise ExtractionError(f"model output was not JSON: {content[:200]!r}")
