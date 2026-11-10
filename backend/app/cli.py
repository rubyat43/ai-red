#!/usr/bin/env python3
# app/cli.py
# Purpose: Interactive terminal UI (CLI) for full control of the AI Red Team Blue-Green Deployment backend.

import os
import sys
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parent.parent
_VENV_PYTHON = _BACKEND_DIR / "venv" / "bin" / "python"

# Ensure direct execution uses the project's venv and backend PYTHONPATH
if _VENV_PYTHON.exists() and Path(sys.prefix).resolve() != (_BACKEND_DIR / "venv").resolve():
    os.execv(str(_VENV_PYTHON), [str(_VENV_PYTHON), __file__, *sys.argv[1:]])

if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))
os.chdir(_BACKEND_DIR)

import csv
import datetime
import json
import subprocess
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.prompt import Confirm, FloatPrompt, IntPrompt, Prompt
from rich.table import Table
from rich.text import Text

from agents.redteam_agent.attacks.registry import get_all_attacks
from agents.redteam_agent.judge import judge_attack_result
from agents.redteam_agent.runner import RedTeamRunner
from agents.target_agent.agent import TargetAgent
from agents.target_agent.prompts import PROMPT_V1_HARDENED
from agents.target_agent.tools.registry import get_default_tool_registry
from agents.target_agent.versions import AgentVersionConfig, get_version_config
from app.agents_init import seed_default_versions
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.deployment import get_deployment_driver
from app.models.entities import (
    AgentVersionModel,
    AttackResultModel,
    ExperimentModel,
    SettingsSnapshotModel,
    TaskResultModel,
    ValidationRunModel,
)
from app.monitoring.prometheus import get_prometheus_metrics_bytes, update_prometheus_metrics
from app.services.decision_service import DecisionService
from app.services.evaluation_service import EvaluationService
from app.services.experiment_service import ExperimentService

console = Console()


def init_system() -> None:
    """Ensure database tables exist and default agent versions are seeded."""
    Base.metadata.create_all(bind=engine)
    seed_default_versions()


def pause() -> None:
    """Wait for user before returning to the previous menu."""
    console.print()
    Prompt.ask("[dim]Press Enter to continue[/dim]", default="", show_default=False)


def ask_choice(title: str, options: List[tuple[str, str]], back_label: str = "Back") -> str:
    """
    Display a numbered menu and return the chosen option key.
    options: list of (key, label) tuples. '0' is reserved for Back/Exit.
    """
    console.print()
    table = Table(box=box.ROUNDED, show_header=False, border_style="cyan", padding=(0, 2))
    table.add_column("Option", style="bold yellow", width=6, justify="center")
    table.add_column("Action", style="white")
    for key, label in options:
        table.add_row(f"[{key}]", label)
    table.add_row("[0]", f"[dim]{back_label}[/dim]")

    console.print(Panel(table, title=f"[bold cyan]{title}[/bold cyan]", border_style="cyan", expand=False))

    valid_keys = {k for k, _ in options} | {"0"}
    while True:
        choice = Prompt.ask("[bold yellow]Select option[/bold yellow]", default="0").strip()
        if choice in valid_keys:
            return choice
        console.print(f"[red]Invalid choice '{choice}'. Please choose one of: {', '.join(sorted(valid_keys))}[/red]")


def render_status_banner() -> None:
    """Render live Blue-Green deployment status and current settings at the top of the main menu."""
    driver = get_deployment_driver()
    state = driver.get_state()
    active = state["active_color"].upper()
    active_style = "bold blue" if active == "BLUE" else "bold green"

    with SessionLocal() as db:
        runs_count = db.query(ValidationRunModel).count()
        versions_count = db.query(AgentVersionModel).count()
        exp_count = db.query(ExperimentModel).count()

    grid = Table.grid(expand=True)
    grid.add_column(ratio=1)
    grid.add_column(ratio=1)
    grid.add_row(
        f"[bold]Live Environment:[/bold] [{active_style}]{active}[/{active_style}] "
        f"(Blue: [cyan]{state['blue_version']}[/cyan] {state['blue_traffic_percent']}% | "
        f"Green: [green]{state['green_version']}[/green] {state['green_traffic_percent']}%)",
        f"[bold]Driver:[/bold] {settings.deployment_driver}  |  [bold]LLM:[/bold] {settings.llm_mode}  |  "
        f"[bold]Risk Limit:[/bold] {settings.risk_threshold:.2f}",
    )
    grid.add_row(
        f"[dim]Versions: {versions_count}  |  Validation Runs: {runs_count}  |  Experiments: {exp_count}[/dim]",
        f"[dim]DB: {settings.database_url}[/dim]",
    )
    console.print(
        Panel(
            grid,
            title="[bold white on red] AI RED TEAM — BLUE-GREEN SECURITY TERMINAL [/bold white on red]",
            border_style="red",
        )
    )


