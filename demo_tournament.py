#!/usr/bin/env python3
"""
Tournament Demo - Best of 3/5/7 Series with All Competition Features

Demonstrates:
- Tournament Mode (Best of 3, 5, or 7)
- Carryover Learning (agents evolve between battles)
- Custom Opponent Builder
- Agent Leaderboard
- Dramatic Announcements
- 8-Team Elimination Brackets (NEW!)

Usage:
    python demo_tournament.py              # Best of 5 tournament (default)
    python demo_tournament.py --bo3        # Best of 3 tournament (first to 2)
    python demo_tournament.py --bo7        # Best of 7 tournament (first to 4)
    python demo_tournament.py --custom     # Custom opponent
    python demo_tournament.py --leaderboard  # Show leaderboard only
    python demo_tournament.py --bracket    # 8-Team elimination bracket
"""

import sys
import time
import random
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.tournament_system import TournamentManager, TournamentFormat
from core.tournament_leaderboard import TournamentLeaderboard, AgentLeaderboard
from core.advanced_phase_system import AdvancedPhaseManager
from core.budget_system import BudgetManager
from agents.opponent_ai import OpponentAI, OpponentBuilder, create_custom_opponent
from agents.evolving_agents import create_mixed_strategic_team, learn_from_battle_results, reset_evolving_team
from core.battle_history import BattleHistoryDB


def run_single_battle(team, opponent, phase_manager, budget_manager, battle_num: int):
    """
    Run a single battle and return results.

    This is a simplified battle loop for the tournament demo.
    """
    print(f"\n{'='*70}")
    print(f"⚔️  BATTLE {battle_num} STARTING")
    print(f"{'='*70}\n")

    # Reset agents for new battle (phase_manager/budget_manager are fresh per battle)
    opponent.reset_for_battle()
    reset_evolving_team(team)

    # Simulate battle (simplified for demo)
    creator_score = 0
    opponent_score = 0
    battle_duration = phase_manager.battle_duration

    # Track agent contributions
    agent_contributions = {agent.name: {'points': 0, 'gifts': 0, 'whales': 0} for agent in team}

    # Simple battle simulation
    for tick in range(0, battle_duration, 1):
        current_time = tick
        time_remaining = battle_duration - tick

        # Update phase manager
        phase_manager.update(current_time)
        multiplier = phase_manager.get_current_multiplier()

        # Agents act
        for agent in team:
            if random.random() < 0.3:  # 30% chance to act per tick
                # Determine gift size based on phase
                if phase_manager.boost1_active or phase_manager.boost2_active:
                    if random.random() < 0.15:
                        points = random.choice([10000, 29999, 44999])  # Whale
                        agent_contributions[agent.name]['whales'] += 1
                    else:
                        points = random.choice([99, 299, 500, 1000])
                elif time_remaining <= 30:
                    points = random.choice([500, 1000, 5000])
                else:
                    points = random.choice([1, 5, 30, 99])

                effective = int(points * multiplier)
                creator_score += effective
                agent_contributions[agent.name]['points'] += effective
                agent_contributions[agent.name]['gifts'] += 1

        # Opponent acts
        result = opponent.update(current_time, creator_score, opponent_score)
        if result['gift_sent']:
            effective = int(result['gift_points'] * multiplier)
            opponent_score += effective

        # Progress indicator every 30 seconds
        if tick % 30 == 0 and tick > 0:
            print(f"   ⏱️  {tick}s: Creator {creator_score:,} vs Opponent {opponent_score:,}")

    # Determine winner
    winner = "creator" if creator_score > opponent_score else "opponent"

    # Find MVP
    mvp_agent = max(agent_contributions.items(), key=lambda x: x[1]['points'])

    print(f"\n{'='*70}")
    print(f"🏁 BATTLE {battle_num} COMPLETE!")
    print(f"   Winner: {winner.upper()}")
    print(f"   Score: Creator {creator_score:,} vs Opponent {opponent_score:,}")
    print(f"   MVP: {mvp_agent[0]} ({mvp_agent[1]['points']:,} points)")
    print(f"{'='*70}\n")

    return {
        'winner': winner,
        'creator_score': creator_score,
        'opponent_score': opponent_score,
        'agent_contributions': agent_contributions,
        'mvp': mvp_agent[0],
        'mvp_contribution': mvp_agent[1]['points']
    }


