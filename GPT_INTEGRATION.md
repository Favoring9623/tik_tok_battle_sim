# GPT-4 Integration for Strategic Battles

## Overview

Advanced GPT-4 integration that enhances strategic battles with real-time AI commentary, strategic analysis, and natural language narration.

---

## 🎯 Features

### 1. Pre-Battle Strategic Analysis
GPT-4 analyzes the team composition and provides strategic predictions:
```
💬 GPT Pre-Battle Analysis:
   "Watch for Kinetik's signature last-second strike and StrikeMaster's
   glove timing expertise. Expect PhaseTracker to trigger Boost #2
   around the 70s mark, setting up a explosive mid-game sequence."
```

### 2. Real-Time Phase Commentary
Intelligent commentary on phase transitions:
```
💬 GPT Commentary:
   "The x3 boost activation shifts momentum dramatically! Creator team
   needs to capitalize on this 30-second window to build their lead."
```

### 3. Agent Action Analysis
Strategic insights on key agent decisions:
```
💬 GPT Analysis:
   "Kinetik's perfectly-timed Phoenix deployment in the final moments
   demonstrates elite sniper instincts - a textbook clutch play!"
```

### 4. Learning Insights for StrikeMaster
GPT analyzes glove activation patterns:
```
💡 GPT Learning Insight:
   "With 50% success rate, StrikeMaster should continue prioritizing
   boost phases over late-game attempts."
```

### 5. Post-Battle Summary
Comprehensive battle analysis with key moments:
```
💬 GPT Battle Summary:
   "The turning point came when PhaseTracker's strategic roses triggered
   Boost #2, followed by StrikeMaster's perfectly-timed glove activation.
   Kinetik emerged as MVP with a devastating final-second Phoenix strike
   that sealed victory. This battle showcased exceptional coordination
   and strategic timing from the creator team."
```

---

## 🚀 Setup

### 1. Install OpenAI Package

```bash
pip install openai
```

### 2. Set API Key

**Option A: Environment Variable**
```bash
export OPENAI_API_KEY='sk-your-api-key-here'
```

**Option B: Direct Parameter**
```python
from agents.gpt_strategic_agents import create_gpt_strategic_team

agents, narrator = create_gpt_strategic_team(
    phase_manager,
    api_key='sk-your-api-key-here'
)
```

**Option C: .env File**
```bash
# .env file
OPENAI_API_KEY=sk-your-api-key-here
```

```python
# Load in Python
from dotenv import load_dotenv
load_dotenv()
```

---

## 📖 Usage

### Quick Start

```bash
# With GPT commentary
export OPENAI_API_KEY='your-key'
python3 demo_gpt_strategic_battle.py

# Without GPT (fallback to standard agents)
python3 demo_gpt_strategic_battle.py
```

### Programmatic Usage

```python
from core.advanced_phase_system import AdvancedPhaseManager
from agents.gpt_strategic_agents import create_gpt_strategic_team

# Create phase manager
phase_manager = AdvancedPhaseManager(battle_duration=180)

# Create GPT-enhanced team
agents, narrator = create_gpt_strategic_team(phase_manager)

# Check if GPT is enabled
if narrator.enabled:
    # Generate pre-battle analysis
    analysis = narrator.generate_pre_battle_analysis(agents, 180)
    print(f"Pre-Battle: {analysis}")

    # Use during battle for commentary
    commentary = narrator.comment_on_phase_transition(
        phase_name="Boost #1 - x3",
        multiplier=3.0,
        current_time=60,
        score_diff=500
    )
    print(f"Commentary: {commentary}")

    # Post-battle summary
    summary = narrator.generate_battle_summary(
        winner="creator",
        final_scores={'creator': 250000, 'opponent': 150000},
        analytics={'boost2_triggered': True, 'gloves_activated': 2}
    )
    print(f"Summary: {summary}")
```

---

## 🤖 GPT-Enhanced Agents

