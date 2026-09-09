import json
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class OnboardingState:
    completed: bool = False
    ai_provider: str = "local"
    pairing_started: bool = False
    permissions_reviewed: bool = False

class OnboardingStore:
    def __init__(self, path: str = "zyra_onboarding.json"):
        self.path = Path(path)

    def load(self) -> OnboardingState:
        if not self.path.exists():
            return OnboardingState()
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return OnboardingState(**data)
        except (OSError, ValueError, TypeError):
            return OnboardingState()

    def save(self, state: OnboardingState) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(".tmp")
        temp.write_text(json.dumps(asdict(state), indent=2), encoding="utf-8")
        temp.replace(self.path)

    def complete(self, ai_provider: str = "local") -> OnboardingState:
        state = self.load()
        state.ai_provider = ai_provider
        state.permissions_reviewed = True
        state.completed = True
        self.save(state)
        return state
