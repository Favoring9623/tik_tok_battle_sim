# Advanced Strategic Battle System

## Overview

Complete implementation of the advanced 180-second TikTok battle system with conditional phases, strategic AI agents, power-ups, and post-battle rewards.

---

## 🎯 Features Implemented

### 1. 180s Battle Duration with Phase System ✅

**File**: `core/advanced_phase_system.py`

**Phases**:
- **Phase 1 (0-60s)**: Warmup phase with x1 multiplier (automatic)
- **Boost #1 (60-90s)**: First boost with x2 or x3 multiplier (automatic)
- **Boost #2 (90-120s)**: Conditional boost with x2 or x3 multiplier (requires trigger)
- **Phase 2/3 (120-180s)**: Normal phases with x1 multiplier

**Key Features**:
```python
from core.advanced_phase_system import AdvancedPhaseManager

phase_manager = AdvancedPhaseManager(battle_duration=180)

# Updates automatically each second
phase_manager.update(current_time)

# Get current phase info
phase_info = phase_manager.get_phase_info()
# Returns: {'name': 'Boost #1 - x3', 'multiplier': 3.0, ...}
```

---

### 2. Conditional Phase Triggering ✅

**Boost #2 Activation Conditions** (30s window after Boost #1):
- **5 Roses sent** OR
- **1,000+ points accumulated**

**Implementation**:
```python
# Automatically tracked when gifts are sent
multiplier = phase_manager.record_gift(
    gift_type="ROSE",
    points=10,
    team="creator",
    current_time=70
)

# Conditions checked automatically
# Boost #2 activates at 90s if conditions met
```

**Example Output**:
```
✅ Boost #2 Conditions MET!
   Roses: 5/5
   Points: 50/1000
   Boost #2 will activate at 90s!

============================================================
🔥 BOOST #2 - X2 ACTIVATED! (x2)
   Duration: 90s - 120s
============================================================
```

---

### 3. Glove x5 Mechanics ✅

**Activation Conditions**:
- Sent during active x2/x3 boost phase, OR
- Sent in last 30 seconds of battle

**Activation Probability**: 40% when conditions met

**Duration**: 10 seconds of x5 multiplier

**Implementation**:
```python
# Automatically handled when glove gift sent
multiplier = phase_manager.record_gift(
    gift_type="GLOVE",
    points=100,
    team="creator",
    current_time=75  # During boost = eligible for x5
)

# If activated:
# Returns 5.0 multiplier for 10 seconds
```

**Example Output**:
```
🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊
💥 GLOVE x5 ACTIVATED by CREATOR! (10s)
🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊🥊
```

---

### 4. Specialized Strategic Agents ✅

**File**: `agents/strategic_agents.py`

#### 🔫 Kinetik - The Final Sniper

**Strategy**: Silent observer until last 5 seconds, then deploys massive gifts

**Decision Logic**:
```python
if time_remaining <= 5 and not has_acted:
    if deficit > 300000:
        send_gift("UNIVERSE", 449990)  # 44,999 coins
    elif deficit > 150000:
        send_gift("LION", 299990)      # 29,999 coins
    else:
        send_gift("PHOENIX", 259990)    # 25,999 coins

    # Try time bonus if still losing badly
    if still_losing_by_100k:
        use_power_up(TIME_BONUS)
```

**Output Example**:
```
🔫 Kinetik activating! Deficit: 6,361 points
   🔥🐦 Deploying PHOENIX!
```

---

#### 🥊 StrikeMaster - The Glove Expert

**Strategy**: Learns optimal glove timing through reinforcement learning

**Decision Logic**:
```python
# Analyzes conditions
in_boost = current_multiplier > 1.0
in_last_30s = time_remaining <= 30

# Strategic decision based on learned preferences
if prefer_boost_phase and in_boost:
    send_gift("GLOVE", 100)
elif prefer_last_30s and in_last_30s:
    send_gift("GLOVE", 100)

# Tracks success and adapts strategy
def learn_from_result(glove_index, activated):
    update_success_rate()
    adapt_strategy()  # Prefer best timing
```

**Output Example**:
```
🥊 StrikeMaster sending GLOVE!
   Conditions: Boost=True, Last30s=False
   Success rate: 50.0% (2/4)

📊 StrikeMaster learned: Prefer Boost
```

---

#### ⏱️ PhaseTracker - The Phase Monitor