def run_tournament(format: TournamentFormat, custom_opponent: bool = False):
    """Run a full tournament."""

    # Initialize database
    db = BattleHistoryDB("data/tournament_demo.db")

    # Tournament budget pool
    creator_budget = random.randint(400000, 600000)
    opponent_budget = random.randint(100000, 300000)

    # Initial setup (for team creation)
    phase_manager = AdvancedPhaseManager(battle_duration=180)
    budget_manager = BudgetManager(creator_budget, opponent_budget, phase_manager)

    # Create team (persists across battles for carryover learning)
    team = create_mixed_strategic_team(phase_manager, db)

    # Store custom opponent config
    custom_builder = None
    if custom_opponent:
        print("\n🔧 Creating CUSTOM opponent...")
        custom_builder = OpponentBuilder("Tournament Nemesis")
        custom_builder.from_preset("boost_specialist")
        custom_builder.set_aggression(final_5s=0.9, x5_active=0.95)
        custom_builder.set_whale_chances(boost=0.4, final=0.5)
        print(custom_builder.preview())

    # Create initial opponent
    if custom_builder:
        opponent = custom_builder.build(phase_manager, budget_manager)
    else:
        opponent = OpponentAI(phase_manager, budget_manager=budget_manager)

    # Initialize tournament
    tournament = TournamentManager(
        format=format,
        total_budget=creator_budget + opponent_budget,
        battle_duration=180,
        enable_carryover_learning=True
    )
    tournament.set_agents(team)

    # Initialize leaderboards
    team_leaderboard = TournamentLeaderboard("data/tournament_leaderboard.json")
    agent_leaderboard = AgentLeaderboard("data/agent_leaderboard.json")

    # Start tournament
    tournament.start_tournament()

    battle_num = 0
    tournament_id = f"T{random.randint(1000, 9999)}"

    while tournament.can_continue():
        battle_num += 1

        # Create FRESH phase_manager and budget_manager for each battle
        phase_manager = AdvancedPhaseManager(battle_duration=180)
        budget_manager = BudgetManager(creator_budget, opponent_budget, phase_manager)

        # Update opponent's references
        opponent.phase_manager = phase_manager
        opponent.budget_manager = budget_manager

        # Run battle
        result = run_single_battle(team, opponent, phase_manager, budget_manager, battle_num)

        # Record agent performances
        for agent in team:
            contrib = result['agent_contributions'].get(agent.name, {'points': 0, 'gifts': 0, 'whales': 0})
            agent_leaderboard.record_agent_performance(
                agent_name=agent.name,
                emoji=agent.emoji,
                battle_id=f"B{battle_num}",
                tournament_id=tournament_id,
                points_donated=contrib['points'],
                gifts_sent=contrib['gifts'],
                whale_gifts=contrib['whales'],
                won=result['winner'] == 'creator',
                was_mvp=(agent.name == result['mvp'])
            )

        # Build agent performance dict for tournament
        agent_performance = {
            name: {'total_donated': data['points']}
            for name, data in result['agent_contributions'].items()
        }

        # Record battle in tournament
        tournament.record_battle_result(
            winner=result['winner'],
            creator_score=result['creator_score'],
            opponent_score=result['opponent_score'],
            budget_spent_this_battle=50000,  # Estimated
            agent_performance=agent_performance
        )

        # Small delay for readability
        time.sleep(0.5)

    # Record tournament in team leaderboard
    team_leaderboard.record_tournament(tournament.get_tournament_stats())

    # Print final results
    print("\n" + "="*80)
    print("📊 TOURNAMENT SUMMARY")
    print("="*80)

    # Team leaderboard
    team_leaderboard.print_leaderboard()

    # Agent leaderboard
    agent_leaderboard.print_leaderboard()

    return tournament


