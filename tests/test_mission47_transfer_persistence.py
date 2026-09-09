from communication.transfer_persistence import (
    PersistedTransfer, TransferStore, verified_resume_point
)

def test_store_persists_and_recovers(tmp_path):
    store = TransferStore(str(tmp_path / "transfers.db"))
    t = PersistedTransfer(
        "t1", "phone", "pc", "a.bin", str(tmp_path / "a.bin"),
        100, 40, 4, "00" * 32, "running"
    )
    store.save(t)
    got = store.get("t1")
    assert got is not None
    assert got.transferred_bytes == 40
    assert got.next_sequence == 4
    assert [x.transfer_id for x in store.recoverable()] == ["t1"]

def test_upsert_advances_checkpoint(tmp_path):
    store = TransferStore(str(tmp_path / "transfers.db"))
    t = PersistedTransfer(
        "t1", "phone", "pc", "a.bin", str(tmp_path / "a.bin"),
        100, 10, 1, "00" * 32, "running"
    )
    store.save(t)
    t2 = PersistedTransfer(
        "t1", "phone", "pc", "a.bin", str(tmp_path / "a.bin"),
        100, 20, 2, "00" * 32, "running"
    )
    store.save(t2)
    got = store.get("t1")
    assert got.transferred_bytes == 20
    assert got.next_sequence == 2

def test_resume_point_is_bounded_by_existing_file(tmp_path):
    p = tmp_path / "a.bin"
    p.write_bytes(b"12345")
    assert verified_resume_point(str(p), 10) == 5
    assert verified_resume_point(str(p), 3) == 3
    assert verified_resume_point(str(tmp_path / "missing"), 3) == 0
