from __future__ import annotations
from urllib.parse import urlparse
from desktop.product_config import ProductConfig

class ConfigurationService:
    ALLOWED_MODELS = {"local", "cloud"}
    ALLOWED_VOICE = {"system", "local", "off"}
    ALLOWED_LANGUAGES = {"en-IN", "en-US", "hi-IN", "kn-IN"}

    def __init__(self, config: ProductConfig | None = None):
        self.config = config or ProductConfig()

    @staticmethod
    def _valid_endpoint(endpoint: str) -> bool:
        try:
            p = urlparse(endpoint)
            return p.scheme in {"http", "https"} and bool(p.netloc)
        except ValueError:
            return False

    def read(self):
        return self.config.load()

    def update(self, *, model_provider, model_endpoint, voice_provider, preferred_language, telemetry=False):
        if model_provider not in self.ALLOWED_MODELS: raise ValueError("Unsupported model provider")
        if not self._valid_endpoint(model_endpoint): raise ValueError("Invalid model endpoint")
        if voice_provider not in self.ALLOWED_VOICE: raise ValueError("Unsupported voice provider")
        if preferred_language not in self.ALLOWED_LANGUAGES: raise ValueError("Unsupported language")
        return self.config.update(
            model_provider=model_provider,
            model_endpoint=model_endpoint,
            voice_provider=voice_provider,
            preferred_language=preferred_language,
            telemetry=bool(telemetry),
        )
