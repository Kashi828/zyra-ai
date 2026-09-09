import secrets
from .persistent_device_store import PersistentDeviceStore


class PersistentEnrollment:
    def __init__(self, store: PersistentDeviceStore):
        self.store = store

    def create_device(self, capabilities):
        device_id = "dev_" + secrets.token_urlsafe(9)
        secret = secrets.token_bytes(32)
        self.store.enroll_device(device_id, secret, capabilities)
        return device_id, secret

    def revoke(self, device_id):
        self.store.revoke_device(device_id)
