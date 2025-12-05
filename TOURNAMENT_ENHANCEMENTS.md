# Tournament System Enhancements

## Overview

Enhanced tournament system with bracket visualization, momentum tracking, and leaderboards.

## New Features

### 1. Tournament Bracket Visualization (`core/tournament_bracket.py`)

**Features:**
- ASCII art tournament brackets
- Series progress tracking (⭐ wins display)
- Battle-by-battle results
- Completed/upcoming battle indicators
- Compact bracket views

**Usage:**
```python
from core.tournament_bracket import TournamentBracket, BracketVisualizer

bracket = TournamentBracket(format_name="BEST_OF_3", battles_to_win=2)

# After each battle
bracket.add_battle_result(
    battle_num=1,
    creator_score=10500,
    opponent_score=8200,
    winner="creator"
)

# Display bracket
bracket.print_bracket()
```

**Output Example:**
```
======================================================================
🏆 BEST_OF_3 TOURNAMENT BRACKET
======================================================================

           CREATOR           vs           OPPONENT
───────────────────────────────────    ───────────────────────────────────
       2 WINS ⭐⭐☆               1 WINS ⭐☆☆

                    (First to 2 wins)

BATTLES:
──────────────────────────────────────────────────────────────────────
  Battle 1:  ✅ Creator 10,500  │  Opponent  8,200 ❌
  Battle 2:  ❌ Creator  7,800  │  Opponent  9,300 ✅
  Battle 3:  ✅ Creator 12,400  │  Opponent 10,100 ❌
======================================================================
```

**Additional Visualizations:**
- `BracketVisualizer.print_series_progress_bar()` - Progress bars
- `BracketVisualizer.print_battle_timeline()` - Horizontal timeline with 🔵/🔴 markers
- `BracketVisualizer.print_score_comparison()` - Bar chart comparison

---

### 2. Series Momentum Tracking (`core/tournament_momentum.py`)

**Features:**
- Real-time momentum state (Strong/Moderate/Neutral)
- Pressure level tracking (None/Low/Moderate/High/Elimination)
- Win streak detection
- Comeback opportunity alerts
- Momentum event detection:
  - Win streaks (2+ consecutive wins)
  - Dominations (>30% margin)
  - Close calls (<10% margin)
  - Clutch wins (winning while facing elimination)

**Usage:**
```python
from core.tournament_momentum import MomentumTracker

momentum = MomentumTracker(battles_to_win=2)

# After each battle
momentum.record_battle(
    battle_num=1,
    winner="creator",
    creator_score=10500,
    opponent_score=8200
)

# Display momentum report
momentum.print_momentum_report()
```

**Output Example:**
```
======================================================================
📊 SERIES MOMENTUM REPORT
======================================================================

Momentum: 🔵🔵 Favoring Creator
Pressure: Creator 😌 None | Opponent 😰 High

🔥 Creator is on a 2-battle win streak!

📰 Key Moments:
   Battle 1: Creator dominated with 24.4% margin!
   Battle 2: Nail-biter! Creator won by only 800 points
======================================================================
```

**Momentum States:**
- `STRONG_CREATOR` (🔵🔵🔵)
- `MODERATE_CREATOR` (🔵🔵)
- `NEUTRAL` (⚪)
- `MODERATE_OPPONENT` (🔴🔴)
- `STRONG_OPPONENT` (🔴🔴🔴)

**Pressure Levels:**
- `ELIMINATION` (💀) - Must win or lose series
- `HIGH` (😰) - One loss away from elimination
- `MODERATE` (😐) - Behind in series
- `LOW` (🙂) - Tied series
- `NONE` (😌) - Leading series

---

### 3. Tournament Leaderboard System (`core/tournament_leaderboard.py`)

**Features:**
- ELO rating system (starts at 1500)
- Persistent tournament history
- Win/loss records (tournaments and individual battles)
- Win streak tracking
- MVP tracking
- JSON save/load
- Comprehensive statistics

**Usage:**
```python
from core.tournament_leaderboard import TournamentLeaderboard

leaderboard = TournamentLeaderboard(save_file="tournament_leaderboard.json")

# After tournament completes
tournament_stats = tournament.get_tournament_stats()
leaderboard.record_tournament(tournament_stats)

# Display leaderboard
leaderboard.print_leaderboard()
```

