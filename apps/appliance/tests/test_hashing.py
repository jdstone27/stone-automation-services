from pathlib import Path

from app.hashing import hash_bytes, hash_file



def test_hash_bytes_is_stable():
    assert hash_bytes(b"receipt") == hash_bytes(b"receipt")
    assert len(hash_bytes(b"receipt")) == 64


def test_hash_bytes_differs_on_content():
    assert hash_bytes(b"receipt-a") != hash_bytes(b"receipt-b")


def test_hash_file_matches_hash_bytes(tmp_path: Path):
    payload = b"%PDF-1.4 fake receipt bytes"
    path = tmp_path / "receipt.pdf"
    path.write_bytes(payload)
    assert hash_file(path) == hash_bytes(payload)


def test_hash_file_handles_multi_chunk(tmp_path: Path):
    # Larger than the 1 MiB read chunk, to exercise the streaming path.
    payload = b"x" * (1024 * 1024 + 17)
    path = tmp_path / "big.pdf"
    path.write_bytes(payload)
    assert hash_file(path) == hash_bytes(payload)
