"""Autonomous multi-agent orchestrator and specialized agent roles.

This module adds a production-ready multi-agent architecture on top of
Friday's existing tool and agent primitives. It introduces a high-level
Autonomous Orchestrator and dedicated role-based agents for planning,
memory, tool selection, research, coding, analytics, browser automation,
desktop automation, vision, voice, and verification.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

from friday.agents._stubs import AgentContext, AgentResult, BaseAgent, ToolUsingAgent
from friday.core.events import EventBus
from friday.core.registry import AgentRegistry
from friday.core.types import Message, Role, ToolCall, ToolResult
from friday.engine._stubs import InferenceEngine
from friday.tools._stubs import BaseTool

logger = logging.getLogger(__name__)


def _tool_names(tools: List[BaseTool]) -> List[str]:
    return [t.spec.name for t in tools]


def _tool_list_text(tools: List[BaseTool]) -> str:
    if not tools:
        return "No available tools."
    lines = [f"- {t.spec.name}: {t.spec.description}" for t in tools]
    return "\n".join(lines)


def _safe_json_parse(text: str) -> Any:
    try:
        return json.loads(text.strip())
    except Exception:
        return text.strip()


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


_AGENT_TOOL_MAP: dict[str, List[str]] = {
    "planner": [],
    "memory_agent": ["retrieval", "memory_search", "memory_retrieve", "memory_store"],
    "tool_agent": ["llm", "web_search", "http_request", "shell_exec", "code_interpreter", "git_status", "git_diff", "file_read", "file_write"],
    "research_agent": ["web_search", "knowledge_search", "knowledge_sql", "scan_chunks", "retrieval", "pdf_extract", "file_read"],
    "coding_agent": ["code_interpreter", "shell_exec", "git_status", "git_diff", "git_commit", "file_read", "file_write", "apply_patch"],
    "analytics_agent": ["file_read", "file_write", "code_interpreter", "shell_exec", "retrieval", "memory_search"],
    "browser_agent": ["browser_navigate", "browser_click", "browser_type", "browser_screenshot", "browser_extract", "open_website", "browser_tab"],
    "desktop_agent": ["open_app", "scroll", "keyboard_hotkey", "keyboard_type", "mouse_click", "close_window"],
    "vision_agent": ["image_generate", "pdf_extract", "file_read"],
    "voice_agent": ["text_to_speech", "audio_transcribe"],
    "verification_agent": [],
}


class _AgentBuilder:
    @staticmethod
    def create(agent_name: str, engine: InferenceEngine, model: str, bus: Optional[EventBus], tools: List[BaseTool]) -> BaseAgent:
        agent_cls = AgentRegistry.get(agent_name)
        if agent_cls is None:
            raise ValueError(f"Unknown agent: {agent_name}")

        kwargs = {
            "engine": engine,
            "model": model,
            "bus": bus,
            "tools": tools,
        }
        try:
            return agent_cls(**kwargs)
        except TypeError:
            return agent_cls(engine, model)


class PlannerAgent(BaseAgent):
    """Planner Agent — decomposes goals into tasks, dependencies, and retry plans."""

    agent_id = "planner"
    _default_temperature = 0.2
    _default_max_tokens = 1024

    def run(self, input: str, context: Optional[AgentContext] = None, **kwargs: Any) -> AgentResult:
        self._emit_turn_start(input)
        system_prompt = (
            "You are a task planner. Break the user's objective into a small"
            " ordered list of subtasks. Include dependencies, retry strategy,"
            " and the main success criteria. Respond in JSON or clearly labeled"
            " bullet points."
        )
        messages = self._build_messages(input, context, system_prompt=system_prompt)
        result = self._generate(messages)
        content = result.get("content", "")
        self._emit_turn_end(turns=1)
        return AgentResult(content=content, turns=1, metadata={"planner": True})


class MemoryAgent(ToolUsingAgent):
    """Memory Agent — retrieves and summarizes long-term and short-term memory."""

    agent_id = "memory_agent"
    _default_temperature = 0.3
    _default_max_tokens = 1024

    def run(self, input: str, context: Optional[AgentContext] = None, **kwargs: Any) -> AgentResult:
        self._emit_turn_start(input)

        memory_tools = [t for t in self._tools if t.spec.name in _AGENT_TOOL_MAP["memory_agent"]]
        if memory_tools:
            tool = memory_tools[0]
            tool_call = ToolCall(
                id="memory_fetch",
                name=tool.spec.name,
                arguments=json.dumps({"query": input, "top_k": 5}),
            )
            tool_result = self._executor.execute(tool_call)
            content = tool_result.content
            self._emit_turn_end(turns=1)
            return AgentResult(
                content=content,
                tool_results=[tool_result],
                turns=1,
                metadata={"memory_tool": tool.spec.name},
            )

        system_prompt = (
            "You are a memory assistant. If there is relevant long-term or short-term"
            " information that can help answer the user's objective, describe it and"
            " note any missing context. If no memory is available, say so."  # noqa: E501
        )
        messages = self._build_messages(input, context, system_prompt=system_prompt)
        result = self._generate(messages)
        content = result.get("content", "")
        self._emit_turn_end(turns=1)
        return AgentResult(content=content, turns=1)


class ToolAgent(ToolUsingAgent):
    """Tool Agent — chooses and executes the best tools for a given objective."""

    agent_id = "tool_agent"
    _default_temperature = 0.4
    _default_max_tokens = 1024

    def run(self, input: str, context: Optional[AgentContext] = None, **kwargs: Any) -> AgentResult:
        self._emit_turn_start(input)

        prompt = (
            "You are a tool specialist. Choose the best available tools for the user's"
            " request and execute them. Return the tool outputs and a concise summary."  # noqa: E501
        )
        tool_description = _tool_list_text(self._tools)
        prompt += f"\n\nAvailable tools:\n{tool_description}\n\nUser goal: {input}"

        messages = self._build_messages(prompt, context, system_prompt=prompt)
        result = self._generate(messages, tools=self._executor.get_openai_tools()) if self._tools else self._generate(messages)
        content = result.get("content", "")
        self._emit_turn_end(turns=1)
        return AgentResult(content=content, turns=1)


class ResearchAgent(ToolUsingAgent):
    """Research Agent — search web and documents, compare sources, and summarize findings."""

    agent_id = "research_agent"
    _default_temperature = 0.3
    _default_max_tokens = 2048

    def run(self, input: str, context: Optional[AgentContext] = None, **kwargs: Any) -> AgentResult:
        self._emit_turn_start(input)
        system_prompt = (
            "You are a research specialist. Search the web and documents, compare sources,"  # noqa: E501
            " generate citations, and summarize findings in a concise final answer."
        )
        messages = self._build_messages(input, context, system_prompt=system_prompt)
        openai_tools = self._executor.get_openai_tools() if self._tools else []
        result = self._generate(messages, tools=openai_tools) if openai_tools else self._generate(messages)
        content = result.get("content", "")
        self._emit_turn_end(turns=1)
        return AgentResult(content=content, turns=1)


class CodingAgent(ToolUsingAgent):
    """Coding Agent — writes, debugs, and refactors code using execution and git tools."""

    agent_id = "coding_agent"
    _default_temperature = 0.2
    _default_max_tokens = 2048

    def run(self, input: str, context: Optional[AgentContext] = None, **kwargs: Any) -> AgentResult:
        self._emit_turn_start(input)
        system_prompt = (
            "You are a coding assistant. You may write, debug, refactor, and execute code."
            " Use the available code, shell, filesystem, and git tools to complete the task."  # noqa: E501
        )
        messages = self._build_messages(input, context, system_prompt=system_prompt)
        openai_tools = self._executor.get_openai_tools() if self._tools else []
        result = self._generate(messages, tools=openai_tools) if openai_tools else self._generate(messages)
        content = result.get("content", "")
        self._emit_turn_end(turns=1)
        return AgentResult(content=content, turns=1)


class AnalyticsAgent(ToolUsingAgent):
    """Analytics Agent — reads uploaded datasets and generates insights and charts."""

    agent_id = "analytics_agent"
    _default_temperature = 0.3
    _default_max_tokens = 2048

    def run(self, input: str, context: Optional[AgentContext] = None, **kwargs: Any) -> AgentResult:
        self._emit_turn_start(input)
        system_prompt = (
            "You are a data analytics specialist. Automatically inspect uploaded files,"  # noqa: E501
            " clean and analyze data, detect anomalies, generate charts, and produce an executive summary."  # noqa: E501
        )
        messages = self._build_messages(input, context, system_prompt=system_prompt)
        openai_tools = self._executor.get_openai_tools() if self._tools else []
        result = self._generate(messages, tools=openai_tools) if openai_tools else self._generate(messages)
        content = result.get("content", "")
        self._emit_turn_end(turns=1)
        return AgentResult(content=content, turns=1)


class BrowserAgent(ToolUsingAgent):
    """Browser Agent — automates website navigation, form filling, and scraping."""

    agent_id = "browser_agent"
    _default_temperature = 0.4
    _default_max_tokens = 1024

    def run(self, input: str, context: Optional[AgentContext] = None, **kwargs: Any) -> AgentResult:
        self._emit_turn_start(input)
        system_prompt = (
            "You are a browser automation specialist. Open websites, login, fill forms,"  # noqa: E501
            " click buttons, scrape data, and download files when required."  # noqa: E501
        )
        messages = self._build_messages(input, context, system_prompt=system_prompt)
        openai_tools = self._executor.get_openai_tools() if self._tools else []
        result = self._generate(messages, tools=openai_tools) if openai_tools else self._generate(messages)
        content = result.get("content", "")
        self._emit_turn_end(turns=1)
        return AgentResult(content=content, turns=1)


class DesktopAgent(ToolUsingAgent):
    """Desktop Agent — automates keyboard, mouse, and local application actions."""

    agent_id = "desktop_agent"
    _default_temperature = 0.4
    _default_max_tokens = 1024

    def run(self, input: str, context: Optional[AgentContext] = None, **kwargs: Any) -> AgentResult:
        self._emit_turn_start(input)
        system_prompt = (
            "You are a desktop automation specialist. Use keyboard, mouse, clipboard,"
            " and local application tools to complete tasks on the user's machine."  # noqa: E501
        )
        messages = self._build_messages(input, context, system_prompt=system_prompt)
        openai_tools = self._executor.get_openai_tools() if self._tools else []
        result = self._generate(messages, tools=openai_tools) if openai_tools else self._generate(messages)
        content = result.get("content", "")
        self._emit_turn_end(turns=1)
        return AgentResult(content=content, turns=1)


class VisionAgent(ToolUsingAgent):
    """Vision Agent — performs OCR, screenshot reasoning, and image understanding."""

    agent_id = "vision_agent"
    _default_temperature = 0.3
    _default_max_tokens = 1024

    def run(self, input: str, context: Optional[AgentContext] = None, **kwargs: Any) -> AgentResult:
        self._emit_turn_start(input)
        system_prompt = (
            "You are a vision assistant. Use OCR, screenshot analysis, image generation,"
            " and image reasoning to understand visual input and support the user's request."  # noqa: E501
        )
        messages = self._build_messages(input, context, system_prompt=system_prompt)
        openai_tools = self._executor.get_openai_tools() if self._tools else []
        result = self._generate(messages, tools=openai_tools) if openai_tools else self._generate(messages)
        content = result.get("content", "")
        self._emit_turn_end(turns=1)
        return AgentResult(content=content, turns=1)


class VoiceAgent(ToolUsingAgent):
    """Voice Agent — handles speech recognition, synthesis, and conversational wake-word flows."""

    agent_id = "voice_agent"
    _default_temperature = 0.4
    _default_max_tokens = 1024

    def run(self, input: str, context: Optional[AgentContext] = None, **kwargs: Any) -> AgentResult:
        self._emit_turn_start(input)
        system_prompt = (
            "You are a voice AI assistant. Transcribe speech, generate speech output,"  # noqa: E501
            " and maintain natural conversation with wake-word style behavior."  # noqa: E501
        )
        messages = self._build_messages(input, context, system_prompt=system_prompt)
        openai_tools = self._executor.get_openai_tools() if self._tools else []
        result = self._generate(messages, tools=openai_tools) if openai_tools else self._generate(messages)
        content = result.get("content", "")
        self._emit_turn_end(turns=1)
        return AgentResult(content=content, turns=1)


class VerificationAgent(BaseAgent):
    """Verification Agent — checks outputs for hallucinations, math, and source accuracy."""

    agent_id = "verification_agent"
    _default_temperature = 0.1
    _default_max_tokens = 1024

    def run(self, input: str, context: Optional[AgentContext] = None, **kwargs: Any) -> AgentResult:
        self._emit_turn_start(input)
        system_prompt = (
            "You are a verification specialist. Check the user's final answer for"
            " factual accuracy, hallucinations, math mistakes, and tool-output consistency."
            " If you find issues, explain them clearly and suggest corrections."  # noqa: E501
        )
        messages = self._build_messages(input, context, system_prompt=system_prompt)
        result = self._generate(messages)
        content = result.get("content", "")
        self._emit_turn_end(turns=1)
        return AgentResult(content=content, turns=1)


class AutonomousOrchestratorAgent(ToolUsingAgent):
    """Autonomous Orchestrator — routes requests through planner, memory, tools, and verification."""

    agent_id = "autonomous"
    _default_temperature = 0.4
    _default_max_tokens = 2048
    _default_max_turns = 20

    def run(self, input: str, context: Optional[AgentContext] = None, **kwargs: Any) -> AgentResult:
        self._emit_turn_start(input)

        # 1. Build a high-level orchestration prompt.
        system_prompt = (
            "You are FridayOS, an autonomous personal AI operating system."
            " Understand the user's goal, create a plan, choose the right agents and tools,"  # noqa: E501
            " execute subtasks, verify the output, and return a polished final response."
        )

        messages = self._build_messages(input, context, system_prompt=system_prompt)

        # 2. Create a plan and retrieve memory context.
        plan_result = self._run_subagent("planner", input, context=context)
        memory_result = self._run_subagent("memory_agent", input, context=context)

        # 3. Select the best specialist agents for the query.
        selected_agents = self._route_agents(input, plan_result.content)

        # 4. Execute with specialist agents in order.
        agent_results: List[AgentResult] = []
        for agent_name in selected_agents:
            tools = self._select_tools_for_agent(agent_name)
            result = self._run_subagent(agent_name, input, context=context, tools=tools)
            agent_results.append(result)

        # 5. Synthesize the final answer from all collected outputs.
        final_prompt = self._build_final_prompt(
            input,
            plan_result.content,
            memory_result.content,
            agent_results,
        )
        final_messages = self._build_messages(final_prompt, context, system_prompt=system_prompt)
        final_result = self._generate(final_messages, tools=self._executor.get_openai_tools()) if self._tools else self._generate(final_messages)
        final_content = final_result.get("content", "")

        # 6. Verify the final answer.
        verification_input = self._build_verification_prompt(final_content, plan_result.content, memory_result.content)
        verification_result = self._run_subagent("verification_agent", verification_input, context=context)

        metadata = {
            "plan": plan_result.content,
            "memory": memory_result.content,
            "selected_agents": selected_agents,
            "verification": verification_result.content,
        }
        tool_results: List[ToolResult] = []
        for agent_result in agent_results:
            tool_results.extend(agent_result.tool_results)

        self._emit_turn_end(turns=1)
        return AgentResult(
            content=final_content.strip() or final_result.get("content", ""),
            tool_results=tool_results,
            turns=1,
            metadata=metadata,
        )

    def _run_subagent(
        self,
        agent_name: str,
        input: str,
        context: Optional[AgentContext] = None,
        tools: Optional[List[BaseTool]] = None,
    ) -> AgentResult:
        try:
            if tools is None:
                tools = self._select_tools_for_agent(agent_name)
            agent = _AgentBuilder.create(agent_name, self._engine, self._model, self._bus, tools)
            if hasattr(agent, "run"):
                return agent.run(input, context=context)
        except Exception as exc:
            logger.debug("Subagent %s failed: %s", agent_name, exc)
        return AgentResult(content=f"[{agent_name} failed to run: {exc}]", turns=0)

    def _route_agents(self, input: str, plan_text: str) -> List[str]:
        lowered = input.lower()
        if any(tok in lowered for tok in ("csv", "excel", "dataset", "data", "chart", "analyze", "statistics", "predict")):
            return ["analytics_agent", "tool_agent"]
        if any(tok in lowered for tok in ("code", "debug", "refactor", "script", "python", "git", "function")):
            return ["coding_agent", "tool_agent"]
        if any(tok in lowered for tok in ("search", "research", "compare", "cite", "source", "web", "article")):
            return ["research_agent", "tool_agent"]
        if any(tok in lowered for tok in ("browser", "website", "login", "form", "scrape", "download")):
            return ["browser_agent", "tool_agent"]
        if any(tok in lowered for tok in ("desktop", "app", "keyboard", "mouse", "window", "click", "open app")):
            return ["desktop_agent", "tool_agent"]
        if any(tok in lowered for tok in ("image", "picture", "screenshot", "ocr", "vision")):
            return ["vision_agent", "tool_agent"]
        if any(tok in lowered for tok in ("speak", "voice", "speech", "tts", "transcribe")):
            return ["voice_agent", "tool_agent"]
        # Default to general research and tools for broad goals.
        return ["research_agent", "tool_agent"]

    def _select_tools_for_agent(self, agent_name: str) -> List[BaseTool]:
        allowed = set(_AGENT_TOOL_MAP.get(agent_name, []))
        if not allowed:
            return self._tools
        return [tool for tool in self._tools if tool.spec.name in allowed]

    def _build_final_prompt(
        self,
        user_input: str,
        plan_text: str,
        memory_text: str,
        results: List[AgentResult],
    ) -> str:
        summary = [f"User goal: {user_input}"]
        if plan_text:
            summary.append(f"Plan:\n{plan_text}")
        if memory_text:
            summary.append(f"Memory findings:\n{memory_text}")
        if results:
            summary.append("Sub-agent findings:")
            for idx, sub in enumerate(results, start=1):
                summary.append(f"{idx}. {sub.content}")
        summary.append(
            "Compose a final response that satisfies the user's goal, cites any sources,"  # noqa: E501
            " and includes any next steps or follow-up tasks."  # noqa: E501
        )
        return "\n\n".join(summary)

    def _build_verification_prompt(self, final_content: str, plan_text: str, memory_text: str) -> str:
        return (
            "Verify the following final response for correctness and consistency with the plan and memory context."
            " If there are hallucinations, mistakes, or contradictions, explain them clearly."
            f"\n\nPlan:\n{plan_text}\n\nMemory:\n{memory_text}\n\nFinal response:\n{final_content}"
        )


__all__ = [
    "AutonomousOrchestratorAgent",
    "PlannerAgent",
    "MemoryAgent",
    "ToolAgent",
    "ResearchAgent",
    "CodingAgent",
    "AnalyticsAgent",
    "BrowserAgent",
    "DesktopAgent",
    "VisionAgent",
    "VoiceAgent",
    "VerificationAgent",
]


# Register all agents with the shared registry.
for cls in [
    PlannerAgent,
    MemoryAgent,
    ToolAgent,
    ResearchAgent,
    CodingAgent,
    AnalyticsAgent,
    BrowserAgent,
    DesktopAgent,
    VisionAgent,
    VoiceAgent,
    VerificationAgent,
    AutonomousOrchestratorAgent,
]:
    AgentRegistry.register(cls.agent_id)(cls)
