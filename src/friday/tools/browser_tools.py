"""Browser automation tools — web open, tab control, YouTube, media keys.

Extracted from PC-Automation (Web_Automation, Tab_Automation,
Youtube_Automation, PlayMusic) and jarvis-ai-assistant (Automation/Web_Open,
Automation/tab_automation, Automation/Play_Music_YT, Automation/Youtube_play_back).
Unified as first-class OpenJarvis tools.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from friday.core.registry import ToolRegistry
from friday.core.types import ToolResult
from friday.tools._stubs import ToolSpec
from friday.tools.automation._base import AutomationTool

# ---------------------------------------------------------------------------
# Open website
# ---------------------------------------------------------------------------


@ToolRegistry.register("open_website")
class OpenWebsiteTool(AutomationTool):
    """Open a website in the default browser."""

    tool_id = "open_website"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="open_website",
            description=(
                "Open a website in the default browser. Accepts a URL or a"
                " bare domain name (e.g. 'example.com' or 'youtube.com')."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL or domain to open.",
                    },
                },
                "required": ["url"],
            },
            category="browser",
            required_capabilities=["network:fetch"],
        )

    def execute(self, **params: Any) -> ToolResult:
        url = params.get("url", "")
        if not url:
            return self._result("No URL provided.", success=False)
        url = url.strip()
        if "://" not in url:
            url = "https://" + url

        # SSRF check via webbrowser (no server-side fetch, but keep guard)
        try:
            import webbrowser

            webbrowser.open(url)
            return self._result(
                f"Opened {url} in the default browser.", success=True, url=url
            )
        except Exception as exc:  # noqa: BLE001
            return self._result(f"Failed to open website: {exc}", success=False)


# ---------------------------------------------------------------------------
# Web search
# ---------------------------------------------------------------------------


@ToolRegistry.register("web_search_open")
class WebSearchOpenTool(AutomationTool):
    """Search the web and open the browser to the results."""

    tool_id = "web_search_open"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="web_search_open",
            description=(
                "Search the web for a query and open the results in the"
                " default browser."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query.",
                    },
                },
                "required": ["query"],
            },
            category="browser",
            required_capabilities=["network:fetch"],
        )

    def execute(self, **params: Any) -> ToolResult:
        query = params.get("query", "")
        if not query:
            return self._result("No query provided.", success=False)
        try:
            import pywhatkit

            pywhatkit.search(query)
            return self._result(
                f"Searching for '{query}' in the browser.", success=True
            )
        except ImportError:
            return self._result(
                "pywhatkit is not installed. Install with: pip install pywhatkit",
                success=False,
            )
        except Exception as exc:  # noqa: BLE001
            return self._result(f"Search error: {exc}", success=False)


# ---------------------------------------------------------------------------
# Browser tab controls (via pyautogui hotkeys)
# ---------------------------------------------------------------------------


@ToolRegistry.register("browser_tab")
class BrowserTabTool(AutomationTool):
    """Control browser tabs (open, close, switch, refresh, zoom, etc.)."""

    tool_id = "browser_tab"

    _ACTIONS = {
        "new_tab": ["ctrl", "t"],
        "close_tab": ["ctrl", "w"],
        "next_tab": ["ctrl", "tab"],
        "previous_tab": ["ctrl", "shift", "tab"],
        "refresh": ["ctrl", "r"],
        "zoom_in": ["ctrl", "+"],
        "zoom_out": ["ctrl", "-"],
        "history": ["ctrl", "h"],
        "bookmarks": ["ctrl", "b"],
        "back": ["alt", "left"],
        "forward": ["alt", "right"],
        "dev_tools": ["ctrl", "shift", "i"],
        "full_screen": ["f11"],
        "private_window": ["ctrl", "shift", "n"],
        "menu": ["alt", "f"],
    }

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="browser_tab",
            description=(
                "Control the browser via keyboard shortcuts. Actions: "
                + ", ".join(sorted(self._ACTIONS.keys()))
                + "."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": sorted(self._ACTIONS.keys()),
                        "description": "Browser action to perform.",
                    },
                },
                "required": ["action"],
            },
            category="browser",
        )

    def execute(self, **params: Any) -> ToolResult:
        action = params.get("action", "")
        keys = self._ACTIONS.get(action)
        if keys is None:
            return self._result(
                f"Unknown browser action: {action}. Valid: {', '.join(self._ACTIONS)}",
                success=False,
            )
        try:
            import pyautogui as gui

            gui.hotkey(*keys)
            return self._result(
                f"Performed browser action: {action}.", success=True, action=action
            )
        except ImportError:
            return self._result(
                "pyautogui is not installed. Install with: pip install pyautogui",
                success=False,
            )
        except Exception as exc:  # noqa: BLE001
            return self._result(f"Browser action error: {exc}", success=False)


# ---------------------------------------------------------------------------
# Media playback control
# ---------------------------------------------------------------------------


@ToolRegistry.register("media_control")
class MediaControlTool(AutomationTool):
    """Control media playback (play/pause/next/volume)."""

    tool_id = "media_control"

    _ACTIONS = {
        "play_pause": ["space"],
        "next": ["media_next"],
        "previous": ["media_prev"],
        "play": ["space"],
        "pause": ["space"],
        "stop": ["space"],
        "volume_up": ["volumeup"],
        "volume_down": ["volumedown"],
        "mute": ["volumemute"],
    }

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="media_control",
            description=(
                "Control media playback. Actions: "
                + ", ".join(sorted(self._ACTIONS.keys()))
                + "."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": sorted(self._ACTIONS.keys()),
                        "description": "Media action to perform.",
                    },
                },
                "required": ["action"],
            },
            category="media",
        )

    def execute(self, **params: Any) -> ToolResult:
        action = params.get("action", "")
        keys = self._ACTIONS.get(action)
        if keys is None:
            return self._result(
                f"Unknown media action: {action}. Valid: {', '.join(self._ACTIONS)}",
                success=False,
            )
        try:
            import pyautogui as gui

            gui.press(*keys)
            return self._result(
                f"Performed media action: {action}.", success=True, action=action
            )
        except ImportError:
            return self._result(
                "pyautogui is not installed. Install with: pip install pyautogui",
                success=False,
            )
        except Exception as exc:  # noqa: BLE001
            return self._result(f"Media error: {exc}", success=False)


# ---------------------------------------------------------------------------
# YouTube playback
# ---------------------------------------------------------------------------


@ToolRegistry.register("youtube_play")
class YouTubePlayTool(AutomationTool):
    """Play a song on YouTube."""

    tool_id = "youtube_play"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="youtube_play",
            description=(
                "Play a song or video on YouTube in the browser. Provide the"
                " song name or search query."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "song": {
                        "type": "string",
                        "description": "Song name or search query.",
                    },
                },
                "required": ["song"],
            },
            category="media",
            required_capabilities=["network:fetch"],
            requires_confirmation=True,
        )

    def execute(self, **params: Any) -> ToolResult:
        song = params.get("song", "")
        if not song:
            return self._result("No song provided.", success=False)
        try:
            import pywhatkit

            pywhatkit.playonyt(song)
            return self._result(
                f"Playing '{song}' on YouTube.", success=True, song=song
            )
        except ImportError:
            return self._result(
                "pywhatkit is not installed. Install with: pip install pywhatkit",
                success=False,
            )
        except Exception as exc:  # noqa: BLE001
            return self._result(f"YouTube error: {exc}", success=False)


__all__ = [
    "BrowserTabTool",
    "MediaControlTool",
    "OpenWebsiteTool",
    "WebSearchOpenTool",
    "YouTubePlayTool",
]
