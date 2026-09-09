from desktop.configuration_profiles import ConfigurationProfileService
from desktop.configuration_service import ConfigurationService
from desktop.configuration_validation import ConfigurationValidationService
from desktop.product_config import ProductConfig


def make_service(tmp_path):
    cfg = ProductConfig(str(tmp_path / "config.json"))
    return ConfigurationService(cfg)


def test_profiles_include_local_and_privacy(tmp_path):
    service = ConfigurationProfileService(make_service(tmp_path))
    names = {item["name"] for item in service.list_profiles()}
    assert {"local", "privacy"} <= names


def test_privacy_profile_disables_voice(tmp_path):
    service = make_service(tmp_path)
    ConfigurationProfileService(service).apply("privacy")
    assert service.read()["voice_provider"] == "off"
    assert service.read()["telemetry"] is False


def test_unknown_profile_rejected(tmp_path):
    service = ConfigurationProfileService(make_service(tmp_path))
    try:
        service.apply("unknown")
        assert False
    except ValueError:
        pass


def test_validation_is_non_mutating(tmp_path):
    service = make_service(tmp_path)
    before = service.read()
    result = ConfigurationValidationService(service).validate()
    after = service.read()
    assert result["valid"] is True
    assert before == after
