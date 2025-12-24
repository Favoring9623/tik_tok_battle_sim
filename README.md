# TikTok Battle Simulator

A simulation framework for TikTok-style live battles featuring AI agents with strategic behaviors, GPT-powered personas, tournament systems, and real-time web dashboards.

## Features

- **Battle Engine** - Event-driven simulation with phases, multipliers, and power-ups
- **AI Agents** - Multiple agent types including strategic specialists and GPT-powered personas
- **Tournament System** - 8-team brackets with elimination rounds and momentum tracking
- **Web Dashboard** - Real-time battle visualization with Socket.IO
- **Gift System** - TikTok-accurate gift catalog with pricing and effects

## Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/Favoring9623/tik_tok_battle_sim.git
cd tik_tok_battle_sim

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Run a Demo Battle

```bash
python demo_battle.py
```

### Run with Web Dashboard

```bash
# Terminal 1: Start web server
python -c "from web.backend.app import run_server; run_server()"

# Terminal 2: Run battle with streaming
python demo_strategic_battle.py --stream
```

Open http://localhost:5000 in your browser.

### Run a Tournament

```bash
python demo_tournament.py --bracket
```

## Project Structure

```
tik_tok_battle_sim/
├── core/                       # Battle engine, scoring, phases
│   ├── battle_engine.py        # Core battle simulation
│   ├── battle_platform.py      # NEW: Unified integration platform
│   ├── ai_battle_controller.py # NEW: AI decision engine
│   ├── gift_sender.py          # Gift automation system
│   ├── score_tracker.py
│   ├── gift_catalog.py
│   └── multiplier_system.py
├── agents/                     # AI agent implementations
│   ├── base_agent.py
│   ├── personas/               # Character-based agents
│   ├── specialists/            # Strategy-focused agents
│   └── gpt_agent.py            # GPT-powered agents
├── tournament/                 # Tournament and bracket system
├── web/                        # Web dashboard
│   ├── backend/app.py          # Flask + Socket.IO server
│   └── frontend/public/        # HTML dashboards
│       ├── index.html          # Main dashboard
│       ├── control-center.html # NEW: Unified control center
│       ├── gift-sender.html    # Gift sending interface
│       ├── ai-battle.html      # AI battle monitor
│       └── ...                 # Other dashboards
├── tests/                      # Test suite
├── data/                       # Session data and databases
│   └── tiktok_session/         # Browser session storage
└── docs/                       # Documentation
    ├── setup/                  # Setup guides
    ├── features/               # Feature documentation
    └── analysis/               # Analysis and findings
```

## Agent Types

### Specialist Agents
| Agent | Strategy |
|-------|----------|
| Strike Master | Precision timing for maximum impact |
| Sentinel | Defensive focus, counters opponent moves |
| Activator | Triggers boost conditions strategically |
| Budget Optimizer | Maximizes points per coin spent |
| Synergy Coordinator | Coordinates with other agents |

### Persona Agents
| Agent | Personality |
|-------|-------------|
| NovaWhale | Strategic whale, drops massive gifts at critical moments |
| PixelPixie | Budget cheerleader, frequent small gifts |
| GlitchMancer | Chaotic wildcard, unpredictable bursts |
| ShadowPatron | Silent observer until crisis strikes |

### GPT-Powered Agents
Agents with dynamic decision-making powered by OpenAI GPT. Configure via `.env`:
```
OPENAI_API_KEY=your-key-here
```

## AI Battle Controller

**NEW** - Intelligent battle assistant that reads live TikTok battle scores and makes real-time decisions.

### Features

- **Real-time Score Reading** - Detects battle bar scores directly from TikTok page
- **Multiple AI Strategies** - Choose from 5 battle strategies
- **Automatic Gift Sending** - Triggers gifts based on battle state
- **Emergency Response** - Detects losing situations and responds intelligently

### AI Strategies

