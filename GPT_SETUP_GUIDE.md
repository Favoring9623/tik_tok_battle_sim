# GPT Intelligence Setup Guide

Get your AI agents thinking with GPT-4! 🧠

---

## Quick Start (5 minutes)

### Step 1: Install OpenAI Package

```bash
pip install openai
```

### Step 2: Get API Key

1. Go to [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Sign up or log in
3. Click "Create new secret key"
4. Copy the key (starts with `sk-...`)

### Step 3: Set Environment Variable

**Linux/Mac:**
```bash
export OPENAI_API_KEY='sk-your-key-here'
```

**Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY='sk-your-key-here'
```

**Or permanently (add to `.bashrc` or `.zshrc`):**
```bash
echo 'export OPENAI_API_KEY="sk-your-key-here"' >> ~/.bashrc
source ~/.bashrc
```

### Step 4: Run Demo!

```bash
python3 demo_gpt_battle.py
```

---

## What You Get

### 🧠 **Intelligent Decision-Making**

Agents analyze battle state and make strategic decisions:

```
Battle State Analysis:
- Time: 47s (LATE phase)
- Creator: 1,280 pts vs Opponent: 1,450 pts
- Losing by 170 points
- 13 seconds remaining

GPT Decision (NovaWhale):
"Not critical yet. Opponent lead is small and we have 13 seconds.
I'll wait until 50s to see if the gap widens. If still losing at 50s,
I'll deploy LION & UNIVERSE for maximum impact."

Action: WAIT
```

### 💬 **Contextual Messages**

Agents generate unique, in-character messages:

**Before (hardcoded):**
```python
messages = ["The tide has turned.", "Consider it done."]
random.choice(messages)
```

**After (GPT-generated):**
```
"The depths stir... patience rewards the vigilant."
(Generated based on: NovaWhale watching a close battle at 35s)
```

### 📖 **Epic Battle Lore**

Automatic narrative generation after each battle:

```
In the twilight hour of the digital colosseum, three champions
emerged from the shadows. PixelPixie, bearer of endless optimism,
scattered roses across the battlefield from the opening bell...

But it was NovaWhale, the silent leviathan, whose emergence at
the 52-second mark would turn legend into reality. With a single
devastating strike of 1,800 points, the titan reversed what seemed
an inevitable defeat, leaving opponents scattered in the wake of
the Universe's gift...
```

---

## Cost Estimates

### GPT-4 Pricing (as of 2024)

| Model | Input | Output | Typical Battle Cost |
|-------|-------|--------|-------------------|
| **GPT-4** | $0.03/1K tokens | $0.06/1K tokens | **$0.10 - $0.25** |
| **GPT-4 Turbo** | $0.01/1K tokens | $0.03/1K tokens | **$0.03 - $0.08** |
| **GPT-3.5 Turbo** | $0.0005/1K tokens | $0.0015/1K tokens | **$0.002 - $0.01** |

**Typical 60-second battle:**
- ~30-50 agent decisions
- ~500-1,500 tokens per decision
- Total: ~2,000-4,000 tokens
- **Cost: $0.10-0.25 per battle** (GPT-4)

### Budget-Friendly Options

**Use GPT-3.5-turbo for testing:**
```python
gpt_engine = GPTDecisionEngine(model="gpt-3.5-turbo")  # 10x cheaper!
```

**Mix models:**
```python
# GPT-4 for complex decisions
gpt_strategic = GPTDecisionEngine(model="gpt-4")

# GPT-3.5 for simple messages
gpt_messages = GPTDecisionEngine(model="gpt-3.5-turbo")
```

---

## Usage Examples

### Basic GPT Battle

```python
from core import BattleEngine
from agents.gpt_agent import GPTNovaWhale, GPTPixelPixie
from extensions.gpt_intelligence import GPTDecisionEngine

# Create GPT engine
gpt_engine = GPTDecisionEngine(model="gpt-4")

# Create GPT-powered agents
engine = BattleEngine()
engine.add_agent(GPTNovaWhale(gpt_engine=gpt_engine))
engine.add_agent(GPTPixelPixie(gpt_engine=gpt_engine))

# Run!
engine.run()
```

### Hybrid Mode (Mix GPT + Traditional)

```python
from agents.personas import GlitchMancer  # Traditional agent
from agents.gpt_agent import GPTNovaWhale  # GPT agent

engine = BattleEngine()
engine.add_agent(GPTNovaWhale())        # Uses GPT for decisions
engine.add_agent(GlitchMancer())        # Uses hardcoded logic

engine.run()
```

### Custom GPT Agent

```python
from agents.gpt_agent import GPTPoweredAgent

class CustomGPTAgent(GPTPoweredAgent):
    def __init__(self):
        personality = """You are a tactical genius who analyzes
        probability and makes calculated risks. You speak like
        a chess grandmaster commenting on the game."""

        super().__init__(
            name="TacticalMind",
            emoji="🎯",
            personality=personality
        )
```

### Battle Lore Generation

```python
from extensions.gpt_intelligence import GPTLoreGenerator

lore_gen = GPTLoreGenerator(model="gpt-4")

battle_data = {
    "winner": "creator",
    "creator_score": 2500,
    "opponent_score": 1800,
    "agents": ["NovaWhale", "PixelPixie"],
    "key_moments": [
        "[15s] Opponent massive spike!",
        "[52s] NovaWhale delivers crushing blow"
    ]
}

epic_story = lore_gen.generate_battle_summary(battle_data, style="epic")
print(epic_story)
```

---

## Troubleshooting

### "OPENAI_API_KEY not found"

**Solution:**
```bash
# Check if set:
echo $OPENAI_API_KEY

# If empty, set it:
export OPENAI_API_KEY='sk-your-key-here'
```

### "Module 'openai' not found"

**Solution:**
```bash
pip install openai
# or
pip install -r requirements.txt
```

### "Rate limit exceeded"

**Solution:**
```python
# Reduce agent decision frequency
gpt_engine = GPTDecisionEngine(model="gpt-3.5-turbo")  # Cheaper, higher limits
```

### "Invalid API key"

**Solution:**
1. Check key copied correctly (no extra spaces)
2. Verify key is active at https://platform.openai.com/api-keys
3. Check you have credits/billing set up

### Agents using fallback mode

The system gracefully degrades if GPT unavailable:

```python
# Check GPT availability
if gpt_engine.is_available():
    print("GPT active!")
else:
    print("Using fallback logic")

# View usage stats
stats = agent.get_gpt_stats()
print(f"GPT usage: {stats['gpt_percentage']}%")
```

---

## Advanced Configuration

### Model Selection

```python
# Fastest, cheapest
gpt = GPTDecisionEngine(model="gpt-3.5-turbo")

# Balanced
gpt = GPTDecisionEngine(model="gpt-4-turbo")

# Most intelligent (but expensive)
gpt = GPTDecisionEngine(model="gpt-4")
```

### Temperature Control

```python
# In extensions/gpt_intelligence.py, modify:

# More creative/unpredictable (default: 0.7)
temperature=0.9

# More consistent/deterministic
temperature=0.3
```

### Fallback Modes

```python
agent = GPTPoweredAgent(
    name="TestAgent",
    personality="...",
    fallback_mode="conservative"  # Options: "random", "conservative", "skip"
)
```

---

## Testing Without GPT

You can test the system without an API key:

```bash
# GPT demo will run in fallback mode
python3 demo_gpt_battle.py

# Shows what would happen with GPT, but uses simple logic instead
```

---

## Next Steps

Once GPT is working:

1. **Experiment with personalities** - Edit agent personalities in `agents/gpt_agent.py`
2. **Try different models** - Test GPT-4 vs GPT-3.5-turbo
3. **Monitor costs** - Check usage at https://platform.openai.com/usage
4. **Create custom agents** - Build your own GPT-powered personas
5. **Generate lore** - Use GPTLoreGenerator for battle narratives

---

## FAQ

**Q: Do I need GPT to use the simulator?**
A: No! Traditional agents work perfectly. GPT is optional for enhanced intelligence.

**Q: How much will this cost?**
A: ~$0.10-0.25 per battle with GPT-4, or $0.002-0.01 with GPT-3.5-turbo.

**Q: Can I use my own OpenAI organization?**
A: Yes, pass `organization="org-xxx"` to GPTDecisionEngine.

**Q: Will agents remember between battles?**
A: Currently no (stateless), but you can implement this with the memory system.

**Q: Can I use local LLMs instead of OpenAI?**
A: Yes! Modify `extensions/gpt_intelligence.py` to use Ollama, LM Studio, etc.

---

## Support

- OpenAI API Docs: https://platform.openai.com/docs
- OpenAI Pricing: https://openai.com/pricing
- API Status: https://status.openai.com

**Ready to give your agents intelligence? Run the demo!**

```bash
python3 demo_gpt_battle.py
```
