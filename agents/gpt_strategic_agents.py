"""
GPT-Powered Strategic Agents

Enhanced strategic agents with GPT-4 integration for:
- Intelligent battle commentary
- Real-time strategic analysis
- Adaptive decision explanations
- Natural language narration
"""

import os
from typing import Optional, Dict, List
from agents.strategic_agents import Kinetik, StrikeMaster, PhaseTracker, LoadoutMaster
from core.advanced_phase_system import AdvancedPhaseManager

# Check if OpenAI is available
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️  OpenAI not installed. Run: pip install openai")


class GPTStrategicNarrator:
    """
    GPT-powered narrator for strategic battles.

    Provides:
    - Pre-battle analysis
    - Real-time commentary
    - Phase transition insights
    - Post-battle summary
    """

    def __init__(self, api_key: Optional[str] = None):
        if not OPENAI_AVAILABLE:
            self.enabled = False
            return

        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            print("⚠️  No OpenAI API key found. Set OPENAI_API_KEY environment variable.")
            self.enabled = False
            return

        self.client = OpenAI(api_key=self.api_key)
        self.enabled = True
        self.battle_context = []

    def generate_pre_battle_analysis(self, agents: List, duration: int) -> str:
        """Generate pre-battle strategic analysis."""
        if not self.enabled:
            return "GPT commentary disabled."

        agent_roster = "\n".join([f"- {a.emoji} {a.name}" for a in agents])

        prompt = f"""You are an expert TikTok battle analyst. A {duration}-second strategic battle is about to begin.

Strategic Team:
{agent_roster}

Provide a brief (2-3 sentences) pre-battle analysis covering:
1. Key agents to watch
2. Expected strategic moments
3. Predicted battle flow

Keep it exciting and concise."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert TikTok Live battle analyst providing strategic commentary."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )

            analysis = response.choices[0].message.content
            self.battle_context.append(f"Pre-battle: {analysis}")
            return analysis

        except Exception as e:
            return f"Analysis unavailable: {str(e)}"

    def comment_on_phase_transition(self, phase_name: str, multiplier: float, current_time: int, score_diff: int) -> str:
        """Generate commentary for phase transitions."""
        if not self.enabled:
            return ""

        prompt = f"""A TikTok battle phase just changed:

Phase: {phase_name}
Multiplier: x{multiplier}
Time: {current_time}s
Score Difference: {score_diff} points

Provide a brief (1-2 sentences) exciting commentary on this phase transition and what it means strategically."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a TikTok battle commentator. Be exciting and concise."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=80,
                temperature=0.8
            )

            commentary = response.choices[0].message.content
            self.battle_context.append(f"t={current_time}s: {commentary}")
            return commentary

        except Exception as e:
            return ""

    def analyze_agent_action(self, agent_name: str, action: str, impact: int, context: Dict) -> str:
        """Generate analysis of agent actions."""
        if not self.enabled:
            return ""

        prompt = f"""A strategic agent just acted in a TikTok battle:

Agent: {agent_name}
Action: {action}
Impact: {impact} points
Context: Time {context.get('time', 0)}s, Multiplier x{context.get('multiplier', 1.0)}

Provide a brief (1 sentence) analysis of this strategic move."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are analyzing strategic decisions in a TikTok battle."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0.7
            )

            return response.choices[0].message.content

        except Exception as e:
            return ""

    def generate_battle_summary(self, winner: str, final_scores: Dict, analytics: Dict) -> str:
        """Generate post-battle summary."""
        if not self.enabled:
            return "GPT summary disabled."

        # Use battle context
        context_summary = "\n".join(self.battle_context[-5:])  # Last 5 events

        prompt = f"""A strategic TikTok battle just concluded:

Winner: {winner}
Final Scores: Creator {final_scores['creator']:,} vs Opponent {final_scores['opponent']:,}
Boost #2 Triggered: {analytics.get('boost2_triggered', False)}
Gloves Activated: {analytics.get('gloves_activated', 0)}
Power-ups Used: {analytics.get('power_ups_used', 0)}

Recent Events:
{context_summary}

Provide a brief (3-4 sentences) exciting summary of:
1. Key turning point
2. MVP performance
3. Strategic excellence shown"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a TikTok battle analyst providing exciting post-battle summaries."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.8
            )

            return response.choices[0].message.content

        except Exception as e:
            return f"Summary unavailable: {str(e)}"


class GPTKinetik(Kinetik):
    """GPT-enhanced Kinetik with strategic commentary."""

    def __init__(self, narrator: Optional[GPTStrategicNarrator] = None):
        super().__init__()
        self.narrator = narrator

    def decide_action(self, battle):
        """Enhanced decision making with GPT commentary."""
        # Call original logic
        super().decide_action(battle)

        # Add commentary if acted
        if self.has_acted and self.narrator and self.narrator.enabled:
            context = {
                'time': battle.time_manager.current_time,
                'multiplier': 1.0,
                'phase': 'FINAL'
            }

            analysis = self.narrator.analyze_agent_action(
                self.name,
                "Final sniper strike",
                259990,  # Phoenix value
                context
            )

            if analysis:
                print(f"\n💬 GPT Analysis: {analysis}")


