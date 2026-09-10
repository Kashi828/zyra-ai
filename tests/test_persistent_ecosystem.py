import secrets

from core.persistent_ecosystem import PersistentEcosystemRegistry
from security.persistent_device_store import PersistentDeviceStore


def test_registry_requires_trusted_device(tmp_path):
    store = PersistentDeviceStore(tmp_path / "security.sqlite3")
    registry = PersistentEcosystemRegistry(store)
    try:
        registry.register("esp-01", "nodemcu", "Lab board")
    except PermissionError:
        pass
    else:
        raise AssertionError("untrusted device was registered")


def test_registry_persists_trusted_nodemcu(tmp_path):
    db = tmp_path / "security.sqlite3"
    store = PersistentDeviceStore(db)
    secret = secrets.token_bytes(32)
    store.enroll_device("esp-01", secret, ["iot.telemetry", "iot.gpio"])
    registry = PersistentEcosystemRegistry(store)
    device = registry.register("esp-01", "nodemcu", "Lab board", online=True)
    assert device.device_id == "esp-01"
    assert device.device_type == "nodemcu"
    assert device.capabilities == frozenset({"iot.telemetry", "iot.gpio"})

    reopened = PersistentEcosystemRegistry(PersistentDeviceStore(db))
    persisted = reopened.get("esp-01")
    assert persisted is not None
    assert persisted.display_name == "Lab board"
    assert persisted.online is True
    assert persisted.revoked is False


def test_revocation_removes_ecosystem_trust(tmp_path):
    store = PersistentDeviceStore(tmp_path / "security.sqlite3")
    store.enroll_device("esp-01", secrets.token_bytes(32), ["iot.telemetry"])
    registry = PersistentEcosystemRegistry(store)
    registry.register("esp-01", "nodemcu", online=True)
    store.revoke_device("esp-01")
    device = registry.get("esp-01")
    assert device.revoked is True
