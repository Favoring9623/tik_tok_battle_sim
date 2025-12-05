"""
GPT Tournament Demo - AI-Powered Intelligent Agents

Demonstrates GPT-4 powered agents making strategic decisions in tournaments.

Features:
- 4 distinct AI personalities (Aggressive, Defensive, Balanced, Tactical)
- Intelligent budget management
- Strategic reward optimization
- Adaptive tournament strategies
"""

import os
from core.battle_engine import BattleEngine
from core.tournament_system import TournamentManager, TournamentFormat
from agents.gpt_tournament_agents import create_gpt_tournament_agent


def main():
    print("\n" + "="*70)
    print("🤖 GPT TOURNAMENT DEMONSTRATION")
    print("="*70 + "\n")

    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  WARNING: OPENAI_API_KEY not set!")
        print("   GPT agents will use fallback rule-based logic.")
        print("   To enable GPT: export OPENAI_API_KEY='your-key-here'\n")
        print("   Continuing with fallback mode for demonstration...\n")
    else:
        print("✅ OpenAI API Key detected")
        print("🤖 GPT-4 agents will make intelligent decisions\n")

    # Create tournament
    tournament = TournamentManager(
        format=TournamentFormat.BEST_OF_3,
        total_budget=250000,
        battle_duration=180
    )

    # Enable random budgets for variety
    tournament.enable_random_budgets()

    # Select GPT agent personality
    print("Available AI Personalities:")
    print("  1. 🔥 Aggressive - High-risk, reward-hunting strategy")
    print("  2. 🛡️ Defensive - Conservative, efficient play")
    print("  3. ⚖️ Balanced - Adaptive, context-aware decisions")
    print("  4. 🎯 Tactical - Precision timing, multiplier mastery\n")

    # For demo, use Balanced personality
    personality = "balanced"
    print(f"Selected: ⚖️ BALANCED GPT Agent\n")

    # Start tournament
    tournament.start_tournament()

    # Run battles
    battle_num = 0
    while tournament.can_continue():
        battle_num += 1

        # Print series status
        if battle_num > 1:
            tournament.print_series_status()
            print("\nStarting next battle with GPT agent...\n")

        # Get scenario
        scenario, limit = tournament.get_random_budget_limit()
        print(f"⚔️  BATTLE {battle_num}")
        print(f"   Scenario: {scenario}")
        if limit:
            print(f"   Budget Limit: {limit:,}")
        print(f"   Remaining: {tournament.shared_budget.remaining:,}\n")

        # Create GPT agent
        gpt_agent = create_gpt_tournament_agent(personality)

        # Create battle
        engine = BattleEngine(
            battle_duration=180,
            tick_speed=0.1,  # Faster for demo
            enable_multipliers=True,
            time_extensions=tournament.get_available_time_extensions("creator"),
            enable_analytics=True
        )

        # Add GPT agent
        engine.add_agent(gpt_agent)

        # Run battle
        print("🤖 GPT Agent is analyzing and making decisions...")
        engine.run(silent=False)  # Show GPT decisions

        # Get results
        winner = engine.analytics.winner
        c_score = engine.analytics.final_scores.get("creator", 0)
        o_score = engine.analytics.final_scores.get("opponent", 0)
        performance = engine.analytics.get_agent_performance()
        budget = sum(stats['total_donated'] for stats in performance.values())

        # Update tournament budget
        tournament.shared_budget.spend(budget, "Tournament")

        # Show GPT stats
        if hasattr(gpt_agent, 'get_gpt_stats'):
            stats = gpt_agent.get_gpt_stats()
            print(f"\n📊 GPT Agent Statistics:")
            print(f"   GPT Decisions: {stats['gpt_decisions']}")
            print(f"   Fallback Decisions: {stats['fallback_decisions']}")
            print(f"   GPT Usage: {stats['gpt_percentage']:.1f}%")

        # Record result
        tournament.record_battle_result(
            winner=winner,
            creator_score=c_score,
            opponent_score=o_score,
            budget_spent_this_battle=budget,
            agent_performance=performance
        )

        if tournament.can_continue():
            print("\n" + "="*70)
            input("Press Enter to continue to next battle...")

    # Tournament complete
    stats = tournament.get_tournament_stats()
    print("\n" + "="*70)
    print("🏆 GPT TOURNAMENT RESULTS")
    print("="*70)
    print(f"\n👑 Champion: {stats['tournament_winner'].upper()}")
    print(f"📊 Score: {stats['creator_wins']}-{stats['opponent_wins']}")
    print(f"💰 Budget: {stats['budget']['spent']:,} / {stats['budget']['total']:,}")

    print(f"\n⭐ Performance Highlights:")
    for b in stats['battles']:
        bonus = " 🎉 BONUS!" if b['bonus_rewards_earned'] else ""
        print(f"   Battle {b['number']}: {b['top_contributor']} ({b['top_contribution']:,}){bonus}")

    print(f"\n🎁 Final Inventory:")
    inv = stats['creator_inventory']
    print(f"   Gloves: {inv['x5_gloves']} | Fogs: {inv['fogs']} | "
          f"Hammers: {inv['hammers']} | Time: {inv['time_extensions']}")

    print("\n" + "="*70)
    print("✅ GPT Tournament Complete!")
    print("="*70 + "\n")

    if not api_key:
        print("💡 TIP: Set OPENAI_API_KEY to see real GPT-4 intelligence in action!")
        print("   Current demo used fallback rule-based decisions.\n")


if __name__ == "__main__":
    main()