### GPTKinetik
Enhanced final sniper with commentary on clutch plays:
```python
from agents.gpt_strategic_agents import GPTKinetik

kinetik = GPTKinetik(narrator=narrator)
kinetik.set_phase_manager(phase_manager)

# When Kinetik acts, GPT provides analysis:
# 💬 GPT Analysis: Devastating final strike deployed at the
#    perfect moment - a masterclass in sniper timing!
```

### GPTStrikeMaster
Glove expert with AI-powered learning insights:
```python
from agents.gpt_strategic_agents import GPTStrikeMaster

strike_master = GPTStrikeMaster(narrator=narrator)

# After learning, GPT provides insights:
# 💡 GPT Learning Insight: Boost phase timing shows
#    superior results - maintain this strategy!
```

### GPTPhaseTracker
Phase monitor with commentary on successful triggers:
```python
from agents.gpt_strategic_agents import GPTPhaseTracker

phase_tracker = GPTPhaseTracker(narrator=narrator)

# On successful Boost #2 trigger:
# 💬 GPT: PhaseTracker's strategic roses successfully
#    triggered Boost #2! Excellent timing.
```

### GPTLoadoutMaster
Power-up manager with tactical commentary:
```python
from agents.gpt_strategic_agents import GPTLoadoutMaster

loadout_master = GPTLoadoutMaster(narrator=narrator)

# On power-up deployment:
# 💬 GPT: Tactical hammer deployment! Neutralizing
#    opponent's momentum.
```

---

## 🎮 GPTStrategicNarrator API

### Methods

#### `generate_pre_battle_analysis(agents, duration)`
Generates strategic preview before battle starts.

**Parameters:**
- `agents`: List of agent objects
- `duration`: Battle duration in seconds

**Returns:** String with 2-3 sentence analysis

**Example:**
```python
analysis = narrator.generate_pre_battle_analysis(agents, 180)
# "Kinetik's last-second timing and StrikeMaster's glove mastery
#  will be crucial. Expect PhaseTracker to secure Boost #2,
#  setting up a explosive mid-game."
```

---

#### `comment_on_phase_transition(phase_name, multiplier, current_time, score_diff)`
Provides commentary on phase changes.

**Parameters:**
- `phase_name`: Name of new phase
- `multiplier`: Current multiplier value
- `current_time`: Battle time in seconds
- `score_diff`: Point difference between teams

**Returns:** String with 1-2 sentence commentary

**Example:**
```python
commentary = narrator.comment_on_phase_transition(
    "Boost #1 - x3", 3.0, 60, 1000
)
# "The x3 boost dramatically amplifies every gift! Creator team
#  must capitalize on this window to extend their lead."
```

---

#### `analyze_agent_action(agent_name, action, impact, context)`
Analyzes individual agent decisions.

**Parameters:**
- `agent_name`: Name of agent
- `action`: Description of action taken
- `impact`: Point impact value
- `context`: Dict with time, multiplier, phase

**Returns:** String with 1 sentence analysis

**Example:**
```python
analysis = narrator.analyze_agent_action(
    "Kinetik",
    "Final sniper strike",
    259990,
    {'time': 175, 'multiplier': 1.0, 'phase': 'FINAL'}
)
# "Perfectly executed clutch play - elite sniper timing!"
```

---

#### `generate_battle_summary(winner, final_scores, analytics)`
Creates comprehensive post-battle summary.

**Parameters:**
- `winner`: "creator" or "opponent"
- `final_scores`: Dict with creator/opponent scores
- `analytics`: Dict with battle statistics

**Returns:** String with 3-4 sentence summary

**Example:**
```python
summary = narrator.generate_battle_summary(
    winner="creator",
    final_scores={'creator': 262240, 'opponent': 8756},
    analytics={
        'boost2_triggered': True,
        'gloves_activated': 0,
        'power_ups_used': 1
    }
)
# "Creator team dominated through strategic power-up deployment
#  and perfect phase timing. The turning point came when Boost #2
#  was triggered, amplifying their lead exponentially. Kinetik's
#  final Phoenix strike sealed an already decisive victory."
```

