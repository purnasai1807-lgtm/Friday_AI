"""File system automation tools — create files, list/search directories.

Extracted from PC-Automation (CreateFile) and jarvis-ai-assistant
(Features/create_file). Unified as first-class OpenJarvis tools.
"""

from __future__ import annotations

import os
from typing import Any, List, Optional

from friday.core.registry import ToolRegistry
from friday.core.types import ToolResult
from friday.tools._stubs import ToolSpec
from friday.tools.automation._base import AutomationTool


@ToolRegistry.register("create_file")
class CreateFileTool(AutomationTool):
    """Create a new file at the given path."""

    tool_id = "create_file"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="create_file",
            description=(
                "Create a new file at the given path. Optionally write content"
                " to it. Creates parent directories as needed."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute path of the file to create.",
                    },
                    "content": {
                        "type": "string",
                        "description": "Optional content to write to the file.",
                    },
                },
                "required": ["path"],
            },
            category="files",
            requires_confirmation=True,
        )

    def execute(self, **params: Any) -> ToolResult:
        path = params.get("path", "")
        content = params.get("content", "")
        if not path:
            return self._result("No file path provided.", success=False)
        path = os.path.abspath(os.path.expanduser(path))
        try:
            parent = os.path.dirname(path)
            if parent:
                os.makedirs(parent, exist_ok=True)
            mode = "w" if content else "x"
            with open(path, mode, encoding="utf-8") as f:
                if content:
                    f.write(content)
            created = os.path.exists(path)
            summary = f"Created file: {path}"
            if content:
                summary += f" ({len(content)} chars written)"
            return self._result(
                summary,
                success=True,
                path=path,
                created=created,
                size=os.path.getsize(path),
            )
        except FileExistsError:
            return self._result(
                f"File already exists: {path}", success=False, path=path
            )
        except Exception as exc:  # noqa: BLE001
            return self._result(f"Failed to create file: {exc}", success=False)


@ToolRegistry.register("list_directory")
class ListDirectoryTool(AutomationTool):
    """List the contents of a directory."""

    tool_id = "list_directory"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="list_directory",
            description="List the files and folders in a directory.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Directory to list (default: current working dir).",
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "List recursively (default false).",
                    },
                },
            },
            category="files",
        )

    def execute(self, **params: Any) -> ToolResult:
        path = params.get("path") or os.getcwd()
        recursive = params.get("recursive", False)
        path = os.path.abspath(os.path.expanduser(path))
        if not os.path.isdir(path):
            return self._result(f"Not a directory: {path}", success=False)
        try:
            if not recursive:
                items = sorted(os.listdir(path))
                lines = []
                for name in items:
                    full = os.path.join(path, name)
                    kind = "dir" if os.path.isdir(full) else "file"
                    lines.append(f"[{kind}] {name}")
                return self._result(
                    "\n".join(lines) if lines else "(empty directory)",
                    success=True,
                    count=len(items),
                )
            else:
                lines = []
                count = 0
                for root, dirs, files in os.walk(path):
                    level = root.replace(path, "").count(os.sep)
                    indent = "  " * level
                    lines.append(f"{indent}{os.path.basename(root) or '/'}/")
                    for f in files:
                        lines.append(f"{indent}  {f}")
                        count += 1
                return self._result(
                    "\n".join(lines),
                    success=True,
                    count=count,
                )
        except Exception as exc:  # noqa: BLE001
            return self._result(f"List error: {exc}", success=False)


@ToolRegistry.register("read_file_content")
class ReadFileContentTool(AutomationTool):
    """Read the text content of a file."""

    tool_id = "read_file_content"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="read_file_content",
            description=(
                "Read the text content of a file. Optionally limit the maximum"
                " number of characters returned."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Absolute path of the file to read.",
                    },
                    "max_chars": {
                        "type": "integer",
                        "description": "Maximum characters to return (default 5000).",
                    },
                },
                "required": ["path"],
            },
            category="files",
        )

    def execute(self, **params: Any) -> ToolResult:
        path = params.get("path", "")
        max_chars = params.get("max_chars", 5000)
        if not path:
            return self._result("No file path provided.", success=False)
        path = os.path.abspath(os.path.expanduser(path))
        if not os.path.isfile(path):
            return self._result(f"Not a file: {path}", success=False)
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            truncated = False
            if max_chars and len(content) > int(max_chars):
                content = content[: int(max_chars)]
                truncated = True
            return self._result(
                content,
                success=True,
                path=path,
                truncated=truncated,
                length=len(content),
            )
        except Exception as exc:  # noqa: BLE001
            return self._result(f"Read error: {exc}", success=False)


__all__ = [
    "CreateFileTool",
    "ListDirectoryTool",
    "ReadFileContentTool",
]
