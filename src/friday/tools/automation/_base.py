"""Shared base and helpers for automation tools.

These tools extend the OpenJarvis ``BaseTool`` ABC with a lightweight
``description()``/``parameters()`` convenience layer (backed by ``ToolSpec``)
and cross-platform safe imports using lazy dependency resolution.
"""

from __future__ import annotations

import platform
import subprocess
import sys
from typing import Any, Dict, List, Optional

from friday.core.types import ToolResult
from friday.tools._stubs import BaseTool, ToolSpec

# ---------------------------------------------------------------------------
# Platform detection
# ---------------------------------------------------------------------------


def is_windows() -> bool:
    """Return ``True`` when running on Windows."""
    return platform.system().lower() == "windows"


def is_macos() -> bool:
    """Return ``True`` when running on macOS."""
    return platform.system().lower() == "darwin"


def is_linux() -> bool:
    """Return ``True`` when running on Linux."""
    return platform.system().lower() == "linux"


# ---------------------------------------------------------------------------
# Lazy dependency helpers
# ---------------------------------------------------------------------------

_IMPORTED = {}


def lazy_import(name: str) -> Any:
    """Import *name* once and cache the module (safe when unavailable)."""
    if name in _IMPORTED:
        return _IMPORTED[name]
    try:
        mod = __import__(name)
        _IMPORTED[name] = mod
    except Exception as exc:  # noqa: BLE001 - any import failure is non-fatal
        _IMPORTED[name] = exc
    return _IMPORTED[name]


def _dep_error(dep: str, extra: str = "") -> str:
    """Return a helpful message when a required dependency is missing."""
    base = f"'{dep}' is not installed."
    if extra:
        return f"{base} {extra}"
    return f"{base} Install it with: pip install {dep}"


# ---------------------------------------------------------------------------
# Clipboard helpers (cross-platform)
# ---------------------------------------------------------------------------


def clipboard_get() -> str:
    """Return the current clipboard text (best-effort, cross-platform)."""
    if is_windows():
        try:
            import win32clipboard  # type: ignore

            win32clipboard.OpenClipboard()
            try:
                if win32clipboard.IsClipboardFormatAvailable(
                    win32clipboard.CF_UNICODETEXT
                ):
                    return win32clipboard.GetClipboardData(
                        win32clipboard.CF_UNICODETEXT
                    )
            finally:
                win32clipboard.CloseClipboard()
        except Exception:
            pass
    try:
        import pyperclip  # type: ignore

        return pyperclip.paste()
    except Exception:
        return ""


def clipboard_set(text: str) -> None:
    """Set the clipboard text (best-effort, cross-platform)."""
    if is_windows():
        try:
            import win32clipboard  # type: ignore

            win32clipboard.OpenClipboard()
            try:
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(
                    win32clipboard.CF_UNICODETEXT, text
                )
            finally:
                win32clipboard.CloseClipboard()
            return
        except Exception:
            pass
    try:
        import pyperclip  # type: ignore

        pyperclip.copy(text)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Shared command runner
# ---------------------------------------------------------------------------


def run_command(
    args: List[str],
    *,
    timeout: int = 30,
    capture: bool = True,
) -> subprocess.CompletedProcess:
    """Run a command and return the ``CompletedProcess``."""
    return subprocess.run(
        args,
        capture_output=capture,
        text=True,
        timeout=timeout,
        check=False,
    )


# ---------------------------------------------------------------------------
# AutomationTool base class
# ---------------------------------------------------------------------------


class AutomationTool(BaseTool):
    """Base class for automation tools.

    Subclasses provide ``spec`` (via ``ToolSpec``) and ``execute``. This base
    adds convenience ``description()`` and ``parameters()`` accessors that
    mirror the ``ToolSpec`` fields, plus ``status()``/``logs()`` helpers to
    satisfy the tool contract required by the integration spec.
    """

    tool_id: str = ""
    is_local: bool = True

    def description(self) -> str:
        """Return the tool description."""
        return self.spec.description

    def parameters(self) -> Dict[str, Any]:
        """Return the tool JSON-schema parameters."""
        return self.spec.parameters

    def permissions(self) -> List[str]:
        """Required capabilities for this tool (RBAC)."""
        return list(self.spec.required_capabilities)

    def status(self) -> Dict[str, Any]:
        """Return the tool's availability status."""
        return {
            "name": self.spec.name,
            "available": True,
            "platform": platform.system().lower(),
            "category": self.spec.category,
        }

    def logs(self) -> str:
        """Return a short log summary (no-op by default)."""
        return ""

    def rollback(self) -> Optional[ToolResult]:
        """Attempt to undo the last action where supported.

        Subclasses override this when a meaningful rollback exists. Returns
        ``None`` by default to indicate no rollback is available.
        """
        return None

    def _result(
        self,
        content: str,
        *,
        success: bool = True,
        **metadata: Any,
    ) -> ToolResult:
        """Build a ``ToolResult`` with the tool name and metadata."""
        return ToolResult(
            tool_name=self.spec.name,
            content=content,
            success=success,
            metadata=metadata,
        )


__all__ = [
    "AutomationTool",
    "clipboard_get",
    "clipboard_set",
    "is_linux",
    "is_macos",
    "is_windows",
    "lazy_import",
    "run_command",
]
