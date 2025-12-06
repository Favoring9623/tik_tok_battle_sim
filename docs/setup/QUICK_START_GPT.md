# GPT Integration - Quick Start Guide

## ⚡ 60-Second Setup

### 1. Install OpenAI
```bash
pip install openai
```

### 2. Set API Key
```bash
export OPENAI_API_KEY='sk-your-key-here'
```

### 3. Run GPT Battle
```bash
python3 demo_gpt_strategic_battle.py
```

**That's it!** 🎉

---

## 🎮 What You Get

### Real-Time AI Commentary
```
💬 GPT Commentary:
   "The x3 boost activation shifts momentum dramatically!
   Creator team must capitalize on this window."
```

### Strategic Analysis
```
💬 GPT Pre-Battle Analysis:
   "Watch for Kinetik's last-second strike and StrikeMaster's
   glove timing. Expect PhaseTracker to trigger Boost #2
   around the 70s mark."
```

### Post-Battle Summary
```
💬 GPT Battle Summary:
   "The turning point came when PhaseTracker triggered Boost #2,
   followed by StrikeMaster's perfectly-timed glove. Kinetik's
   final Phoenix strike sealed victory - a masterclass in timing!"
```

---

## 💰 Cost

**~5 cents per battle** with GPT-4

Want cheaper? Use GPT-3.5-Turbo:
```python
# Edit agents/gpt_strategic_agents.py
model="gpt-3.5-turbo"  # Change from "gpt-4"
```

**~0.5 cents per battle** with GPT-3.5

---

## 🔧 Code Examples

### Basic Usage
```python
from core.advanced_phase_system import AdvancedPhaseManager
from agents.gpt_strategic_agents import create_gpt_strategic_team

# Create phase manager
phase_manager = AdvancedPhaseManager(battle_duration=180)

# Create GPT team
agents, narrator = create_gpt_strategic_team(phase_manager)

# Check if working
print(f"GPT enabled: {narrator.enabled}")
```

### Pre-Battle Analysis
```python
if narrator.enabled:
    analysis = narrator.generate_pre_battle_analysis(agents, 180)
    print(f"💬 {analysis}")
```

### Phase Commentary
```python
commentary = narrator.comment_on_phase_transition(
    phase_name="Boost #1 - x3",
    multiplier=3.0,
    current_time=60,
    score_diff=500
)
print(f"💬 {commentary}")
```

### Post-Battle Summary
```python
summary = narrator.generate_battle_summary(
    winner="creator",
    final_scores={'creator': 250000, 'opponent': 150000},
    analytics={'boost2_triggered': True}
)
print(f"💬 {summary}")
```

---

## 🎯 Features

| Feature | Description | When Used |
|---------|-------------|-----------|
| Pre-Battle Analysis | Strategic predictions | Before battle |
| Phase Commentary | Real-time insights | Phase transitions |
| Agent Analysis | Action evaluation | Key agent moves |
| Learning Insights | Strategy adaptation | After glove attempts |
| Battle Summary | Complete overview | Post-battle |

---

## ⚠️ Troubleshooting

### No API Key
```bash
export OPENAI_API_KEY='your-key'
```

### Package Missing
```bash
pip install openai
```

### Rate Limits
Add delays between battles:
```python
import time
time.sleep(2)  # Wait 2 seconds
```

---

## 📖 Full Documentation

See **GPT_INTEGRATION.md** for:
- Complete API documentation
- Configuration options
- Cost optimization
- Advanced examples
- Security best practices

---

## 🚀 Next Steps

1. **Try it:** Run demo and see GPT commentary
2. **Customize:** Adjust prompts for your style
3. **Integrate:** Add to your own battles
4. **Optimize:** Switch models to reduce cost

---

**Need Help?**
- Full docs: `GPT_INTEGRATION.md`
- System docs: `STRATEGIC_BATTLE_SYSTEM.md`
- Code: `agents/gpt_strategic_agents.py`

**Happy battling with AI commentary!** 🤖✨
