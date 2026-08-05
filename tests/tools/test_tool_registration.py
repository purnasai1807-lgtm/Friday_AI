"""Verify that importing friday.tools registers all built-in tools."""

from __future__ import annotations

import importlib
import sys

from friday.core.registry import ToolRegistry

# Every tool name that should be registered after importing the package.
EXPECTED_TOOLS = {
    # calculator.py
    "calculator",
    # think.py
    "think",
    # retrieval.py
    "retrieval",
    # llm_tool.py
    "llm",
    # file_read.py
    "file_read",
    # file_write.py
    "file_write",
    # web_search.py
    "web_search",
    # code_interpreter.py
    "code_interpreter",
    # code_interpreter_docker.py
    "code_interpreter_docker",
    # repl.py
    "repl",
    # storage_tools.py
    "memory_store",
    "memory_retrieve",
    "memory_search",
    "memory_index",
    # channel_tools.py
    "channel_send",
    "channel_list",
    "channel_status",
    # http_request.py
    "http_request",
    # shell_exec.py
    "shell_exec",
    # memory_manage.py
    "memory_manage",
    # user_profile_manage.py
    "user_profile_manage",
    # skill_manage.py
    "skill_manage",
    # apply_patch.py
    "apply_patch",
    # git_tool.py
    "git_status",
    "git_diff",
    "git_commit",
    "git_log",
    # db_query.py
    "db_query",
    # pdf_tool.py
    "pdf_extract",
    # image_tool.py
    "image_generate",
    # audio_tool.py
    "audio_transcribe",
    # knowledge_tools.py
    "kg_add_entity",
    "kg_add_relation",
    "kg_query",
    "kg_neighbors",
    # system_tools.py
    "battery_status",
    "volume_get",
    "volume_set",
    "brightness_get",
    "brightness_set",
    "clipboard_get",
    "clipboard_set",
    "running_apps",
    "get_ip",
    # desktop_tools.py
    "open_app",
    "scroll",
    "keyboard_hotkey",
    "keyboard_type",
    "mouse_move",
    "mouse_click",
    "close_window",
    # browser_tools.py
    "open_website",
    "web_search_open",
    "browser_tab",
    "media_control",
    "youtube_play",
    # files_tools.py
    "create_file",
    "list_directory",
    "read_file_content",
    # media_tools.py
    "get_joke",
    "get_advice",
    "get_weather",
}


def _reload_tool_modules() -> None:
    """Reload all friday.tools.* submodules to re-trigger @register decorators.

    The autouse ``_clean_registries`` fixture clears all registries before each
    test.  A plain ``import friday.tools`` won't re-register because the
    submodules are already cached in ``sys.modules``.  We must reload the
    individual submodules so their class-level ``@ToolRegistry.register``
    decorators execute again.
    """
    for mod_name in list(sys.modules):
        if (
            mod_name.startswith("friday.tools.")
            and not mod_name.endswith("_stubs")
            and not mod_name.endswith("agent_tools")
        ):
            try:
                importlib.reload(sys.modules[mod_name])
            except Exception:
                pass


def test_all_builtin_tools_registered():
    _reload_tool_modules()

    registered = set(ToolRegistry.keys())
    missing = EXPECTED_TOOLS - registered
    assert not missing, (
        f"Tools not registered (missing import in __init__.py?): {sorted(missing)}"
    )
