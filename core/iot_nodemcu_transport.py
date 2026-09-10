from dataclasses import dataclass
from urllib.parse import urlparse

import urllib.request
import json


ALLOWED_ACTIONS = frozenset({"status", "gpio.read", "gpio.write"})


@dataclass(frozen=True)
class NodeMCUResult:
    ok: bool
    action: str
    status_code: int
    payload: dict
    error: str = ""


class NodeMCUTransport:
    """Small allowlisted HTTP transport for a trusted NodeMCU agent.

    The transport never accepts shell/code execution actions and only talks to
    explicitly configured HTTP(S) endpoints. TLS is required for non-loopback
    endpoints when ``require_tls`` is enabled.
    """

    def __init__(self, base_url, secret=None, timeout=5.0, require_tls=True):
        parsed = urlparse(str(base_url))
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("invalid NodeMCU endpoint")
        if require_tls and parsed.hostname not in {"127.0.0.1", "localhost", "::1"} and parsed.scheme != "https":
            raise ValueError("TLS is required for non-loopback NodeMCU endpoints")
        self.base_url = str(base_url).rstrip("/")
        self.secret = secret
        self.timeout = float(timeout)
        self.require_tls = bool(require_tls)

    def request(self, action, payload=None):
        if action not in ALLOWED_ACTIONS:
            return NodeMCUResult(False, action, 403, {}, "action is not allowed")
        body = dict(payload or {})
        if action == "gpio.write":
            if "pin" not in body or "value" not in body:
                return NodeMCUResult(False, action, 400, {}, "pin and value are required")
            if not isinstance(body["pin"], int) or not isinstance(body["value"], (bool, int)):
                return NodeMCUResult(False, action, 400, {}, "invalid gpio arguments")
            body["value"] = int(bool(body["value"]))
        data = json.dumps(body).encode("utf-8")
        headers = {"Content-Type": "application/json", "X-Zyra-Device-Secret": self.secret} if self.secret else {"Content-Type": "application/json"}
        request = urllib.request.Request(
            f"{self.base_url}/v1/{action}", data=data, headers=headers, method="POST"
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
                payload = json.loads(raw) if raw else {}
                return NodeMCUResult(True, action, response.status, payload)
        except Exception as exc:
            return NodeMCUResult(False, action, 502, {}, str(exc))
