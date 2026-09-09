from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ConfigField:
    name: str
    label: str
    secret: bool = False
    mutable: bool = True


FIELDS = (
    ConfigField("model_provider", "Model provider"),
    ConfigField("model_endpoint", "Model endpoint"),
    ConfigField("voice_provider", "Voice provider"),
    ConfigField("preferred_language", "Preferred language"),
    ConfigField("telemetry", "Optional diagnostics"),
)


def public_config(data: dict[str, Any]) -> dict[str, Any]:
    return {field.name: data.get(field.name) for field in FIELDS if not field.secret}


def validate_config_shape(data: dict[str, Any]) -> bool:
    return all(field.name in data for field in FIELDS)
