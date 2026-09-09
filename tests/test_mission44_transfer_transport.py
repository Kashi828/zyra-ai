from communication.transfer_protocol import (
    TransferEventType, make_chunk, make_ack, make_progress
)
from communication.transfer_transport import TransferTransport

def test_transfer_roundtrip():
    t = TransferTransport()
    t.start("t1", 100, {"filename": "x.bin", "size": 100})
    a = t.accept_chunk("t1", 1, 60)
    assert a.event_type == TransferEventType.ACK
    t.accept_chunk("t1", 2, 40)
    done = t.complete("t1")
    assert done.event_type == TransferEventType.COMPLETE
    assert any(e.event_type == TransferEventType.PROGRESS and e.payload["transferred"] == 100
               for e in t.events("t1"))

def test_cancel_blocks_completion():
    t = TransferTransport()
    t.start("t1", 100, {})
    t.cancel("t1")
    try:
        t.complete("t1")
    except ValueError:
        pass
    else:
        assert False

def test_chunk_size_is_bounded():
    t = TransferTransport()
    t.start("t1", 10, {})
    try:
        t.accept_chunk("t1", 0, 1024 * 1024 + 1)
    except ValueError:
        pass
    else:
        assert False

def test_protocol_factories():
    assert make_chunk("t1", 0, "abc").event_type == TransferEventType.CHUNK
    assert make_ack("t1", 0).event_type == TransferEventType.ACK
    assert make_progress("t1", 0, 5, 10).payload["transferred"] == 5
