from config.product_config import ProductConfig
from config.permissions_profile import PermissionProfile

def test_production_defaults_are_local_first():
    cfg = ProductConfig.production_defaults()
    assert cfg.environment == "production"
    assert cfg.local_only is True
    assert cfg.remote_access_enabled is False
    assert cfg.require_confirmation_for_sensitive_actions is True

def test_remote_access_requires_non_local_mode():
    cfg = ProductConfig(local_only=True, remote_access_enabled=True)
    try:
        cfg.validate()
    except ValueError:
        pass
    else:
        assert False

def test_permissions_allow_and_block():
    p = PermissionProfile("d1", {"pc.apps"})
    assert p.allows("pc.apps")
    p.block("pc.apps")
    assert not p.allows("pc.apps")
    p.grant("pc.apps")
    assert p.allows("pc.apps")

def test_confirmation_is_device_scoped():
    p = PermissionProfile("d1", {"pc.apps"}, {"pc.apps"})
    assert p.needs_confirmation("pc.apps")
    q = PermissionProfile("d2", {"pc.apps"})
    assert not q.needs_confirmation("pc.apps")