---

## ⚙️ Configuration

### GPT Model Selection

Default: `gpt-4`

To change models, edit `agents/gpt_strategic_agents.py`:
```python
# Line 50, 85, 120, 160 - change model parameter
response = self.client.chat.completions.create(
    model="gpt-4-turbo",  # or "gpt-3.5-turbo" for faster/cheaper
    ...
)
```

### Token Limits

Default token limits per function:
- `generate_pre_battle_analysis`: 150 tokens
- `comment_on_phase_transition`: 80 tokens
- `analyze_agent_action`: 50 tokens
- `generate_battle_summary`: 200 tokens

Adjust in respective functions:
```python
response = self.client.chat.completions.create(
    ...
    max_tokens=150,  # Adjust as needed
    ...
)
```

### Temperature Settings

Default temperatures:
- Pre-battle analysis: 0.7 (balanced)
- Phase commentary: 0.8 (creative)
- Agent analysis: 0.7 (balanced)
- Battle summary: 0.8 (creative)

---

## 💰 Cost Estimation

### GPT-4 Pricing (as of 2024)
- Input: $0.03 per 1K tokens
- Output: $0.06 per 1K tokens

### Typical Battle Cost

**With full commentary (3 phase commentaries + analysis + summary):**
- Input tokens: ~800
- Output tokens: ~400
- **Total cost: ~$0.048 per battle** (~5 cents)

**Conservative mode (only summary):**
- Input tokens: ~300
- Output tokens: ~150
- **Total cost: ~$0.018 per battle** (~2 cents)

### Cost Optimization

**Option 1: Use GPT-3.5-Turbo**
```python
model="gpt-3.5-turbo"  # 10x cheaper
```

**Option 2: Limit Commentary**
```python
# Only comment on first phase transition
if phase_transition_count == 1:
    commentary = narrator.comment_on_phase_transition(...)
```

**Option 3: Summary Only**
```python
# Skip real-time commentary, only use post-battle summary
if narrator.enabled:
    summary = narrator.generate_battle_summary(...)
```

---

## 🔒 Security & Best Practices

### API Key Security

**✅ DO:**
- Use environment variables
- Use `.env` files (add to `.gitignore`)
- Rotate keys regularly
- Use project-specific keys

**❌ DON'T:**
- Hard-code keys in source files
- Commit keys to version control
- Share keys in public repositories
- Use production keys for testing

### Error Handling

GPT integration includes graceful fallbacks:
```python
if not narrator.enabled:
    # Falls back to standard strategic agents
    # Battle continues without GPT features
```

All GPT calls are wrapped in try-except:
```python
try:
    response = self.client.chat.completions.create(...)
    return response.choices[0].message.content
except Exception as e:
    return ""  # Fails silently, doesn't break battle
```

---

## 🧪 Testing

### Test Without API Key
```bash
python3 demo_gpt_strategic_battle.py
```
Expected: Graceful fallback to standard agents

### Test With Invalid Key
```bash
export OPENAI_API_KEY='invalid-key'
python3 demo_gpt_strategic_battle.py
```
Expected: Warning message, continues without GPT

### Test GPT Narrator
```bash
export OPENAI_API_KEY='your-valid-key'
python3 agents/gpt_strategic_agents.py
```
Expected: Pre-battle analysis generated successfully

### Test Full Battle
```bash
export OPENAI_API_KEY='your-valid-key'
python3 demo_gpt_strategic_battle.py
```
Expected: Full commentary throughout battle

---

## 📊 Example Output

### Complete GPT-Enhanced Battle

