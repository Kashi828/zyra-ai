from desktop.product_config import ProductConfig
from desktop.configuration_service import ConfigurationService

def test_config_defaults(tmp_path):
    c = ProductConfig(str(tmp_path/"config.json")).load()
    assert c["model_provider"] == "local"
    assert c["telemetry"] is False

def test_config_persists(tmp_path):
    s = ConfigurationService(ProductConfig(str(tmp_path/"config.json")))
    result = s.update(model_provider="local", model_endpoint="http://127.0.0.1:11434",
                      voice_provider="system", preferred_language="kn-IN")
    assert result["preferred_language"] == "kn-IN"

def test_config_rejects_bad_endpoint(tmp_path):
    s = ConfigurationService(ProductConfig(str(tmp_path/"config.json")))
    try:
        s.update(model_provider="local", model_endpoint="bad", voice_provider="system", preferred_language="en-IN")
        assert False
    except ValueError:
        pass
