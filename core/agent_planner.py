from __future__ import annotations

from dataclasses import asdict, dataclass
import re


@dataclass(frozen=True)
class AgentStep:
    index: int
    action: str
    payload: dict
    capability: str


@dataclass(frozen=True)
class AgentPlan:
    goal: str
    steps: tuple[AgentStep, ...]


class AgentPlanner:
    """Turns natural-language beta goals into a bounded, allowlisted action plan.

    Planning is deliberately deterministic in beta: the planner can compose only
    the actions already exposed by the Windows command registry. It never emits
    arbitrary shell commands or tool names.
    """

    _SEPARATOR = re.compile(r"\s+(?:and then|then|followed by)\s+", re.IGNORECASE)

    def plan(self, goal: str) -> AgentPlan:
        text = str(goal or "").strip()
        if not text:
            raise ValueError("goal is required")

        parts = [part.strip(" .") for part in self._SEPARATOR.split(text) if part.strip()]
        if not parts:
            raise ValueError("goal is required")

        steps = tuple(self._parse_step(part, index) for index, part in enumerate(parts))
        return AgentPlan(goal=text, steps=steps)

    def _parse_step(self, text: str, index: int) -> AgentStep:
        urls = re.findall(r"https?://[^\s]+", text)
        if urls:
            return AgentStep(index, "open_url", {"url": urls[0].rstrip(".,)" )}, "windows.browser")

        folder = re.match(r"^(?:open|show)\s+(?:folder|directory)\s+(.+)$", text, re.IGNORECASE)
        if folder:
            return AgentStep(index, "open_folder", {"path": folder.group(1).strip().strip('"')}, "windows.files.read")

        app = re.match(r"^(?:open|launch|start)\s+(.+)$", text, re.IGNORECASE)
        if app:
            return AgentStep(index, "open_app", {"name": app.group(1).strip().strip('"')}, "windows.apps")

        raise ValueError(f"goal step is not mapped to a safe action: {text}")

    @staticmethod
    def to_dict(plan: AgentPlan) -> dict:
        return {"goal": plan.goal, "steps": [asdict(step) for step in plan.steps]}
