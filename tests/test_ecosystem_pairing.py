import pytest

from security.ecosystem_pairing import EcosystemPairingService


def test_pairing_code_is_single_use():
    service = EcosystemPairingService(ttl_seconds=60)
    request, code = service.create("esp-01", "nodemcu", "http://192.168.1.20")
    approved = service.approve(request.pairing_id, code)
    assert approved.consumed is True
    with pytest.raises(PermissionError):
        service.approve(request.pairing_id, code)


def test_wrong_code_is_rejected():
    service = EcosystemPairingService()
    request, _ = service.create("esp-02", "nodemcu")
    with pytest.raises(PermissionError):
        service.approve(request.pairing_id, "000000")


def test_pairing_record_never_contains_plain_code():
    service = EcosystemPairingService()
    request, code = service.create("esp-03", "nodemcu")
    assert request.code_hash != code
    assert len(request.code_hash) == 64
