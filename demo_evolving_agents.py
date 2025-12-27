"""
Evolving Agents Training Demo

Demonstrates self-improving agents that learn from battles:
- Multi-battle training sessions
- Performance evolution tracking
- Strategy adaptation visualization
- A/B testing comparison
"""

import sys
import os

# Ensure we can import from project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime

from core.battle_engine import BattleEngine
from core.advanced_phase_system import AdvancedPhaseManager, PowerUpType
from core.battle_history import (
    BattleHistoryDB, BattleRecord, AgentBattleRecord,
    GiftTimingRecord, generate_battle_id
)
from agents.evolving_agents import (
    create_evolving_team, reset_evolving_team,
    learn_from_battle_results, get_team_evolution_status
)
from agents.learning_system import StrategyOptimizer


def run_training_session(
    num_battles: int = 10,
    db_path: str = "data/training_history.db",
    verbose: bool = True
):
    """
    Run a training session with evolving agents.

    Args:
        num_battles: Number of battles to train
        db_path: Path to database
        verbose: Print detailed output
    """

    print("\n" + "🧬"*35)
    print("EVOLVING AGENTS TRAINING SESSION")
    print("🧬"*35 + "\n")

    print(f"📋 Training Configuration:")
    print(f"   Battles: {num_battles}")
    print(f"   Database: {db_path}")
    print(f"   Battle Duration: 180s each")
    print(f"   Mode: Accelerated (0.01s ticks)")

    # Initialize database
    print("\n📊 Initializing Battle History Database...")
    db = BattleHistoryDB(db_path)
    print(f"   Previous battles in DB: {db.get_battle_count()}")

    # Create phase manager and evolving team
    print("\n👥 Creating Evolving Team...")
    phase_manager = AdvancedPhaseManager(battle_duration=180)
    team = create_evolving_team(phase_manager, db=db)

    # Add power-ups
    phase_manager.add_power_up(PowerUpType.HAMMER, "creator")
    phase_manager.add_power_up(PowerUpType.FOG, "creator")
    phase_manager.add_power_up(PowerUpType.TIME_BONUS, "creator")

    print(f"   Agents: {', '.join(a.name for a in team)}")

    # Track training progress
    training_history = []
    wins = 0
    losses = 0

    print(f"\n{'='*70}")
    print("🏋️ TRAINING START")
    print(f"{'='*70}\n")

    for battle_num in range(1, num_battles + 1):
        battle_id = generate_battle_id()

        if verbose:
            print(f"\n📍 Battle {battle_num}/{num_battles} [{battle_id[:20]}...]")

        # Reset for new battle
        reset_evolving_team(team)
        phase_manager = AdvancedPhaseManager(battle_duration=180)
        phase_manager.add_power_up(PowerUpType.HAMMER, "creator")
        phase_manager.add_power_up(PowerUpType.FOG, "creator")
        phase_manager.add_power_up(PowerUpType.TIME_BONUS, "creator")

        # Update team with new phase manager
        for agent in team:
            agent.set_phase_manager(phase_manager)

        # Create battle engine
        engine = BattleEngine(
            battle_duration=180,
            tick_speed=0.01,  # Very fast for training
            enable_multipliers=False,
            enable_analytics=True
        )

        # Add agents
        for agent in team:
            engine.add_agent(agent)

        # Wrap tick to update phase manager
        original_tick = engine._tick

        def wrapped_tick(silent):
            original_tick(silent)
            phase_manager.update(engine.time_manager.current_time)

        engine._tick = wrapped_tick

        # CRITICAL FIX: Subscribe to GIFT_SENT events to track Boost #2 progress
        from core.event_bus import EventType

        def record_gift_for_phase_manager(event):
            """Record gifts in phase manager for Boost #2 threshold tracking."""
            gift_name = event.data.get("gift", event.data.get("gift_name", "Gift"))
            points = event.data.get("points", 0)
            current_time = int(event.timestamp)
            # All agents in this team are "creator" side
            phase_manager.record_gift(gift_name, points, "creator", current_time)

        engine.event_bus.subscribe(EventType.GIFT_SENT, record_gift_for_phase_manager)

        # Run battle (silent for speed)
        try:
            engine.run(silent=True)
        except Exception as e:
            if verbose:
                print(f"   ⚠️ Battle error: {e}")
            continue

        # Get results
        won = engine.analytics.winner == 'creator'
        if won:
            wins += 1
        else:
            losses += 1

        # Collect battle stats
        agent_perf = engine.analytics.get_agent_performance()
        phase_analytics = phase_manager.get_analytics()

        battle_stats = {
            'points_donated': sum(p['total_donated'] for p in agent_perf.values()),
            'boost2_triggered': phase_analytics['boost2_triggered'],
            'gloves_activated': phase_analytics['gloves_activated'],
            'gifts_sent': sum(p['gifts_sent'] for p in agent_perf.values())
        }

        # Record to database
        battle_record = BattleRecord(
            battle_id=battle_id,
            timestamp=datetime.now().isoformat(),
            duration=engine.time_manager.current_time,
            winner=engine.analytics.winner,
            creator_score=engine.analytics.final_scores['creator'],
            opponent_score=engine.analytics.final_scores['opponent'],
            margin=abs(engine.analytics.final_scores['creator'] - engine.analytics.final_scores['opponent']),
            boost2_triggered=phase_analytics['boost2_triggered'],
            gloves_activated=phase_analytics['gloves_activated'],
            power_ups_used=phase_analytics['power_ups_used'],
            total_gifts_sent=battle_stats['gifts_sent']
        )
        db.record_battle(battle_record)

        # Record agent performances
        for agent_name, perf in agent_perf.items():
            agent_type = 'unknown'
            for agent in team:
                if agent.name == agent_name:
                    agent_type = agent.agent_type
                    break

            agent_record = AgentBattleRecord(
                battle_id=battle_id,
                agent_name=agent_name,
                agent_type=agent_type,
                points_donated=perf['total_donated'],
                gifts_sent=perf['gifts_sent'],
                avg_gift_value=perf['avg_gift_value'],
                best_gift_value=perf.get('best_gift', {}).get('points', 0),
                early_phase_gifts=perf.get('gift_timing', {}).get('early', 0),
                mid_phase_gifts=perf.get('gift_timing', {}).get('mid', 0),
                late_phase_gifts=perf.get('gift_timing', {}).get('late', 0),
                final_phase_gifts=perf.get('gift_timing', {}).get('final', 0),
                gloves_sent=0,
                gloves_activated=0,
                power_ups_used=0,
                won=won
            )
            db.record_agent_performance(agent_record)

        # Learn from battle
        rewards = learn_from_battle_results(team, won, battle_stats)

        # Track progress
        win_rate = wins / battle_num
        training_history.append({
            'battle': battle_num,
            'won': won,
            'win_rate': win_rate,
            'creator_score': engine.analytics.final_scores['creator'],
            'opponent_score': engine.analytics.final_scores['opponent'],
            'boost2_triggered': phase_analytics['boost2_triggered']
        })

        if verbose:
            result = "✅ WIN" if won else "❌ LOSS"
            print(f"   {result} | Creator: {engine.analytics.final_scores['creator']:,} vs "
                  f"Opponent: {engine.analytics.final_scores['opponent']:,}")
            print(f"   📈 Running Win Rate: {win_rate*100:.1f}% ({wins}/{battle_num})")

    print(f"\n{'='*70}")
    print("🏁 TRAINING COMPLETE")
    print(f"{'='*70}")

    # Final statistics
    final_win_rate = wins / num_battles
    print(f"\n📊 Training Results:")
    print(f"   Total Battles: {num_battles}")
    print(f"   Wins: {wins} | Losses: {losses}")
    print(f"   Final Win Rate: {final_win_rate*100:.1f}%")

    # Agent evolution status
    print(f"\n🧬 Agent Evolution Status:")
    status = get_team_evolution_status(team)
    for name, s in status.items():
        print(f"\n   {name}:")
        print(f"      Battles Learned: {s.get('battles', 0)}")
        print(f"      Win Rate: {s.get('win_rate', 0)*100:.1f}%")
        if 'params' in s:
            print(f"      Evolved Params: {s['params']}")

    # Run strategy optimization
    print(f"\n🧬 Running Strategy Optimization...")
    optimizer = StrategyOptimizer(db)
    optimized_params = optimizer.run_optimization_cycle()

    for agent_type, params in optimized_params.items():
        # Save to database
        agent_stats = db.get_agent_stats(f"Evolving{agent_type.title().replace('_', '')}")
        if agent_stats['total_battles'] > 0:
            db.save_strategy_params(
                agent_type=agent_type,
                params={k: float(v) if isinstance(v, (int, float)) else v for k, v in params.items()},
                win_rate=agent_stats['win_rate'],
                sample_size=agent_stats['total_battles']
            )

    # Performance evolution graph (ASCII)
    print(f"\n📈 Win Rate Evolution:")
    print_win_rate_graph(training_history)

    # Database summary
    print(f"\n💾 Database Summary:")
    print(f"   Total battles recorded: {db.get_battle_count()}")
    recent = db.get_recent_battles(5)
    print(f"   Recent battles:")
    for b in recent:
        print(f"      {b['winner'].upper()} | {b['creator_score']:,} vs {b['opponent_score']:,}")

    db.close()

    print(f"\n{'='*70}")
    print("✅ Training Session Complete!")
    print(f"{'='*70}\n")

    return training_history


