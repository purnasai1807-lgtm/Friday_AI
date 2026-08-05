# Jarvis 2.0 Integration — Repository Analysis Report

## 1. Overview

This report documents the analysis of three repositories prior to integration:

| Repository              | Role                                                  |
| ----------------------- | ----------------------------------------------------- |
| **OpenJarvis (Friday)** | Primary project — the integration target / foundation |
| **PC-Automation**       | Source of desktop & system automation features        |
| **jarvis-ai-assistant** | Source of voice, media, and assistant features        |

OpenJarvis remains the primary project. The other two repositories are treated as
**source references** — their best reusable functionality is extracted and refactored
into OpenJarvis as first-class tools.

## 2. Folder Structures

### OpenJarvis (Friday)

```
src/friday/
├── agents/          # Agent implementations (BaseAgent, ToolUsingAgent, orchestrators)
├── channels/        # Messaging channels (Telegram, Discord, Slack, ...)
├── cli/             # Command-line interface
├── connectors/      # Data connectors (Gmail, notion, obsidian, ...)
├── core/            # Config, registry, events, types
├── engine/          # Inference engines (ollama, litellm, cloud, ...)
├── mcp/             # Model Context Protocol server/client
├── security/        # Capabilities, guardrails, taint, SSRF checks
├── speech/          # STT/TTS backends
├── tools/           # Tool system (BaseTool, ToolExecutor, ToolSpec)
│   └── storage/     # Memory backends (sqlite, faiss, bm25, ...)
├── server/          # FastAPI server
├── sessions/        # Session management
├── skills/          # Skill manifests
```

### PC-Automation

```
PC-Automation-main/
├── Battery/          # Battery monitoring
├── Brightness/       # Brightness control (WMI)
├── CheckIP/          # IP lookup
├── CheckRunningApp/  # Running processes
├── CreateFile/       # File creation
├── GetAdvice/        # Advice API
├── GetJokes/         # Jokes API
├── Open_App/         # App launcher (pyautogui)
├── PlayMusic/        # Music playback
├── Scrole_System/    # Scroll control
├── Set_Volume/       # Volume control (pycaw)
├── Tab_Automation/   # Browser tab shortcuts
├── Web_Automation/   # Web open
├── Youtube_Automation/ # YouTube media
```

### jarvis-ai-assistant

```
jarvis-ai-assistant-main/
├── Automation/       # Automation_Brain, open_App, Web_Open, Play_Music_YT, ...
├── Brain/            # Assistant brain
├── Data/             # Dialog data
├── Features/         # battery, volume, brightness, jokes, advice, ...
├── NetHyTechSTT/     # Speech-to-text
├── Real_Time/        # Google real-time
├── TextToImage/      # Image generation
├── TextToSpeech/     # Fast TTS
├── Time_Operations/  # Time & alerts
├── Vision/           # Vision models
├── Weather_Check/    # Weather scraping
├── Whatsapp_automation/ # WhatsApp automation
```

## 3. Architecture

- **OpenJarvis** uses a clean, registry-based architecture: `BaseTool` ABC +
  `ToolSpec` metadata + `ToolRegistry.register()` decorator + `ToolExecutor`
  dispatch. Agents use `BaseAgent`/`ToolUsingAgent` + `AgentRegistry`. This is
  the superior architecture and is retained as the foundation.
- **PC-Automation** and **jarvis-ai-assistant** are monolithic scripts with
  functions called directly, no registry, no dependency injection, no tool
  abstraction, and heavy use of blocking `input()` calls.

## 4. Dependencies

| Repo                | Key deps                                                                |
| ------------------- | ----------------------------------------------------------------------- |
| OpenJarvis          | click, openai, httpx, rich, fastapi, pydantic, psutil, pyautogui, pycaw |
| PC-Automation       | pyautogui, requests, beautifulsoup4, psutil, pywhatkit, pycaw           |
| jarvis-ai-assistant | pyautogui, pywhatkit, pycaw, selenium, winotify, playsound              |

The dependency overlap (pyautogui, psutil, pycaw, pywhatkit, requests) reinforces
the decision to unify into a single dependency set owned by OpenJarvis.

