from dataclasses import dataclass
from typing import Any, Mapping, Protocol
from urllib.parse import urlparse


ALLOWED_ACTIONS = frozenset({"status", "gpio.read", "gpio.write"})


@dataclass(frozen=True)
class NodeMCUDevice:
    device_id: str
    endpoint: str
    capabilities: frozenset[str]


class NodeMCUTransport(Protocol):
    def request(self, endpoint: str, action: str, payload: Mapping[str, Any]) -> Mapping[str, Any]: ...


def validate_endpoint(endpoint: str) -> str:
    parsed = urlparse(endpoint)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("NodeMCU endpoint must be an enrolled HTTP(S) endpoint")
    return endpoint.rstrip("/")


class NodeMCUAdapter:
    """Small allowlisted adapter for an enrolled NodeMCU/ESP device."""

    def __init__(self, device: NodeMCUDevice, transport: NodeMCUTransport):
        self.device = device
        self.transport = transport
        self.endpoint = validate_endpoint(device.endpoint)

    def execute(self, action: str, payload: Mapping[str, Any] | None = None) -> Mapping[str, Any]:
        if action not in ALLOWED_ACTIONS:
            raise PermissionError("NodeMCU action is not allowed")
        return self.transport.request(self.endpoint, action, payload or {})
