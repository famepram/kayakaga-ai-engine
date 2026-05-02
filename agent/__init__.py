"""
Finai Agent Package
Personal Finance Advisor AI with agentic reasoning
"""

from .brain import FinaiAgent
from .tools import (
    get_transactions,
    calculate_budget,
    get_account_balances,
    simulate_investment,
    get_goals,
    categorize_transaction,
    TOOL_DEFINITIONS,
    TOOL_HANDLERS
)
from .prompts import build_system_prompt, build_welcome_message

__all__ = [
    "FinaiAgent",
    "get_transactions",
    "calculate_budget",
    "get_account_balances",
    "simulate_investment",
    "get_goals",
    "categorize_transaction",
    "TOOL_DEFINITIONS",
    "TOOL_HANDLERS",
    "build_system_prompt",
    "build_welcome_message"
]