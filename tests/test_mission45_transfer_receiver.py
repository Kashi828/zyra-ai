import hashlib
from communication.transfer_receiver import TransferReceiver, MAX_CHUNK

def test_receive_and_verify(tmp_path):
    data = b"hello zyra" * 100
    target = tmp_path / "out.bin"
    r = TransferReceiver(str(target), len(data), hashlib.sha256(data).hexdigest())
    r.start()
    assert r.accept(data[:100]) == 100
    r.accept(data[100:])
    assert r.finish()
    assert target.read_bytes() == data

def test_tampered_expected_hash_removes_output(tmp_path):
    data = b"abc"
    target = tmp_path / "out.bin"
    r = TransferReceiver(str(target), 3, "00" * 32)
    r.start()
    r.accept(data)
    assert not r.finish()
    assert not target.exists()

def test_incomplete_transfer_rejected(tmp_path):
    target = tmp_path / "out.bin"
    r = TransferReceiver(str(target), 10, "00" * 32)
    r.start()
    r.accept(b"abc")
    try:
        r.finish()
    except ValueError:
        pass
    else:
        assert False

def test_oversized_chunk_rejected(tmp_path):
    target = tmp_path / "out.bin"
    r = TransferReceiver(str(target), MAX_CHUNK + 1, "00" * 32)
    r.start()
    try:
        r.accept(b"x" * (MAX_CHUNK + 1))
    except ValueError:
        pass
    else:
        assert False
