from core.runtime_security import build_runtime_security
from security.api_auth_guard import ApiAuthGuard
from security.api_rate_limiter import SlidingWindowRateLimiter
from security.session_service import SessionService
from security.session_rotation_store import SessionRotationStore
from security.emergency_stop import EmergencyStop


class ProductionSecurityContext:
    def __init__(self, db_path="data/zyra_security.sqlite3"):
        self.runtime = build_runtime_security(db_path)
        self.emergency_stop = EmergencyStop()
        self.runtime.authorization.emergency_stop = self.emergency_stop
        self.api_rate_limiter = SlidingWindowRateLimiter(limit=60, window_seconds=60)
        self.api_auth = ApiAuthGuard(self.runtime.store, self.api_rate_limiter)
        self.refresh_store = SessionRotationStore(self.runtime.store.db_path)
        self.sessions = SessionService(self.runtime.store, self.refresh_store)

    @property
    def store(self):
        return self.runtime.store

    @property
    def authorization(self):
        return self.runtime.authorization


def build_production_security(db_path="data/zyra_security.sqlite3"):
    return ProductionSecurityContext(db_path)
