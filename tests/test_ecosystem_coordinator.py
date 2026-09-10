from core.ecosystem_coordinator import EcosystemCoordinator


def test_routes_low_risk_capability_between_online_devices():
    coordinator = EcosystemCoordinator()
    coordinator.register_device("phone", "android", ["android.ui"])
    coordinator.register_device("pc", "windows", ["windows.browser"])

    decision = coordinator.route("phone", "pc", "windows.browser")

    assert decision.allowed is True
    assert decision.reason == "route authorized"


def test_denies_unregistered_target():
    coordinator = EcosystemCoordinator()
    coordinator.register_device("phone", "android", ["android.ui"])

    decision = coordinator.route("phone", "pc", "windows.browser")

    assert decision.allowed is False
    assert decision.reason == "target device is not registered"


def test_denies_offline_target():
    coordinator = EcosystemCoordinator()
    coordinator.register_device("phone", "android", ["android.ui"])
    coordinator.register_device("pc", "windows", ["windows.browser"], online=False)

    decision = coordinator.route("phone", "pc", "windows.browser")

    assert decision.allowed is False
    assert decision.reason == "target device is offline"


def test_requires_confirmation_for_privileged_target_capability():
    coordinator = EcosystemCoordinator()
    coordinator.register_device("phone", "android", ["android.ui"])
    coordinator.register_device("pc", "windows", ["windows.admin"])

    decision = coordinator.route("phone", "pc", "windows.admin")

    assert decision.allowed is False
    assert decision.reason == "target capability requires confirmation"


def test_snapshot_contains_registered_devices():
    coordinator = EcosystemCoordinator()
    coordinator.register_device("phone", "android", ["android.ui"])

    snapshot = coordinator.snapshot()

    assert snapshot["devices"][0]["device_id"] == "phone"
    assert snapshot["devices"][0]["device_type"] == "android"