## 5. Entry Points

- **OpenJarvis**: `friday.cli:main` (console script) + `friday.server` (FastAPI).
- **PC-Automation**: `main.py` (blocking REPL loop).
- **jarvis-ai-assistant**: `jarvis.py` (voice-driven REPL loop).

## 6. Services / Utilities / Modules

### Voice modules

- **jarvis-ai-assistant**: `NetHyTechSTT/listen.py`, `TextToSpeech/Fast_DF_TTS.py`.
  Merged into OpenJarvis `friday/speech` (already present, superior).

### Automation modules

- **PC-Automation**: Battery, Brightness, Volume, Open_App, Scroll, Tab, Web, YouTube.
- **jarvis-ai-assistant**: Automation/_ (Open_App, Web_Open, Play_Music_YT, ...).
  Extracted into OpenJarvis `src/friday/tools/_\_tools.py`.

### Browser modules / Desktop modules / Memory / Plugins / GUI / APIs

- OpenJarvis already provides `browser.py`, `friday/tools/storage/*`, a plugin
  registry, a Tauri dashboard (`frontend/`, `desktop/`), and FastAPI + MCP servers.
  These are retained as-is.

## 7. Identified Issues

### Duplicate code / functionality

The following features existed in **multiple** repositories and were unified:

| Feature     | PC-Automation      | jarvis-ai                    | OpenJarvis (final)                  |
| ----------- | ------------------ | ---------------------------- | ----------------------------------- |
| Battery     | Battery/Battery.py | Automation/Battery.py        | `battery_status`                    |
| Volume      | Set_Volume         | Features/set_get_volume      | `volume_get` / `volume_set`         |
| Brightness  | Brightness         | Features/set_br              | `brightness_get` / `brightness_set` |
| Open App    | Open_App           | Automation/open_App          | `open_app`                          |
| Tab         | Tab_Automation     | Automation/tab_automation    | `browser_tab`                       |
| Scroll      | Scrole_System      | Automation/scrool_system     | `scroll`                            |
| YouTube     | Youtube_Automation | Automation/Youtube_play_back | `youtube_play`                      |
| Create File | CreateFile         | Features/create_file         | `create_file`                       |
| IP          | CheckIP            | Features/find_my_ip          | `get_ip`                            |
| Running App | CheckRunningApp    | Features/check_running_app   | `running_apps`                      |
| Jokes       | GetJokes           | Features/get_jokes           | `get_joke`                          |
| Advice      | GetAdvice          | Features/get_advice          | `get_advice`                        |
| Weather     | —                  | Weather_Check                | `get_weather`                       |

### Unused / broken / missing

- **PC-Automation** `myenv/` contains a full vendored virtualenv — not used, excluded.
- **PC-Automation** `Data/`, `speaker_health/`, `Microphone_Health/` are empty or
  stubs.
- Blocking `input()` calls in both source repos are unsuitable for an agent-driven
  architecture; replaced with parameterized tool `execute(**params)`.
- Missing deps in source repos (e.g., `fuzzywuzzy` in PC-Automation) are dropped in
  favor of OpenJarvis's regex/rule planner.

### Circular imports

None introduced. New tool modules import only from `friday.core.*` and
`friday.tools.automation._base`, which is acyclic.

### Security issues addressed

- **Confirmation gating**: sensitive tools (`volume_set`, `brightness_set`,
  `create_file`, `open_app`, `close_window`) set `requires_confirmation=True`.
- **Capability/RBAC**: network tools require `network:fetch` capability.
- **Windows-only guards**: WMI/pycaw tools return a clean error on non-Windows.
- No direct shell execution of user text.

## 8. Decision Summary

- **Primary project**: OpenJarvis (Friday). Unchanged architecture.
- **Best implementation per feature**: Taken from whichever source had the most
  robust, cross-cutting implementation (e.g., WMI brightness from PC-Automation,
  weather scraping from jarvis-ai-assistant).
- **No duplicate implementations retained**: every feature has exactly one tool.
- **Imported folders kept in place** as source references (not executed).
