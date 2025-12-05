"""
Specialist Agents - Advanced tactical agents with specific roles.

🔫 Kinetik - Final seconds sniper
🥊 StrikeMaster - x5 glove strike master
📊 Activator - Bonus multiplier session trigger
🛡️ Sentinel - Defense and stealth specialist
🛡️ DefenseMaster - Counter-strategy and defense specialist
💰 BudgetOptimizer - Efficiency and ROI specialist
🎭 ChaoticTrickster - Psychological warfare specialist
🎯 SynergyCoordinator - Team combo specialist
"""

from .kinetik_sniper import AgentKinetik, GPTKinetik
from .strike_master import AgentStrikeMaster, GPTStrikeMaster
from .activator import AgentActivator, GPTActivator
from .sentinel import AgentSentinel, GPTSentinel
from .defense_master import DefenseMaster
from .budget_optimizer import BudgetOptimizer
from .chaotic_trickster import ChaoticTrickster
from .synergy_coordinator import SynergyCoordinator

__all__ = [
    'AgentKinetik',
    'GPTKinetik',
    'AgentStrikeMaster',
    'GPTStrikeMaster',
    'AgentActivator',
    'GPTActivator',
    'AgentSentinel',
    'GPTSentinel',
    # New agents (v1.3)
    'DefenseMaster',
    'BudgetOptimizer',
    'ChaoticTrickster',
    'SynergyCoordinator',
]
