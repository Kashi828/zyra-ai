from communication.transfer_persistence import PersistedTransfer, TransferStore
from communication.transfer_recovery import TransferRecoveryManager

def test_recovery_finds_existing_checkpoint(tmp_path):
    target = tmp_path / "a.bin"
    target.write_bytes(b"12345")
    store = TransferStore(str(tmp_path / "db.sqlite"))
    store.save(PersistedTransfer(
        "t1", "phone", "pc", "a.bin", str(target),
        5, 5, 1, "00"*32, "running"
    ))
    decisions = TransferRecoveryManager(store).scan()
    assert decisions[0].action == "resume"
    assert decisions[0].resume_bytes == 5

def test_recovery_requeues_when_destination_shorter(tmp_path):
    target = tmp_path / "a.bin"
    target.write_bytes(b"12")
    store = TransferStore(str(tmp_path / "db.sqlite"))
    store.save(PersistedTransfer(
        "t1", "phone", "pc", "a.bin", str(target),
        5, 5, 1, "00"*32, "running"
    ))
    decisions = TransferRecoveryManager(store).scan()
    assert decisions[0].action == "resume_from_disk"
    assert decisions[0].resume_bytes == 2
    assert store.get("t1").status == "queued"

def test_invalid_checkpoint_fails(tmp_path):
    store = TransferStore(str(tmp_path / "db.sqlite"))
    store.save(PersistedTransfer(
        "t1", "phone", "pc", "a.bin", str(tmp_path/"a.bin"),
        5, 6, 1, "00"*32, "running"
    ))
    decisions = TransferRecoveryManager(store).scan()
    assert decisions[0].action == "fail"
    assert store.get("t1").status == "failed"
