from communication.transfer_checkpoint import TransferCheckpoint, TransferStatus

def test_checkpoint_pause_resume():
    c = TransferCheckpoint("t1", 100)
    c.checkpoint(50, 5)
    assert c.status == TransferStatus.RUNNING
    c.pause()
    assert c.status == TransferStatus.PAUSED
    c.resume()
    assert c.status == TransferStatus.RUNNING
    assert c.transferred_bytes == 50
    assert c.next_sequence == 5

def test_invalid_checkpoint_rejected():
    c = TransferCheckpoint("t1", 100)
    for transferred in (-1, 101):
        try:
            c.checkpoint(transferred, 0)
        except ValueError:
            pass
        else:
            assert False

def test_completed_cannot_cancel():
    c = TransferCheckpoint("t1", 10)
    c.status = TransferStatus.COMPLETED
    try:
        c.cancel()
    except ValueError:
        pass
    else:
        assert False
