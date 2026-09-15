import pytest

from core.agent_planner import AgentPlanner


def test_planner_composes_allowlisted_steps():
    plan = AgentPlanner().plan("open calculator then open https://example.com")
    assert plan.goal == "open calculator then open https://example.com"
    assert [step.action for step in plan.steps] == ["open_app", "open_url"]
    assert [step.capability for step in plan.steps] == ["windows.apps", "windows.browser"]
    assert plan.steps[0].payload == {"name": "calculator"}
    assert plan.steps[1].payload == {"url": "https://example.com"}


def test_planner_supports_folder_chain():
    plan = AgentPlanner().plan("open folder C:\\Users\\Public followed by open notepad")
    assert [step.action for step in plan.steps] == ["open_folder", "open_app"]
    assert plan.steps[0].payload["path"] == "C:\\Users\\Public"


def test_planner_rejects_unknown_action():
    with pytest.raises(ValueError, match="not mapped"):
        AgentPlanner().plan("delete everything")
