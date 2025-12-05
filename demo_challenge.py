#!/usr/bin/env python3
"""
Challenge Mode Demo - Test Your Skills!

Pre-built scenarios that test specific skills:
- Survival challenges (defend against threats)
- Comeback challenges (overcome disadvantages)
- Efficiency challenges (win with limited resources)
- Mastery challenges (perfect execution)

Usage:
    python demo_challenge.py                    # List all challenges
    python demo_challenge.py --play <id>        # Play a specific challenge
    python demo_challenge.py --progress         # Show progress
    python demo_challenge.py --play first_victory  # Play "First Victory"
"""

import sys
import time
import random
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.challenge_system import ChallengeManager, ChallengeCategory, ChallengeDifficulty
from core.advanced_phase_system import AdvancedPhaseManager
from core.budget_system import BudgetManager
from agents.opponent_ai import OpponentAI, StrategyProfile
from agents.evolving_agents import create_mixed_strategic_team, reset_evolving_team
from core.battle_history import BattleHistoryDB


def run_challenge_battle(challenge, team, phase_manager, budget_manager, opponent):
    """
    Run a battle for a challenge and collect stats.
    """
    config = challenge.config

    # Apply start conditions
    creator_score = config.creator_start_score
    opponent_score = config.opponent_start_score
    start_time = config.start_time

    # Track stats for challenge evaluation
    stats = {
        'creator_score': 0,
        'opponent_score': 0,
        'winner': None,
        'boost1_points': 0,
        'boost2_points': 0,
        'boost2_qualified': False,
        'whale_gifts_sent': 0,
        'roses_sent': 0,
        'gloves_activated': 0,
        'x5_points': 0,
        'lead_at_175s': 0,
        'max_deficit': 0,
        'budget_spent': 0,
        'only_roses': True,  # Track if only roses sent
        'threshold_efficiency': 999,
        'glove_activated': False,
    }

    # Agent contribution tracking
    agent_contributions = {agent.name: {'points': 0, 'gifts': 0, 'whales': 0} for agent in team}

    print(f"\n{'='*70}")
    print(f"⚔️  CHALLENGE BATTLE STARTING")
    print(f"{'='*70}")

    if creator_score > 0 or opponent_score > 0:
        print(f"   Starting scores: Creator {creator_score:,} vs Opponent {opponent_score:,}")
    if start_time > 0:
        print(f"   Starting at {start_time}s (only {config.battle_duration - start_time}s remaining!)")
    print()

    battle_duration = config.battle_duration

    # Simulate battle
    for tick in range(start_time, battle_duration, 1):
        current_time = tick
        time_remaining = battle_duration - tick

        # Update phase manager
        phase_manager.update(current_time)
        multiplier = phase_manager.get_current_multiplier()

        # Track if in boost phases
        in_boost1 = phase_manager.boost1_active
        in_boost2 = phase_manager.boost2_active
        in_x5 = phase_manager.active_glove_x5 and phase_manager.active_glove_owner == "creator"

        # Agents act
        for agent in team:
            if random.random() < 0.3:  # 30% chance to act
                # Determine gift size based on phase and restrictions
                if not config.whale_gifts_allowed:
                    # Rose only mode
                    points = 1
                elif in_boost1 or in_boost2 or in_x5:
                    if random.random() < 0.15:
                        points = random.choice([10000, 29999, 44999])
                        stats['whale_gifts_sent'] += 1
                        agent_contributions[agent.name]['whales'] += 1
                    else:
                        points = random.choice([99, 299, 500, 1000])
                elif time_remaining <= 30:
                    points = random.choice([500, 1000, 5000])
                else:
                    points = random.choice([1, 5, 30, 99])

                # Track roses
                if points == 1:
                    stats['roses_sent'] += 1
                elif points > 1:
                    stats['only_roses'] = False

                effective = int(points * multiplier)
                creator_score += effective
                agent_contributions[agent.name]['points'] += effective
                agent_contributions[agent.name]['gifts'] += 1
                stats['budget_spent'] += points

                # Track boost points
                if in_boost1:
                    stats['boost1_points'] += effective
                if in_boost2:
                    stats['boost2_points'] += effective
                if in_x5:
                    stats['x5_points'] += effective

        # Opponent acts
        result = opponent.update(current_time, creator_score, opponent_score)
        if result['gift_sent']:
            effective = int(result['gift_points'] * multiplier)
            opponent_score += effective

        # Track glove activations
        if phase_manager.active_glove_x5 and phase_manager.active_glove_owner == "creator":
            if not stats['glove_activated']:
                stats['gloves_activated'] += 1
                stats['glove_activated'] = True
        else:
            stats['glove_activated'] = False

        # Track max deficit
        deficit = opponent_score - creator_score
        if deficit > stats['max_deficit']:
            stats['max_deficit'] = deficit

        # Track lead at 175s (for snipe survival)
        if tick == 175:
            stats['lead_at_175s'] = creator_score - opponent_score

        # Progress indicator
        if tick % 30 == 0 and tick > start_time:
            lead = creator_score - opponent_score
            lead_str = f"+{lead:,}" if lead >= 0 else f"{lead:,}"
            print(f"   ⏱️  {tick}s: Creator {creator_score:,} vs Opponent {opponent_score:,} ({lead_str})")

    # Determine winner
    stats['creator_score'] = creator_score
    stats['opponent_score'] = opponent_score
    stats['winner'] = 'creator' if creator_score > opponent_score else 'opponent'

    # Find MVP
    mvp_agent = max(agent_contributions.items(), key=lambda x: x[1]['points'])

    print(f"\n{'='*70}")
    print(f"🏁 CHALLENGE BATTLE COMPLETE!")
    print(f"   Winner: {stats['winner'].upper()}")
    print(f"   Score: Creator {creator_score:,} vs Opponent {opponent_score:,}")
    print(f"   Margin: {abs(creator_score - opponent_score):,} points")
    print(f"   MVP: {mvp_agent[0]} ({mvp_agent[1]['points']:,} points)")
    print(f"{'='*70}\n")

    return stats


