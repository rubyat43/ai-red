# app/api/routes/attacks.py
# Purpose: Endpoint listing the AI Red Team attack library.

from typing import List
from fastapi import APIRouter
from app.schemas.schemas import AttackInfo
from agents.redteam_agent.attacks.registry import get_all_attacks

router = APIRouter(prefix="/attacks", tags=["Attacks Library"])


@router.get("", response_model=List[AttackInfo], summary="List Red Team Attack Vectors")
def get_attack_library():
    """
    Returns metadata and prompt variations for all registered Red Team attack modules.
    """
    attacks = get_all_attacks()
    return [
        AttackInfo(
            name=a.name,
            category=a.category,
            severity=a.severity,
            description=a.description,
            prompts=a.build_prompts(),
        )
        for a in attacks
    ]