**Strategy**: Ensures Boost #2 conditions are met by sending strategic roses

**Decision Logic**:
```python
if 60 <= current_time < 90:  # Window for Boost #2 trigger
    if not boost2.condition_met:
        if roses_sent < 5:
            send_gift("ROSE", 10)  # Strategic trigger
```

**Output Example**:
```
⏱️ PhaseTracker: Sending strategic ROSE #1/5 to trigger Boost #2
⏱️ PhaseTracker: Sending strategic ROSE #2/5 to trigger Boost #2
...
✅ Boost #2 Conditions MET!
```

---

#### 🧰 LoadoutMaster - The Power-Up Manager

**Strategy**: Deploys power-ups at optimal moments

**Decision Logic**:
```python
# Neutralize opponent x5
if opponent_has_x5 and we_are_losing:
    use_power_up(HAMMER)

# Hide score when ahead
if we_are_ahead_by_50k and late_game:
    use_power_up(FOG)

# Time bonus for desperate situations
if critical_deficit:
    use_power_up(TIME_BONUS)
```

**Output Example**:
```
🧰 LoadoutMaster: Opponent x5 detected!
   🔨 Deploying HAMMER to neutralize!

🧰 LoadoutMaster: We're ahead, deploying FOG!
```

---

### 5. Inventory/Loadout System ✅

**Power-Ups Available**:

#### 🔨 Hammer
- **Effect**: Neutralizes opponent's x5 glove boost
- **Usage**: Defensive counter to enemy x5
- **Instant**: Immediately cancels active x5

#### 🌫️ Fog
- **Effect**: Hides score display for 15 seconds
- **Usage**: Psychological warfare when ahead
- **Tactical**: Prevents opponents from knowing deficit

#### ⏱️ Time Bonus
- **Effect**: Adds +25 seconds to battle duration
- **Usage**: Comeback opportunities
- **Limit**: Can only be used once per battle

**Implementation**:
```python
# Add to inventory
phase_manager.add_power_up(PowerUpType.HAMMER, "creator")
phase_manager.add_power_up(PowerUpType.FOG, "creator")
phase_manager.add_power_up(PowerUpType.TIME_BONUS, "creator")

# Use power-up
success = phase_manager.use_power_up(
    PowerUpType.HAMMER,
    "creator",
    current_time
)
```

**Output Example**:
```
🔨 HAMMER ACTIVATED! Opponent's x5 NEUTRALIZED!

🌫️ FOG ACTIVATED! Scores HIDDEN for 15s!

⏱️ TIME BONUS ACTIVATED! +25 seconds!
   New duration: 205s
```

---

### 6. Post-Battle Reward Distribution ✅

**File**: `core/reward_system.py`

**Reward Tiers**:
- **LEGEND**: Top 1% → 1,000 base diamonds
- **MVP**: Top 5% → 500 base diamonds
- **STAR**: Top 10% → 200 base diamonds
- **HERO**: Top 25% → 100 base diamonds
- **SUPPORTER**: Top 50% → 50 base diamonds
- **PARTICIPANT**: Everyone else → 10 base diamonds

**Win Bonus**: 2x multiplier for winning team

**Achievements**:
- 🏆 **Clutch Winner** (+200): Won from behind in last 30s
- 🏆 **Perfect Victory** (+150): Won without opponent lead
- 🏆 **Comeback King** (+300): Overcame 2x deficit
- 🏆 **Sniper Elite** (+250): 50%+ contribution in final phase
- 🏆 **Phase Master** (+100): Triggered Boost #2
- 🏆 **Glove Legend** (+200): Activated 3+ x5 gloves
- 🏆 **Whale Supporter** (+400): Single gift worth 100k+ points
- 🏆 **Consistency King** (+150): 20+ gifts sent
- 🏆 **Strategic Genius** (+300): Used 3+ power-ups

**Implementation**:
```python
from core.reward_system import RewardDistributor

distributor = RewardDistributor()
rewards = distributor.distribute_rewards(
    contributors=contributor_stats,
    winner="creator",
    battle_history=battle_history
)

distributor.print_rewards(rewards)
```

