"""Content hashing — the basis of idempotency.

A document's identity is its bytes. The same receipt dropped twice, renamed, or
re-sent through the API is the same document and must not be processed again.
"""

import hashlib
from pathlib import Path

# Why: hash in chunks so a large scanned PDF never loads fully into memory.
_CHUNK_BYTES = 1024 * 1024


def hash_bytes(payload: bytes) -> str:
    """Return the lowercase hex SHA-256 of a byte string."""
    return hashlib.sha256(payload).hexdigest()


def hash_file(path: Path) -> str:
    """Return the lowercase hex SHA-256 of a file's contents."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(_CHUNK_BYTES):
            digest.update(chunk)
    return digest.hexdigest()
