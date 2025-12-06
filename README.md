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
├── core/                   # Battle engine, scoring, phases
│   ├── battle_engine.py
│   ├── score_tracker.py
│   ├── gift_catalog.py
│   └── multiplier_system.py
├── agents/                 # AI agent implementations
│   ├── base_agent.py
│   ├── personas/           # Character-based agents
│   ├── specialists/        # Strategy-focused agents
│   └── gpt_agent.py        # GPT-powered agents
├── tournament/             # Tournament and bracket system
├── web/                    # Web dashboard
│   ├── backend/app.py      # Flask + Socket.IO server
│   └── frontend/public/    # HTML dashboards
├── tests/                  # Test suite
└── docs/                   # Documentation
    ├── setup/              # Setup guides
    ├── features/           # Feature documentation
    └── analysis/           # Analysis and findings
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

## Web Dashboard

Three dashboard views available:

- **/** - Main battle dashboard
- **/strategic-battle** - Strategic battle with phases and boosts
- **/tournament** - 8-team bracket tournament view

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

## Documentation

See `docs/` directory:
- `docs/setup/` - Installation and GPT setup guides
- `docs/features/` - Feature documentation
- `docs/analysis/` - Battle analytics and findings

## License

MIT License
