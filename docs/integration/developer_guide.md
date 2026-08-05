# Developer Guide — Jarvis 2.0 Integration

## 1. Adding a New Automation Tool

1. Add a class to the appropriate module in `src/friday/tools/` (e.g.,
   `system_tools.py`, `desktop_tools.py`, `browser_tools.py`, `files_tools.py`,
   `media_tools.py`), or create a new `*_tools.py` module.
2. Subclass `AutomationTool` (from `friday.tools.automation._base`) or
   `BaseTool`.
3. Decorate with `@ToolRegistry.register("tool_name")`.
4. Implement:
   - `spec` property → `ToolSpec(name, description, parameters, category, ...)`
   - `execute(**params) -> ToolResult`
5. Register the module in `src/friday/tools/__init__.py` (additive `try/except`).

```python
from friday.core.registry import ToolRegistry
from friday.core.types import ToolResult
from friday.tools._stubs import ToolSpec
from friday.tools.automation._base import AutomationTool

@ToolRegistry.register("example_tool")
class ExampleTool(AutomationTool):
    tool_id = "example_tool"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="example_tool",
            description="Do an example thing.",
            parameters={"type": "object", "properties": {}},
            category="system",
        )

    def execute(self, **params):
        return self._result("Did the thing.", success=True)
```

## 2. Adding a Planner Rule

Open `src/friday/agents/automation_agent.py` and add a `(regex, tool_name,
extractor)` tuple to `_PLAN_RULES`.

```python
(r"example (regex)", "example_tool", lambda m: {"key": m.group(1)}),
```

## 3. Tool Contract

Every tool should expose (inherited from `AutomationTool` where applicable):

- `execute(**params)` — required
- `spec` — required
- `description()`, `parameters()`, `permissions()`, `status()`, `logs()`,
  `rollback()` — provided by `AutomationTool`

## 4. Testing

Follow the existing test layout:

- Tool tests: `tests/tools/test_<module>_tools.py`
- Agent tests: `tests/agents/test_automation_agent.py`

Run:

```bash
PYTHONPATH=src pytest tests/tools/test_automation_tools.py tests/agents/test_automation_agent.py -q
```

> Note: `tests/conftest.py` auto-clears registries between tests.

## 5. Conventions

- **SOLID / Clean Architecture**: tools are single-responsibility; inject
  dependencies via `execute(**params)` and the agent constructor.
- **PEP 8** + type hints (`from __future__ import annotations`).
- **Lazy imports**: import optional deps (`psutil`, `wmi`, `pycaw`) inside
  `execute()` so the package loads without them.
- **Windows-only**: guard with `is_windows()` and return a clean error otherwise.
- **Security**: set `requires_confirmation=True` for destructive actions and
  `required_capabilities=["network:fetch"]` for network tools.

## 6. Directory Reference

```
src/friday/tools/
├── automation/          # Shared base + helpers (_base.py, __init__.py)
├── system_tools.py      # battery, volume, brightness, clipboard, running_apps, ip
├── desktop_tools.py     # open_app, keyboard, mouse, close_window
├── browser_tools.py     # browser_tab, scroll, open_website, youtube_play, media_control
├── files_tools.py       # create_file, list_directory, file_search
├── media_tools.py       # get_joke, get_advice, get_weather
src/friday/agents/
└── automation_agent.py  # AutomationAgent + plan_request() planner
docs/integration/       # analysis, feature comparison, architecture, tool docs, guides
```
