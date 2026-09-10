from security.emergency_stop import EmergencyStop
from security.persistent_authorization_gateway import PersistentAuthorizationGateway


class FakeStore:
    def __init__(self):
        self.device = {"revoked": False, "capabilities": frozenset({"pc.apps"})}

    def get_device(self, device_id):
        return self.device if device_id == "pc-1" else None

    def validate_session(self, session_id, device_id):
        return session_id == "sess-1" and device_id == "pc-1"


def test_emergency_stop_blocks_authorization():
    stop = EmergencyStop()
    gateway = PersistentAuthorizationGateway(FakeStore(), stop)
    stop.engage("operator stop")

    decision = gateway.authorize("pc-1", "sess-1", "pc.apps")

    assert decision.allowed is False
    assert decision.reason == "ZYRA emergency stop is engaged"


def test_authorization_resumes_after_stop_release():
    stop = EmergencyStop()
    gateway = PersistentAuthorizationGateway(FakeStore(), stop)
    stop.engage()
    stop.release()

    decision = gateway.authorize("pc-1", "sess-1", "pc.apps")

    assert decision.allowed is True
