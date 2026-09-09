from dataclasses import dataclass
import hashlib
from pathlib import Path

MAX_CHUNK = 1024 * 1024
MAX_TRANSFER = 250 * 1024 * 1024

@dataclass(frozen=True)
class TransferManifest:
    transfer_id: str
    filename: str
    size: int
    sha256: str
    chunk_size: int

def build_manifest(path: str, transfer_id: str, chunk_size: int = MAX_CHUNK) -> TransferManifest:
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(path)
    size = p.stat().st_size
    if size > MAX_TRANSFER:
        raise ValueError("transfer exceeds maximum size")
    if chunk_size <= 0 or chunk_size > MAX_CHUNK:
        raise ValueError("invalid chunk size")
    digest = hashlib.sha256()
    with p.open("rb") as f:
        while data := f.read(1024 * 1024):
            digest.update(data)
    return TransferManifest(transfer_id, p.name, size, digest.hexdigest(), chunk_size)

def iter_chunks(path: str, chunk_size: int = MAX_CHUNK):
    if chunk_size <= 0 or chunk_size > MAX_CHUNK:
        raise ValueError("invalid chunk size")
    with open(path, "rb") as f:
        index = 0
        while data := f.read(chunk_size):
            yield index, data
            index += 1

def verify_file(path: str, expected_sha256: str, expected_size: int) -> bool:
    p = Path(path)
    if not p.is_file() or p.stat().st_size != expected_size:
        return False
    digest = hashlib.sha256()
    with p.open("rb") as f:
        while data := f.read(1024 * 1024):
            digest.update(data)
    return digest.hexdigest().lower() == expected_sha256.lower()
