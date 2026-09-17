from pathlib import Path

from security.pairing_enrollment import PairingEnrollmentService
from security.capability_authorizer import CapabilityAuthorizer


def test_enrollment_issues_device_identity_and_capabilities():
    s = PairingEnrollmentService({"pc.apps", "pc.files"})
    offer, code = s.create_offer({"pc.apps"})
    r = s.enroll(offer.offer_id, code)
    assert r.device_id.startswith("dev_")
    assert "pc.apps" in r.capabilities
    assert "pc.files" not in r.capabilities
    assert len(r.device_secret) == 32


def test_offer_is_single_use():
    s = PairingEnrollmentService()
    offer, code = s.create_offer(set())
    s.enroll(offer.offer_id, code)
    try:
        s.enroll(offer.offer_id, code)
    except ValueError:
        pass
    else:
        assert False


def test_enroll_rejects_capabilities_outside_offer_grant():
    s = PairingEnrollmentService({"pc.apps", "pc.files"})
    offer, code = s.create_offer({"pc.apps"})
    try:
        s.enroll(offer.offer_id, code, requested_capabilities={"pc.files"})
    except PermissionError:
        pass
    else:
        assert False


def test_capability_authorizer():
    a = CapabilityAuthorizer()
    a.set_capabilities("d1", {"pc.apps"})
    assert a.allows("d1", "pc.apps")
    assert not a.allows("d1", "pc.files")
    try:
        a.require("d1", "pc.files")
    except PermissionError:
        pass
    else:
        assert False


def test_route_and_android_model_exist():
    assert Path("api/pairing_enrollment_routes.py").exists()
    assert Path("android/app/src/main/java/com/zyra/enrollment/EnrollmentState.kt").exists()