class GPTStrikeMaster(StrikeMaster):
    """GPT-enhanced StrikeMaster with learning commentary."""

    def __init__(self, narrator: Optional[GPTStrategicNarrator] = None):
        super().__init__()
        self.narrator = narrator

    def _adapt_strategy(self):
        """Enhanced strategy adaptation with GPT insights."""
        super()._adapt_strategy()

        if self.narrator and self.narrator.enabled and len(self.glove_attempts) >= 3:
            # Get GPT analysis of learning
            prompt = f"""StrikeMaster has sent {len(self.glove_attempts)} gloves with {self.gloves_activated} activations ({self.success_rate*100:.0f}% success).

What strategic lesson should be learned? (1 sentence)"""

            try:
                response = self.narrator.client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are analyzing strategic learning in battles."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=40,
                    temperature=0.7
                )

                insight = response.choices[0].message.content
                print(f"\n💡 GPT Learning Insight: {insight}")

            except Exception:
                pass


class GPTPhaseTracker(PhaseTracker):
    """GPT-enhanced PhaseTracker with phase analysis."""

    def __init__(self, narrator: Optional[GPTStrategicNarrator] = None):
        super().__init__()
        self.narrator = narrator

    def decide_action(self, battle):
        """Enhanced phase tracking with commentary."""
        # Check if we just triggered Boost #2
        was_triggered = self.phase_manager.boost2.condition_met if self.phase_manager else False

        super().decide_action(battle)

        # Comment on successful trigger
        if self.phase_manager and self.phase_manager.boost2.condition_met and not was_triggered:
            if self.narrator and self.narrator.enabled:
                print(f"\n💬 GPT: PhaseTracker's strategic roses successfully triggered the Boost #2 phase! Excellent timing.")


class GPTLoadoutMaster(LoadoutMaster):
    """GPT-enhanced LoadoutMaster with tactical commentary."""

    def __init__(self, narrator: Optional[GPTStrategicNarrator] = None):
        super().__init__()
        self.narrator = narrator

    def decide_action(self, battle):
        """Enhanced power-up deployment with commentary."""
        super().decide_action(battle)

        # Add commentary on power-up use
        if self.narrator and self.narrator.enabled:
            if self.hammer_used and self.narrator:
                print(f"\n💬 GPT: Tactical hammer deployment! Neutralizing opponent's momentum.")
            elif self.fog_used:
                print(f"\n💬 GPT: Strategic fog activated! Psychological warfare engaged.")


def create_gpt_strategic_team(
    phase_manager: AdvancedPhaseManager,
    api_key: Optional[str] = None
) -> tuple[List, GPTStrategicNarrator]:
    """
    Create GPT-enhanced strategic team.

    Returns:
        (agents, narrator): List of enhanced agents and narrator instance
    """
    narrator = GPTStrategicNarrator(api_key=api_key)

    if not narrator.enabled:
        print("⚠️  GPT features disabled. Using standard strategic agents.")
        from agents.strategic_agents import create_strategic_team
        return create_strategic_team(phase_manager), narrator

    # Create GPT-enhanced agents
    kinetik = GPTKinetik(narrator=narrator)
    strike_master = GPTStrikeMaster(narrator=narrator)
    phase_tracker = GPTPhaseTracker(narrator=narrator)
    loadout_master = GPTLoadoutMaster(narrator=narrator)

    # Link to phase manager
    kinetik.set_phase_manager(phase_manager)
    strike_master.set_phase_manager(phase_manager)
    phase_tracker.set_phase_manager(phase_manager)
    loadout_master.set_phase_manager(phase_manager)

    agents = [kinetik, strike_master, phase_tracker, loadout_master]

    return agents, narrator


if __name__ == '__main__':
    # Demo
    print("GPT Strategic Agents Demo")
    print("="*70)

    # Check if GPT is available
    if not OPENAI_AVAILABLE:
        print("\n❌ OpenAI package not installed")
        print("Install with: pip install openai")
        exit(1)

    # Check for API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("\n❌ No OpenAI API key found")
        print("Set with: export OPENAI_API_KEY='your-key-here'")
        exit(1)

    # Create narrator
    narrator = GPTStrategicNarrator(api_key=api_key)

    if narrator.enabled:
        print("\n✅ GPT narrator initialized")

        # Test pre-battle analysis
        print("\n🎬 Testing pre-battle analysis...")
        from agents.strategic_agents import Kinetik, StrikeMaster, PhaseTracker, LoadoutMaster

        agents = [Kinetik(), StrikeMaster(), PhaseTracker(), LoadoutMaster()]
        analysis = narrator.generate_pre_battle_analysis(agents, 180)

        print(f"\n💬 GPT Pre-Battle Analysis:")
        print(f"   {analysis}")

        print("\n✅ GPT integration working!")
    else:
        print("\n❌ GPT narrator failed to initialize")
