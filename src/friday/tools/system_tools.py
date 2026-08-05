"""System automation tools — battery, volume, brightness, clipboard, running apps, IP.

Extracted from PC-Automation (Battery, Set_Volume, Brightness, CheckRunningApp,
CheckIP) and jarvis-ai-assistant (Automation/Battery, Features/set_get_volume,
Features/check_running_app, Features/find_my_ip). The best implementation from
each source is unified here as first-class OpenJarvis tools.
"""

from __future__ import annotations

import platform
from typing import Any, List, Optional

from friday.core.registry import ToolRegistry
from friday.core.types import ToolResult
from friday.tools._stubs import BaseTool, ToolSpec
from friday.tools.automation._base import (
    AutomationTool,
    clipboard_get,
    clipboard_set,
    is_windows,
    run_command,
)


# ---------------------------------------------------------------------------
# Battery
# ---------------------------------------------------------------------------


@ToolRegistry.register("battery_status")
class BatteryTool(AutomationTool):
    """Report battery level, charging state, and remaining time."""

    tool_id = "battery_status"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="battery_status",
            description=(
                "Report the current battery percentage, whether the device is"
                " plugged in / charging, and estimated time remaining."
            ),
            parameters={
                "type": "object",
                "properties": {},
            },
            category="system",
        )

    def execute(self, **params: Any) -> ToolResult:
        try:
            import psutil
        except ImportError:
            return self._result(
                "psutil is not installed. Install with: pip install psutil",
                success=False,
            )
        try:
            battery = psutil.sensors_battery()
        except Exception as exc:  # noqa: BLE001
            return self._result(f"Battery error: {exc}", success=False)
        if battery is None:
            return self._result(
                "No battery detected on this device.", success=False
            )
        percent = int(battery.percent)
        plugged = battery.power_plugged
        secsleft = getattr(battery, "secsleft", None)
        time_left = ""
        if secsleft is not None and secsleft != -1 and secsleft != -2:
            mins = int(secsleft // 60)
            hours, mm = divmod(mins, 60)
            time_left = f", {hours}h {mm}m remaining"
        state = "charging" if plugged else "discharging"
        content = (
            f"Battery: {percent}% | {state}{time_left}"
        )
        return self._result(
            content,
            success=True,
            percent=percent,
            plugged=plugged,
            secsleft=secsleft,
        )


# ---------------------------------------------------------------------------
# Volume (pycaw-based, best implementation from PC-Automation)
# ---------------------------------------------------------------------------


def _get_volume_interface():
    """Return the pycaw master volume interface, or raise ImportError."""
    from ctypes import POINTER, cast

    from comtypes import CLSCTX_ALL
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

    devices = AudioUtilities.GetSpeakers()
    interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
    return cast(interface, POINTER(IAudioEndpointVolume))


@ToolRegistry.register("volume_get")
class VolumeGetTool(AutomationTool):
    """Get the current system master volume level."""

    tool_id = "volume_get"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="volume_get",
            description="Get the current system master volume as a percentage.",
            parameters={"type": "object", "properties": {}},
            category="system",
        )

    def execute(self, **params: Any) -> ToolResult:
        if not is_windows():
            return self._result(
                "Volume control is only supported on Windows.", success=False
            )
        try:
            volume = _get_volume_interface()
        except ImportError:
            return self._result(
                "pycaw/pywin32 not installed. Install with: pip install pycaw comtypes",
                success=False,
            )
        except Exception as exc:  # noqa: BLE001
            return self._result(f"Volume error: {exc}", success=False)
        try:
            level = volume.GetMasterVolumeLevelScalar() * 100
            return self._result(
                f"The device is running on {int(round(level))}% volume level.",
                success=True,
                volume=int(round(level)),
            )
        except Exception as exc:  # noqa: BLE001
            return self._result(f"Volume error: {exc}", success=False)


