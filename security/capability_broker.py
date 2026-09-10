from dataclasses import dataclass
from enum import Enum
from typing import FrozenSet, Iterable


class CapabilityRisk(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class CapabilitySpec:
    name: str
    risk: CapabilityRisk
    description: str


@dataclass(frozen=True)
class CapabilityDecision:
    allowed: bool
    requires_confirmation: bool
    reason: str
    capability: str


CAPABILITIES: dict[str, CapabilitySpec] = {
    "android.ui": CapabilitySpec("android.ui", CapabilityRisk.LOW, "Interact with explicitly exposed Android UI actions"),
    "android.accessibility": CapabilitySpec("android.accessibility", CapabilityRisk.MEDIUM, "Use user-enabled Android accessibility capabilities"),
    "android.device_management": CapabilitySpec("android.device_management", CapabilityRisk.HIGH, "Use explicitly provisioned device-management capabilities"),
    "windows.files.read": CapabilitySpec("windows.files.read", CapabilityRisk.LOW, "Read files within the approved scope"),
    "windows.files.write": CapabilitySpec("windows.files.write", CapabilityRisk.MEDIUM, "Create or modify files within the approved scope"),
    "windows.browser": CapabilitySpec("windows.browser", CapabilityRisk.LOW, "Control an approved browser session"),
    "windows.apps": CapabilitySpec("windows.apps", CapabilityRisk.MEDIUM, "Launch or control approved desktop applications"),
    "windows.admin": CapabilitySpec("windows.admin", CapabilityRisk.HIGH, "Perform an explicitly approved administrative operation"),
    "windows.system": CapabilitySpec("windows.system", CapabilityRisk.HIGH, "Perform an explicitly approved system operation"),
}


class CapabilityBroker:
    """Deterministic capability gate; the model never receives raw OS privileges."""

    def __init__(self, granted: Iterable[str] = ()):
        self._granted: FrozenSet[str] = frozenset(granted)

    def granted(self) -> tuple[str, ...]:
        return tuple(sorted(self._granted))

    def evaluate(self, capability: str, *, confirmed: bool = False) -> CapabilityDecision:
        spec = CAPABILITIES.get(capability)
        if spec is None:
            return CapabilityDecision(False, False, "unknown capability", capability)
        if spec.risk == CapabilityRisk.BLOCKED:
            return CapabilityDecision(False, False, "capability blocked", capability)
        if capability not in self._granted:
            return CapabilityDecision(False, False, "capability not granted", capability)
        if spec.risk == CapabilityRisk.HIGH and not confirmed:
            return CapabilityDecision(False, True, "explicit confirmation required", capability)
        if spec.risk == CapabilityRisk.MEDIUM and not confirmed:
            return CapabilityDecision(False, True, "confirmation required", capability)
        return CapabilityDecision(True, False, "capability granted", capability)

    def require(self, capability: str, *, confirmed: bool = False) -> CapabilityDecision:
        return self.evaluate(capability, confirmed=confirmed)
