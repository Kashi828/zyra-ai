from security.capability_broker import CapabilityBroker


def test_unknown_capability_is_denied():
    decision = CapabilityBroker({"windows.files.read"}).evaluate("windows.shell")
    assert decision.allowed is False
    assert decision.requires_confirmation is False


def test_ungranted_capability_is_denied():
    decision = CapabilityBroker().evaluate("windows.files.read")
    assert decision.allowed is False
    assert decision.reason == "capability not granted"


def test_low_risk_granted_capability_runs():
    decision = CapabilityBroker({"windows.files.read"}).evaluate("windows.files.read")
    assert decision.allowed is True
    assert decision.requires_confirmation is False


def test_medium_risk_requires_confirmation():
    broker = CapabilityBroker({"windows.files.write"})
    pending = broker.evaluate("windows.files.write")
    approved = broker.evaluate("windows.files.write", confirmed=True)
    assert pending.allowed is False
    assert pending.requires_confirmation is True
    assert approved.allowed is True


def test_high_risk_requires_confirmation():
    broker = CapabilityBroker({"windows.admin"})
    pending = broker.evaluate("windows.admin")
    approved = broker.evaluate("windows.admin", confirmed=True)
    assert pending.allowed is False
    assert pending.requires_confirmation is True
    assert approved.allowed is True


def test_grants_are_not_wildcards():
    decision = CapabilityBroker({"windows.admin"}).evaluate("windows.system", confirmed=True)
    assert decision.allowed is False
    assert decision.reason == "capability not granted"
