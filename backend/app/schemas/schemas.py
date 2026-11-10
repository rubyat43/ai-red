# app/schemas/schemas.py
# Purpose: Pydantic request and response schemas for API validation and serialization.

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class AgentVersionCreate(BaseModel):
    version_id: str
    name: str
    description: Optional[str] = ""
    system_prompt: str
    input_filter: bool = True
    output_filter: bool = True
    trust_tool_output: bool = False
    sanitize_memory: bool = True
    allowed_tools: List[str] = ["search_docs", "read_file"]


class AgentVersionResponse(BaseModel):
    id: int
    version_id: str
    name: str
    description: str
    system_prompt: str
    input_filter: bool
    output_filter: bool
    trust_tool_output: bool
    sanitize_memory: bool
    allowed_tools: List[str]
    created_at: datetime


class AttackResultSchema(BaseModel):
    id: int
    attack_name: str
    category: str
    severity: str
    prompt: str
    agent_reply: str
    is_success: bool
    canary_leak: bool
    privilege_escalation: bool
    tool_misuse: bool
    policy_violation: bool
    latency_ms: float
    notes: str


class TaskResultSchema(BaseModel):
    id: int
    task_id: str
    prompt: str
    agent_reply: str
    is_success: bool
    latency_ms: float


class ValidationRunCreate(BaseModel):
    version_id: str


class ValidationRunResponse(BaseModel):
    id: int
    version_id: str
    status: str
    attacks_total: int
    attacks_done: int
    current_step: str
    risk_score: float
    decision: str
    metrics: Dict[str, float]
    reasons: List[str]
    created_at: datetime
    completed_at: Optional[datetime] = None


class ValidationRunDetail(ValidationRunResponse):
    attack_results: List[AttackResultSchema] = []
    task_results: List[TaskResultSchema] = []


class DeploymentStateResponse(BaseModel):
    active_color: str
    blue_version: str
    green_version: str
    blue_traffic_percent: int
    green_traffic_percent: int
    last_switch_at: datetime
    notes: str


class AttackInfo(BaseModel):
    name: str
    category: str
    severity: str
    description: str
    prompts: List[str]


class SettingsPayload(BaseModel):
    risk_threshold: float = 0.25
    max_response_time_ms: float = 4000.0
    risk_weights: Dict[str, float] = Field(default_factory=dict)
    critical_rules: Dict[str, int] = Field(default_factory=dict)
    llm_mode: Optional[str] = "mock"
    deployment_driver: Optional[str] = "local"


class ExperimentCreate(BaseModel):
    title: Optional[str] = "Baseline vs Proposed Red Team Validation"
    rounds: int = 10


class ExperimentResponse(BaseModel):
    id: int
    title: str
    baseline_results: List[Dict[str, Any]]
    proposed_results: List[Dict[str, Any]]
    summary: Dict[str, Any]
    created_at: datetime


class ChatMessageRequest(BaseModel):
    message: str


class ChatMessageResponse(BaseModel):
    reply: str
    version: str
    color: str
    trace: Dict[str, Any]
