"""Desktop automation tools — app launcher, keyboard, mouse, scroll, window mgmt.

Extracted from PC-Automation (Open_App, Scrole_System, Tab_Automation) and
jarvis-ai-assistant (Automation/open_App, Automation/scrool_system,
Automation/tab_automation). Unified as first-class OpenJarvis tools.
"""

from __future__ import annotations

import subprocess
import time
from typing import Any, Dict, List, Optional

from friday.core.registry import ToolRegistry
from friday.core.types import ToolResult
from friday.tools._stubs import ToolSpec
from friday.tools.automation._base import AutomationTool, run_command


# ---------------------------------------------------------------------------
# App launcher
# ---------------------------------------------------------------------------

_APP_ALIASES: Dict[str, str] = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "paint": "mspaint.exe",
    "cmd": "cmd.exe",
    "command prompt": "cmd.exe",
    "terminal": "cmd.exe",
    "file explorer": "explorer.exe",
    "explorer": "explorer.exe",
    "task manager": "taskmgr.exe",
    "control panel": "control.exe",
    "settings": "ms-settings:",
    "chrome": "chrome.exe",
    "google chrome": "chrome.exe",
    "firefox": "firefox.exe",
    "edge": "msedge.exe",
    "word": "winword.exe",
    "excel": "excel.exe",
    "powerpoint": "powerpnt.exe",
    "notepad++": "notepad++.exe",
}


@ToolRegistry.register("open_app")
class OpenAppTool(AutomationTool):
    """Launch an application by name."""

    tool_id = "open_app"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="open_app",
            description=(
                "Launch an application on the desktop by name (e.g. 'notepad',"
                " 'calculator', 'chrome'). Falls back to a Windows search."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "app": {
                        "type": "string",
                        "description": "Name of the application to open.",
                    },
                },
                "required": ["app"],
            },
            category="desktop",
            requires_confirmation=True,
        )

    def execute(self, **params: Any) -> ToolResult:
        app = params.get("app", "")
        if not app:
            return self._result("No app name provided.", success=False)
        name = app.strip().lower()
        exe = _APP_ALIASES.get(name, name)

        # Try direct launch first
        try:
            subprocess.Popen(
                exe,
                shell=(exe == name),  # shell only for unknown names
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return self._result(
                f"Opened {app}.", success=True, app=app, method="direct"
            )
        except Exception as exc:  # noqa: BLE001
            # Fall back to Windows search (pyautogui)
            try:
                import pyautogui as gui

                gui.press("win")
                time.sleep(0.2)
                gui.write(app)
                time.sleep(0.2)
                gui.press("enter")
                return self._result(
                    f"Opened {app} via search.",
                    success=True,
                    app=app,
                    method="search",
                )
            except Exception as exc2:  # noqa: BLE001
                return self._result(
                    f"Failed to open '{app}': {exc} / {exc2}", success=False
                )


# ---------------------------------------------------------------------------
# Scroll
# ---------------------------------------------------------------------------


@ToolRegistry.register("scroll")
class ScrollTool(AutomationTool):
    """Scroll the active window up or down."""

    tool_id = "scroll"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="scroll",
            description=(
                "Scroll the active window. Use 'up'/'down' and an optional"
                " number of clicks/notches."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "direction": {
                        "type": "string",
                        "enum": ["up", "down"],
                        "description": "Scroll direction.",
                    },
                    "clicks": {
                        "type": "integer",
                        "description": "Number of scroll notches (default 3).",
                    },
                },
                "required": ["direction"],
            },
            category="desktop",
        )

    def execute(self, **params: Any) -> ToolResult:
        direction = params.get("direction", "down")
        clicks = params.get("clicks", 3)
        try:
            clicks = int(clicks)
        except (TypeError, ValueError):
            clicks = 3
        if direction not in ("up", "down"):
            return self._result(
                f"Invalid direction: {direction}. Use 'up' or 'down'.",
                success=False,
            )
        try:
            import pyautogui as gui

            amount = clicks if direction == "down" else -clicks
            gui.scroll(amount)
            return self._result(
                f"Scrolled {direction} {clicks} notches.",
                success=True,
                direction=direction,
                clicks=clicks,
            )
        except ImportError:
            return self._result(
                "pyautogui is not installed. Install with: pip install pyautogui",
                success=False,
            )
        except Exception as exc:  # noqa: BLE001
            return self._result(f"Scroll error: {exc}", success=False)


# ---------------------------------------------------------------------------
# Keyboard
# ---------------------------------------------------------------------------


@ToolRegistry.register("keyboard_hotkey")
class KeyboardHotkeyTool(AutomationTool):
    """Send a keyboard hotkey combination."""

    tool_id = "keyboard_hotkey"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="keyboard_hotkey",
            description=(
                "Send a keyboard hotkey combination, e.g. "
                "['ctrl', 'c'] to copy, ['alt', 'f4'] to close a window."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "keys": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of key names to press together.",
                    },
                },
                "required": ["keys"],
            },
            category="desktop",
            requires_confirmation=True,
        )

    def execute(self, **params: Any) -> ToolResult:
        keys = params.get("keys")
        if not keys or not isinstance(keys, list) or not keys:
            return self._result("No keys provided.", success=False)
        try:
            import pyautogui as gui

            gui.hotkey(*[str(k) for k in keys])
            return self._result(
                f"Pressed hotkey: {'+'.join(map(str, keys))}.",
                success=True,
                keys=keys,
            )
        except ImportError:
            return self._result(
                "pyautogui is not installed. Install with: pip install pyautogui",
                success=False,
            )
        except Exception as exc:  # noqa: BLE001
            return self._result(f"Hotkey error: {exc}", success=False)