| Strategy | Description |
|----------|-------------|
| **Smart** | Adaptive - adjusts based on score gap and time remaining |
| **Aggressive** | High-intensity gift bombardment to build lead |
| **Defensive** | Conservative play, counter-punches when opponent surges |
| **Sniper** | Waits for critical moments, strikes precisely |
| **Conservative** | Minimal intervention, only acts in emergencies |

### Usage

```bash
# Run AI Battle Controller
python run_ai_battle.py @username --strategy smart

# Available options
--strategy [smart|aggressive|defensive|sniper|conservative]
--demo      # Demo mode (no actual gift sending)
--budget N  # Set coin budget
```

### Battle States

The AI recognizes these battle states:
- `NO_BATTLE` - Stream is live but no battle active
- `ACTIVE` - Battle in progress
- `ENDING` - Final 30 seconds (critical phase)
- `FINAL` - Last 10 seconds (all-in phase)
- `FINISHED` - Battle ended

## Web Dashboard

Dashboard views available:

- **/** - Main battle dashboard
- **/control-center** - **NEW** Unified AI Battle Control Center
- **/strategic-battle** - Strategic battle with phases and boosts
- **/tournament** - 8-team bracket tournament view
- **/live** - Real TikTok Live battle dashboard (connect to actual streams)
- **/analytics** - Advanced analytics with charts and statistics
- **/replay** - Battle replay system with playback controls
- **/leaderboard** - Top agents and gifters rankings
- **/obs/setup** - OBS streaming overlay configuration
- **/audience** - Audience participation page (voting, power-ups)
- **/host** - Host controls for managing audience
- **/gift-sender** - Manual gift sending interface
- **/ai-battle** - AI Battle monitoring view

## Audience Interaction

Let viewers participate in battles:

| Page | Purpose |
|------|---------|
| `/audience` | Mobile-friendly page for viewers to vote and trigger power-ups |
| `/host` | Host dashboard to manage votes, view stats, control power-ups |

**Features:**
- **Voting** - Viewers predict the winner (Creator vs Opponent)
- **Power-ups** - Trigger Score Boost, Freeze, Double Points, Random Effect
- **Real-time Results** - Vote bar updates live via WebSocket
- **Activity Feed** - See votes and power-ups as they happen
- **Cooldowns** - Prevent power-up spam (30 second cooldown)

**API Endpoints:**
- `GET /api/audience/votes` - Get current vote counts
- `POST /api/audience/reset` - Reset all votes

## Leaderboard System

Track top performers across all battles:

| Tab | Description |
|-----|-------------|
| AI Agents | Rankings by total points, wins, battles, avg points |
| Top Gifters | Rankings by coins spent, gifts sent, battles participated |

**Features:**
- **Podium Display** - Top 3 shown with medals
- **Multiple Sort Options** - Sort by different metrics
- **Real-time Updates** - Auto-refreshes after battles
- **Agent Stats** - Wins, points, gifts, efficiency tracking
- **Gifter Stats** - Coins, gifts, favorite gift tracking

**API Endpoints:**
- `GET /api/leaderboard/agents` - Top agents (supports `?sort=` and `?limit=`)
- `GET /api/leaderboard/gifters` - Top gifters (supports `?sort=` and `?limit=`)
- `GET /api/leaderboard/summary` - Overall statistics
- `GET /api/leaderboard/agent/<name>` - Individual agent rank and stats
- `GET /api/leaderboard/gifter/<username>` - Individual gifter rank and stats

## Control Center

Unified dashboard for all battle operations at `/control-center`:

| Feature | Description |
|---------|-------------|
| **Live Score Display** | Real-time battle scores with visual gap indicator |
| **Strategy Selector** | Switch AI strategies mid-battle |
| **Mode Configuration** | Observer, Supporter, Manual, or Hybrid modes |
| **Decision Feed** | Live stream of AI decisions and reasoning |
| **Statistics Panel** | Gifts sent, decisions made, win/loss tracking |
| **Quick Actions** | Pause/resume, emergency modes, strategy switching |

### Battle Platform Modes

