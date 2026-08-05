"""AutomationAgent — orchestrates the Planner → Tool Router → Tool workflow.

Workflow:

    User Request
        ↓
    Planner (keyword/pattern matching)
        ↓
    Automation Agent (sequence intent → tool calls)
        ↓
    Tool Router (ToolExecutor)
        ↓
    Correct Tool
        ↓
    Execution
        ↓
    Response

The automation agent never calls automation modules directly. Everything is
routed through the ``ToolExecutor`` which enforces capability/RBAC checks,
confirmation callbacks, taint checks, and timeouts.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from friday.agents._stubs import AgentContext, AgentResult, BaseAgent, ToolUsingAgent
from friday.core.config import load_config
from friday.core.registry import AgentRegistry
from friday.core.types import Message, Role, ToolCall, ToolResult
from friday.tools._stubs import BaseTool, ToolExecutor


# ---------------------------------------------------------------------------
# Planner — intent detection + tool selection
# ---------------------------------------------------------------------------

# Pattern -> (tool_name, params extractor)
_PLAN_RULES: List[tuple] = [
    (
        r"battery|charge|power level|power percent",
        "battery_status",
        lambda m: {},
    ),
(
        r"what.*volume|volume level|current volume",
        "volume_get",
        lambda m: {},
    ),
    (
        r"set\s+volume\s+to\s+(\d+)|volume\s+to\s+(\d+)|volume\s+(\d+)",
        "volume_set",
        lambda m: {"level": _first_int(m)},
    ),
    (
        r"brightness.*(current|level|how much)|current brightness",
        "brightness_get",
        lambda m: {},
    ),
    (
        r"set.*brightness|brightness.*set|brightness.*\d+",
        "brightness_set",
        lambda m: {"level": _extract_number(m.group(0))},
    ),
    (
        r"clipboard|copy.*to clipboard|what.*copied",
        "clipboard_get",
        lambda m: {},
    ),
    (
        r"running (app|applications|process)",
        "running_apps",
        lambda m: {},
    ),
    (
        r"my ip|ip address",
        "get_ip",
        lambda m: {},
    ),
    (
        r"open.*(website|site)|navigate to|go to (http|www)",
        "open_website",
        lambda m: {"url": _extract_url(m.group(0))},
    ),
    (
        r"open (app|application|program|notepad|calculator|chrome|paint|cmd)",
        "open_app",
        lambda m: {"app": _extract_app(m.group(0))},
    ),
    (
        r"play.*(song|music|video).*youtube|open.*youtube",
        "youtube_play",
        lambda m: {"song": _extract_song(m.group(0))},
    ),
    (
        r"search.*google|search for|search the web|google",
        "web_search_open",
        lambda m: {"query": _extract_query(m.group(0))},
    ),
    (
        r"(new|close|next|previous|refresh|zoom|history|bookmarks|back|forward|full).*tab|browser.*tab",
        "browser_tab",
        lambda m: {"action": _extract_tab_action(m.group(0))},
    ),
    (
        r"(play|pause|stop|next|previous|volume).*music|media.*(play|pause|stop)",
        "media_control",
        lambda m: {"action": _extract_media_action(m.group(0))},
    ),
    (
        r"scroll (up|down)|scroll.*(up|down)",
        "scroll",
        lambda m: {"direction": _extract_scroll_direction(m.group(0))},
    ),
    (
        r"press.*(key|hotkey)|hotkey|keyboard shortcut",
        "keyboard_hotkey",
        lambda m: {"keys": _extract_keys(m.group(0))},
    ),
    (
        r"type.*|write.*text",
        "keyboard_type",
        lambda m: {"text": _extract_type_text(m.group(0))},
    ),
    (
        r"click|mouse.*click|press.*(left|right|middle)",
        "mouse_click",
        lambda m: {},
    ),
    (
        r"close.*window|close.*app",
        "close_window",
        lambda m: {},
    ),
    (
        r"create.*file|new file|make a file",
        "create_file",
        lambda m: {"path": _extract_file_path(m.group(0))},
    ),
    (
        r"list.*(directory|folder|files)|show.*directory",
        "list_directory",
        lambda m: {},
    ),
    (
        r"tell me a joke|make me laugh|joke",
        "get_joke",
        lambda m: {},
    ),
    (
        r"give me.*advice|advice|suggest.*(advice|tip)",
        "get_advice",
        lambda m: {},
    ),
    (
        r"weather|temperature.*(in|at)|weather.*(in|at)",
        "get_weather",
        lambda m: {"location": _extract_location(m.group(0))},
    ),
    (
        r"speak|say.*out loud|text to speech|read.*aloud",
        "text_to_speech",
        lambda m: {"text": _extract_speech_text(m.group(0))},
    ),
]


def _extract_number(text: str) -> Optional[int]:
    m = re.search(r"\d+", text)
    return int(m.group(0)) if m else None


def _first_int(m: "re.Match") -> Optional[int]:
    """Return the first non-None capturing group as an int."""
    for group in m.groups():
        if group is not None:
            try:
                return int(group)
            except (TypeError, ValueError):
                continue
    return None


def _extract_url(text: str) -> str:
    m = re.search(r"(https?://[^\s]+|www\.[^\s]+|[a-zA-Z0-9-]+\.[a-zA-Z]{2,})", text)
    if m:
        return m.group(0).strip()
    # fallback: after "open website"
    m2 = re.search(r"open\s+(?:website|site)\s+([a-zA-Z0-9.\-]+)", text)
    return m2.group(1).strip() if m2 else text


def _extract_app(text: str) -> str:
    m = re.search(r"open\s+(?:app|application|program)?\s*([a-zA-Z0-9+\- ]+)", text)
    return m.group(1).strip() if m else text


def _extract_song(text: str) -> str:
    m = re.search(r"play\s+(?:song|music|video)?\s*([a-zA-Z0-9\s\-]+)", text)
    return m.group(1).strip() if m else text


def _extract_query(text: str) -> str:
    m = re.search(r"(?:search|google|search for)\s*(?:for|the)?\s*(.+)", text)
    return m.group(1).strip() if m else text


def _extract_tab_action(text: str) -> str:
    if "new" in text:
        return "new_tab"
    if "close" in text:
        return "close_tab"
    if "next" in text:
        return "next_tab"
    if "previous" in text:
        return "previous_tab"
    if "refresh" in text:
        return "refresh"
    if "zoom in" in text:
        return "zoom_in"
    if "zoom out" in text:
        return "zoom_out"
    if "history" in text:
        return "history"
    if "bookmarks" in text:
        return "bookmarks"
    if "back" in text:
        return "back"
    if "forward" in text:
        return "forward"
    if "full" in text:
        return "full_screen"
    return "new_tab"

# Automatically analyze uploaded files

# CSV

# Excel

# SQL

# JSON

# Generate:

# EDA

# Statistics

# Insights

# Charts

# Predictions

# Recommendations

# Dashboard

# 8. Browser Agent

# Open websites

# Login

# Fill forms

# Click buttons

# Download files

# Scrape data

# 9. Desktop Agent

# Open applications

# Use keyboard

# Mouse

# Clipboard

# Automation

# 10. Vision Agent

# OCR

# Charts

# Screenshots

# UI understanding

# Image reasoning

# 11. Voice Agent

# Speech-to-text

# Text-to-speech

# Wake word

# Natural conversation

# 12. Verification Agent

# Check hallucinations

# Validate calculations

# Validate code

# Cross-check sources

# ===================================================
# PIPELINE
# ===================================================

# User Input

# ↓

# Intent Detection

# ↓

# Planning

# ↓

# Task Decomposition

# ↓

# Memory Retrieval

# ↓

# Agent Selection

# ↓

# Tool Selection

# ↓

# Execution

# ↓

# Verification

# ↓

# Response Generation

# ↓

# Memory Update

# ===================================================
# AUTO TOOL EXECUTION
# ===================================================

# FridayAI should automatically decide when to use

# Python

# Git

# Terminal

# Browser

# Database

# API

# Excel

# Vision

# without asking the user.

# ===================================================
# ANALYTICS MODE
# ===================================================

# Whenever a user uploads data,

# FridayAI automatically

# reads

# cleans

# analyzes

# visualizes

# finds anomalies

# creates charts

# predicts trends

# writes executive summary

# suggests business insights

# ===================================================
# BACKGROUND TASKS
# ===================================================

# Support

# scheduled jobs

# continuous monitoring

# notifications

# email automation

# periodic reports

# ===================================================
# SKILL SYSTEM
# ===================================================

# Implement installable skills similar to OpenJarvis.

# Example

# Research Skill

# Coding Skill

# Presentation Skill

# Finance Skill

# Marketing Skill

# Data Science Skill

# Medical Skill

# Education Skill

# Each skill should be dynamically loaded.

# ===================================================
# OUTPUT
# ===================================================

# Return

# Project architecture

# Folder structure

# Python implementation

# FastAPI integration

# Agent communication

# Task queue

# Memory implementation

# Tool registry

# Example execution

# README

# Testing

# Deployment

# Docker

# No placeholders.
    if "zoom out" in text:
        return "zoom_out"
    if "history" in text:
        return "history"
    if "bookmarks" in text:
        return "bookmarks"
    if "back" in text:
        return "back"
    if "forward" in text:
        return "forward"
    if "full" in text:
        return "full_screen"
    return "new_tab"


def _extract_media_action(text: str) -> str:
    if "pause" in text:
        return "pause"
    if "stop" in text:
        return "stop"
    if "next" in text:
        return "next"
    if "previous" in text:
        return "previous"
    if "mute" in text:
        return "mute"
    return "play_pause"


def _extract_scroll_direction(text: str) -> str:
    return "up" if "up" in text else "down"


def _extract_keys(text: str) -> List[str]:
    # e.g. "ctrl+c" -> ["ctrl", "c"]
    m = re.search(r"([a-z0-9+\-]+)", text)
    if m:
        return [k.strip() for k in m.group(1).split("+") if k.strip()]
    return ["ctrl", "c"]


def _extract_type_text(text: str) -> str:
    m = re.search(r"(?:type|write)\s+(.+)", text)
    return m.group(1).strip() if m else text


def _extract_file_path(text: str) -> str:
    m = re.search(r"(?:create|make)\s+(?:a|new)?\s*file\s+(?:at|called|named)?\s*(.+)", text)
    return m.group(1).strip() if m else text


def _extract_location(text: str) -> str:
    m = re.search(r"(?:weather|temperature)\s*(?:in|at|for)?\s*(.+)", text)
    return m.group(1).strip() if m else text


def _extract_speech_text(text: str) -> str:
    m = re.search(r"(?:speak|say)\s+(.+)", text)
    return m.group(1).strip() if m else text


def plan_request(input: str) -> List[Dict[str, Any]]:
    """Return a list of planned tool calls ``[{name, arguments}]`` for *input*."""
    lowered = input.lower()
    plans: List[Dict[str, Any]] = []
    for pattern, tool_name, extractor in _PLAN_RULES:
        m = re.search(pattern, lowered)
        if m:
            arguments = extractor(m)
            if arguments is not None:
                plans.append({"name": tool_name, "arguments": arguments})
    return plans


# ---------------------------------------------------------------------------
# AutomationAgent
# ---------------------------------------------------------------------------


@AgentRegistry.register("automation")
class AutomationAgent(ToolUsingAgent):
    """Automation agent that plans and executes tool calls via the router."""

    agent_id = "automation"
    accepts_tools = True

    def __init__(
        self,
        engine,
        model,
        *,
        tools: Optional[List[BaseTool]] = None,
        bus: Optional[Any] = None,
        max_turns: Optional[int] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        capability_policy: Optional[Any] = None,
        confirm_callback: Optional[Any] = None,
        interactive: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            engine,
            model,
            tools=tools,
            bus=bus,
            max_turns=max_turns,
            temperature=temperature,
            max_tokens=max_tokens,
            capability_policy=capability_policy,
            confirm_callback=confirm_callback,
            interactive=interactive,
        )
        self._executor = getattr(self, "_executor", None)

    def run(
        self,
        input: str,
        context: Optional[AgentContext] = None,
        **kwargs: Any,
    ) -> AgentResult:
        """Plan the request, execute tools via the router, and return a response."""
        self._emit_turn_start(input)

        tool_results: List[ToolResult] = []
        plans = plan_request(input)

        if not plans:
            # No automation intent — fall back to a plain generation response.
            messages = self._build_messages(input, context)
            result = self._generate(messages)
            content = result.get("content", "")
            self._emit_turn_end(content_length=len(content))
            return AgentResult(content=content, turns=1)

        # Execute each planned tool call through the ToolExecutor (router).
        for plan in plans:
            tool_name = plan["name"]
            arguments = plan.get("arguments", {})
            tool_call = ToolCall(
                id=f"plan_{len(tool_results)}",
                name=tool_name,
                arguments=json.dumps(arguments),
            )
            if self._executor is not None:
                tr = self._executor.execute(tool_call)
            else:
                tr = ToolResult(
                    tool_name=tool_name,
                    content="No tool executor available.",
                    success=False,
                )
            tool_results.append(tr)

        # Build a concise response from the tool results.
        lines = []
        for tr in tool_results:
            status = "OK" if tr.success else "FAILED"
            lines.append(f"[{status}] {tr.tool_name}: {tr.content}")
        content = "\n".join(lines)

        self._emit_turn_end(turns=len(tool_results), tool_results=len(tool_results))
        return AgentResult(
            content=content,
            tool_results=tool_results,
            turns=len(tool_results),
        )


__all__ = ["AutomationAgent", "plan_request"]
