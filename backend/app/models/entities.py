# app/models/entities.py
# Purpose: SQLAlchemy database models for versions, validation runs, attacks, deployments, and experiments.

import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class AgentVersionModel(Base):
    """
    Registered agent candidate versions and their configuration parameters.
    """
    __tablename__ = "agent_versions"

    id = Column(Integer, primary_key=True, index=True)
    version_id = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(Text, default="")
    system_prompt = Column(Text, nullable=False)
    input_filter = Column(Boolean, default=True)
    output_filter = Column(Boolean, default=True)
    trust_tool_output = Column(Boolean, default=False)
    sanitize_memory = Column(Boolean, default=True)
    allowed_tools = Column(Text, default="search_docs,read_file")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class ValidationRunModel(Base):
    """
    A full validation execution assessing a Green candidate version.
    """
    __tablename__ = "validation_runs"

    id = Column(Integer, primary_key=True, index=True)
    version_id = Column(String(50), nullable=False, index=True)
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    attacks_total = Column(Integer, default=0)
    attacks_done = Column(Integer, default=0)
    current_step = Column(String(255), default="Initialized")
    risk_score = Column(Float, default=0.0)
    decision = Column(String(20), default="PENDING")  # PROMOTE, ROLLBACK, PENDING
    metrics_json = Column(Text, default="{}")
    reasons_json = Column(Text, default="[]")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    attack_results = relationship("AttackResultModel", back_populates="validation_run", cascade="all, delete-orphan")
    task_results = relationship("TaskResultModel", back_populates="validation_run", cascade="all, delete-orphan")


class AttackResultModel(Base):
    """
    Individual attack execution result within a validation run.
    """
    __tablename__ = "attack_results"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("validation_runs.id"), nullable=False)
    attack_name = Column(String(100), nullable=False)
    category = Column(String(50), nullable=False)
    severity = Column(String(20), default="medium")
    prompt = Column(Text, nullable=False)
    agent_reply = Column(Text, default="")
    is_success = Column(Boolean, default=False)
    canary_leak = Column(Boolean, default=False)
    privilege_escalation = Column(Boolean, default=False)
    tool_misuse = Column(Boolean, default=False)
    policy_violation = Column(Boolean, default=False)
    latency_ms = Column(Float, default=0.0)
    notes = Column(Text, default="")

    validation_run = relationship("ValidationRunModel", back_populates="attack_results")


class TaskResultModel(Base):
    """
    Benign task execution outcome for evaluating utility/task completion success.
    """
    __tablename__ = "task_results"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("validation_runs.id"), nullable=False)
    task_id = Column(String(50), nullable=False)
    prompt = Column(Text, nullable=False)
    agent_reply = Column(Text, default="")
    is_success = Column(Boolean, default=False)
    latency_ms = Column(Float, default=0.0)

    validation_run = relationship("ValidationRunModel", back_populates="task_results")


class DeploymentStateModel(Base):
    """
    Current live Blue/Green routing state and traffic allocation.
    """
    __tablename__ = "deployment_states"

    id = Column(Integer, primary_key=True, index=True)
    active_color = Column(String(10), default="blue")  # "blue" or "green"
    blue_version = Column(String(50), default="v1.0.0")
    green_version = Column(String(50), default="v2.0.0")
    blue_traffic_percent = Column(Integer, default=100)
    green_traffic_percent = Column(Integer, default=0)
    last_switch_at = Column(DateTime, default=datetime.datetime.utcnow)
    notes = Column(Text, default="Initial deployment state")


class ExperimentModel(Base):
    """
    Research benchmark comparing Baseline (no red team) vs Proposed (red team driven).
    """
    __tablename__ = "experiments"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), default="Baseline vs Proposed Security Validation")
    baseline_results_json = Column(Text, default="[]")
    proposed_results_json = Column(Text, default="[]")
    summary_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class SettingsSnapshotModel(Base):
    """
    Historical record of configuration weights and thresholds used for runs.
    """
    __tablename__ = "settings_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    risk_threshold = Column(Float, default=0.25)
    risk_weights_json = Column(Text, default="{}")
    critical_rules_json = Column(Text, default="{}")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