@ToolRegistry.register("keyboard_type")
class KeyboardTypeTool(AutomationTool):
    """Type text using the keyboard."""

    tool_id = "keyboard_type"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="keyboard_type",
            description="Type the given text using the keyboard.",
            parameters={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to type.",
                    },
                    "interval": {
                        "type": "number",
                        "description": "Seconds between keystrokes (default 0.05).",
                    },
                },
                "required": ["text"],
            },
            category="desktop",
            requires_confirmation=True,
        )

    def execute(self, **params: Any) -> ToolResult:
        text = params.get("text", "")
        if not text:
            return self._result("No text provided.", success=False)
        interval = params.get("interval", 0.05)
        try:
            import pyautogui as gui

            gui.write(text, interval=float(interval))
            return self._result(
                f"Typed {len(text)} characters.", success=True, length=len(text)
            )
        except ImportError:
            return self._result(
                "pyautogui is not installed. Install with: pip install pyautogui",
                success=False,
            )
        except Exception as exc:  # noqa: BLE001
            return self._result(f"Type error: {exc}", success=False)


# ---------------------------------------------------------------------------
# Mouse
# ---------------------------------------------------------------------------


@ToolRegistry.register("mouse_move")
class MouseMoveTool(AutomationTool):
    """Move the mouse cursor to screen coordinates."""

    tool_id = "mouse_move"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="mouse_move",
            description="Move the mouse cursor to the given screen coordinates.",
            parameters={
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "X coordinate."},
                    "y": {"type": "integer", "description": "Y coordinate."},
                },
                "required": ["x", "y"],
            },
            category="desktop",
            requires_confirmation=True,
        )

    def execute(self, **params: Any) -> ToolResult:
        x = params.get("x")
        y = params.get("y")
        if x is None or y is None:
            return self._result("Both x and y are required.", success=False)
        try:
            import pyautogui as gui

            gui.moveTo(int(x), int(y))
            return self._result(
                f"Moved mouse to ({x}, {y}).", success=True, x=x, y=y
            )
        except ImportError:
            return self._result(
                "pyautogui is not installed. Install with: pip install pyautogui",
                success=False,
            )
        except Exception as exc:  # noqa: BLE001
            return self._result(f"Mouse error: {exc}", success=False)


@ToolRegistry.register("mouse_click")
class MouseClickTool(AutomationTool):
    """Click the mouse at the current position or at coordinates."""

    tool_id = "mouse_click"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="mouse_click",
            description=(
                "Click the mouse. Optionally provide x/y to move first."
                " button: 'left', 'right', or 'middle'."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "x": {"type": "integer", "description": "Optional X coordinate."},
                    "y": {"type": "integer", "description": "Optional Y coordinate."},
                    "button": {
                        "type": "string",
                        "enum": ["left", "right", "middle"],
                        "description": "Which button to click (default 'left').",
                    },
                    "clicks": {
                        "type": "integer",
                        "description": "Number of clicks (default 1).",
                    },
                },
            },
            category="desktop",
            requires_confirmation=True,
        )

    def execute(self, **params: Any) -> ToolResult:
        x = params.get("x")
        y = params.get("y")
        button = params.get("button", "left")
        clicks = params.get("clicks", 1)
        try:
            import pyautogui as gui

            if x is not None and y is not None:
                gui.moveTo(int(x), int(y))
            gui.click(clicks=int(clicks), button=button)
            return self._result(
                f"Clicked {button} ({clicks} time(s)).",
                success=True,
                button=button,
                clicks=clicks,
            )
        except ImportError:
            return self._result(
                "pyautogui is not installed. Install with: pip install pyautogui",
                success=False,
            )
        except Exception as exc:  # noqa: BLE001
            return self._result(f"Click error: {exc}", success=False)


# ---------------------------------------------------------------------------
# Window management
# ---------------------------------------------------------------------------


@ToolRegistry.register("close_window")
class CloseWindowTool(AutomationTool):
    """Close the active window."""

    tool_id = "close_window"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="close_window",
            description="Close the currently active window (Alt+F4).",
            parameters={"type": "object", "properties": {}},
            category="desktop",
            requires_confirmation=True,
        )

    def execute(self, **params: Any) -> ToolResult:
        try:
            import pyautogui as gui

            gui.hotkey("alt", "f4")
            return self._result("Closed active window.", success=True)
        except ImportError:
            return self._result(
                "pyautogui is not installed. Install with: pip install pyautogui",
                success=False,
            )
        except Exception as exc:  # noqa: BLE001
            return self._result(f"Close error: {exc}", success=False)


__all__ = [
    "CloseWindowTool",
    "KeyboardHotkeyTool",
    "KeyboardTypeTool",
    "MouseClickTool",
    "MouseMoveTool",
    "OpenAppTool",
    "ScrollTool",
]
