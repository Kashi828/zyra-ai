from desktop.configuration_service import ConfigurationService
from desktop.configuration_status import ConfigurationStatusService
from desktop.product_config import ProductConfig


def test_configuration_status_exposes_non_secret_summary(tmp_path):
    service = ConfigurationService(ProductConfig(str(tmp_path / "config.json")))
    result = ConfigurationStatusService(service).read()
    assert result["model_provider"] == "local"
    assert result["voice_provider"] == "system"
    assert result["preferred_language"] == "en-IN"
    assert result["telemetry"] is False
    assert result["endpoint_configured"] is True


def test_configuration_status_hides_endpoint_value(tmp_path):
    service = ConfigurationService(ProductConfig(str(tmp_path / "config.json")))
    result = ConfigurationStatusService(service).read()
    assert "model_endpoint" not in result
