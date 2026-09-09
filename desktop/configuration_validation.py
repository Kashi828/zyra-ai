from __future__ import annotations

from desktop.configuration_service import ConfigurationService


class ConfigurationValidationService:
    def __init__(self, service: ConfigurationService | None = None) -> None:
        self.service = service or ConfigurationService()

    def validate(self) -> dict[str, object]:
        data = self.service.read()
        errors: list[str] = []
        if data.get("model_provider") not in self.service.ALLOWED_MODELS:
            errors.append("Unsupported model provider")
        if not self.service._valid_endpoint(str(data.get("model_endpoint", ""))):
            errors.append("Invalid model endpoint")
        if data.get("voice_provider") not in self.service.ALLOWED_VOICE:
            errors.append("Unsupported voice provider")
        if data.get("preferred_language") not in self.service.ALLOWED_LANGUAGES:
            errors.append("Unsupported language")
        return {"valid": not errors, "errors": errors,
                "model_provider": data.get("model_provider"),
                "voice_provider": data.get("voice_provider"),
                "preferred_language": data.get("preferred_language")}