def _load_version_config(version_id: str) -> AgentVersionConfig:
    """Load an AgentVersionConfig from the database or fall back to presets."""
    with SessionLocal() as db:
        rec = db.query(AgentVersionModel).filter(AgentVersionModel.version_id == version_id).first()
        if rec:
            allowed = [t.strip() for t in rec.allowed_tools.split(",") if t.strip()]
            return AgentVersionConfig(
                version_id=rec.version_id,
                name=rec.name,
                description=rec.description or "",
                system_prompt=rec.system_prompt,
                input_filter=rec.input_filter,
                output_filter=rec.output_filter,
                trust_tool_output=rec.trust_tool_output,
                sanitize_memory=rec.sanitize_memory,
                allowed_tools=allowed,
            )
    return get_version_config(version_id)


def _select_version_prompt(prompt_text: str = "Select agent version") -> Optional[str]:
    """Show registered agent versions in a numbered list and let the user pick one."""
    with SessionLocal() as db:
        versions = db.query(AgentVersionModel).order_by(AgentVersionModel.id.asc()).all()

    if not versions:
        console.print("[red]No agent versions registered.[/red]")
        return None

    table = Table(title="Registered Agent Versions", box=box.SIMPLE_HEAVY)
    table.add_column("#", style="bold yellow", width=4)
    table.add_column("Version ID", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Input Filter", justify="center")
    table.add_column("Output Filter", justify="center")
    table.add_column("Sanitize Mem", justify="center")
    table.add_column("Allowed Tools", style="dim")

    for idx, v in enumerate(versions, start=1):
        table.add_row(
            str(idx),
            v.version_id,
            v.name,
            "[green]ON[/green]" if v.input_filter else "[red]OFF[/red]",
            "[green]ON[/green]" if v.output_filter else "[red]OFF[/red]",
            "[green]ON[/green]" if v.sanitize_memory else "[red]OFF[/red]",
            v.allowed_tools,
        )
    console.print(table)
    console.print("[dim]Enter number (1..N) or 0 to cancel[/dim]")

    while True:
        raw = Prompt.ask(prompt_text, default="1").strip()
        if raw == "0":
            return None
        if raw.isdigit() and 1 <= int(raw) <= len(versions):
            return versions[int(raw) - 1].version_id
        # Also allow typing exact version_id
        for v in versions:
            if v.version_id == raw:
                return v.version_id
        console.print("[red]Invalid selection. Enter a valid row number or version ID.[/red]")


# ---------------------------------------------------------------------------
# 1. Deployment & Blue-Green Status Menu
# ---------------------------------------------------------------------------
def menu_deployments() -> None:
    while True:
        driver = get_deployment_driver()
        state = driver.get_state()

        state_table = Table(title="Blue-Green Deployment State", box=box.ROUNDED, border_style="blue")
        state_table.add_column("Field", style="bold cyan")
        state_table.add_column("Value", style="white")
        active_color = state["active_color"].upper()
        badge = f"[bold blue]{active_color}[/bold blue]" if active_color == "BLUE" else f"[bold green]{active_color}[/bold green]"
        state_table.add_row("Active Live Color", badge)
        state_table.add_row("Blue Version", f"{state['blue_version']} ({state['blue_traffic_percent']}% traffic)")
        state_table.add_row("Green Version", f"{state['green_version']} ({state['green_traffic_percent']}% traffic)")
        state_table.add_row("Driver", str(state.get("driver", settings.deployment_driver)))
        state_table.add_row("Last Switch", str(state["last_switch_at"]))
        state_table.add_row("Notes", state["notes"])
        console.print()
        console.print(state_table)

        choice = ask_choice(
            "Deployment & Blue-Green Control",
            [
                ("1", "Deploy a version to Green (staging, 0% traffic)"),
                ("2", "Manually Promote Green to live traffic (100%)"),
                ("3", "Manually Rollback to Blue (100% safe traffic)"),
                ("4", f"Switch Deployment Driver (current: {settings.deployment_driver})"),
            ],
        )

        if choice == "0":
            return
        elif choice == "1":
            ver = _select_version_prompt("Choose version to stage in Green")
            if ver:
                url = driver.deploy_green(ver)
                console.print(f"[green]Deployed '{ver}' to Green ({url}) with 0% live traffic.[/green]")
                pause()
        elif choice == "2":
            if Confirm.ask(f"Switch 100% live traffic to Green ({state['green_version']})?", default=False):
                driver.promote_green()
                console.print("[bold green]Promoted Green to live production traffic.[/bold green]")
                pause()
        elif choice == "3":
            driver.rollback_to_blue()
            console.print("[bold yellow]Rolled back: 100% traffic routed to Blue.[/bold yellow]")
            pause()
        elif choice == "4":
            new_driver = Prompt.ask("Select driver", choices=["local", "k8s"], default=settings.deployment_driver)
            settings.deployment_driver = new_driver
            console.print(f"[green]Deployment driver switched to '{new_driver}'.[/green]")
            pause()


# ---------------------------------------------------------------------------
# 2. Validation Runs (AI Red Team Gate) Menu
# ---------------------------------------------------------------------------
def _execute_cli_validation(version_id: str, external_url: Optional[str] = None) -> None:
    """Run full Red Team validation with a live terminal progress bar and persist results."""
    driver = get_deployment_driver()

    with SessionLocal() as db:
        run = ValidationRunModel(
            version_id=version_id,
            status="running",
            attacks_total=0,
            attacks_done=0,
            current_step=f"Deploying {version_id} to Green",
            decision="PENDING",
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        run_id = run.id

    if external_url:
        console.print(f"\n[cyan]Run #{run_id}: Targeting external HTTP agent at {external_url}[/cyan]")
    else:
        driver.deploy_green(version_id)
        console.print(f"\n[cyan]Run #{run_id}: Deployed '{version_id}' to Green environment[/cyan]")

    version_cfg = _load_version_config(version_id)
    candidate_agent = None if external_url else TargetAgent(version_config=version_cfg)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        attack_task = progress.add_task("[red]Running AI Red Team attacks...", total=None)

        def on_progress(done: int, total: int, step_desc: str) -> None:
            progress.update(attack_task, total=total, completed=done, description=f"[red]{step_desc}")
            with SessionLocal() as p_db:
                p_run = p_db.query(ValidationRunModel).filter(ValidationRunModel.id == run_id).first()
                if p_run:
                    p_run.attacks_done = done
                    p_run.attacks_total = total
                    p_run.current_step = step_desc
                    p_db.commit()

        runner = RedTeamRunner(
            target_agent=candidate_agent,
            target_url=external_url,
            progress_callback=on_progress,
        )
        attack_items = runner.run_all_attacks()
        progress.update(attack_task, description="[green]Attacks complete. Running benign tasks...")
        task_items = runner.run_all_tasks()

    metrics, risk_score, critical_counts = EvaluationService.evaluate_run(attack_items, task_items)
    decision_data = DecisionService.decide(
        risk_score=risk_score,
        metrics=metrics,
        critical_counts=critical_counts,
    )
    decision = decision_data["decision"]
    reasons = decision_data["reasons"]

    if decision == "PROMOTE":
        driver.promote_green()
        step_msg = f"Promoted Green ({version_id}) to production live traffic"
    else:
        driver.rollback_to_blue()
        step_msg = f"Rolled back to Blue. Green ({version_id}) rejected due to security risks"

    with SessionLocal() as db:
        run = db.query(ValidationRunModel).filter(ValidationRunModel.id == run_id).first()
        if run:
            for a in attack_items:
                db.add(
                    AttackResultModel(
                        run_id=run.id,
                        attack_name=a.attack_name,
                        category=a.category,
                        severity=a.severity,
                        prompt=a.prompt,
                        agent_reply=a.agent_reply,
                        is_success=a.is_success,
                        canary_leak=a.canary_leak,
                        privilege_escalation=a.privilege_escalation,
                        tool_misuse=a.tool_misuse,
                        policy_violation=a.policy_violation,
                        latency_ms=a.latency_ms,
                        notes=a.notes,
                    )
                )
            for t in task_items:
                db.add(
                    TaskResultModel(
                        run_id=run.id,
                        task_id=t.task_id,
                        prompt=t.prompt,
                        agent_reply=t.agent_reply,
                        is_success=t.is_success,
                        latency_ms=t.latency_ms,
                    )
                )
            run.status = "completed"
            run.current_step = step_msg
            run.risk_score = risk_score
            run.decision = decision
            run.metrics_json = json.dumps(metrics)
            run.reasons_json = json.dumps(reasons)
            run.completed_at = datetime.datetime.now(datetime.UTC).replace(tzinfo=None)
            db.commit()

    update_prometheus_metrics(metrics, risk_score, decision)
    _print_run_detail(run_id)


def _print_run_detail(run_id: int) -> None:
    """Display full validation run report in the terminal."""
    with SessionLocal() as db:
        run = db.query(ValidationRunModel).filter(ValidationRunModel.id == run_id).first()
        if not run:
            console.print(f"[red]Run #{run_id} not found.[/red]")
            return
        attacks = db.query(AttackResultModel).filter(AttackResultModel.run_id == run_id).all()
        tasks = db.query(TaskResultModel).filter(TaskResultModel.run_id == run_id).all()

    metrics = json.loads(run.metrics_json or "{}")
    reasons = json.loads(run.reasons_json or "[]")

    dec_style = "bold green" if run.decision == "PROMOTE" else "bold red" if run.decision == "ROLLBACK" else "yellow"
    summary = Table.grid(padding=(0, 3))
    summary.add_row("[bold]Run ID:[/bold]", f"#{run.id}", "[bold]Version:[/bold]", run.version_id)
    summary.add_row("[bold]Decision:[/bold]", f"[{dec_style}]{run.decision}[/{dec_style}]", "[bold]Risk Score:[/bold]", f"{run.risk_score:.4f} (limit {settings.risk_threshold:.2f})")
    summary.add_row("[bold]Status:[/bold]", run.status, "[bold]Attacks:[/bold]", f"{run.attacks_done}/{run.attacks_total}")
    console.print()
    console.print(Panel(summary, title=f"[bold]Validation Run #{run.id} Summary[/bold]", border_style="green" if run.decision == "PROMOTE" else "red"))

    if reasons:
        console.print("[bold]Decision Reasons:[/bold]")
        for r in reasons:
            console.print(f"  • {r}")

    if metrics:
        m_table = Table(title="Security & Utility Metrics", box=box.SIMPLE)
        m_table.add_column("Metric", style="cyan")
        m_table.add_column("Value", justify="right", style="bold")
        for k, v in metrics.items():
            m_table.add_row(k, f"{v:.4f}" if isinstance(v, float) and v <= 1.0 else f"{v:.2f}")
        console.print(m_table)

    if attacks:
        a_table = Table(title=f"Attack Results ({len(attacks)} payloads)", box=box.ROUNDED, show_lines=True)
        a_table.add_column("#", width=3)
        a_table.add_column("Category", style="cyan", width=18)
        a_table.add_column("Result", width=14)
        a_table.add_column("Flags", width=22)
        a_table.add_column("Prompt / Notes", style="white")
        for idx, a in enumerate(attacks, start=1):
            res_str = "[bold red]BREACHED[/bold red]" if a.is_success else "[green]BLOCKED[/green]"
            flags = []
            if a.canary_leak:
                flags.append("[red]CANARY_LEAK[/red]")
            if a.privilege_escalation:
                flags.append("[red]PRIV_ESC[/red]")
            if a.tool_misuse:
                flags.append("[yellow]TOOL_MISUSE[/yellow]")
            if a.policy_violation:
                flags.append("[yellow]POLICY[/yellow]")
            flag_str = ", ".join(flags) if flags else "[dim]none[/dim]"
            snippet = a.prompt[:75] + ("..." if len(a.prompt) > 75 else "")
            a_table.add_row(str(idx), a.category, res_str, flag_str, f"{snippet}\n[dim]{a.notes}[/dim]")
        console.print(a_table)

    if tasks:
        passed = sum(1 for t in tasks if t.is_success)
        console.print(f"[bold]Benign Tasks Passed:[/bold] {passed}/{len(tasks)}")


def menu_validation_runs() -> None:
    while True:
        choice = ask_choice(
            "Validation Runs (AI Red Team Gate)",
            [
                ("1", "Start new Validation Run (Built-in / Registered Agent Version)"),
                ("2", "Start new Validation Run against External HTTP Agent URL"),
                ("3", "List all Validation Runs"),
                ("4", "Inspect a Validation Run in detail"),
            ],
        )

        if choice == "0":
            return
        elif choice == "1":
            ver = _select_version_prompt("Choose agent version to validate")
            if ver:
                _execute_cli_validation(ver)
                pause()
        elif choice == "2":
            url = Prompt.ask("Enter target agent base URL (must expose POST /chat)", default="http://127.0.0.1:8001").strip()
            host = urlparse(url).hostname or ""
            if host not in settings.allowed_target_hosts:
                console.print(
                    f"[red]Host '{host}' is not in ALLOWED_TARGET_HOSTS ({settings.allowed_target_hosts}).[/red]"
                )
                if Confirm.ask("Add this host to ALLOWED_TARGET_HOSTS for this session?", default=False):
                    settings.allowed_target_hosts.append(host)
                else:
                    pause()
                    continue
            label = Prompt.ask("Label for this external candidate version", default="external-green")
            try:
                _execute_cli_validation(label, external_url=url)
            except Exception as exc:
                console.print(f"[red]Failed to validate external agent: {exc}[/red]")
            pause()
        elif choice == "3":
            with SessionLocal() as db:
                runs = db.query(ValidationRunModel).order_by(ValidationRunModel.id.desc()).limit(25).all()
            if not runs:
                console.print("[yellow]No validation runs recorded yet.[/yellow]")
            else:
                table = Table(title="Recent Validation Runs", box=box.ROUNDED)
                table.add_column("ID", style="bold yellow", width=5)
                table.add_column("Version", style="cyan")
                table.add_column("Status")
                table.add_column("Decision")
                table.add_column("Risk Score", justify="right")
                table.add_column("Created At", style="dim")
                for r in runs:
                    dec = (
                        "[bold green]PROMOTE[/bold green]"
                        if r.decision == "PROMOTE"
                        else "[bold red]ROLLBACK[/bold red]"
                        if r.decision == "ROLLBACK"
                        else r.decision
                    )
                    table.add_row(str(r.id), r.version_id, r.status, dec, f"{r.risk_score:.4f}", str(r.created_at)[:19])
                console.print(table)
            pause()
        elif choice == "4":
            run_id = IntPrompt.ask("Enter Run ID")
            _print_run_detail(run_id)
            pause()


# ---------------------------------------------------------------------------
# 3. Agent Versions Menu
# ---------------------------------------------------------------------------
def menu_agent_versions() -> None:
    while True:
        choice = ask_choice(
            "Agent Versions (Target Profiles)",
            [
                ("1", "List all registered Agent Versions"),
                ("2", "Inspect full profile & system prompt of a version"),
                ("3", "Register / Create a new custom Agent Version"),
            ],
        )
        if choice == "0":
            return
        elif choice == "1":
            with SessionLocal() as db:
                versions = db.query(AgentVersionModel).order_by(AgentVersionModel.id.asc()).all()
            table = Table(title="Agent Versions", box=box.ROUNDED)
            table.add_column("Version ID", style="cyan")
            table.add_column("Name", style="bold")
            table.add_column("In Filter")
            table.add_column("Out Filter")
            table.add_column("Trust Tool")
            table.add_column("Sanitize Mem")
            table.add_column("Allowed Tools")
            for v in versions:
                table.add_row(
                    v.version_id,
                    v.name,
                    "YES" if v.input_filter else "NO",
                    "YES" if v.output_filter else "NO",
                    "YES" if v.trust_tool_output else "NO",
                    "YES" if v.sanitize_memory else "NO",
                    v.allowed_tools,
                )
            console.print(table)
            pause()
        elif choice == "2":
            ver = _select_version_prompt("Select version to inspect")
            if ver:
                cfg = _load_version_config(ver)
                info = (
                    f"[bold]Name:[/bold] {cfg.name}\n"
                    f"[bold]Description:[/bold] {cfg.description}\n"
                    f"[bold]Input Filter:[/bold] {cfg.input_filter}  |  [bold]Output Filter:[/bold] {cfg.output_filter}\n"
                    f"[bold]Trust Tool Output:[/bold] {cfg.trust_tool_output}  |  [bold]Sanitize Memory:[/bold] {cfg.sanitize_memory}\n"
                    f"[bold]Allowed Tools:[/bold] {', '.join(cfg.allowed_tools)}\n\n"
                    f"[bold]System Prompt:[/bold]\n[dim]{cfg.system_prompt}[/dim]"
                )
                console.print(Panel(info, title=f"Version {cfg.version_id}", border_style="cyan"))
                pause()
        elif choice == "3":
            version_id = Prompt.ask("New Version ID (e.g. v2.1.0)").strip()
            with SessionLocal() as db:
                if db.query(AgentVersionModel).filter(AgentVersionModel.version_id == version_id).first():
                    console.print(f"[red]Version '{version_id}' already exists.[/red]")
                    pause()
                    continue
                name = Prompt.ask("Display Name", default=f"Custom {version_id}")
                desc = Prompt.ask("Description", default="Custom agent security profile")
                sys_prompt = Prompt.ask("System Prompt", default=PROMPT_V1_HARDENED)
                in_filter = Confirm.ask("Enable Input Filter?", default=True)
                out_filter = Confirm.ask("Enable Output Filter?", default=True)
                trust_tool = Confirm.ask("Trust Tool Output blindly?", default=False)
                sanitize_mem = Confirm.ask("Sanitize Memory?", default=True)
                available_tools = list(get_default_tool_registry().keys())
                console.print(f"Available tools: [cyan]{', '.join(available_tools)}[/cyan]")
                tools_raw = Prompt.ask("Allowed tools (comma-separated)", default="search_docs,read_file")

                db.add(
                    AgentVersionModel(
                        version_id=version_id,
                        name=name,
                        description=desc,
                        system_prompt=sys_prompt,
                        input_filter=in_filter,
                        output_filter=out_filter,
                        trust_tool_output=trust_tool,
                        sanitize_memory=sanitize_mem,
                        allowed_tools=tools_raw,
                    )
                )
                db.commit()
            console.print(f"[green]Registered agent version '{version_id}'.[/green]")
            pause()


# ---------------------------------------------------------------------------
# 4. Live Interactive Chat Menu
# ---------------------------------------------------------------------------
def _chat_session(version_id: str, label: str) -> None:
    cfg = _load_version_config(version_id)
    agent = TargetAgent(version_config=cfg)
    console.print(
        Panel(
            f"Chatting with [bold cyan]{label}[/bold cyan] (version: [bold]{version_id}[/bold])\n"
            f"Type [bold yellow]/exit[/bold yellow] or [bold yellow]quit[/bold yellow] to return to menu. "
            f"Type [bold yellow]/reset[/bold yellow] to clear memory.",
            border_style="green",
        )
    )
    while True:
        try:
            msg = Prompt.ask("[bold green]You[/bold green]")
        except (EOFError, KeyboardInterrupt):
            break
        if msg.strip().lower() in {"/exit", "exit", "quit", "/quit"}:
            break
        if msg.strip().lower() == "/reset":
            agent = TargetAgent(version_config=cfg)
            console.print("[dim]Agent memory reset.[/dim]")
            continue
        if not msg.strip():
            continue

        reply = agent.handle(msg)
        console.print(f"[bold cyan]Agent ({version_id}):[/bold cyan] {reply.reply}")
        tools_used = reply.trace.get("tools_executed", [])
        flags = reply.trace.get("flags", [])
        console.print(
            f"[dim]  ↳ latency={reply.latency_ms:.1f}ms | tools={tools_used} | flags={flags}[/dim]"
        )


def menu_live_chat() -> None:
    while True:
        driver = get_deployment_driver()
        state = driver.get_state()
        active_color = state["active_color"]
        active_ver = state["green_version"] if active_color == "green" else state["blue_version"]

        choice = ask_choice(
            "Live Interactive Chat",
            [
                ("1", f"Chat with currently LIVE production agent ({active_color.upper()} -> {active_ver})"),
                ("2", "Chat with a specific Agent Version (sandbox test)"),
            ],
        )
        if choice == "0":
            return
        elif choice == "1":
            _chat_session(active_ver, f"LIVE {active_color.upper()}")
        elif choice == "2":
            ver = _select_version_prompt("Select agent version to chat with")
            if ver:
                _chat_session(ver, f"Sandbox {ver}")


# ---------------------------------------------------------------------------
# 5. AI Red Team Attack Library Menu
# ---------------------------------------------------------------------------
def menu_attacks() -> None:
    attacks = get_all_attacks()
    while True:
        choice = ask_choice(
            "AI Red Team Attack Library",
            [
                ("1", "List all attack categories"),
                ("2", "Inspect attack prompts for a category"),
                ("3", "Run a single attack category against an Agent Version"),
            ],
        )
        if choice == "0":
            return
        elif choice == "1":
            table = Table(title="Registered Attack Vectors", box=box.ROUNDED)
            table.add_column("#", style="yellow", width=4)
            table.add_column("Name", style="bold")
            table.add_column("Category", style="cyan")
            table.add_column("Severity")
            table.add_column("Payloads", justify="right")
            table.add_column("Description")
            for idx, a in enumerate(attacks, start=1):
                sev_color = "red" if a.severity in ("critical", "high") else "yellow"
                table.add_row(
                    str(idx),
                    a.name,
                    a.category,
                    f"[{sev_color}]{a.severity.upper()}[/{sev_color}]",
                    str(len(a.build_prompts())),
                    a.description,
                )
            console.print(table)
            pause()
        elif choice in {"2", "3"}:
            for idx, a in enumerate(attacks, start=1):
                console.print(f"  [{idx}] {a.name} ({a.category})")
            sel = IntPrompt.ask("Choose attack number", default=1)
            if not (1 <= sel <= len(attacks)):
                console.print("[red]Invalid attack index.[/red]")
                pause()
                continue
            atk = attacks[sel - 1]
            if choice == "2":
                console.print(Panel(f"[bold]{atk.name}[/bold] — {atk.description}", border_style="red"))
                for i, p in enumerate(atk.build_prompts(), start=1):
                    console.print(f"[yellow]{i}.[/yellow] {p}")
                pause()
            else:
                ver = _select_version_prompt("Choose target version to attack")
                if not ver:
                    continue
                agent = TargetAgent(version_config=_load_version_config(ver))
                for i, p in enumerate(atk.build_prompts(), start=1):
                    reply_obj = agent.handle(p)
                    judg = judge_attack_result(atk, reply_obj.reply, reply_obj.trace)
                    status = "[bold red]BREACHED[/bold red]" if judg["is_success"] else "[green]BLOCKED[/green]"
                    console.print(f"\n[bold]Payload {i}:[/bold] {p}")
                    console.print(f"[bold]Reply:[/bold] {reply_obj.reply}")
                    console.print(f"[bold]Result:[/bold] {status} — {judg['notes']}")
                pause()


# ---------------------------------------------------------------------------
# 6. Comparative Experiments Menu
# ---------------------------------------------------------------------------
def _print_experiment_summary(summary: Dict[str, Any], title: str) -> None:
    base = summary.get("baseline", {})
    prop = summary.get("proposed", {})
    table = Table(title=title, box=box.ROUNDED)
    table.add_column("Metric", style="bold cyan")
    table.add_column("Baseline (Health Check Only)", justify="right", style="yellow")
    table.add_column("Proposed (AI Red Team + Blue-Green)", justify="right", style="green")
    table.add_row("Total Rounds", str(summary.get("total_rounds", "-")), str(summary.get("total_rounds", "-")))
    table.add_row("Decision Accuracy (%)", f"{base.get('decision_accuracy_percent', 0)}%", f"{prop.get('decision_accuracy_percent', 0)}%")
    table.add_row("Vulnerable Versions Promoted", str(base.get("vulnerable_versions_promoted", 0)), str(prop.get("vulnerable_versions_promoted", 0)))
    table.add_row("Leakage Incident Rate (%)", f"{base.get('leakage_incident_rate', 0)}%", f"{prop.get('leakage_incident_rate', 0)}%")
    table.add_row("Avg Decision Time (ms)", str(base.get("avg_decision_time_ms", 0)), str(prop.get("avg_decision_time_ms", 0)))
    table.add_row("Service Availability", str(base.get("service_availability", "-")), str(prop.get("service_availability", "-")))
    console.print(table)
    console.print(f"[bold green]Risk Reduction:[/bold green] {summary.get('risk_reduction_percent', 0)}%")


def menu_experiments() -> None:
    while True:
        choice = ask_choice(
            "Comparative Experiments (Baseline vs Proposed)",
            [
                ("1", "Run new Baseline vs Proposed Experiment"),
                ("2", "List past Experiments"),
                ("3", "Inspect Experiment & Export CSV"),
            ],
        )
        if choice == "0":
            return
        elif choice == "1":
            rounds = IntPrompt.ask("Number of experiment rounds", default=10)
            with console.status("[cyan]Running comparative experiment...[/cyan]"):
                res = ExperimentService.run_comparative_experiment(rounds=rounds)
            _print_experiment_summary(res["summary"], f"Experiment #{res['id']} Results")
            pause()
        elif choice == "2":
            with SessionLocal() as db:
                exps = db.query(ExperimentModel).order_by(ExperimentModel.id.desc()).all()
            if not exps:
                console.print("[yellow]No experiments recorded yet.[/yellow]")
            else:
                table = Table(title="Recorded Experiments", box=box.ROUNDED)
                table.add_column("ID", style="yellow")
                table.add_column("Title")
                table.add_column("Baseline Acc")
                table.add_column("Proposed Acc")
                table.add_column("Created At", style="dim")
                for e in exps:
                    s = json.loads(e.summary_json or "{}")
                    table.add_row(
                        str(e.id),
                        e.title,
                        f"{s.get('baseline', {}).get('decision_accuracy_percent', '-')}%",
                        f"{s.get('proposed', {}).get('decision_accuracy_percent', '-')}%",
                        str(e.created_at)[:19],
                    )
                console.print(table)
            pause()
        elif choice == "3":
            exp_id = IntPrompt.ask("Enter Experiment ID")
            with SessionLocal() as db:
                exp = db.query(ExperimentModel).filter(ExperimentModel.id == exp_id).first()
            if not exp:
                console.print(f"[red]Experiment #{exp_id} not found.[/red]")
                pause()
                continue
            summary = json.loads(exp.summary_json or "{}")
            baseline = json.loads(exp.baseline_results_json or "[]")
            proposed = json.loads(exp.proposed_results_json or "[]")
            _print_experiment_summary(summary, f"Experiment #{exp.id}: {exp.title}")
            if Confirm.ask("Export combined records to CSV?", default=False):
                out_path = Prompt.ask("CSV output path", default=f"experiment_{exp.id}.csv")
                rows = baseline + proposed
                if rows:
                    with open(out_path, "w", newline="", encoding="utf-8") as f:
                        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
                        writer.writeheader()
                        writer.writerows(rows)
                    console.print(f"[green]Exported {len(rows)} rows to {os.path.abspath(out_path)}[/green]")
            pause()


# ---------------------------------------------------------------------------
# 7. Settings, Thresholds & Prometheus Metrics Menu
# ---------------------------------------------------------------------------
def _save_settings_snapshot() -> None:
    with SessionLocal() as db:
        db.add(
            SettingsSnapshotModel(
                risk_threshold=settings.risk_threshold,
                risk_weights_json=json.dumps(settings.risk_weights),
                critical_rules_json=json.dumps(settings.critical_rules),
                created_at=datetime.datetime.now(datetime.UTC).replace(tzinfo=None),
            )
        )
        db.commit()


def menu_settings() -> None:
    while True:
        s_table = Table(title="Current Evaluation & System Settings", box=box.ROUNDED)
        s_table.add_column("Setting", style="cyan")
        s_table.add_column("Value", style="bold")
        s_table.add_row("risk_threshold", str(settings.risk_threshold))
        s_table.add_row("max_response_time_ms", str(settings.max_response_time_ms))
        s_table.add_row("llm_mode", settings.llm_mode)
        s_table.add_row("llm_model", settings.llm_model)
        s_table.add_row("deployment_driver", settings.deployment_driver)
        s_table.add_row("risk_weights", json.dumps(settings.risk_weights))
        s_table.add_row("critical_rules", json.dumps(settings.critical_rules))
        console.print()
        console.print(s_table)

        choice = ask_choice(
            "Settings & Observability",
            [
                ("1", "Update Risk Threshold (0.0 - 1.0)"),
                ("2", "Update Risk Weights"),
                ("3", "Update Critical Rules"),
                ("4", f"Toggle LLM Mode (current: {settings.llm_mode})"),
                ("5", "View Prometheus /metrics output"),
            ],
        )
        if choice == "0":
            return
        elif choice == "1":
            val = FloatPrompt.ask("New risk_threshold (0.0 - 1.0)", default=settings.risk_threshold)
            settings.risk_threshold = max(0.0, min(1.0, val))
            _save_settings_snapshot()
            console.print(f"[green]Updated risk_threshold to {settings.risk_threshold}[/green]")
            pause()
        elif choice == "2":
            new_weights = {}
            for k, v in settings.risk_weights.items():
                new_weights[k] = FloatPrompt.ask(f"Weight for {k}", default=v)
            total = round(sum(new_weights.values()), 4)
            console.print(f"Sum of weights: [bold]{total}[/bold]")
            if abs(total - 1.0) > 0.01:
                console.print("[yellow]Warning: Weights do not sum to 1.0.[/yellow]")
            if Confirm.ask("Save new weights?", default=True):
                settings.risk_weights = new_weights
                _save_settings_snapshot()
                console.print("[green]Risk weights updated.[/green]")
            pause()
        elif choice == "3":
            for k, v in settings.critical_rules.items():
                settings.critical_rules[k] = IntPrompt.ask(f"{k}", default=v)
            _save_settings_snapshot()
            console.print("[green]Critical rules updated.[/green]")
            pause()
        elif choice == "4":
            mode = Prompt.ask("Select LLM mode", choices=["mock", "provider"], default=settings.llm_mode)
            settings.llm_mode = mode
            console.print(f"[green]LLM mode set to '{mode}'.[/green]")
            pause()
        elif choice == "5":
            data, _ = get_prometheus_metrics_bytes()
            console.print(Panel(Text(data.decode("utf-8"), style="dim"), title="Prometheus /metrics", border_style="cyan"))
            pause()


# ---------------------------------------------------------------------------
# 8. Diagnostics & Tests Menu
# ---------------------------------------------------------------------------
def menu_diagnostics() -> None:
    while True:
        choice = ask_choice(
            "Diagnostics & Test Suite",
            [
                ("1", "Run backend pytest suite"),
                ("2", "Start FastAPI HTTP server (uvicorn) in foreground"),
            ],
        )
        if choice == "0":
            return
        elif choice == "1":
            console.print("[cyan]Running pytest tests/...[/cyan]")
            subprocess.run([sys.executable, "-m", "pytest", "tests/", "-v"], check=False)
            pause()
        elif choice == "2":
            console.print(f"[cyan]Starting FastAPI server on http://{settings.host}:{settings.port} (Ctrl+C to stop)...[/cyan]")
            try:
                subprocess.run(
                    [sys.executable, "-m", "uvicorn", "app.main:app", "--host", settings.host, "--port", str(settings.port)],
                    check=False,
                )
            except KeyboardInterrupt:
                console.print("\n[yellow]Server stopped. Returning to terminal menu.[/yellow]")
            pause()


# ---------------------------------------------------------------------------
# Main Loop
# ---------------------------------------------------------------------------
def main() -> None:
    """Entry point for the interactive terminal application."""
    init_system()
    while True:
        render_status_banner()
        choice = ask_choice(
            "Main Menu",
            [
                ("1", "Deployments & Blue-Green Traffic Control"),
                ("2", "Validation Runs (Run AI Red Team & View Results)"),
                ("3", "Agent Versions (View & Create Profiles)"),
                ("4", "Live Interactive Chat (Production & Sandbox)"),
                ("5", "AI Red Team Attack Library (Browse & Single Test)"),
                ("6", "Comparative Experiments (Baseline vs Proposed + CSV)"),
                ("7", "Settings, Thresholds & Prometheus Metrics"),
                ("8", "Diagnostics, Pytest & API Server"),
            ],
            back_label="Exit Terminal",
        )

        if choice == "0":
            console.print("[bold cyan]Exiting AI Red Team Terminal. Goodbye![/bold cyan]")
            break
        elif choice == "1":
            menu_deployments()
        elif choice == "2":
            menu_validation_runs()
        elif choice == "3":
            menu_agent_versions()
        elif choice == "4":
            menu_live_chat()
        elif choice == "5":
            menu_attacks()
        elif choice == "6":
            menu_experiments()
        elif choice == "7":
            menu_settings()
        elif choice == "8":
            menu_diagnostics()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold cyan]Interrupted. Exiting.[/bold cyan]")