| Mode | Description |
|------|-------------|
| **Observer** | Watch and analyze only, no intervention |
| **Supporter** | AI-controlled gift sending based on strategy |
| **Manual** | Full manual control via dashboard |
| **Hybrid** | AI suggestions with manual override capability |

**API Endpoints:**
- `GET /api/battle-platform/status` - Current platform state and statistics
- `WS start_battle_platform` - Start platform with username and config
- `WS stop_battle_platform` - Stop platform gracefully
- `WS platform_set_strategy` - Change AI strategy in real-time
- `WS platform_pause` / `platform_resume` - Pause/resume operations

## OBS Streaming Integration

Stream your battles with professional overlays:

| Overlay | URL | Description |
|---------|-----|-------------|
| Full Overlay | `/obs/overlay` | Complete battle UI with scores, timer, gifts |
| Score Widget | `/obs/scores` | Minimal score display for corners |
| Gift Alerts | `/obs/alerts` | Animated gift notifications |
| Setup Guide | `/obs/setup` | Interactive configuration tool |

**Quick Setup:**
1. Open `/obs/setup` in your browser
2. Choose overlay type and customize options
3. Copy the generated URL
4. Add as Browser Source in OBS (1920x1080 for full overlay)
5. Enable transparency - overlays have transparent backgrounds

**URL Parameters:**
- `?position=top` - Move overlay to top
- `?hideGifts=true` - Hide gift feed
- `?hideTimer=true` - Hide timer
- `?compact=true` - Compact score widget
- `?minPoints=1000` - Filter small gift alerts

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

Environment variables:
- `OPENAI_API_KEY` - For GPT-powered agents
- `SECRET_KEY` - Flask session secret
- `FLASK_DEBUG` - Enable debug mode (true/false)

## Running Tests

```bash
python -m pytest tests/ -v
```

## Docker Deployment

```bash
# Build and run
docker-compose up --build

# Or just build
docker build -t tiktok-battle-sim .
docker run -p 5000:5000 tiktok-battle-sim
```

## Documentation

See `docs/` directory:
- `docs/setup/` - Installation and GPT setup guides
- `docs/features/` - Feature documentation
- `docs/analysis/` - Battle analytics and findings

## Roadmap

### Completed
- [x] Core battle engine with phases, multipliers, power-ups
- [x] AI agents (specialists + GPT-powered personas)
- [x] Tournament system with 8-team brackets
- [x] Real-time web dashboard with Socket.IO
- [x] Mobile-responsive UI
- [x] Docker containerization
- [x] GitHub Actions CI pipeline
- [x] Test suite (62 tests)
- [x] SQLite database for battle history
- [x] User authentication system
- [x] **Sound effects and audio feedback** *(Dec 2025)*
- [x] **Strategic Intelligence** - Surrender logic, aggressive/defensive modes *(Dec 2025)*
- [x] **Snipe Mode** - Final seconds tactical execution for Creator team *(Dec 2025)*
- [x] **Live TikTok Integration** - Real-time gift tracking via TikTokLive *(Dec 2025)*
- [x] **Auto-reconnect** - Persistent connection to live streams *(Dec 2025)*

### Recently Completed *(Dec 2025)*
- [x] **Dashboard Live** - Web interface for real TikTok battles at `/live`
- [x] **Advanced Analytics Dashboard** - Charts, statistics, agent performance at `/analytics`
- [x] **Battle Replay System** - Replay battles with playback controls at `/replay`
- [x] **OBS Streaming Integration** - Professional overlays for streamers at `/obs/setup`
- [x] **Audience Voting/Interaction** - Viewer participation with votes and power-ups at `/audience`
- [x] **Leaderboard System** - Top agents and gifters rankings at `/leaderboard`
- [x] **AI Battle Controller** - Intelligent real-time battle assistant with multiple strategies
- [x] **Unified Control Center** - Central dashboard for all battle operations at `/control-center`
- [x] **Battle Platform API** - Integrated platform combining AI controller and gift sender

### Planned
- [ ] Discord/Telegram notifications
- [ ] Machine learning model for optimal gift timing

## License

MIT License