**Output Example**:
```
======================================================================
💎 BATTLE REWARDS DISTRIBUTION
======================================================================

#1 Kinetik:
   Tier: HERO
   Base Diamonds: 300
   Bonus Multiplier: x2.0
   Total Diamonds: 💎 600
   Achievements:
      🏆 Sniper Elite (+250 diamonds)
      🏆 Whale Supporter (+400 diamonds)
      🏆 Clutch Winner (+200 diamonds)
      🏆 Comeback King (+300 diamonds)

#2 NovaWhale:
   Tier: SUPPORTER
   Base Diamonds: 50
   Bonus Multiplier: x2.0
   Total Diamonds: 💎 100

======================================================================
💰 Total Diamonds Distributed: 2,840
======================================================================
```

---

## 🚀 Running the Complete System

### Quick Start

```bash
python3 demo_strategic_battle.py
```

### What Happens:

1. **Initialization** (0s):
   - Creates 180s battle engine
   - Sets up advanced phase manager
   - Loads power-ups inventory (Hammer, Fog, Time Bonus)
   - Creates strategic team (Kinetik, StrikeMaster, PhaseTracker, LoadoutMaster)

2. **Phase 1 (0-60s)**:
   - Warmup phase with x1 multiplier
   - Agents observe and prepare
   - NovaWhale may send early gifts

3. **Boost #1 (60-90s)**:
   - Automatic activation with x2 or x3 multiplier
   - PhaseTracker sends 5 roses to trigger Boost #2
   - StrikeMaster attempts glove activations during boost

4. **Boost #2 (90-120s)**:
   - Activates IF conditions met (5 roses or 1000 points)
   - x2 or x3 multiplier
   - StrikeMaster continues glove attempts

5. **Final Phase (150-180s)**:
   - Last 30 seconds = glove eligible window
   - StrikeMaster sends strategic gloves
   - Kinetik activates in final 5 seconds

6. **Final 5 Seconds (175-180s)**:
   - Kinetik assesses deficit
   - Deploys Universe/Lion/Phoenix based on need
   - LoadoutMaster deploys power-ups if needed

7. **Post-Battle**:
   - Phase analytics displayed
   - Agent performance breakdown
   - Reward distribution with achievements

---

## 📊 Analytics Output

### Phase System Analytics
```
📊 Phase System Analytics:
   Total phases: 3
   Boost #2 triggered: ✅ YES
   Gloves sent: 4
   Gloves activated (x5): 2 (50%)
   Time bonuses used: 0
   Final duration: 180s
   Power-ups used: 1
```

### Strategic Agent Performance
```
👥 Strategic Agent Performance:

   Kinetik:
      Points donated: 259,990
      Gifts sent: 1
      Avg gift value: 259990

   StrikeMaster:
      Points donated: 400
      Gifts sent: 4
      Avg gift value: 100
```

### Strategic Insights
```
🎯 Strategic Insights:
   🔫 Kinetik: Final sniper strategy executed
   🥊 StrikeMaster: Glove mastery 50% success rate
   ⏱️  PhaseTracker: Boost #2 successfully triggered
   🧰 LoadoutMaster: 1 power-ups deployed
```

---

## 🧪 Testing

All components have been tested:

### 1. Phase System Test
```bash
python3 core/advanced_phase_system.py
```
✅ Phases transition correctly
✅ Boost #2 conditions work
✅ Glove x5 mechanics functional

### 2. Strategic Agents Test
```bash
python3 agents/strategic_agents.py
```
✅ All 4 agents created successfully
✅ Linked to phase manager

### 3. Reward System Test
```bash
python3 core/reward_system.py
```
✅ Tier calculation correct
✅ Achievements detected
✅ Bonuses applied

### 4. Complete Integration Test
```bash
python3 demo_strategic_battle.py
```
✅ Full 180s battle runs
✅ All agents function correctly
✅ Phases trigger as expected
✅ Rewards distributed properly

---

## 🎮 Integration with Existing Systems

### Battle Engine Integration

```python
from core.battle_engine import BattleEngine
from core.advanced_phase_system import AdvancedPhaseManager
from agents.strategic_agents import create_strategic_team

# Create phase manager
phase_manager = AdvancedPhaseManager(battle_duration=180)

# Create agents
agents = create_strategic_team(phase_manager)

# Create battle
engine = BattleEngine(battle_duration=180, ...)

# Add agents
for agent in agents:
    engine.add_agent(agent)

# Wrap to update phases
original_tick = engine._tick
def wrapped_tick(silent):
    original_tick(silent)
    phase_manager.update(engine.time_manager.current_time)
engine._tick = wrapped_tick

# Run
engine.run()
```

