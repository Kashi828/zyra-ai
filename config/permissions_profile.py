from dataclasses import dataclass, field

DEFAULT_CAPABILITIES = {
    "pc.apps",
    "pc.files",
    "pc.web",
}

@dataclass
class PermissionProfile:
    device_id: str
    capabilities: set[str] = field(default_factory=set)
    require_confirmation: set[str] = field(default_factory=set)
    blocked: set[str] = field(default_factory=set)

    def allows(self, capability: str) -> bool:
        return capability in self.capabilities and capability not in self.blocked

    def needs_confirmation(self, capability: str) -> bool:
        return capability in self.require_confirmation

    def block(self, capability: str) -> None:
        self.blocked.add(capability)

    def grant(self, capability: str) -> None:
        self.capabilities.add(capability)
        self.blocked.discard(capability)
