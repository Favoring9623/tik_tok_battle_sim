"""
GPT Intelligence - AI-powered decision making and narrative generation.

Uses OpenAI's GPT-4 to:
- Make strategic battle decisions
- Generate contextual messages
- Create battle lore and narratives
"""

import os
from typing import Dict, Any, Optional, List
import json


# Try to load .env file if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()  # Load .env file from current directory
except ImportError:
    pass  # python-dotenv not installed, that's ok


class GPTDecisionEngine:
    """
    GPT-powered decision making for agents.

    Analyzes battle state and agent personality to make intelligent decisions.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        """
        Initialize GPT decision engine.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var or .env file)
            model: Model to use (gpt-4, gpt-4-turbo, gpt-3.5-turbo, or GPT_MODEL env var)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("GPT_MODEL") or model  # Check env var first
        self.client = None

        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
            except ImportError:
                print("⚠️  OpenAI package not installed. Run: pip install openai")
            except Exception as e:
                print(f"⚠️  GPT initialization error: {e}")

    def is_available(self) -> bool:
        """Check if GPT is available and configured."""
        return self.client is not None

    def decide_action(self,
                     agent_name: str,
                     personality: str,
                     battle_state: Dict[str, Any],
                     agent_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ask GPT to decide what action the agent should take.

        Args:
            agent_name: Name of the agent
            personality: Agent's personality description
            battle_state: Current battle state (time, scores, phase, etc.)
            agent_state: Agent's current state (emotion, budget, etc.)

        Returns:
            Dictionary with decision:
            {
                "action": "gift" | "message" | "wait",
                "gift_type": str (if action=gift),
                "gift_value": int (if action=gift),
                "message": str (if action=message),
                "reasoning": str
            }
        """
        if not self.is_available():
            return {"action": "wait", "reasoning": "GPT not available"}

        # Build context prompt
        prompt = self._build_decision_prompt(
            agent_name, personality, battle_state, agent_state
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a strategic AI agent in a TikTok battle. Respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=200
                # Note: response_format removed for compatibility with all GPT-4 models
            )

            # Parse JSON from response
            content = response.choices[0].message.content.strip()

            # Try to extract JSON if wrapped in markdown code blocks
            if content.startswith("```"):
                # Remove markdown code blocks
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
                content = content.strip()

            decision = json.loads(content)
            return decision

        except json.JSONDecodeError as e:
            print(f"⚠️  GPT JSON parse error: {e}")
            print(f"   Response was: {content[:100]}...")
            return {"action": "wait", "reasoning": "JSON parse error"}
        except Exception as e:
            print(f"⚠️  GPT decision error: {e}")
            return {"action": "wait", "reasoning": f"Error: {e}"}

    def _build_decision_prompt(self,
                               agent_name: str,
                               personality: str,
                               battle_state: Dict[str, Any],
                               agent_state: Dict[str, Any]) -> str:
        """Build the decision prompt for GPT."""

        return f"""You are {agent_name}, an AI agent in a TikTok live battle.

YOUR PERSONALITY:
{personality}

CURRENT BATTLE STATE:
- Time: {battle_state.get('time', 0)}s / 60s (Phase: {battle_state.get('phase', 'EARLY')})
- Creator Score: {battle_state.get('creator_score', 0)}
- Opponent Score: {battle_state.get('opponent_score', 0)}
- Score Difference: {battle_state.get('score_diff', 0)} (positive = losing)
- Leader: {battle_state.get('leader', 'unknown')}
- Time Remaining: {battle_state.get('time_remaining', 60)}s

YOUR STATE:
- Current Emotion: {agent_state.get('emotion', 'CALM')}
- Total Donated: {agent_state.get('total_donated', 0)} points
- Budget Remaining: {agent_state.get('budget', 'unlimited')}
- Actions Taken: {agent_state.get('action_count', 0)}

AVAILABLE GIFT OPTIONS:
{self._format_gift_options(agent_name)}

DECISION REQUIRED:
Based on your personality and the battle state, decide your next action.

Respond with JSON in this format:
{{
    "action": "gift" | "message" | "wait",
    "gift_type": "ROSE" | "GALAXY" | "UNIVERSE" | "LION & UNIVERSE" (if action=gift),
    "gift_value": 10-1800 (if action=gift),
    "message": "your message here" (if action=message),
    "reasoning": "brief explanation of why you chose this action"
}}

Remember:
- Stay true to your personality
- Consider timing and battle dynamics
- Don't spam - choose impactful moments
- Your decision should make strategic sense
"""

    def _format_gift_options(self, agent_name: str) -> str:
        """Format gift options based on agent type."""

        options = {
            "NovaWhale": [
                "LION & UNIVERSE: 1800 points (your signature move)",
                "UNIVERSE: 1200 points",
                "GALAXY: 800 points"
            ],
            "PixelPixie": [
                "ROSE: 10 points (your go-to)",
                "HEART: 20 points",
                "SPARKLE: 50 points"
            ],
            "GlitchMancer": [
                "TikTok Gift: 60 points (for burst mode)",
                "GLITCH: 100 points",
                "CHAOS: 150 points"
            ],
            "ShadowPatron": [
                "GALAXY: 400 points (your strike weapon)",
                "SHADOW: 600 points",
                "VOID: 800 points"
            ],
            "Dramatron": [
                "Theatrical Gift: 50-100 points",
                "DRAMA: 120 points",
                "SPOTLIGHT: 200 points"
            ]
        }

        agent_options = options.get(agent_name, ["Generic Gift: 100 points"])
        return "\n".join(f"- {opt}" for opt in agent_options)

    def generate_message(self,
                        agent_name: str,
                        personality: str,
                        context: str,
                        message_type: str = "chat") -> str:
        """
        Generate a contextual message for an agent.

        Args:
            agent_name: Agent name
            personality: Agent personality
            context: Current situation context
            message_type: Type of message (chat, cheer, taunt, etc.)

        Returns:
            Generated message string
        """
        if not self.is_available():
            return f"[{agent_name}]"

        prompt = f"""You are {agent_name} in a TikTok battle.

YOUR PERSONALITY:
{personality}

SITUATION:
{context}

Generate a {message_type} message that fits your personality.
Keep it SHORT (1-15 words max), dramatic, and in-character.
Use emojis sparingly if they fit your style.

Respond with ONLY the message text, no quotes or formatting."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a creative AI generating short, in-character messages."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=50
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"⚠️  Message generation error: {e}")
            return f"[{agent_name}]"