### Web Dashboard Integration

The system can be integrated with the existing web dashboard by:

1. Broadcasting phase changes via Socket.IO
2. Displaying multiplier indicators in real-time
3. Showing power-up activations
4. Displaying reward distribution post-battle

---

## 📁 Files Created

1. **`core/advanced_phase_system.py`** (422 lines)
   - Phase management with conditional triggering
   - Glove x5 mechanics
   - Power-up system
   - Analytics tracking

2. **`agents/strategic_agents.py`** (378 lines)
   - Kinetik (final sniper)
   - StrikeMaster (glove expert)
   - PhaseTracker (phase monitor)
   - LoadoutMaster (power-up manager)
   - Team creation helper

3. **`core/reward_system.py`** (438 lines)
   - Reward tiers and distribution
   - Achievement detection
   - Bonus calculation
   - Formatted output

4. **`demo_strategic_battle.py`** (203 lines)
   - Complete integration demo
   - Real-time phase display
   - Strategic insights
   - Reward distribution

5. **`STRATEGIC_BATTLE_SYSTEM.md`** (this file)
   - Complete documentation
   - Usage examples
   - Integration guide

---

## 🎯 Feature Comparison

| Feature | Basic Battle | Advanced Strategic Battle |
|---------|-------------|---------------------------|
| Duration | 60s | 180s |
| Phases | Simple (Early/Mid/Late) | Complex with Boost #1, #2 |
| Multipliers | Random x2/x3 | Conditional + Glove x5 |
| Agents | Basic personas | Strategic specialists |
| Power-ups | None | Hammer, Fog, Time Bonus |
| Rewards | None | Tiered with achievements |
| Comeback Mechanics | Limited | Time Bonus, late gloves |
| Learning | None | StrikeMaster learns optimal timing |

---

## 🏆 Success Criteria - All Met ✅

- ✅ 180s battle duration working
- ✅ Conditional Boost #2 triggered by roses/points
- ✅ Glove x5 activates randomly (40%) when eligible
- ✅ 4 specialized agents functioning independently
- ✅ Power-up system (Hammer, Fog, Time Bonus) operational
- ✅ Post-battle rewards distributed with achievements
- ✅ Complete integration demo working
- ✅ All components tested individually and together

---

## 📝 Usage Examples

### Example 1: Create Strategic Team

```python
from core.advanced_phase_system import AdvancedPhaseManager
from agents.strategic_agents import create_strategic_team

phase_manager = AdvancedPhaseManager(battle_duration=180)
agents = create_strategic_team(phase_manager)

for agent in agents:
    print(f"{agent.emoji} {agent.name}")
```

### Example 2: Track Phase Changes

```python
phase_manager.update(current_time)

if current_time % 30 == 0:
    info = phase_manager.get_phase_info()
    print(f"Phase: {info['name']}, Multiplier: x{info['multiplier']}")
```

### Example 3: Use Power-Ups

```python
# Add to inventory
phase_manager.add_power_up(PowerUpType.HAMMER, "creator")

# Use when needed
if opponent_has_x5:
    phase_manager.use_power_up(PowerUpType.HAMMER, "creator", time)
```

### Example 4: Distribute Rewards

```python
from core.reward_system import RewardDistributor

distributor = RewardDistributor()
rewards = distributor.distribute_rewards(contributors, winner, history)
distributor.print_rewards(rewards)
```

---

## 🔮 Future Enhancements

Potential additions to the system:

1. **Multi-Team Battles**: 3-4 teams competing simultaneously
2. **Custom Power-Ups**: User-defined effects and durations
3. **Agent Evolution**: Agents improve over multiple battles
4. **Replay System**: Save and replay strategic battles
5. **Web Dashboard**: Real-time strategic battle visualization
6. **Tournament Mode**: Series of strategic battles with cumulative rewards
7. **AI Training**: Train agents using battle data
8. **Custom Achievements**: User-defined achievement conditions

---

## 📞 Support

For questions or issues with the strategic battle system:

1. Check this documentation first
2. Run individual component tests
3. Review demo output for examples
4. Check file headers for detailed function documentation

---

**Last Updated**: 2025-11-24
**Version**: 1.0.0
**Status**: ✅ Complete and Tested