@ToolRegistry.register("volume_set")
class VolumeSetTool(AutomationTool):
    """Set the system master volume to a percentage."""

    tool_id = "volume_set"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="volume_set",
            description=(
                "Set the system master volume to a given percentage (0-100)."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "level": {
                        "type": "integer",
                        "description": "Volume percentage (0-100).",
                    },
                },
                "required": ["level"],
            },
            category="system",
            requires_confirmation=True,
        )

    def execute(self, **params: Any) -> ToolResult:
        level = params.get("level")
        if level is None:
            return self._result("No level provided.", success=False)
        try:
            level = int(level)
        except (TypeError, ValueError):
            return self._result(f"Invalid level: {level}", success=False)
        if not 0 <= level <= 100:
            return self._result(
                f"Volume must be between 0 and 100, got {level}.", success=False
            )
        if not is_windows():
            return self._result(
                "Volume control is only supported on Windows.", success=False
            )
        try:
            volume = _get_volume_interface()
        except ImportError:
            return self._result(
                "pycaw/pywin32 not installed. Install with: pip install pycaw comtypes",
                success=False,
            )
        except Exception as exc:  # noqa: BLE001
            return self._result(f"Volume error: {exc}", success=False)
        try:
            volume.SetMasterVolumeLevelScalar(level / 100, None)
            return self._result(
                f"Volume set to {level}%.",
                success=True,
                level=level,
            )
        except Exception as exc:  # noqa: BLE001
            return self._result(f"Volume error: {exc}", success=False)


# ---------------------------------------------------------------------------
# Brightness (WMI-based, best from PC-Automation)
# ---------------------------------------------------------------------------


def _get_brightness_wmi():
    """Return the current brightness percentage via WMI."""
    import wmi

    w = wmi.WMI(namespace="wmi")
    monitors = w.WmiMonitorBrightness()
    return int(monitors[0].CurrentBrightness)


def _set_brightness_wmi(level: int) -> None:
    import wmi

    w = wmi.WMI(namespace="wmi")
    methods = w.WmiMonitorBrightnessMethods()[0]
    methods.WmiSetBrightness(level, 0)


@ToolRegistry.register("brightness_get")
class BrightnessGetTool(AutomationTool):
    """Get the current screen brightness percentage."""

    tool_id = "brightness_get"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="brightness_get",
            description="Get the current screen brightness as a percentage.",
            parameters={"type": "object", "properties": {}},
            category="system",
        )

    def execute(self, **params: Any) -> ToolResult:
        if not is_windows():
            return self._result(
                "Brightness control is only supported on Windows.", success=False
            )
        try:
            level = _get_brightness_wmi()
            return self._result(
                f"Current brightness: {level}%.",
                success=True,
                brightness=level,
            )
        except ImportError:
            return self._result(
                "wmi not installed. Install with: pip install wmi", success=False
            )
        except Exception as exc:  # noqa: BLE001
            return self._result(f"Brightness error: {exc}", success=False)


@ToolRegistry.register("brightness_set")
class BrightnessSetTool(AutomationTool):
    """Set the screen brightness to a percentage."""

    tool_id = "brightness_set"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="brightness_set",
            description=(
                "Set the screen brightness to a given percentage (0-100)."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "level": {
                        "type": "integer",
                        "description": "Brightness percentage (0-100).",
                    },
                },
                "required": ["level"],
            },
            category="system",
            requires_confirmation=True,
        )

    def execute(self, **params: Any) -> ToolResult:
        level = params.get("level")
        if level is None:
            return self._result("No level provided.", success=False)
        try:
            level = int(level)
        except (TypeError, ValueError):
            return self._result(f"Invalid level: {level}", success=False)
        if not 0 <= level <= 100:
            return self._result(
                f"Brightness must be between 0 and 100, got {level}.",
                success=False,
            )
        if not is_windows():
            return self._result(
                "Brightness control is only supported on Windows.", success=False
            )
        try:
            _set_brightness_wmi(level)
            return self._result(
                f"Brightness set to {level}%.",
                success=True,
                level=level,
            )
        except ImportError:
            return self._result(
                "wmi not installed. Install with: pip install wmi", success=False
            )
        except Exception as exc:  # noqa: BLE001
            return self._result(f"Brightness error: {exc}", success=False)


