# Setup Guide — Jarvis 2.0

## 1. Prerequisites

- Python **3.10+** (recommended 3.11/3.12)
- `uv` (recommended) or `pip`
- Windows recommended for full desktop/brightness/volume tooling
  (other platforms work but some tools degrade gracefully)

## 2. Install the Project

### Using uv (recommended)

```bash
uv sync --extra tools-automation
```

### Using pip

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[tools-automation]"
```

> The `tools-automation` extra pulls in the automation dependencies
> (`psutil`, `pyautogui`, `pycaw`, `comtypes`, `wmi`, `requests`,
> `beautifulsoup4`, `pyperclip`). See `pyproject.toml`.

## 3. Verify Installation

```bash
python -c "import friday; import friday.tools; print('tools:', len(friday.tools.ToolRegistry.keys()))"
```

This should list all registered tools, including the new automation tools
(`battery_status`, `volume_set`, `open_app`, `create_file`, ...).

## 4. Run the Tests

```bash
# With src layout and no installed package:
PYTHONPATH=src pytest tests/tools/test_automation_tools.py tests/agents/test_automation_agent.py -q
```

## 5. Use the Automation Agent

```python
from friday.agents.automation_agent import AutomationAgent, plan_request

# Plan an intent
plans = plan_request("set volume to 40")
print(plans)  # [{'name': 'volume_set', 'arguments': {'level': 40}}]

# Build an agent with a real engine and the tool executor
agent = AutomationAgent(engine, "gpt-4o", tools=[...])
result = agent.run("what's the weather in London?")
print(result.content)
```

## 6. Platform Notes

- **Brightness / Volume**: Windows-only (WMI / pycaw). On non-Windows these tools
  return a clean "not supported" result.
- **Playwright (browser.py)**: optional — `uv sync --extra browser`.
- The imported source repos (`PC-Automation-main/`, `jarvis-ai-assistant-main/`)
  are kept for reference only and are not required at runtime.
