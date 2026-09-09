class CapabilityAuthorizer:
    def __init__(self, profiles=None):
        self.profiles = profiles or {}

    def set_capabilities(self, device_id: str, capabilities):
        self.profiles[device_id] = set(capabilities)

    def allows(self, device_id: str, capability: str) -> bool:
        return capability in self.profiles.get(device_id, set())

    def require(self, device_id: str, capability: str):
        if not self.allows(device_id, capability):
            raise PermissionError("device lacks required capability")