```
🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖
GPT-POWERED STRATEGIC BATTLE
🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖🤖

======================================================================
🎙️  GPT PRE-BATTLE ANALYSIS
======================================================================

💬 Watch for Kinetik's signature last-second intervention and
   StrikeMaster's adaptive glove timing. PhaseTracker should secure
   Boost #2 around 70s, creating a powerful mid-game surge that could
   decide the battle.

======================================================================
🚀 BATTLE START - GPT Commentary Enabled
======================================================================

⏱️  t=60s | Phase: Boost #1 - x3 | Multiplier: x3.0

💬 GPT Commentary: The x3 multiplier activation creates a critical
   30-second window! Every gift sent now has triple impact - this is
   where battles are won or lost.

🥊 StrikeMaster sending GLOVE!
   Conditions: Boost=True, Last30s=False
   Success rate: 0.0% (0/0)

⏱️ PhaseTracker: Sending strategic ROSE #1/5 to trigger Boost #2
✅ Boost #2 Conditions MET!

💬 GPT: PhaseTracker's strategic roses successfully triggered Boost #2!
   Excellent timing.

⏱️  t=90s | Phase: Boost #2 - x2 | Multiplier: x2.0

💬 GPT Commentary: Boost #2 secured through perfect coordination!
   The doubled multiplier extends the advantage window significantly.

🔫 Kinetik activating! Deficit: 6,361 points
   🔥🐦 Deploying PHOENIX!

💬 GPT Analysis: Devastating final-second deployment! Kinetik's
   sniper timing is textbook perfect - this is how clutch victories
   are secured.

======================================================================
🎙️  GPT BATTLE SUMMARY
======================================================================

💬 The battle's turning point came at 70s when PhaseTracker's strategic
   roses triggered Boost #2, creating an extended multiplier window.
   StrikeMaster showed impressive adaptation with 50% glove success.
   But it was Kinetik's perfectly-timed Phoenix strike in the final
   seconds that delivered the knockout blow, demonstrating elite
   sniper instincts. A masterclass in coordinated strategic play!

======================================================================
💎 BATTLE REWARDS DISTRIBUTION
======================================================================

#1 Kinetik: 💎 2,700 diamonds
   🏆 Sniper Elite, Whale Supporter, Clutch Winner, Comeback King

✅ GPT-Powered Strategic Battle Complete!
🤖 GPT-4 provided real-time strategic commentary throughout the battle!
```

---

## 🔮 Future Enhancements

Potential GPT integration expansions:

1. **Adaptive Strategy Suggestions**
   - GPT recommends optimal next moves for agents
   - Real-time tactical adjustments

2. **Opponent Prediction**
   - GPT predicts opponent behavior patterns
   - Anticipates counter-strategies

3. **Multi-Battle Learning**
   - GPT remembers past battles
   - Evolves commentary based on agent history

4. **Voice Commentary**
   - Text-to-speech GPT commentary
   - Real-time audio narration

5. **Custom Personality Modes**
   - Professional analyst mode
   - Hype commentator mode
   - Technical breakdown mode

---

## 📞 Troubleshooting

### "No OpenAI API key found"
**Solution:** Set environment variable
```bash
export OPENAI_API_KEY='your-key'
```

### "OpenAI package not installed"
**Solution:** Install package
```bash
pip install openai
```

### "Rate limit exceeded"
**Solution:** Add delay between API calls
```python
import time
time.sleep(1)  # Wait 1 second between calls
```

### "Invalid API key"
**Solution:** Verify key is correct and active
```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Commentary not appearing
**Solution:** Check narrator.enabled flag
```python
print(f"GPT enabled: {narrator.enabled}")
```

---

## 📁 Files

1. **`agents/gpt_strategic_agents.py`** (458 lines)
   - GPTStrategicNarrator class
   - GPT-enhanced agent subclasses
   - Integration utilities

2. **`demo_gpt_strategic_battle.py`** (238 lines)
   - Complete GPT battle demo
   - Commentary integration examples
   - Usage documentation

3. **`GPT_INTEGRATION.md`** (this file)
   - Setup instructions
   - API documentation
   - Best practices guide

---

**Last Updated**: 2025-11-24
**Version**: 1.0.0
**Status**: ✅ Ready for Production
**OpenAI API Version**: v1.0+