class GPTLoreGenerator:
    """
    Generates dramatic battle narratives and lore.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.client = None

        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
            except ImportError:
                print("⚠️  OpenAI package not installed. Run: pip install openai")
            except Exception as e:
                print(f"⚠️  GPT initialization error: {e}")

    def is_available(self) -> bool:
        return self.client is not None

    def generate_battle_summary(self,
                               battle_data: Dict[str, Any],
                               style: str = "epic") -> str:
        """
        Generate a narrative summary of a battle.

        Args:
            battle_data: Battle results and timeline
            style: Narrative style (epic, poetic, dramatic, comedic)

        Returns:
            Narrative text
        """
        if not self.is_available():
            return "GPT lore generation not available."

        prompt = self._build_lore_prompt(battle_data, style)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": f"You are a {style} storyteller narrating TikTok battles."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.9,
                max_tokens=500
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"⚠️  Lore generation error: {e}")
            return f"Error generating lore: {e}"

    def _build_lore_prompt(self, battle_data: Dict[str, Any], style: str) -> str:
        """Build the lore generation prompt."""

        winner = battle_data.get('winner', 'unknown')
        creator_score = battle_data.get('creator_score', 0)
        opponent_score = battle_data.get('opponent_score', 0)
        agents = battle_data.get('agents', [])
        key_moments = battle_data.get('key_moments', [])

        return f"""Generate a {style} narrative summary of this TikTok battle:

BATTLE OUTCOME:
- Winner: {winner.upper()}
- Final Score: Creator {creator_score} vs Opponent {opponent_score}
- Margin: {abs(creator_score - opponent_score)} points

AGENTS WHO PARTICIPATED:
{', '.join(agents)}

KEY MOMENTS:
{self._format_key_moments(key_moments)}

Write a 3-5 paragraph {style} narrative that:
1. Sets the scene
2. Describes the key dramatic moments
3. Highlights agent contributions and personality
4. Builds to the climactic conclusion
5. Captures the emotional arc

Make it feel like an epic tale, not just a dry recap.
"""

    def _format_key_moments(self, moments: List[str]) -> str:
        """Format key moments for the prompt."""
        if not moments:
            return "- The battle progressed with various gifts and messages"
        return "\n".join(f"- {moment}" for moment in moments[:10])

    def generate_agent_quote(self,
                           agent_name: str,
                           personality: str,
                           situation: str) -> str:
        """Generate a memorable quote for an agent in a specific situation."""

        if not self.is_available():
            return f"[{agent_name} quote]"

        prompt = f"""You are {agent_name}.

YOUR PERSONALITY:
{personality}

SITUATION:
{situation}

Generate a single, memorable quote (10-25 words) that captures your personality and response to this situation.
Make it dramatic, quotable, and true to character.

Respond with ONLY the quote, no attribution or formatting."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a creative writer generating memorable character quotes."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.9,
                max_tokens=100
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            return f"[Quote generation error: {e}]"
