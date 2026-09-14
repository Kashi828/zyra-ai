from dataclasses import dataclass
from typing import Any, Mapping

from core.iot_nodemcu import NodeMCUAdapter


ACTION_CAPABILITIES = {
    "status": "iot.telemetry",
    "gpio.read": "iot.telemetry",
    "gpio.write": "iot.gpio",
}


@dataclass(frozen=True)
class NodeMCUCommandResult:
    ok: bool
    action: str
    message: str
    payload: Mapping[str, Any]


class NodeMCUCommandBridge:
    """Capability-aware runtime bridge for an enrolled NodeMCU device."""

    def __init__(self, adapter: NodeMCUAdapter):
        self.adapter = adapter

    def execute(self, action: str, payload: Mapping[str, Any] | None = None, capabilities=()):
        capability = ACTION_CAPABILITIES.get(action)
        if capability is None:
            return NodeMCUCommandResult(False, action, "unsupported NodeMCU action", {})
        if capability not in set(capabilities):
            return NodeMCUCommandResult(False, action, "missing NodeMCU capability", {})
        try:
            result = self.adapter.execute(action, payload or {})
        except (PermissionError, ValueError) as exc:
            return NodeMCUCommandResult(False, action, str(exc), {})
        if isinstance(result, Mapping):
            ok = bool(result.get("ok", False))
            return NodeMCUCommandResult(ok, action, "NodeMCU command completed" if ok else "NodeMCU command failed", dict(result))
        return NodeMCUCommandResult(False, action, "invalid NodeMCU response", {})
