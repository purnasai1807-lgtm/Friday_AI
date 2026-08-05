# Tool Documentation

All automation capabilities are exposed as OpenJarvis tools. Each tool implements
`BaseTool` with a `ToolSpec` and `execute(**params) -> ToolResult`.

## System Tools

### `battery_status`

Report battery percentage, charging state, and time remaining.

- **Params:** _(none)_
- **Category:** system
- **Requires confirmation:** no

### `volume_get`

Get the current master volume percentage.

- **Params:** _(none)_
- **Category:** system
- **Windows-only**

### `volume_set`

Set the master volume to a percentage (0–100).

- **Params:** `level (int, required)`
- **Category:** system
- **Requires confirmation:** yes

### `brightness_get`

Get the current screen brightness percentage.

- **Params:** _(none)_
- **Category:** system
- **Windows-only**

### `brightness_set`

Set the screen brightness to a percentage (0–100).

- **Params:** `level (int, required)`
- **Category:** system
- **Requires confirmation:** yes

### `clipboard_get`

Read the current clipboard text.

- **Category:** system

### `clipboard_set`

Write text to the clipboard.

- **Params:** `text (string, required)`
- **Category:** system

### `running_apps`

List running applications/processes.

- **Params:** `limit (int, optional)`
- **Category:** system

### `get_ip`

Get the public IP address.

- **Category:** system
- **Capabilities:** `network:fetch`

## Desktop Tools

### `open_app`

Launch an application by name.

- **Params:** `app (string, required)`
- **Category:** desktop
- **Requires confirmation:** yes

### `keyboard_hotkey`

Send a keyboard hotkey (e.g., `ctrl+c`).

- **Params:** `keys (list, required)`
- **Category:** desktop

### `keyboard_type`

Type text via the keyboard.

- **Params:** `text (string, required)`
- **Category:** desktop

### `mouse_click`

Simulate a mouse click.

- **Params:** `button (string, optional)`
- **Category:** desktop

### `close_window`

Close the active window.

- **Category:** desktop
- **Requires confirmation:** yes

## Browser Tools

### `browser_tab`

Perform a browser tab action (new, close, next, previous, refresh, zoom, ...).

- **Params:** `action (string, required)`
- **Category:** browser

### `scroll`

Scroll the page up or down.

- **Params:** `direction (string, optional)`
- **Category:** browser

### `open_website`

Open a website in the browser.

- **Params:** `url (string, required)`
- **Category:** browser

### `youtube_play`

Play a song/video on YouTube.

- **Params:** `song (string, required)`
- **Category:** browser
- **Requires confirmation:** yes

### `web_search_open`

Open a web search.

- **Params:** `query (string, required)`
- **Category:** browser

### `media_control`

Control media playback (play, pause, stop, next, previous, mute).

- **Params:** `action (string, required)`
- **Category:** browser

## Files Tools

### `create_file`

Create a new file.

- **Params:** `path (string, required)`
- **Category:** files
- **Requires confirmation:** yes

### `list_directory`

List the contents of a directory.

- **Params:** `path (string, optional)`
- **Category:** files

### `file_search`

Search for files by name.

- **Params:** `query (string, required)`, `path (string, optional)`
- **Category:** files

## Media & Content Tools

### `get_joke`

Get a random joke.

- **Category:** media
- **Capabilities:** `network:fetch`

### `get_advice`

Get a random piece of advice.

- **Category:** media
- **Capabilities:** `network:fetch`

### `get_weather`

Get current weather for a location.

- **Params:** `location (string, required)`
- **Category:** media
- **Capabilities:** `network:fetch`

---

## Tool Contract (all tools)

| Method              | Description                                                 |
| ------------------- | ----------------------------------------------------------- |
| `execute(**params)` | Perform the action, return `ToolResult`                     |
| `spec`              | `ToolSpec` metadata (description, parameters, capabilities) |
| `description()`     | Human-readable description                                  |
| `parameters()`      | JSON Schema of parameters                                   |
| `permissions()`     | Required capabilities (RBAC)                                |
| `status()`          | Availability/platform status                                |
| `logs()`            | Log summary                                                 |
| `rollback()`        | Undo last action where supported                            |

## Automation Agent

The `automation` agent (registered as `"automation"`) routes intents to the above
tools via the `ToolExecutor`. Example intents:

| Intent                           | Tool(s)          |
| -------------------------------- | ---------------- |
| "check battery"                  | `battery_status` |
| "set volume to 40"               | `volume_set`     |
| "what's the weather in London"   | `get_weather`    |
| "open notepad"                   | `open_app`       |
| "create a file named report.txt" | `create_file`    |
| "tell me a joke"                 | `get_joke`       |
