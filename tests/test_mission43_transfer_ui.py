from communication.transfer_session import TransferSession, TransferStatus
import subprocess, sys, pathlib

def test_transfer_session_progress_and_clamping():
    s = TransferSession("t1", "phone", "pc", "a.bin", 100)
    s.update(40)
    assert s.status == TransferStatus.RUNNING
    assert s.transferred_bytes == 40
    s.update(200)
    assert s.transferred_bytes == 100

def test_completed_state_contract():
    s = TransferSession("t1", "phone", "pc", "a.bin", 100)
    s.status = TransferStatus.COMPLETED
    s.transferred_bytes = 100
    assert s.status.value == "completed"
    assert s.transferred_bytes == s.total_bytes

def test_android_transfer_controller_exists():
    p = pathlib.Path("android/app/src/main/java/com/zyra/transfer/TransferController.kt")
    assert p.exists()
    text = p.read_text()
    assert "fun updateProgress" in text
    assert "fun complete" in text
