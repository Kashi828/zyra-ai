from dataclasses import dataclass
from pathlib import Path

from security.persistent_device_store import PersistentDeviceStore
from security.persistent_authorization_gateway import PersistentAuthorizationGateway


@dataclass
class RuntimeSecurity:
    store: PersistentDeviceStore
    authorization: PersistentAuthorizationGateway


def build_runtime_security(db_path="data/zyra_security.sqlite3") -> RuntimeSecurity:
    path = Path(db_path)
    store = PersistentDeviceStore(path)
    return RuntimeSecurity(
        store=store,
        authorization=PersistentAuthorizationGateway(store),
    )
