from dataclasses import dataclass
from typing import Iterable

from security.capability_broker import CapabilityBroker


@dataclass(frozen=True)
class EcosystemDevice:
    device_id: str
    device_type: str
    capabilities: frozenset[str]
    online: bool = True


@dataclass(frozen=True)
class RouteDecision:
    allowed: bool
    source_device_id: str
    target_device_id: str
    capability: str
    reason: str


class EcosystemCoordinator:
    """Routes work between explicitly trusted ZYRA devices without granting global OS access."""

    def __init__(self):
        self._devices: dict[str, EcosystemDevice] = {}

    def register_device(
        self,
        device_id: str,
        device_type: str,
        capabilities: Iterable[str],
        *,
        online: bool = True,
    ) -> EcosystemDevice:
        if not device_id:
            raise ValueError("device_id is required")
        if not device_type:
            raise ValueError("device_type is required")
        device = EcosystemDevice(
            device_id=device_id,
            device_type=device_type,
            capabilities=frozenset(capabilities),
            online=bool(online),
        )
        self._devices[device_id] = device
        return device

    def unregister_device(self, device_id: str) -> None:
        self._devices.pop(device_id, None)

    def set_online(self, device_id: str, online: bool) -> EcosystemDevice:
        device = self._devices.get(device_id)
        if device is None:
            raise KeyError(device_id)
        updated = EcosystemDevice(
            device.device_id,
            device.device_type,
            device.capabilities,
            bool(online),
        )
        self._devices[device_id] = updated
        return updated

    def devices(self) -> tuple[EcosystemDevice, ...]:
        return tuple(sorted(self._devices.values(), key=lambda item: item.device_id))

    def get_device(self, device_id: str) -> EcosystemDevice | None:
        return self._devices.get(device_id)

    def route(
        self,
        source_device_id: str,
        target_device_id: str,
        capability: str,
    ) -> RouteDecision:
        source = self._devices.get(source_device_id)
        target = self._devices.get(target_device_id)
        if source is None:
            return RouteDecision(False, source_device_id, target_device_id, capability, "source device is not registered")
        if target is None:
            return RouteDecision(False, source_device_id, target_device_id, capability, "target device is not registered")
        if not source.online:
            return RouteDecision(False, source_device_id, target_device_id, capability, "source device is offline")
        if not target.online:
            return RouteDecision(False, source_device_id, target_device_id, capability, "target device is offline")

        decision = CapabilityBroker(target.capabilities).evaluate(capability, confirmed=False)
        if not decision.allowed:
            reason = decision.reason
            if decision.requires_confirmation:
                reason = "target capability requires confirmation"
            return RouteDecision(False, source_device_id, target_device_id, capability, reason)

        return RouteDecision(True, source_device_id, target_device_id, capability, "route authorized")

    def snapshot(self) -> dict:
        return {
            "devices": [
                {
                    "device_id": item.device_id,
                    "device_type": item.device_type,
                    "capabilities": sorted(item.capabilities),
                    "online": item.online,
                }
                for item in self.devices()
            ]
        }
