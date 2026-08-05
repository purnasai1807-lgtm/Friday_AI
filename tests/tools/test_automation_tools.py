"""Tests for the integrated automation tools (system, browser, files, media)."""

from __future__ import annotations

import importlib
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

from friday.core.registry import ToolRegistry

# Import modules so @ToolRegistry.register decorators run.
import friday.tools.system_tools  # noqa: F401
import friday.tools.desktop_tools  # noqa: F401
import friday.tools.browser_tools  # noqa: F401
import friday.tools.files_tools  # noqa: F401
import friday.tools.media_tools  # noqa: F401


def _reload_tool_modules() -> None:
    """Reload tool modules to re-trigger @register decorators (after clean)."""
    for mod_name in list(sys.modules):
        if mod_name.startswith("friday.tools.") and not mod_name.endswith("_stubs"):
            try:
                importlib.reload(sys.modules[mod_name])
            except Exception:
                pass


def _get_tool(name: str):
    _reload_tool_modules()
    return ToolRegistry.create(name)


# ---------------------------------------------------------------------------
# System tools
# ---------------------------------------------------------------------------


def test_battery_status_tool_registered():
    _reload_tool_modules()
    assert ToolRegistry.contains("battery_status")
    tool = ToolRegistry.create("battery_status")
    assert tool.spec.name == "battery_status"
    assert tool.spec.category == "system"


def test_battery_status_execute():
    import psutil

    with patch.object(psutil, "sensors_battery") as mock_sb:
        mock_battery = type(
            "B", (), {"percent": 75.0, "power_plugged": True, "secsleft": -1}
        )()
        mock_sb.return_value = mock_battery
        tool = _get_tool("battery_status")
        result = tool.execute()
        assert result.success is True
        assert "75%" in result.content
        assert "charging" in result.content


def test_volume_get_and_set_registered():
    _reload_tool_modules()
    assert ToolRegistry.contains("volume_get")
    assert ToolRegistry.contains("volume_set")


def test_brightness_get_and_set_registered():
    _reload_tool_modules()
    assert ToolRegistry.contains("brightness_get")
    assert ToolRegistry.contains("brightness_set")


def test_clipboard_get_and_set_registered():
    _reload_tool_modules()
    assert ToolRegistry.contains("clipboard_get")
    assert ToolRegistry.contains("clipboard_set")


def test_clipboard_set_execute():
    tool = _get_tool("clipboard_set")
    result = tool.execute(text="hello world")
    assert result.success is True
    assert "length" in result.metadata


def test_running_apps_registered():
    _reload_tool_modules()
    assert ToolRegistry.contains("running_apps")


def test_get_ip_registered():
    _reload_tool_modules()
    assert ToolRegistry.contains("get_ip")


# ---------------------------------------------------------------------------
# Desktop tools
# ---------------------------------------------------------------------------


def test_open_app_registered():
    _reload_tool_modules()
    assert ToolRegistry.contains("open_app")


def test_open_app_execute_validates():
    tool = _get_tool("open_app")
    result = tool.execute(app="")
    assert result.success is False
    assert "No app name" in result.content


def test_scroll_registered():
    _reload_tool_modules()
    assert ToolRegistry.contains("scroll")


def test_scroll_invalid_direction():
    tool = _get_tool("scroll")
    result = tool.execute(direction="sideways")
    assert result.success is False
    assert "Invalid direction" in result.content


def test_keyboard_tools_registered():
    _reload_tool_modules()
    assert ToolRegistry.contains("keyboard_hotkey")
    assert ToolRegistry.contains("keyboard_type")


def test_mouse_tools_registered():
    _reload_tool_modules()
    assert ToolRegistry.contains("mouse_move")
    assert ToolRegistry.contains("mouse_click")


def test_close_window_registered():
    _reload_tool_modules()
    assert ToolRegistry.contains("close_window")


# ---------------------------------------------------------------------------
# Browser tools
# ---------------------------------------------------------------------------


def test_open_website_registered():
    _reload_tool_modules()
    assert ToolRegistry.contains("open_website")


def test_open_website_no_url():
    tool = _get_tool("open_website")
    result = tool.execute(url="")
    assert result.success is False


def test_web_search_open_registered():
    _reload_tool_modules()
    assert ToolRegistry.contains("web_search_open")


def test_browser_tab_registered():
    _reload_tool_modules()
    assert ToolRegistry.contains("browser_tab")


def test_browser_tab_unknown_action():
    tool = _get_tool("browser_tab")
    result = tool.execute(action="definitely_not_a_real_action")
    assert result.success is False
    assert "Unknown browser action" in result.content


def test_media_control_registered():
    _reload_tool_modules()
    assert ToolRegistry.contains("media_control")


def test_youtube_play_registered():
    _reload_tool_modules()
    assert ToolRegistry.contains("youtube_play")


# ---------------------------------------------------------------------------
# Files tools
# ---------------------------------------------------------------------------


def test_create_file_registered():
    _reload_tool_modules()
    assert ToolRegistry.contains("create_file")


def test_create_file_execute(tmp_path: Path):
    tool = _get_tool("create_file")
    target = tmp_path / "nested" / "hello.txt"
    result = tool.execute(path=str(target), content="hello")
    assert result.success is True
    assert target.exists()
    assert target.read_text() == "hello"


def test_create_file_no_path():
    tool = _get_tool("create_file")
    result = tool.execute(path="")
    assert result.success is False


def test_list_directory_registered():
    _reload_tool_modules()
    assert ToolRegistry.contains("list_directory")


def test_list_directory_execute(tmp_path: Path):
    (tmp_path / "a.txt").write_text("a")
    (tmp_path / "folder").mkdir()
    tool = _get_tool("list_directory")
    result = tool.execute(path=str(tmp_path))
    assert result.success is True
    assert "a.txt" in result.content
    assert "folder" in result.content


def test_read_file_content_registered():
    _reload_tool_modules()
    assert ToolRegistry.contains("read_file_content")


def test_read_file_content_execute(tmp_path: Path):
    target = tmp_path / "sample.txt"
    target.write_text("content here")
    tool = _get_tool("read_file_content")
    result = tool.execute(path=str(target))
    assert result.success is True
    assert result.content == "content here"


# ---------------------------------------------------------------------------
# Media tools
# ---------------------------------------------------------------------------


def test_get_joke_registered():
    _reload_tool_modules()
    assert ToolRegistry.contains("get_joke")


def test_get_joke_execute():
    tool = _get_tool("get_joke")
    with patch("friday.tools.media_tools._fetch_json") as mock_fetch:
        mock_fetch.return_value = {"joke": "Why did the chicken cross the road?"}
        result = tool.execute()
        assert result.success is True
        assert "chicken" in result.content


def test_get_advice_registered():
    _reload_tool_modules()
    assert ToolRegistry.contains("get_advice")


def test_get_advice_execute():
    tool = _get_tool("get_advice")
    with patch("friday.tools.media_tools._fetch_json") as mock_fetch:
        mock_fetch.return_value = {"slip": {"advice": "Take time to rest."}}
        result = tool.execute()
        assert result.success is True
        assert "rest" in result.content


def test_get_weather_registered():
    _reload_tool_modules()
    assert ToolRegistry.contains("get_weather")


def test_get_weather_no_location():
    tool = _get_tool("get_weather")
    result = tool.execute(location="")
    assert result.success is False
