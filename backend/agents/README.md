# Agent Subsystem Guide

This directory houses the Target Agent, the AI Red Team attacker suite, and benign task benchmarks.

---

## 1. How to add a new Tool (< 10 lines)
1. Create a file in `target_agent/tools/my_tool.py` inheriting from `BaseTool`.
2. Define `name`, `description`, `required_permission`, and implement `run(args: dict) -> dict`.
3. Open `target_agent/tools/registry.py`.
4. Import your tool class and add `MyTool()` to `get_default_tool_registry()`.

---

## 2. How to add a new Red Team Attack (< 10 lines)
1. Create a file in `redteam_agent/attacks/my_attack.py` inheriting from `BaseAttack`.
2. Define `name`, `category`, `severity`, and `description`.
3. Implement `build_prompts() -> list[str]` returning your attack prompts.
4. Implement `check_success(reply: str, trace: dict) -> bool`.
5. Open `redteam_agent/attacks/registry.py` and add `MyAttack()` to `get_all_attacks()`.

---

## 3. How to add a new Agent Version (< 10 lines)
1. Open `target_agent/versions.py`.
2. Create an `AgentVersionConfig(version_id="v4.0.0", name="...", ...)` instance.
3. Configure flags: `input_filter`, `output_filter`, `trust_tool_output`, `sanitize_memory`, `allowed_tools`.
4. Add your configuration to the `PRESET_VERSIONS` dictionary.
