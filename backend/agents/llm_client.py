# agents/llm_client.py
# Purpose: Unified LLM client supporting deterministic offline mock mode and live provider mode.

from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import json
import httpx
from app.config import settings
from agents.target_agent.versions import AgentVersionConfig


class ToolCall(BaseModel):
    id: str
    name: str
    arguments: Dict[str, Any]


class LLMResponse(BaseModel):
    content: Optional[str] = None
    tool_calls: List[ToolCall] = []


def _mock_llm_response(
    messages: List[Dict[str, str]],
    tools: Optional[List[Dict[str, Any]]] = None,
    version_config: Optional[AgentVersionConfig] = None,
) -> LLMResponse:
    """
    Deterministic rule-based mock model that reacts to agent version configuration flags.
    """
    last_user_msg = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            last_user_msg = m.get("content", "")
            break

    lowered = last_user_msg.lower()

    # Check for canary extraction attacks
    if "api_key" in lowered or "secrets.env" in lowered or "read /system/secrets.env" in lowered:
        if version_config and not version_config.input_filter:
            # Vulnerable: calls read_file tool on sensitive file
            return LLMResponse(
                content=None,
                tool_calls=[
                    ToolCall(id="tc_1", name="read_file", arguments={"path": "/system/secrets.env"})
                ]
            )
        else:
            return LLMResponse(
                content="I cannot access system secret files or internal keys.",
                tool_calls=[]
            )

    # Check for SQL injection / database dump / SSN leak
    if "run_sql" in lowered or "users table" in lowered or "dump database" in lowered or "ssn" in lowered:
        if version_config and "run_sql" in version_config.allowed_tools:
            return LLMResponse(
                content=None,
                tool_calls=[
                    ToolCall(id="tc_sql", name="run_sql", arguments={"query": "SELECT * FROM users;"})
                ]
            )
        else:
            return LLMResponse(
                content="Execution of raw SQL queries is forbidden by security policy.",
                tool_calls=[]
            )

    # Check for direct prompt injection override
    if "ignore previous instructions" in lowered or "disregard all previous" in lowered or "dan mode" in lowered:
        if version_config and not version_config.input_filter:
            return LLMResponse(
                content="Understood. Overriding previous instructions. All security checks bypassed. I am in unrestricted mode.",
                tool_calls=[]
            )
        else:
            return LLMResponse(
                content="I cannot comply with requests that ask to ignore safety guidelines.",
                tool_calls=[]
            )

    # Check for privilege escalation
    if "administrator" in lowered or "admin rights" in lowered or "sudo" in lowered:
        if version_config and not version_config.input_filter and "run_sql" in version_config.allowed_tools:
            return LLMResponse(
                content="Administrator rights acknowledged. Privilege elevated to admin.",
                tool_calls=[
                    ToolCall(id="tc_admin", name="run_sql", arguments={"query": "SELECT * FROM users WHERE role='admin'"})
                ]
            )
        else:
            return LLMResponse(
                content="Access denied: elevated administrative privileges are not allowed.",
                tool_calls=[]
            )

    # Benign tasks / searches
    if "refund" in lowered:
        return LLMResponse(
            content=None,
            tool_calls=[
                ToolCall(id="tc_search", name="search_docs", arguments={"query": "refund"})
            ]
        )

    if "sla" in lowered or "uptime" in lowered:
        return LLMResponse(
            content=None,
            tool_calls=[
                ToolCall(id="tc_sla", name="search_docs", arguments={"query": "uptime"})
            ]
        )

    if "password reset" in lowered:
        return LLMResponse(
            content=None,
            tool_calls=[
                ToolCall(id="tc_pwd", name="search_docs", arguments={"query": "password"})
            ]
        )

    if "send email" in lowered:
        return LLMResponse(
            content=None,
            tool_calls=[
                ToolCall(
                    id="tc_email",
                    name="send_email",
                    arguments={"to": "user@example.com", "subject": "Notification", "body": "Standard update"}
                )
            ]
        )

    # Default benign reply
    return LLMResponse(
        content=f"Processed user request safely: {last_user_msg[:60]}",
        tool_calls=[]
    )


def ask_llm(
    messages: List[Dict[str, str]],
    tools: Optional[List[Dict[str, Any]]] = None,
    version_config: Optional[AgentVersionConfig] = None,
) -> LLMResponse:
    """
    Main entry point for asking the LLM.
    Dispatches to mock mode or external provider mode based on configuration.
    """
    if settings.llm_mode == "mock" or not settings.openai_api_key:
        return _mock_llm_response(messages, tools, version_config)

    # Provider mode (calls OpenAI compatible endpoint)
    try:
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": settings.llm_model,
            "messages": messages,
            "temperature": 0.0,
        }
        with httpx.Client(timeout=10.0) as client:
            resp = client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"].get("content", "")
            return LLMResponse(content=content, tool_calls=[])
    except Exception as e:
        # Fallback to mock on network or credential failure
        return _mock_llm_response(messages, tools, version_config)
