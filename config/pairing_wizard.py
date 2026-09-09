from dataclasses import dataclass
from enum import Enum

class PairingStep(str, Enum):
    IDLE="idle"
    REVIEW="review"
    COMPLETE="complete"
    CANCELLED="cancelled"

@dataclass
class PairingWizard:
    step: PairingStep=PairingStep.IDLE
    offer_id: str|None=None
    pc_name: str|None=None
    fingerprint: str|None=None
    device_id: str|None=None

    def load_offer(self, offer_id, pc_name, fingerprint):
        if not offer_id or not pc_name or not fingerprint:
            raise ValueError("pairing offer requires identity fields")
        self.offer_id=offer_id
        self.pc_name=pc_name
        self.fingerprint=fingerprint
        self.step=PairingStep.REVIEW

    def confirm(self, device_id):
        if self.step != PairingStep.REVIEW or not device_id:
            raise ValueError("pairing confirmation invalid")
        self.device_id=device_id
        self.step=PairingStep.COMPLETE

    def cancel(self):
        self.step=PairingStep.CANCELLED
