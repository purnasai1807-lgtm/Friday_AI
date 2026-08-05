# Migration Guide — PC-Automation & jarvis-ai-assistant → OpenJarvis

This guide explains how functionality from **PC-Automation** and
**jarvis-ai-assistant** was migrated into **OpenJarvis**, and how to keep using it.

## 1. What Was Migrated

All reusable functionality was extracted and refactored into first-class
OpenJarvis tools under `src/friday/tools/`. The source repositories remain in the
repo as **references** and are **not executed** at runtime.

| Old location                                       | OpenJarvis tool                     |
| -------------------------------------------------- | ----------------------------------- |
| `PC-Automation/Battery/Battery.py`                 | `battery_status`                    |
| `PC-Automation/Set_Volume`                         | `volume_get` / `volume_set`         |
| `PC-Automation/Brightness`                         | `brightness_get` / `brightness_set` |
| `PC-Automation/Open_App`                           | `open_app`                          |
| `PC-Automation/Tab_Automation`                     | `browser_tab`                       |
| `PC-Automation/Scrole_System`                      | `scroll`                            |
| `PC-Automation/CheckIP`                            | `get_ip`                            |
| `PC-Automation/CheckRunningApp`                    | `running_apps`                      |
| `PC-Automation/CreateFile`                         | `create_file`                       |
| `PC-Automation/GetJokes`                           | `get_joke`                          |
| `PC-Automation/GetAdvice`                          | `get_advice`                        |
| `jarvis-ai-assistant/Automation/open_App`          | `open_app`                          |
| `jarvis-ai-assistant/Automation/Youtube_play_back` | `media_control`                     |
| `jarvis-ai-assistant/Features/*`                   | `system_tools` / `desktop_tools`    |
| `jarvis-ai-assistant/Weather_Check`                | `get_weather`                       |

## 2. Behavioral Changes

1. **No blocking `input()`.** Old scripts prompted interactively; the new tools
   accept parameters via `execute(**params)`.
2. **No direct function calls.** Logic is dispatched through the `ToolExecutor`
   router, which adds RBAC, confirmation, taint checks, and timeouts.
3. **Windows-only guarded.** Brightness/volume tools return a clean error message
   on non-Windows rather than crashing.
4. **Confirmation prompts.** Destructive actions (`volume_set`, `brightness_set`,
   `create_file`, `open_app`, `close_window`) require a confirmation callback.

## 3. Example: Old → New

**Old (PC-Automation main.py):**

```python
from Battery.Battery import *
from Data.data import command_phrases

def Auto_Brain(cmd):
    for phrase, func in command_phrases.items():
        if fuzz.ratio(cmd.lower(), phrase.lower()) >= 85:
            func()
```

**New (OpenJarvis):**

```python
from friday.agents.automation_agent import AutomationAgent, plan_request

plans = plan_request("check battery percentage")
# -> [{'name': 'battery_status', 'arguments': {}}]
```

## 4. Deleting Redundant Code

Duplicate implementations were **not** deleted until the unified tool was verified
via the test suite (`tests/tools/test_automation_tools.py`,
`tests/agents/test_automation_agent.py`). The original source repos are preserved
as references per the integration requirements.

## 5. Backward Compatibility

No existing OpenJarvis module was modified except additive imports in
`src/friday/tools/__init__.py` and `src/friday/agents/__init__.py`. All prior
functionality (voice, dashboard, plugins, memory, conversation, configuration)
continues to work unchanged.