# ---------------------------------------------------------------------------
# Clipboard
# ---------------------------------------------------------------------------


@ToolRegistry.register("clipboard_get")
class ClipboardGetTool(AutomationTool):
    """Read the current clipboard text."""

    tool_id = "clipboard_get"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="clipboard_get",
            description="Get the current clipboard text content.",
            parameters={"type": "object", "properties": {}},
            category="system",
        )

    def execute(self, **params: Any) -> ToolResult:
        text = clipboard_get()
        if not text:
            return self._result("Clipboard is empty.", success=True, text="")
        return self._result(text, success=True, text=text)


@ToolRegistry.register("clipboard_set")
class ClipboardSetTool(AutomationTool):
    """Write text to the clipboard."""

    tool_id = "clipboard_set"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="clipboard_set",
            description="Set the clipboard text to the given content.",
            parameters={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to copy to the clipboard.",
                    },
                },
                "required": ["text"],
            },
            category="system",
        )

    def execute(self, **params: Any) -> ToolResult:
        text = params.get("text", "")
        if not text:
            return self._result("No text provided.", success=False)
        clipboard_set(text)
        return self._result(
            f"Copied {len(text)} characters to the clipboard.",
            success=True,
            length=len(text),
        )


# ---------------------------------------------------------------------------
# Running apps
# ---------------------------------------------------------------------------


@ToolRegistry.register("running_apps")
class RunningAppsTool(AutomationTool):
    """List currently running applications/processes."""

    tool_id = "running_apps"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="running_apps",
            description=(
                "List the currently running applications/processes on the system."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of apps to return.",
                    },
                },
            },
            category="system",
        )

    def execute(self, **params: Any) -> ToolResult:
        try:
            import psutil
        except ImportError:
            return self._result(
                "psutil is not installed. Install with: pip install psutil",
                success=False,
            )
        limit = params.get("limit") or 50
        try:
            limit = int(limit)
        except (TypeError, ValueError):
            limit = 50
        try:
            processes = sorted(
                {p.name() for p in psutil.process_iter(["name"])}
            )
        except Exception as exc:  # noqa: BLE001
            return self._result(f"Error listing processes: {exc}", success=False)
        if not processes:
            return self._result("No running applications found.", success=True)
        shown = processes[:limit]
        content = "\n".join(f"- {name}" for name in shown)
        if len(processes) > limit:
            content += f"\n... and {len(processes) - limit} more."
        return self._result(
            content,
            success=True,
            count=len(processes),
            shown=len(shown),
        )


# ---------------------------------------------------------------------------
# IP address
# ---------------------------------------------------------------------------


@ToolRegistry.register("get_ip")
class IpTool(AutomationTool):
    """Get the public IP address of this device."""

    tool_id = "get_ip"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="get_ip",
            description="Get the public IP address of this device.",
            parameters={"type": "object", "properties": {}},
            category="system",
            required_capabilities=["network:fetch"],
        )

    def execute(self, **params: Any) -> ToolResult:
        try:
            import requests
        except ImportError:
            return self._result(
                "requests is not installed. Install with: pip install requests",
                success=False,
            )
        try:
            resp = requests.get("https://api64.ipify.org?format=json", timeout=10)
            resp.raise_for_status()
            ip = resp.json()["ip"]
            return self._result(f"Your IP address is {ip}.", success=True, ip=ip)
        except Exception as exc:  # noqa: BLE001
            return self._result(f"IP error: {exc}", success=False)


__all__ = [
    "BatteryTool",
    "BrightnessGetTool",
    "BrightnessSetTool",
    "ClipboardGetTool",
    "ClipboardSetTool",
    "IpTool",
    "RunningAppsTool",
    "VolumeGetTool",
    "VolumeSetTool",
]
