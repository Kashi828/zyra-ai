from security.session_registry import ActiveSession, SessionRegistry

def test_registry_accepts_active_bound_session():
    r = SessionRegistry()
    r.register(ActiveSession("s1", "d1", 1000, 2000, "mac"))
    assert r.validate("s1", "d1", now=1500)
    assert not r.validate("s1", "d2", now=1500)

def test_registry_rejects_expired():
    r = SessionRegistry()
    r.register(ActiveSession("s1", "d1", 1000, 2000, "mac"))
    assert not r.validate("s1", "d1", now=2000)

def test_registry_revoke_is_terminal():
    r = SessionRegistry()
    r.register(ActiveSession("s1", "d1", 1000, 2000, "mac"))
    assert r.revoke("s1")
    assert not r.validate("s1", "d1", now=1200)
    assert not r.revoke("unknown")