**Output Example:**
```
================================================================================
🏆 TOURNAMENT LEADERBOARD
================================================================================

📊 ELO RATINGS:
   Creator:  1532  (High: 1548, Low: 1500)
   Opponent: 1468  (High: 1500, Low: 1452)

🏆 TOURNAMENT RECORD:
   Creator : 3W - 2L (60.0%) | Avg Score: 28,450
   Opponent: 2W - 3L (40.0%) | Avg Score: 24,320

⚔️ BATTLE RECORD:
   Creator:  8W - 6L (57.1%)
   Opponent: 6W - 8L (42.9%)

🔥 WIN STREAKS:
   Creator: 2 current (Longest: 3)

📋 RECENT TOURNAMENTS:
   T0005 [2025-01-15 14:23] ✅ BEST_OF_3 - 2-1 (MVP: NovaWhale)
   T0004 [2025-01-15 14:10] ❌ BEST_OF_3 - 1-2 (MVP: GlitchMancer)
   T0003 [2025-01-15 13:55] ✅ BEST_OF_3 - 2-0 (MVP: PixelPixie)
================================================================================
```

**Tracked Statistics:**
- Tournament record (W-L, win %)
- Battle record (W-L, win %)
- Total points scored/spent
- Current win streak / longest streak
- ELO rating + high/low
- Complete tournament history
- MVP per tournament

**ELO System:**
- K-factor: 32
- Starting rating: 1500
- Updates after each tournament
- Tracks rating highs/lows

---

## Enhanced Demo

**File:** `demo_tournament_enhanced_full.py`

Showcases all features:
- Bracket visualization
- Momentum tracking
- Leaderboard with ELO ratings
- Best of 3 format
- Multiple tournament support

**Run:**
```bash
python3 demo_tournament_enhanced_full.py
```

**Features:**
1. Interactive - choose how many tournaments to run (1-5)
2. Shows bracket after each battle
3. Displays momentum shifts
4. Updates leaderboard with ELO ratings
5. Saves progress to `tournament_leaderboard.json`
6. Run multiple times to build tournament history!

**Example Flow:**
```
1. Load existing leaderboard (if any)
2. Show current standings
3. Run tournament(s)
   - Display pre-battle status
   - Show live bracket updates
   - Track momentum shifts
   - Record in leaderboard
4. Final visualizations:
   - Complete bracket
   - Progress bars
   - Battle timeline
   - Score comparison
   - Final momentum report
5. Updated leaderboard with new ELO ratings
6. Session summary
```

---

## Integration with Existing System

All new features integrate seamlessly with the existing `TournamentManager`:

```python
from core.battle_engine import BattleEngine
from core.tournament_system import TournamentManager, TournamentFormat
from core.tournament_bracket import TournamentBracket
from core.tournament_momentum import MomentumTracker
from core.tournament_leaderboard import TournamentLeaderboard

# Initialize all systems
tournament = TournamentManager(format=TournamentFormat.BEST_OF_3)
bracket = TournamentBracket(format_name="BEST_OF_3", battles_to_win=2)
momentum = MomentumTracker(battles_to_win=2)
leaderboard = TournamentLeaderboard()

# Run battles
while tournament.can_continue():
    # ... run battle ...

    # Record in all systems
    tournament.record_battle_result(...)
    bracket.add_battle_result(...)
    momentum.record_battle(...)

# After tournament
leaderboard.record_tournament(tournament.get_tournament_stats())
```

---

## Files Created

1. **`core/tournament_bracket.py`** - Bracket visualization
2. **`core/tournament_momentum.py`** - Momentum tracking
3. **`core/tournament_leaderboard.py`** - Leaderboard system
4. **`demo_tournament_enhanced_full.py`** - Complete demo

---

## Future Enhancements (Pending)

### Web Dashboard Tournament Support
- Real-time tournament streaming
- Live bracket display
- Momentum visualization
- Leaderboard web view

### Advanced Formats
- Single/double elimination brackets
- Round-robin tournaments
- Swiss system
- Custom tournament structures

---

## Summary

✅ **Tournament Bracket Visualization** - ASCII art brackets with progress tracking
✅ **Series Momentum Tracking** - Real-time psychological momentum and pressure
✅ **Tournament Leaderboard** - ELO ratings with persistent history
✅ **Enhanced Demo** - Showcases all features with multiple tournament support

All features are production-ready and integrate with the existing tournament system!
