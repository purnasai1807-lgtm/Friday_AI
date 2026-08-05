# FridayAI → Autonomous Multi-Agent Cortex — Task Tracker

## Phase 1: Cortex Core Subsystem (`src/friday/agents/cortex/`)

- [x] Create `types.py` — TaskState, Task, PlanStep, DependencyGraph, AgentRequest, shared results
- [x] Create `task_queue.py` — dependency-aware background task queue with worker pool + retries
- [x] Create `registry.py` — AgentCapabilityRegistry (intent→agent) + tool planner
- [x] Create `planner.py` — PlannerAgent (goal decomposition, dependency graph, scheduling, retry)
- [x] Create `memory_agent.py` — MemoryAgent (long/short-term, semantic retrieval, history, project memory)
- [x] Create `tool_agent.py` — ToolAgent (auto tool selection + execution via ToolExecutor)
- [x] Create `research_agent.py` — ResearchAgent (web search, compare, cite, summarize)
- [x] Create `coding_agent.py` — CodingAgent (write/debug/test/refactor/explain/run)
- [x] Create `analytics_agent.py` — AnalyticsAgent (CSV/Excel/SQL/JSON → EDA/stats/charts/predictions)
- [x] Create `browser_agent.py` — BrowserAgent (Playwright open/login/fill/click/download/scrape)
- [x] Create `desktop_agent.py` — DesktopAgent (apps/keyboard/mouse/clipboard)
- [x] Create `vision_agent.py` — VisionAgent (OCR, charts, screenshots, image reasoning)
- [x] Create `voice_agent.py` — VoiceAgent (STT/TTS, wake word, conversation)
- [x] Create `verification_agent.py` — VerificationAgent (hallucination, calc/code validation, cross-check)
- [x] Create `orchestrator.py` — CortexOrchestratorAgent (full pipeline orchestration)
- [x] Create `pipeline.py` — Cortex facade + run() implementing the whole pipeline
- [x] Create `__init__.py` — auto-register all cortex agents

## Phase 2: Integration

- [x] Update `src/friday/agents/__init__.py` — register cortex agents (additive)
- [x] Create `src/friday/server/cortex_routes.py` — /v1/cortex/\* routes + WebSocket
- [x] Update `src/friday/server/app.py` — optional cortex router inclusion
- [x] Update `pyproject.toml` — add cortex + analytics/vision/voice/browser extras

## Phase 3: Tests (`tests/agents/cortex/`)

- [x] test_types, test_task_queue, test_planner, test_orchestrator
- [x] test_memory_agent, test_tool_agent, test_research_agent, test_coding_agent
- [x] test_analytics_agent, test_verification_agent, test_pipeline

## Phase 4: Docs & Deploy

- [x] `docs/cortex/architecture.md`
- [x] `docs/cortex/README.md` (full README + example execution)
- [x] `docs/cortex/testing.md`
- [x] `docs/cortex/deployment.md`
- [x] `deploy/docker/Dockerfile.cortex`
- [x] `deploy/docker/docker-compose.cortex.yml`
- [x] `examples/cortex/example_run.py`

## Phase 5: Verification

- [x] Run pytest suite for cortex tests
- [x] Confirm agent registration (all 12 cortex agents)
- [x] Confirm backward compatibility (additive changes only)
