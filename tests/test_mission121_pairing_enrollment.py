import pytest

from security.pairing_enrollment import PairingEnrollmentService


def test_offer_requires_code_and_is_single_use():
    service = PairingEnrollmentService(default_capabilities={"windows.files.read"})
    offer, code = service.create_offer()

    result = service.enroll(offer.offer_id, code, {"windows.files.read"})
    assert result.device_id.startswith("dev_")
    assert len(result.device_secret) == 32

    with pytest.raises(ValueError):
        service.enroll(offer.offer_id, code)


def test_wrong_code_is_rejected():
    service = PairingEnrollmentService(default_capabilities={"windows.files.read"})
    offer, _ = service.create_offer()

    with pytest.raises(ValueError):
        service.enroll(offer.offer_id, "000000")


def test_capability_escalation_is_rejected():
    service = PairingEnrollmentService(default_capabilities={"windows.files.read"})
    offer, code = service.create_offer()

    with pytest.raises(PermissionError):
        service.enroll(offer.offer_id, code, {"windows.files.write"})


def test_offer_does_not_store_plaintext_code():
    service = PairingEnrollmentService(default_capabilities={"windows.files.read"})
    offer, code = service.create_offer()

    assert code not in offer.code_hash
    assert len(offer.code_hash) == 64
