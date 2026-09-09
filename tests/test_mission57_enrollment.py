from security.pairing_enrollment import PairingEnrollmentService
from security.capability_authorizer import CapabilityAuthorizer
from pathlib import Path

def test_enrollment_issues_device_identity_and_capabilities():
    s=PairingEnrollmentService({"pc.apps","pc.files"})
    r=s.enroll("offer1", {"pc.apps"})
    assert r.device_id.startswith("dev_")
    assert "pc.apps" in r.capabilities
    assert "pc.files" not in r.capabilities
    assert len(r.device_secret)==32

def test_offer_is_single_use():
    s=PairingEnrollmentService()
    s.enroll("offer1", set())
    try: s.enroll("offer1", set())
    except ValueError: pass
    else: assert False

def test_capability_authorizer():
    a=CapabilityAuthorizer()
    a.set_capabilities("d1", {"pc.apps"})
    assert a.allows("d1","pc.apps")
    assert not a.allows("d1","pc.files")
    try: a.require("d1","pc.files")
    except PermissionError: pass
    else: assert False

def test_route_and_android_model_exist():
    assert Path("api/pairing_enrollment_routes.py").exists()
    assert Path("android/app/src/main/java/com/zyra/enrollment/EnrollmentState.kt").exists()
