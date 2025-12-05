# TikTok AI Battle Simulator v2.0

An event-driven, modular simulation framework for TikTok-style live battles featuring AI agents with emotions, personalities, and inter-agent communication.

## 🎯 Overview

This project simulates TikTok live battles where AI agents act as donors/supporters, each with unique personalities, strategies, and emotional responses. It's designed for:

- **Performance art installations** - Visual, audio, and narrative experiences
- **Research & experimentation** - Agent behavior, emergence, and AI coordination
- **Content creation** - Generate battle narratives, highlight reels, lore
- **Prototyping** - Test battle mechanics and AI strategies

## ✨ Key Features

### 🏗️ **Modular Architecture**
- **Event-Driven System**: Loose coupling via pub/sub event bus
- **Plugin-Based Agents**: Drop in new agents without touching core code
- **Separation of Concerns**: Battle logic, agents, UI, and persistence are independent
- **Testable & Observable**: Every component can be tested and monitored in isolation

### 🤖 **Intelligent Agents**
- **Emotion System**: Agents have emotional states (calm, excited, frustrated, vengeful, etc.)
- **Memory & Learning**: Agents remember past battles and develop relationships
- **Inter-Agent Communication**: Agents can message each other, creating drama
- **Unique Personalities**: 5 pre-built personas with distinct strategies

### 📊 **Analytics & Insights**
- **Event Logging**: Complete battle history for replay and analysis
- **Real-Time Metrics**: Scores, momentum, win probability
- **Agent Statistics**: Contribution tracking, win rates, emotional arcs

## 🎭 Built-In Agent Personas

| Agent | Emoji | Personality | Strategy |
|-------|-------|-------------|----------|
| **NovaWhale** | 🐋 | Strategic whale | Waits for critical moments, drops massive gifts |
| **PixelPixie** | 🧚‍♀️ | Budget cheerleader | Frequent small gifts with constant encouragement |
| **GlitchMancer** | 🌀 | Chaotic wildcard | Unpredictable burst-mode gift attacks |
| **ShadowPatron** | 👤 | Silent observer | Completely silent until crisis, then strikes |
| **Dramatron** | 🎭 | Theatrical performer | Narrates battle like a Shakespearean play |

## 🚀 Quick Start

### Installation

```bash
# Clone or navigate to project directory
cd tik_tok_battle_sim

# Install dependencies (if needed)
pip install -r requirements.txt  # (currently minimal dependencies)
```

### Run Demo Battle

```bash
python3 demo_battle.py
```

This runs a 60-second simulated battle with all 5 AI agents competing to help the creator win.

### Basic Usage

```python
from core import BattleEngine, EventBus
from agents.personas import NovaWhale, PixelPixie, GlitchMancer

# Create battle engine
engine = BattleEngine(battle_duration=60, tick_speed=0.25)

# Add agents
engine.add_agent(NovaWhale())
engine.add_agent(PixelPixie())
engine.add_agent(GlitchMancer())

# Subscribe to events
def on_battle_end(event):
    winner = event.data['winner']
    print(f"Winner: {winner}")

engine.event_bus.subscribe(EventType.BATTLE_ENDED, on_battle_end)

# Run the battle!
engine.run()
```

## 📐 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                 PRESENTATION LAYER                       │
│    (Streamlit Dashboard, CLI, Web API - Future)         │
└──────────────────────┬──────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────┐
│              EVENT BUS (Pub/Sub)                         │
│  - Battle events, agent actions, score changes, etc.    │
└─────┬──────────────┬────────────────┬───────────────────┘
      │              │                │
┌─────▼─────┐  ┌────▼────────┐  ┌────▼──────────────────┐
│ CORE      │  │  AGENTS     │  │  EXTENSIONS           │
│           │  │             │  │                       │
│ • Battle  │  │ • Emotion   │  │ • Lore Generator      │
│   Engine  │  │   System    │  │ • TTS (future)        │
│ • Score   │  │ • Memory    │  │ • Analytics           │
│   Tracker │  │   System    │  │ • OBS Integration     │
│ • Time    │  │ • Comms     │  │                       │
│   Manager │  │   Channel   │  │                       │
└───────────┘  └─────────────┘  └───────────────────────┘
```

### Core Components

#### `core/`
- **`event_bus.py`** - Central event system (pub/sub pattern)
- **`battle_engine.py`** - Main simulation orchestrator
- **`score_tracker.py`** - Score management and momentum tracking
- **`time_manager.py`** - Battle timing and phase detection

#### `agents/`
- **`base_agent.py`** - Abstract base class for all agents
- **`emotion_system.py`** - Emotional state modeling
- **`memory_system.py`** - Long-term agent memory
- **`communication.py`** - Inter-agent messaging

#### `agents/personas/`
Pre-built agent implementations:
- `nova_whale.py`
- `pixel_pixie.py`
- `glitch_mancer.py`
- `shadow_patron.py`
- `dramatron.py`

## 🎨 Creating Custom Agents

Creating a new agent is simple - inherit from `BaseAgent` and implement `decide_action()`:

```python
from agents.base_agent import BaseAgent
from agents.emotion_system import EmotionalState

class MyCustomAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="MyAgent", emoji="⚡")
        self.custom_budget = 500

    def decide_action(self, battle):
        """Your custom logic here."""
        current_time = battle.time_manager.current_time
        creator_score = battle.score_tracker.creator_score

        # Example: Send gift if losing in final 15 seconds
        if current_time > 45 and creator_score < battle.score_tracker.opponent_score:
            self.send_gift(battle, "POWER GIFT", 200)
            self.send_message("Time to turn this around! ⚡")

    def get_personality_prompt(self) -> str:
        return "I'm a strategic supporter who acts in critical moments."

# Use it:
engine.add_agent(MyCustomAgent())
```

## 🔮 Future Extensions

Based on your original vision, here are the next features to implement:

### Phase 1: Performance Layer ✅ **READY TO BUILD**
- **GPT Integration** - Use OpenAI for dynamic decision-making (already has infrastructure)
- **TTS Voiceover** - ElevenLabs or pyttsx3 for agent voices
- **Web Dashboard** - React/Vue real-time visualization
- **Lore Generator** - GPT-powered narrative summaries

### Phase 2: Broadcast Ready
- **OBS Integration** - Browser source overlays
- **Dynamic Soundtrack** - Music changes based on battle intensity
- **Advanced Visualizations** - Emotion indicators, momentum meters
- **Replay System** - Battle replay with highlights

### Phase 3: Interaction & Gamification
- **Audience Voting** - Let viewers influence AI decisions
- **Squad Builder** - Custom team composition
- **Leaderboards** - Track agent performance across battles
- **Live Data Integration** - Read-only TikTok battle data (view-only scraping)

### Phase 4: Research & Analytics
- **Battle Analytics Dashboard** - Deep insights into agent behavior
- **Strategy Optimization** - Machine learning on successful patterns
- **A/B Testing Framework** - Test different agent configurations
- **Export Capabilities** - JSON, CSV data export

## 🛠️ Development Roadmap

Current Status: **Foundation Complete** ✅

- [x] Event-driven architecture
- [x] Emotion modeling system
- [x] Inter-agent communication
- [x] 5 unique agent personas
- [x] Memory/persistence framework
- [x] Comprehensive analytics
- [ ] GPT decision-making integration
- [ ] TTS voiceover system
- [ ] Web dashboard (React/Streamlit)
- [ ] OBS streaming integration
- [ ] Live TikTok data integration (view-only)

## 📊 Example Output

```
======================================================================
🎬 TikTok AI Battle Simulator v2.0 - Demo Battle
======================================================================

🎭 Dramatron: "ACT I: The curtain rises upon our tale!"
🧚‍♀️ PixelPixie 🔥: Sends ROSE 🎁 (+12)
📢 PixelPixie: "Let's goooo! 🌟"

🌀 GlitchMancer: ⚡ BURST MODE ACTIVATED ⚡
🌀 GlitchMancer 🌀: Sends TikTok Gift 🎁 (+106)
🌀 GlitchMancer 🌀: Sends TikTok Gift 🎁 (+106)
...

🏆 Final Score:
   Creator:  2,914 points
   Opponent: 1,086 points
   Winner:   CREATOR

🤖 Agent Contributions:
   🧚‍♀️ PixelPixie      - 104 points (10 gifts) - EXCITED
   🌀 GlitchMancer    - 1,863 points (23 gifts) - CHAOTIC
   🎭 Dramatron       - 947 points (11 gifts) - TRIUMPHANT
```

## 🧪 Research Applications

This framework enables exploration of:
- **Emergent Agent Behavior** - How do agents coordinate without explicit coordination code?
- **Emotional Dynamics** - How do emotions affect decision-making effectiveness?
- **Strategy Optimization** - Which gifting patterns maximize win rates?
- **Narrative Generation** - Can AI create compelling stories from battle data?
- **Human-AI Coordination** - How might real users interact with AI agents?

## 📄 License

[Your chosen license]

## 🤝 Contributing

Contributions welcome! Some ideas:
- New agent personas
- GPT integration for decision-making
- Web dashboard implementation
- TTS voiceover system
- Battle replay viewer
- Analytics visualizations

## 🙏 Acknowledgments

Built for experimental and educational purposes, exploring AI agent behavior in competitive social scenarios.

---

**Ready to build the next phase?** Let's add GPT integration, TTS, or a web dashboard! 🚀
