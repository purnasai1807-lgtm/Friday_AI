# Feature Comparison — PC-Automation vs jarvis-ai-assistant vs OpenJarvis

For every overlapping feature, the best implementation is selected and unified into
OpenJarvis. Duplicate implementations are **never** retained.

## Voice

| Aspect     | OpenJarvis                                                           | jarvis-ai-assistant           |
| ---------- | -------------------------------------------------------------------- | ----------------------------- |
| STT        | `friday/speech` (faster-whisper, openai)                             | `NetHyTechSTT/listen.py`      |
| TTS        | `friday/speech/tts.py` (cartesia, kokoro, openai)                    | `TextToSpeech/Fast_DF_TTS.py` |
| **Winner** | **OpenJarvis** — registry-based, multiple backends, production-grade | —                             |

**Decision:** Keep OpenJarvis `friday/speech`. The `text_to_speech` tool is reused.

## Browser Automation

| Aspect     | OpenJarvis                         | PC-Automation      | jarvis-ai-assistant         |
| ---------- | ---------------------------------- | ------------------ | --------------------------- |
| Approach   | Playwright engine                  | pyautogui hotkeys  | pyautogui + selenium        |
| Tabs       | `browser.py` (navigate/click/type) | `Tab_Automation`   | `Automation/tab_automation` |
| **Winner** | **OpenJarvis** (Playwright)        | pyautogui fallback | —                           |

**Decision:** Keep OpenJarvis `browser.py` (Playwright). Extract the pyautogui
hotkey fallbacks into `browser_tools.py` (`browser_tab`, `scroll`) for non-headless
desktop control.

## Desktop Automation

| Aspect     | OpenJarvis | PC-Automation                        | jarvis-ai-assistant               |
| ---------- | ---------- | ------------------------------------ | --------------------------------- |
| Open App   | —          | `Open_App` (pyautogui)               | `Automation/open_App` (pyautogui) |
| Keyboard   | —          | —                                    | automations                       |
| Mouse      | —          | —                                    | automations                       |
| Window     | —          | —                                    | `close` (alt+f4)                  |
| **Winner** | —          | **PC-Automation** (simpler, correct) | —                                 |

**Decision:** Extract into `desktop_tools.py` (`open_app`, `keyboard_hotkey`,
`keyboard_type`, `mouse_click`, `close_window`).

## Window Management / Clipboard / File Operations

| Feature        | Source                     | Final Tool                        |
| -------------- | -------------------------- | --------------------------------- |
| Clipboard      | (new)                      | `clipboard_get` / `clipboard_set` |
| Create File    | PC-Automation `CreateFile` | `create_file`                     |
| List Directory | (new)                      | `list_directory`                  |
| File Search    | (new)                      | `file_search`                     |

## Volume / Brightness / Battery

| Feature    | PC-Automation        | jarvis-ai-assistant       | Final Tool                          |
| ---------- | -------------------- | ------------------------- | ----------------------------------- |
| Volume     | `Set_Volume` (pycaw) | `Features/set_get_volume` | `volume_get` / `volume_set`         |
| Brightness | `Brightness` (WMI)   | `Features/set_br`         | `brightness_get` / `brightness_set` |
| Battery    | `Battery` (psutil)   | `Automation/Battery`      | `battery_status`                    |

**Decision:** Use the **PC-Automation** implementations (WMI brightness, pycaw
volume, psutil battery) — cleaner and more robust.

## Application Launcher / Keyboard / Mouse / Browser / Plugins / Logging / Config / Memory / Conversation / Tool Routing

| Feature               | Provider                                                       |
| --------------------- | -------------------------------------------------------------- |
| App launcher          | `desktop_tools.open_app`                                       |
| Keyboard / Mouse      | `desktop_tools`                                                |
| Browser               | `browser_tools` + existing `browser.py`                        |
| Plugins               | OpenJarvis `SkillRegistry` (retained)                          |
| Logging / Config      | OpenJarvis `core/config.py` (retained)                         |
| Memory / Conversation | OpenJarvis `friday/tools/storage` + `core/types.py` (retained) |
| Tool Routing          | OpenJarvis `ToolExecutor` (retained)                           |

## Automation Agent

A new `AutomationAgent` (registered as `"automation"`) implements the
**Planner → Tool Router → Tool** workflow. `plan_request()` maps natural-language
intents to tool calls; the agent never calls automation modules directly —
everything goes through the `ToolExecutor` router.

## Conclusion

All duplicate functionality is collapsed into a single canonical tool per feature,
all owned by OpenJarvis. No duplicate implementations remain.
