# Jarvis 2.0 — Architecture

## 1. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           User  (Voice / CLI / GUI / API)            │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────┐
│                        Agent Layer                                   │
│   AutomationAgent (Planner → Tool Router → Tool)                     │
│   + other agents (simple, react, openhands, deep_research, ...)      │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────────────┐
│                        Tool Router (ToolExecutor)                    │
│   • capability/RBAC checks   • confirmation callbacks                │
│   • taint checks             • timeouts                              │
│   • event bus (TOOL_CALL_START/END)                                  │
└───────────────────────────────┬─────────────────────────────────────┘
        ┌──────────────┬────────┴──────────┬──────────────┐
        ▼              ▼                   ▼              ▼
  ┌──────────┐ ┌────────────┐ ┌──────────────┐ ┌──────────────────┐
  │System    │ │Desktop     │ │Browser       │ │Media & Files     │
  │Tools     │ │Tools       │ │Tools         │ │Tools             │
  └──────────┘ └────────────┘ └──────────────┘ └──────────────────┘
```

## 2. Tool System

Every capability is a **tool** implementing the `BaseTool` ABC:

- `spec` → `ToolSpec` (name, description, parameters JSON Schema, category,
  required capabilities, confirmation flag, timeouts)
- `execute(**params) -> ToolResult`
- Registered via `@ToolRegistry.register("name")`
- Auto-discovered by importing `friday.tools`

The `ToolExecutor` is the single **tool router**. Agents never call automation
modules directly.

## 3. Automation Agent Workflow

```
User Request
    ↓
Planner (plan_request: keyword/pattern matching → tool calls)
    ↓
AutomationAgent (sequence intent → tool calls)
    ↓
Tool Router (ToolExecutor)
    ↓
Correct Tool (execute)
    ↓
Response (ToolResult → AgentResult)
```

- If no rule matches, the agent falls back to a plain LLM generation.
- Sensitive tools require confirmation.
- Windows-only tools fail gracefully on other platforms.

## 4. Module Map

| Module             | Tools Registered                                                                                                                             |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------- |
| `system_tools.py`  | `battery_status`, `volume_get`, `volume_set`, `brightness_get`, `brightness_set`, `clipboard_get`, `clipboard_set`, `running_apps`, `get_ip` |
| `desktop_tools.py` | `open_app`, `keyboard_hotkey`, `keyboard_type`, `mouse_click`, `close_window`                                                                |
| `browser_tools.py` | `browser_tab`, `scroll`, `open_website`, `youtube_play`, `web_search_open`, `media_control`                                                  |
| `files_tools.py`   | `create_file`, `list_directory`, `file_search`                                                                                               |
| `media_tools.py`   | `get_joke`, `get_advice`, `get_weather`                                                                                                      |

## 5. Dependencies & Injection

- **Dependency Injection**: tools receive all inputs via `execute(**params)`;
  the agent receives its `engine`, `model`, `tools`, `bus`, and policy via
  constructor injection.
- **SOLID**: each tool is a single-responsibility class; the ABC gives an
  interface (I); the registry gives open/closed extension (O); the router
  delegates (L); the executor depends on abstractions (D).
- **Clean Architecture**: tools sit at the boundary; the agent layer orchestrates;
  core types (`ToolResult`, `ToolCall`) are shared primitives.

## 6. Security

- RBAC: `required_capabilities` (e.g., `network:fetch`) enforced by the router.
- Confirmation: destructive tools require a confirmation callback.
- Platform guards: WMI/pycaw tools return clean errors off-Windows.
- No direct shell execution of user input.