def print_win_rate_graph(history: list, width: int = 50):
    """Print ASCII graph of win rate evolution."""
    if not history:
        return

    print(f"\n   100% |", end="")

    # Create buckets
    bucket_size = max(1, len(history) // 10)
    buckets = []
    for i in range(0, len(history), bucket_size):
        bucket = history[i:i+bucket_size]
        avg_rate = sum(h['win_rate'] for h in bucket) / len(bucket)
        buckets.append(avg_rate)

    # Print graph
    for threshold in [1.0, 0.75, 0.5, 0.25]:
        if threshold == 1.0:
            print("")
        else:
            print(f"   {int(threshold*100):3d}% |", end="")

        for rate in buckets:
            if rate >= threshold:
                print("█", end="")
            elif rate >= threshold - 0.125:
                print("▄", end="")
            else:
                print(" ", end="")
        print("")

    print(f"     0% |" + "─" * len(buckets))
    print(f"        " + "".join(f"{i+1}" for i in range(len(buckets))))
    print(f"        Battles (buckets of {bucket_size})")


def run_comparison_test(
    num_battles: int = 20,
    db_path: str = "data/comparison_test.db"
):
    """
    Run A/B comparison between evolved and non-evolved agents.
    """

    print("\n" + "🔬"*35)
    print("EVOLVED vs NON-EVOLVED COMPARISON")
    print("🔬"*35 + "\n")

    db = BattleHistoryDB(db_path)

    # Run with evolved agents
    print("🧬 Phase 1: Testing EVOLVED agents...")
    evolved_wins = 0
    for i in range(num_battles):
        phase_manager = AdvancedPhaseManager(battle_duration=180)
        team = create_evolving_team(phase_manager, db=db)

        engine = BattleEngine(
            battle_duration=180,
            tick_speed=0.01,
            enable_multipliers=False,
            enable_analytics=True
        )

        for agent in team:
            engine.add_agent(agent)

        original_tick = engine._tick
        def make_wrapped_tick(pm):
            def wrapped_tick(silent):
                original_tick(silent)
                pm.update(engine.time_manager.current_time)
            return wrapped_tick

        engine._tick = make_wrapped_tick(phase_manager)

        # CRITICAL FIX: Subscribe to GIFT_SENT events for Boost #2 tracking
        from core.event_bus import EventType
        def make_gift_recorder(pm):
            def record_gift(event):
                gift_name = event.data.get("gift", "Gift")
                points = event.data.get("points", 0)
                current_time = int(event.timestamp)
                pm.record_gift(gift_name, points, "creator", current_time)
            return record_gift
        engine.event_bus.subscribe(EventType.GIFT_SENT, make_gift_recorder(phase_manager))

        try:
            engine.run(silent=True)
            if engine.analytics.winner == 'creator':
                evolved_wins += 1
        except:
            pass

    evolved_rate = evolved_wins / num_battles

    # Run with standard strategic agents
    print("📋 Phase 2: Testing STANDARD agents...")
    from agents.strategic_agents import create_strategic_team

    standard_wins = 0
    for i in range(num_battles):
        phase_manager = AdvancedPhaseManager(battle_duration=180)
        team = create_strategic_team(phase_manager)

        engine = BattleEngine(
            battle_duration=180,
            tick_speed=0.01,
            enable_multipliers=False,
            enable_analytics=True
        )

        for agent in team:
            engine.add_agent(agent)

        original_tick = engine._tick
        def make_wrapped_tick(pm):
            def wrapped_tick(silent):
                original_tick(silent)
                pm.update(engine.time_manager.current_time)
            return wrapped_tick

        engine._tick = make_wrapped_tick(phase_manager)

        # CRITICAL FIX: Subscribe to GIFT_SENT events for Boost #2 tracking
        from core.event_bus import EventType
        def make_gift_recorder(pm):
            def record_gift(event):
                gift_name = event.data.get("gift", "Gift")
                points = event.data.get("points", 0)
                current_time = int(event.timestamp)
                pm.record_gift(gift_name, points, "creator", current_time)
            return record_gift
        engine.event_bus.subscribe(EventType.GIFT_SENT, make_gift_recorder(phase_manager))

        try:
            engine.run(silent=True)
            if engine.analytics.winner == 'creator':
                standard_wins += 1
        except:
            pass

    standard_rate = standard_wins / num_battles

    # Results
    print(f"\n{'='*70}")
    print("📊 COMPARISON RESULTS")
    print(f"{'='*70}")

    print(f"\n🧬 EVOLVED Agents:")
    print(f"   Wins: {evolved_wins}/{num_battles}")
    print(f"   Win Rate: {evolved_rate*100:.1f}%")

    print(f"\n📋 STANDARD Agents:")
    print(f"   Wins: {standard_wins}/{num_battles}")
    print(f"   Win Rate: {standard_rate*100:.1f}%")

    diff = evolved_rate - standard_rate
    print(f"\n📈 Difference: {diff*100:+.1f}%")

    if diff > 0.05:
        print(f"   🏆 EVOLVED agents perform better!")
    elif diff < -0.05:
        print(f"   📋 STANDARD agents perform better")
    else:
        print(f"   ≈ Performance is similar")

    db.close()

    return {
        'evolved': {'wins': evolved_wins, 'rate': evolved_rate},
        'standard': {'wins': standard_wins, 'rate': standard_rate},
        'difference': diff
    }


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Evolving Agents Training")
    parser.add_argument('--battles', type=int, default=10, help='Number of training battles')
    parser.add_argument('--compare', action='store_true', help='Run comparison test')
    parser.add_argument('--quiet', action='store_true', help='Less verbose output')

    args = parser.parse_args()

    if args.compare:
        run_comparison_test(num_battles=args.battles)
    else:
        run_training_session(
            num_battles=args.battles,
            verbose=not args.quiet
        )


if __name__ == '__main__':
    main()