def show_leaderboards():
    """Show current leaderboards."""
    team_leaderboard = TournamentLeaderboard("data/tournament_leaderboard.json")
    agent_leaderboard = AgentLeaderboard("data/agent_leaderboard.json")

    team_leaderboard.print_leaderboard()
    agent_leaderboard.print_leaderboard()

    # Show detailed card for top agent if available
    rankings = agent_leaderboard.get_rankings()
    if rankings:
        print("\n🔍 Top Agent Details:")
        agent_leaderboard.print_agent_card(rankings[0]['name'])


def run_bracket_tournament():
    """
    Run an 8-team elimination bracket tournament.

    Demonstrates the new EliminationTournament system with:
    - Seeded brackets
    - Round progression
    - Championship finals
    """
    from core.tournament_bracket import TournamentTeam, EliminationTournament, TournamentRunner

    print("\n" + "=" * 70)
    print("   🏆 8-TEAM ELIMINATION BRACKET TOURNAMENT")
    print("=" * 70)

    # Create 8 teams with different agent compositions
    teams = [
        TournamentTeam(name="Kinetik Snipers", seed=1, emoji="🔫"),
        TournamentTeam(name="Chaos Legion", seed=2, emoji="🎭"),
        TournamentTeam(name="Defense Force", seed=3, emoji="🛡️"),
        TournamentTeam(name="Budget Masters", seed=4, emoji="💰"),
        TournamentTeam(name="Synergy Squad", seed=5, emoji="🎯"),
        TournamentTeam(name="Rose Spammers", seed=6, emoji="🌹"),
        TournamentTeam(name="Whale Watchers", seed=7, emoji="🐋"),
        TournamentTeam(name="Wild Cards", seed=8, emoji="🃏"),
    ]

    print("\n   Registered Teams:")
    for team in teams:
        print(f"   #{team.seed} {team.emoji} {team.name}")

    # Create tournament
    tournament = EliminationTournament(teams, elimination_type="single")

    # Show initial bracket
    print("\n   Initial Bracket:")
    tournament.print_bracket()

    # Create runner with custom battle simulation
    runner = TournamentRunner(tournament)

    # Run round by round with pauses for drama
    while not tournament.is_complete():
        round_name = tournament.round_names.get(
            tournament.current_round,
            f"ROUND {tournament.current_round}"
        )

        print(f"\n{'='*60}")
        print(f"   ⚔️ {round_name} ⚔️")
        print(f"{'='*60}")

        input("\n   Press Enter to start this round...")

        runner.run_round(verbose=True)

        # Show updated bracket
        tournament.print_bracket()

        time.sleep(0.5)

    # Final results
    print("\n" + "=" * 70)
    print("   🏆 TOURNAMENT COMPLETE! 🏆")
    print("=" * 70)

    tournament.print_standings()

    print(f"\n   👑 CHAMPION: {tournament.champion.emoji} {tournament.champion.name}!")
    print(f"   Record: {tournament.champion.wins}-{tournament.champion.losses}")
    print(f"   Point Differential: +{tournament.champion.point_differential:,}")

    print("\n" + "=" * 70 + "\n")


