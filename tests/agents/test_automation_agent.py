"""Tests for the AutomationAgent (Planner → Tool Router → Tool workflow)."""

from __future__ import annotations

import importlib
import sys
from unittest.mock import MagicMock, patch

from friday.agents.automation_agent import AutomationAgent, plan_request
from friday.core.registry import AgentRegistry, ToolRegistry

# Import modules so registries populate.
import friday.agents.automation_agent  # noqa: F401
import friday.tools.system_tools  # noqa: F401
import friday.tools.desktop_tools  # noqa: F401
import friday.tools.browser_tools  # noqa: F401
import friday.tools.files_tools  # noqa: F401
import friday.tools.media_tools  # noqa: F401


def _reload_all() -> None:
    """Reload tool and agent modules to re-trigger registrations."""
    for mod_name in list(sys.modules):
        if mod_name.startswith("friday.tools.") and not mod_name.endswith("_stubs"):
            try:
                importlib.reload(sys.modules[mod_name])
            except Exception:
                pass
    for mod_name in list(sys.modules):
        if mod_name.startswith("friday.agents.") and not mod_name.endswith("_stubs"):
            try:
                importlib.reload(sys.modules[mod_name])
            except Exception:
                pass


def _make_agent(mock_engine):
    """Build an AutomationAgent with a mock engine and all tools."""
    _reload_all()
    tools = []
    for name in ToolRegistry.keys():
        try:
            tools.append(ToolRegistry.create(name))
        except Exception:
            pass
    return AutomationAgent(
        mock_engine,
        "test-model",
        tools=tools,
        interactive=False,
    )


# ---------------------------------------------------------------------------
# Planner tests
# ---------------------------------------------------------------------------


def test_plan_battery_request():
    plans = plan_request("what is my battery percentage")
    assert any(p["name"] == "battery_status" for p in plans)


def test_plan_volume_set_request():
    plans = plan_request("set volume to 50")
    assert any(p["name"] == "volume_set" for p in plans)
    vol = next(p for p in plans if p["name"] == "volume_set")
    assert vol["arguments"]["level"] == 50


def test_plan_open_website_request():
    plans = plan_request("open the website example.com")
    assert any(p["name"] == "open_website" for p in plans)


def test_plan_open_app_request():
    plans = plan_request("open notepad please")
    assert any(p["name"] == "open_app" for p in plans)


def test_plan_joke_request():
    plans = plan_request("tell me a joke")
    assert any(p["name"] == "get_joke" for p in plans)


def test_plan_weather_request():
    plans = plan_request("what is the weather in London")
    assert any(p["name"] == "get_weather" for p in plans)


def test_plan_no_match_returns_empty():
    plans = plan_request("this is not an automation command at all")
    assert plans == []


# ---------------------------------------------------------------------------
# Agent tests
# ---------------------------------------------------------------------------


def test_automation_agent_registered():
    _reload_all()
    assert AgentRegistry.contains("automation")


def test_automation_agent_runs_battery(mock_engine):
    import psutil

    agent = _make_agent(mock_engine())
    with patch.object(psutil, "sensors_battery") as mock_sb:
        mock_battery = type(
            "B", (), {"percent": 80.0, "power_plugged": True, "secsleft": -1}
        )()
        mock_sb.return_value = mock_battery
        result = agent.run("what is my battery percentage")
        assert result.turns >= 1
        assert any(tr.tool_name == "battery_status" for tr in result.tool_results)
        assert any(tr.success for tr in result.tool_results)


def test_automation_agent_runs_create_file(mock_engine, tmp_path):
    agent = _make_agent(mock_engine())
    target = tmp_path / "created.txt"
    result = agent.run(f"create a file at {target}")
    # create_file requires confirmation; with interactive=False it is denied.
    # So the tool result should exist but may be unsuccessful. At minimum the
    # agent should have routed to the create_file tool.
    assert any(tr.tool_name == "create_file" for tr in result.tool_results)


def test_automation_agent_no_match_uses_engine(mock_engine):
    agent = _make_agent(mock_engine())
    result = agent.run("hello there, how are you?")
    assert result.tool_results == []
    assert result.content == "Hello!"  # from mock_engine


def test_automation_agent_executes_through_router(mock_engine):
    """Verify the agent routes through ToolExecutor, not direct module calls."""
    agent = _make_agent(mock_engine())
    with patch.object(agent._executor, "execute") as mock_exec:
        mock_exec.return_value = MagicMock(
            tool_name="get_joke",
            content="mock joke",
            success=True,
        )
        result = agent.run("tell me a joke")
        assert any(
            tr.tool_name == "get_joke" for tr in result.tool_results
        )
        mock_exec.assert_called()
