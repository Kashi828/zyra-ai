from __future__ import annotations
import os

def get_release_info() -> dict[str, object]:
    return {"product":"ZYRA AI","channel":os.environ.get("ZYRA_RELEASE_CHANNEL","beta"),"supported_channels":["beta","stable"],"installer_target":"win32-x64-nsis"}