def run_quick_bracket():
    """
    Run an 8-team elimination bracket quickly (no pauses).
    """
    from core.tournament_bracket import TournamentTeam, EliminationTournament, TournamentRunner

    print("\n" + "=" * 70)
    print("   🏆 QUICK 8-TEAM ELIMINATION BRACKET")
    print("=" * 70)

    # Create 8 teams
    teams = [
        TournamentTeam(name="Kinetik Snipers", seed=1, emoji="🔫"),
        TournamentTeam(name="Chaos Legion", seed=2, emoji="🎭"),
        TournamentTeam(name="Defense Force", seed=3, emoji="🛡️"),
        TournamentTeam(name="Budget Masters", seed=4, emoji="💰"),
        TournamentTeam(name="Synergy Squad", seed=5, emoji="🎯"),
        TournamentTeam(name="Rose Spammers", seed=6, emoji="🌹"),
        TournamentTeam(name="Whale Watchers", seed=7, emoji="🐋"),
        TournamentTeam(name="Wild Cards", seed=8, emoji="🃏"),
    ]

    tournament = EliminationTournament(teams, elimination_type="single")
    runner = TournamentRunner(tournament)

    # Run full tournament
    runner.run_tournament(verbose=True)

    print(f"\n   👑 CHAMPION: {tournament.champion.emoji} {tournament.champion.name}!")
    print("\n" + "=" * 70 + "\n")


def demo_custom_opponent_builder():
    """Demonstrate the Custom Opponent Builder."""
    print("\n" + "="*70)
    print("🔧 CUSTOM OPPONENT BUILDER DEMO")
    print("="*70)

    # Show available presets
    print("\n📋 Available Presets:")
    for name, config in OpponentBuilder.PRESETS.items():
        print(f"   • {name}: {config['description']}")

    # Create custom opponent from preset
    print("\n🎯 Creating 'Snipe Master' from 'all_in_snipe' preset...")
    builder = OpponentBuilder("Snipe Master")
    builder.from_preset("all_in_snipe")
    builder.set_aggression(final_5s=0.99)
    builder.set_whale_chances(final=0.7)
    builder.set_glove_timing(final_5s=0.99)

    print(builder.preview())

    # Export to dict
    config = builder.to_dict()
    print("\n📤 Exported configuration:")
    print(f"   Name: {config['name']}")
    print(f"   Description: {config['description']}")

    # Save to file
    builder.save_to_file("data/snipe_master_config.json")

    # Create from scratch
    print("\n🔨 Creating fully custom 'Whale Hunter'...")
    custom = OpponentBuilder("Whale Hunter")
    custom.description = "Focuses on sending whale gifts during boosts"
    custom.set_aggression(normal=0.2, boost1=0.6, boost2=0.7, final_5s=0.8)
    custom.set_whale_chances(normal=0.2, boost=0.5, final=0.4)
    custom.set_reserves(boost2=0.35, snipe=0.15)

    print(custom.preview())

    print("\n✅ Custom Opponent Builder demo complete!")


def main():
    parser = argparse.ArgumentParser(description="Tournament Demo")
    parser.add_argument("--bo3", action="store_true", help="Run Best of 3 tournament (first to 2)")
    parser.add_argument("--bo7", action="store_true", help="Run Best of 7 tournament (first to 4)")
    parser.add_argument("--custom", action="store_true", help="Use custom opponent")
    parser.add_argument("--leaderboard", action="store_true", help="Show leaderboards only")
    parser.add_argument("--builder-demo", action="store_true", help="Demo opponent builder")
    parser.add_argument("--bracket", action="store_true", help="Run 8-team elimination bracket")
    parser.add_argument("--quick-bracket", action="store_true", help="Run bracket without pauses")

    args = parser.parse_args()

    # Ensure data directory exists
    Path("data").mkdir(exist_ok=True)

    if args.leaderboard:
        show_leaderboards()
    elif args.builder_demo:
        demo_custom_opponent_builder()
    elif args.bracket:
        run_bracket_tournament()
    elif args.quick_bracket:
        run_quick_bracket()
    else:
        # Determine format: --bo3 | default (bo5) | --bo7
        if args.bo3:
            format = TournamentFormat.BEST_OF_3
        elif args.bo7:
            format = TournamentFormat.BEST_OF_7
        else:
            format = TournamentFormat.BEST_OF_5
        run_tournament(format, custom_opponent=args.custom)


if __name__ == "__main__":
    main()
