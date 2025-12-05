"""
GPT Persona Agents Demo - The Original Cast with AI Intelligence! 🤖

Watch your favorite persona agents (NovaWhale, PixelPixie, GlitchMancer, etc.)
powered by GPT-4 for intelligent, in-character decision-making!

Features:
- All 5 classic persona agents with GPT intelligence
- Maintains original personalities and styles
- Strategic decision-making enhanced by AI
- Real-time battle commentary
"""

import os
from core.battle_engine import BattleEngine
from agents.personas.gpt_personas import (
    GPTNovaWhale,
    GPTPixelPixie,
    GPTGlitchMancer,
    GPTShadowPatron,
    GPTDramatron,
    create_gpt_persona_team
)
from extensions.gpt_intelligence import GPTDecisionEngine


def print_banner():
    """Print demo banner."""
    print("\n" + "="*70)
    print("🎭 GPT PERSONA AGENTS DEMONSTRATION 🎭")
    print("="*70 + "\n")


def check_api_status():
    """Check and display API key status."""
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("⚠️  WARNING: OPENAI_API_KEY not set!")
        print("   GPT persona agents will use fallback rule-based logic.")
        print("   To enable GPT-4 intelligence:")
        print()
        print("   Option 1 - Environment variable:")
        print("     export OPENAI_API_KEY='sk-your-key-here'")
        print()
        print("   Option 2 - .env file (recommended):")
        print("     echo 'OPENAI_API_KEY=sk-your-key-here' > .env")
        print("     pip install python-dotenv")
        print()
        print("   Continuing with fallback mode for demonstration...\n")
        return False
    else:
        print("✅ OpenAI API Key detected")
        print("🤖 GPT-4 will power agent personalities and decisions")
        print(f"   Key length: {len(api_key)} characters\n")
        return True


def print_agent_intro():
    """Introduce the agents."""
    print("🎭 THE CAST:")
    print("  🐋 NovaWhale - Strategic whale, waits for critical moments")
    print("  🧚‍♀️ PixelPixie - Enthusiastic cheerleader, budget but boundless energy")
    print("  🌀 GlitchMancer - Chaotic burst-mode agent with glitched speech")
    print("  👤 ShadowPatron - Silent observer, strikes in crisis")
    print("  🎭 Dramatron - Theatrical performer, everything is a show")
    print()


def run_persona_battle():
    """Run a battle with GPT persona agents."""

    print_banner()
    api_available = check_api_status()
    print_agent_intro()

    # Create shared GPT engine (efficient - reuses same connection)
    gpt_engine = GPTDecisionEngine()

    if gpt_engine.is_available():
        print("🧠 Shared GPT Engine initialized")
        print("   Model: GPT-4")
        print("   All agents will share this engine for efficiency\n")
    else:
        print("⚙️  Using fallback mode (rule-based decisions)\n")

    # Create battle engine
    print("🎬 Creating battle engine...")
    engine = BattleEngine(
        battle_duration=60,  # Classic 60s battle
        tick_speed=0.15,      # Slightly slower for readability
        enable_multipliers=True,
        enable_analytics=True
    )

    # Add all GPT persona agents
    print("🎭 Adding GPT-powered persona agents...\n")

    agents = create_gpt_persona_team(shared_engine=gpt_engine)

    for agent in agents:
        engine.add_agent(agent)
        print(f"   ✓ {agent.emoji} {agent.name} ready!")

    print(f"\n{'='*70}")
    print("🎬 BATTLE START - Watch the personas in action!")
    print(f"{'='*70}\n")

    # Run the battle
    engine.run(silent=False)

    # Battle complete - show results
    print(f"\n{'='*70}")
    print("📊 BATTLE ANALYTICS SUMMARY")
    print(f"{'='*70}\n")

    # Get analytics
    winner = engine.analytics.winner
    c_score = engine.analytics.final_scores.get("creator", 0)
    o_score = engine.analytics.final_scores.get("opponent", 0)

    print(f"🏆 Battle Result:")
    print(f"   Winner: {winner.upper()}")
    print(f"   Final Score: Creator {c_score:,} vs Opponent {o_score:,}")
    print(f"   Margin: {abs(c_score - o_score):,} points\n")

    # Agent performance
    performance = engine.analytics.get_agent_performance()

    print("👥 Agent Performance:\n")
    for agent_name, stats in performance.items():
        total = stats['total_donated']
        gifts = stats['gifts_sent']
        avg = stats['avg_gift_value']
        best = stats['best_gift']

        print(f"   {agent_name}:")
        print(f"      Total donated: {total:,} points")
        print(f"      Gifts sent: {gifts}")
        print(f"      Avg gift value: {avg}")
        print(f"      Best gift: {best['name']} ({best['value']})")
        print()

    # Show GPT usage statistics
    print("📊 GPT Intelligence Statistics:\n")

    total_gpt = 0
    total_fallback = 0

    for agent in agents:
        if hasattr(agent, 'get_gpt_stats'):
            stats = agent.get_gpt_stats()
            gpt_count = stats['gpt_decisions']
            fallback_count = stats['fallback_decisions']
            percentage = stats['gpt_percentage']

            total_gpt += gpt_count
            total_fallback += fallback_count

            print(f"   {agent.emoji} {agent.name}:")
            print(f"      GPT Decisions: {gpt_count}")
            print(f"      Fallback Decisions: {fallback_count}")
            print(f"      GPT Usage: {percentage:.1f}%")
            print()

    total_decisions = total_gpt + total_fallback
    overall_gpt_percentage = (total_gpt / max(1, total_decisions)) * 100

    print(f"   🎯 Overall GPT Usage: {overall_gpt_percentage:.1f}%")
    print(f"   Total decisions: {total_decisions:,} ({total_gpt:,} GPT, {total_fallback:,} fallback)\n")

    # Multiplier usage
    if engine.analytics.multiplier_sessions:
        print("⚡ Multiplier Sessions:\n")
        sessions = engine.analytics.multiplier_sessions
        total_duration = sum(s.duration if hasattr(s, 'duration') else 0 for s in sessions)
        coverage = (total_duration / 60) * 100

        print(f"   Sessions triggered: {len(sessions)}")
        print(f"   Total duration: {total_duration}s")
        print(f"   Battle coverage: {coverage:.1f}%\n")

    print(f"{'='*70}")
    print("✅ GPT Persona Demo Complete!")
    print(f"{'='*70}\n")

    if not api_available:
        print("💡 TIP: Set OPENAI_API_KEY to see real GPT-4 intelligence!")
        print("   Current demo used fallback rule-based decisions.")
        print("   With GPT-4, agents make smarter, more in-character decisions!\n")
    else:
        print("🎉 You just witnessed GPT-4 powered persona agents!")
        print("   Each agent made intelligent, in-character decisions based on")
        print("   battle state, timing, and their unique personalities!\n")


def main():
    """Main entry point."""
    try:
        run_persona_battle()
    except KeyboardInterrupt:
        print("\n\n⚠️  Battle interrupted by user.")
        print("Thanks for watching! 🎭\n")
    except Exception as e:
        print(f"\n❌ Error during battle: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
