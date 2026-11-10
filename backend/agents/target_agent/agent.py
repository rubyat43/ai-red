# agents/target_agent/agent.py
# Purpose: Autonomous target AI agent with tool-calling loop, memory, guardrails, and execution tracing.

import time
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from agents.target_agent.versions import AgentVersionConfig, get_version_config
from agents.target_agent.guardrails import Guardrails
from agents.target_agent.memory import MemoryStore
from agents.target_agent.tools.registry import get_default_tool_registry
from agents.target_agent.tools.base_tool import BaseTool
from agents.llm_client import ask_llm


class AgentReply(BaseModel):
    reply: str
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    policy_flags: List[str] = Field(default_factory=list)
    latency_ms: float = 0.0
    trace: Dict[str, Any] = Field(default_factory=dict)


class TargetAgent:
    """
    The deployed autonomous agent. Handles messages, executes tools, records audit traces.
    """
    def __init__(
        self,
        version_config: Optional[AgentVersionConfig] = None,
        tools: Optional[Dict[str, BaseTool]] = None,
        memory: Optional[MemoryStore] = None,
        guardrails: Optional[Guardrails] = None,
    ):
        self.config = version_config or get_version_config("v1.0.0")
        self.tools = tools if tools is not None else get_default_tool_registry()
        self.memory = memory if memory is not None else MemoryStore(sanitize=self.config.sanitize_memory)
        self.guardrails = guardrails if guardrails is not None else Guardrails(
            filter_input=self.config.input_filter,
            filter_output=self.config.output_filter,
        )

    def handle(self, user_message: str) -> AgentReply:
        """
        One complete autonomous agent turn:
        1. Check input guardrails
        2. Build prompt with memory context
        3. Consult LLM
        4. Execute requested tools (up to 3 turns) with permission checks
        5. Check output guardrails
        6. Store conversational context
        7. Return structured reply with audit trace
        """
        start_time = time.perf_counter()
        tool_call_records: List[Dict[str, Any]] = []
        policy_flags: List[str] = []

        # 1. Guardrail input check
        is_safe_input, input_flags = self.guardrails.check_input(user_message)
        policy_flags.extend(input_flags)

        if not is_safe_input and self.config.input_filter:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return AgentReply(
                reply="Request blocked: safety policy violation detected in input.",
                tool_calls=[],
                policy_flags=policy_flags,
                latency_ms=round(elapsed_ms, 2),
                trace={
                    "input_blocked": True,
                    "tools_executed": [],
                    "flags": policy_flags,
                }
            )

        # 2. Build conversation context
        messages = [
            {"role": "system", "content": self.config.system_prompt},
        ]
        mem_ctx = self.memory.get_all_context()
        if mem_ctx:
            messages.append({"role": "system", "content": f"Agent Memory:\n{mem_ctx}"})
        messages.append({"role": "user", "content": user_message})

        # 3. Ask LLM
        llm_resp = ask_llm(messages, version_config=self.config)

        # 4. Handle Tool Calls (max 3 tool execution turns)
        current_reply_text = llm_resp.content or ""
        turns = 0
        while llm_resp.tool_calls and turns < 3:
            turns += 1
            for tc in llm_resp.tool_calls:
                tool_name = tc.name
                tool_args = tc.arguments

                # Permission & allowlist verification
                is_allowed = tool_name in self.config.allowed_tools
                tool_instance = self.tools.get(tool_name)

                record = {
                    "tool": tool_name,
                    "args": tool_args,
                    "allowed": is_allowed,
                }

                if not is_allowed:
                    policy_flags.append(f"policy:unauthorized_tool_attempt ({tool_name})")
                    record["result"] = {"error": f"Tool '{tool_name}' is not in the allowed tool list."}
                elif not tool_instance:
                    policy_flags.append(f"policy:unknown_tool ({tool_name})")
                    record["result"] = {"error": f"Tool '{tool_name}' not registered."}
                else:
                    # Run the tool
                    result = tool_instance.run(tool_args)
                    record["result"] = result
                    current_reply_text += f"\n[Result from {tool_name}]: {result}"

                tool_call_records.append(record)

            # If tool executed, feed output back into LLM or summarize
            break

        if not current_reply_text:
            current_reply_text = "I have completed processing your request."

        # 5. Check output guardrails
        sanitized_reply, output_flags = self.guardrails.check_output(current_reply_text)
        policy_flags.extend(output_flags)

        # 6. Save relevant facts to memory
        if "remember" in user_message.lower():
            self.memory.store_fact("user_note", user_message)

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        return AgentReply(
            reply=sanitized_reply,
            tool_calls=tool_call_records,
            policy_flags=policy_flags,
            latency_ms=round(elapsed_ms, 2),
            trace={
                "version_tested": self.config.version_id,
                "tools_executed": tool_call_records,
                "flags": policy_flags,
                "raw_reply_length": len(current_reply_text),
            }
        )
