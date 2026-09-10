from dataclasses import dataclass


@dataclass(frozen=True)
class PersistentEcosystemDevice:
    device_id: str
    device_type: str
    display_name: str
    capabilities: frozenset[str]
    online: bool
    last_seen: int
    revoked: bool
    endpoint: str = ""


class PersistentEcosystemRegistry:
    """Synchronizes the in-memory coordinator from durable trusted-device state."""

    def __init__(self, store):
        self.store = store

    def register(self, device_id, device_type, display_name="", online=True, endpoint=""):
        self.store.upsert_ecosystem_device(device_id, device_type, display_name, online, endpoint)
        return self.get(device_id)

    def set_online(self, device_id, online):
        self.store.set_ecosystem_online(device_id, online)
        return self.get(device_id)

    def get(self, device_id):
        item = self.store.get_ecosystem_device(device_id)
        return self._convert(item) if item else None

    def devices(self):
        return tuple(self._convert(item) for item in self.store.list_ecosystem_devices())

    @staticmethod
    def _convert(item):
        return PersistentEcosystemDevice(
            device_id=item["device_id"],
            device_type=item["device_type"],
            display_name=item["display_name"],
            capabilities=item["capabilities"],
            online=item["online"],
            last_seen=item["last_seen"],
            revoked=item["revoked"],
            endpoint=item.get("endpoint", ""),
        )
