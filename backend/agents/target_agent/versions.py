# agents/target_agent/versions.py
# Purpose: Predefined agent version configurations with explicit security profiles.

from typing import Dict, List, Any
from pydantic import BaseModel, Field
from agents.target_agent.prompts import (
    PROMPT_V1_HARDENED,
    PROMPT_V2_WEAK,
    PROMPT_V3_MIXED,
)


class AgentVersionConfig(BaseModel):
    version_id: str
    name: str
    description: str
    system_prompt: str
    input_filter: bool = True
    output_filter: bool = True
    trust_tool_output: bool = False
    sanitize_memory: bool = True
    allowed_tools: List[str] = Field(default_factory=lambda: ["search_docs", "read_file"])
    expected_outcome: str = "PROMOTE"  # "PROMOTE" or "ROLLBACK"


VERSION_V1_HARDENED = AgentVersionConfig(
    version_id="v1.0.0",
    name="v1 - Hardened Baseline",
    description="Strict system prompt, input/output filtering enabled, admin tools restricted, sanitized memory.",
    system_prompt=PROMPT_V1_HARDENED,
    input_filter=True,
    output_filter=True,
    trust_tool_output=False,
    sanitize_memory=True,
    allowed_tools=["search_docs", "read_file"],
    expected_outcome="PROMOTE",
)

VERSION_V2_WEAK = AgentVersionConfig(
    version_id="v2.0.0",
    name="v2 - Vulnerable Candidate",
    description="Permissive prompt, input/output filters disabled, trusts tool outputs, allows run_sql, unsanitized memory.",
    system_prompt=PROMPT_V2_WEAK,
    input_filter=False,
    output_filter=False,
    trust_tool_output=True,
    sanitize_memory=False,
    allowed_tools=["search_docs", "read_file", "send_email", "run_sql"],
    expected_outcome="ROLLBACK",
)

VERSION_V3_MIXED = AgentVersionConfig(
    version_id="v1.5.0",
    name="v3 - Mixed Security",
    description="Standard input/output filter, but memory is unsanitized and vulnerable to two-turn memory poisoning.",
    system_prompt=PROMPT_V3_MIXED,
    input_filter=True,
    output_filter=True,
    trust_tool_output=False,
    sanitize_memory=False,
    allowed_tools=["search_docs", "read_file", "send_email"],
    expected_outcome="ROLLBACK",
)

PRESET_VERSIONS: Dict[str, AgentVersionConfig] = {
    "v1.0.0": VERSION_V1_HARDENED,
    "v2.0.0": VERSION_V2_WEAK,
    "v1.5.0": VERSION_V3_MIXED,
}


def get_version_config(version_id: str) -> AgentVersionConfig:
    """
    Retrieve version configuration by version ID, or fallback to v1.0.0.
    """
    if version_id in PRESET_VERSIONS:
        return PRESET_VERSIONS[version_id]
    # Return hardened default for unknown custom version tags
    return AgentVersionConfig(
        version_id=version_id,
        name=f"Custom Version {version_id}",
        description="Dynamic user configured version",
        system_prompt=PROMPT_V1_HARDENED,
    )