def play_challenge(challenge_id: str, manager: ChallengeManager):
    """Play a specific challenge."""

    # Start challenge
    challenge = manager.start_challenge(challenge_id)
    if not challenge:
        return

    config = challenge.config

    # Initialize systems
    db = BattleHistoryDB("data/challenge_battles.db")

    # Create phase manager with challenge settings
    phase_manager = AdvancedPhaseManager(battle_duration=config.battle_duration)

    # Override boost settings if needed
    if not config.boost1_enabled:
        phase_manager.boost1_time = -1  # Disable
    if not config.boost2_enabled:
        phase_manager.boost2_threshold_start = 9999  # Never trigger

    # Create budget manager with challenge settings
    creator_budget = config.creator_budget or 300000
    opponent_budget = config.opponent_budget or 200000
    budget_manager = BudgetManager(creator_budget, opponent_budget, phase_manager)

    # Create team
    team = create_mixed_strategic_team(phase_manager, db)
    reset_evolving_team(team)

    # Create opponent with challenge settings
    strategy = None
    if config.opponent_strategy:
        strategy_map = {
            "sniper": StrategyProfile.SNIPER,
            "early_aggressor": StrategyProfile.EARLY_AGGRESSOR,
            "late_dominator": StrategyProfile.LATE_DOMINATOR,
            "steady_pressure": StrategyProfile.STEADY_PRESSURE,
            "boost2_specialist": StrategyProfile.BOOST2_SPECIALIST,
            "momentum_rider": StrategyProfile.MOMENTUM_RIDER,
            "chaotic": StrategyProfile.CHAOTIC,
        }
        strategy = strategy_map.get(config.opponent_strategy)

    opponent = OpponentAI(phase_manager, budget_manager=budget_manager, strategy=strategy)

    # Run the challenge battle
    battle_result = run_challenge_battle(challenge, team, phase_manager, budget_manager, opponent)

    # Evaluate result
    result = manager.evaluate_result(challenge_id, battle_result)

    return result


def main():
    parser = argparse.ArgumentParser(description="Challenge Mode Demo")
    parser.add_argument("--play", type=str, help="Play a specific challenge by ID")
    parser.add_argument("--progress", action="store_true", help="Show progress")
    parser.add_argument("--list", action="store_true", help="List all challenges")

    args = parser.parse_args()

    # Ensure data directory exists
    Path("data").mkdir(exist_ok=True)

    # Initialize manager
    manager = ChallengeManager("data/challenge_progress.json")

    if args.progress:
        manager.print_progress()
    elif args.play:
        play_challenge(args.play, manager)
        manager.print_progress()
    elif args.list:
        manager.print_challenge_list()
    else:
        # Default: show challenge list
        manager.print_challenge_list()
        print("\n💡 To play a challenge:")
        print("   python demo_challenge.py --play first_victory")
        print("\n💡 To see your progress:")
        print("   python demo_challenge.py --progress")


if __name__ == "__main__":
    main()
