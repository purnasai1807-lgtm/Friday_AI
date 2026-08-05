"""Media & content tools — jokes, advice, weather, text-to-speech.

Extracted from PC-Automation (GetJokes, GetAdvice) and jarvis-ai-assistant
(Features/get_jokes, Features/get_advice, Weather_Check/check_weather,
TextToSpeech/Fast_DF_TTS). Unified as first-class OpenJarvis tools.
"""

from __future__ import annotations

from typing import Any, Optional

from friday.core.registry import ToolRegistry
from friday.core.types import ToolResult
from friday.tools._stubs import ToolSpec
from friday.tools.automation._base import AutomationTool


def _fetch_json(
    url: str,
    *,
    timeout: int = 10,
    headers: Optional[dict] = None,
) -> Optional[dict]:
    """Fetch a JSON payload from *url*, returning None on any failure."""
    try:
        import requests

        resp = requests.get(url, timeout=timeout, headers=headers)
        resp.raise_for_status()
        return resp.json()
    except Exception:  # noqa: BLE001
        return None


# ---------------------------------------------------------------------------
# Jokes
# ---------------------------------------------------------------------------


@ToolRegistry.register("get_joke")
class GetJokeTool(AutomationTool):
    """Get a random joke."""

    tool_id = "get_joke"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="get_joke",
            description="Get a random joke from an online API.",
            parameters={"type": "object", "properties": {}},
            category="media",
            required_capabilities=["network:fetch"],
        )

    def execute(self, **params: Any) -> ToolResult:
        data = _fetch_json(
            "https://icanhazdadjoke.com/",
            headers={"Accept": "application/json"},
        )
        if data and data.get("joke"):
            return self._result(data["joke"], success=True)
        return self._result("Failed to fetch a joke.", success=False)


# ---------------------------------------------------------------------------
# Advice
# ---------------------------------------------------------------------------


@ToolRegistry.register("get_advice")
class GetAdviceTool(AutomationTool):
    """Get a random piece of advice."""

    tool_id = "get_advice"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="get_advice",
            description="Get a random piece of advice from an online API.",
            parameters={"type": "object", "properties": {}},
            category="media",
            required_capabilities=["network:fetch"],
        )

    def execute(self, **params: Any) -> ToolResult:
        data = _fetch_json("https://api.adviceslip.com/advice")
        if data and data.get("slip", {}).get("advice"):
            return self._result(data["slip"]["advice"], success=True)
        return self._result("Failed to fetch advice.", success=False)


# ---------------------------------------------------------------------------
# Weather
# ---------------------------------------------------------------------------


@ToolRegistry.register("get_weather")
class GetWeatherTool(AutomationTool):
    """Get the current weather for a location."""

    tool_id = "get_weather"

    @property
    def spec(self) -> ToolSpec:
        return ToolSpec(
            name="get_weather",
            description=(
                "Get the current weather for a given location or address."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City, address, or location name.",
                    },
                },
                "required": ["location"],
            },
            category="media",
            required_capabilities=["network:fetch"],
        )

    def execute(self, **params: Any) -> ToolResult:
        location = params.get("location", "")
        if not location:
            return self._result("No location provided.", success=False)
        try:
            import requests
            from bs4 import BeautifulSoup
        except ImportError:
            return self._result(
                "requests/beautifulsoup4 not installed. Install with: "
                "pip install requests beautifulsoup4",
                success=False,
            )
        search_url = (
            "https://www.google.com/search?q=weather+"
            + location.replace(" ", "+")
        )
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                " (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
        }
        try:
            resp = requests.get(search_url, headers=headers, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            loc = soup.find("div", attrs={"id": "wob_loc"})
            weather = soup.find("span", attrs={"id": "wob_dc"})
            temp = soup.find("span", attrs={"id": "wob_tm"})
            if not (loc and weather and temp):
                return self._result(
                    "Could not parse weather data for that location.",
                    success=False,
                )
            report = (
                f"Weather: {weather.text}\n"
                f"Temperature: {temp.text}°C\n"
                f"Location: {loc.text}"
            )
            return self._result(report, success=True, location=location)
        except Exception as exc:  # noqa: BLE001
            return self._result(f"Weather error: {exc}", success=False)


__all__ = [
    "GetAdviceTool",
    "GetJokeTool",
    "GetWeatherTool",
]
