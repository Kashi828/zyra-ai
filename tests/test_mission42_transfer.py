import hashlib
from pathlib import Path

from communication.transfer_manager import build_manifest, iter_chunks, verify_file, MAX_CHUNK
from communication.clipboard_handoff import ClipboardQueue

def test_manifest_and_chunk_integrity(tmp_path):
    p = tmp_path / "hello.txt"
    data = b"hello zyra" * 100
    p.write_bytes(data)
    m = build_manifest(str(p), "t1", chunk_size=10)
    reconstructed = b"".join(chunk for _, chunk in iter_chunks(str(p), 10))
    assert reconstructed == data
    assert m.size == len(data)
    assert verify_file(str(p), hashlib.sha256(data).hexdigest(), len(data))

def test_tampered_file_rejected(tmp_path):
    p = tmp_path / "file.bin"
    p.write_bytes(b"abc")
    m = build_manifest(str(p), "t2")
    p.write_bytes(b"abd")
    assert not verify_file(str(p), m.sha256, m.size)

def test_chunk_limit():
    try:
        list(iter_chunks(__file__, MAX_CHUNK + 1))
    except ValueError:
        pass
    else:
        assert False

def test_clipboard_handoff():
    q = ClipboardQueue()
    q.push(ClipboardQueue.make_text("c1", "hello", "phone"))
    assert q.pending("pc")[0].content == "hello"
