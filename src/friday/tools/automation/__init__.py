"""Automation tools package — extracted from PC-Automation and jarvis-ai-assistant.

These tools expose desktop, browser, media, and system automation capabilities
as first-class OpenJarvis ``BaseTool`` implementations, routed through the
unified ``ToolExecutor``.
"""

from __future__ import annotations

from friday.tools.automation._base import (
    AutomationTool,
    clipboard_set,
    clipboard_get,
    is_windows,
)

__all__ = [
    "AutomationTool",
    "clipboard_get",
    "clipboard_set",
    "is_windows",
]
