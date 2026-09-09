from __future__ import annotations

from dataclasses import asdict, dataclass
from urllib.parse import urlparse
from urllib.request import Request, urlopen

@dataclass(frozen=True)
class RuntimeHealth:
    api: str
    model_endpoint: str
    voice: str
    runtime: str

class RuntimeHealthService:
    def __init__(self, model_endpoint: str = "http://127.0.0.1:11434") -> None:
        self.model_endpoint = model_endpoint

    @staticmethod
    def _is_local(endpoint: str) -> bool:
        try:
            return urlparse(endpoint).hostname in {"127.0.0.1", "localhost", "::1"}
        except ValueError:
            return False

    def check_model(self, timeout: float = 1.0) -> str:
        if not self._is_local(self.model_endpoint):
            return "configured"
        try:
            request = Request(self.model_endpoint, method="GET")
            with urlopen(request, timeout=timeout) as response:
                return "online" if 200 <= response.status < 500 else "offline"
        except Exception:
            return "offline"

    def read(self, *, api: str = "online", voice: str = "unconfigured") -> dict:
        model = self.check_model()
        runtime = "ready" if api == "online" and model in {"online", "configured"} else "degraded"
        return asdict(RuntimeHealth(api=api, model_endpoint=model, voice=voice, runtime=runtime))
