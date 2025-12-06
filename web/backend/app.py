"""
TikTok Battle Simulator - Web Dashboard Backend

Flask + SocketIO server for real-time battle visualization.
"""

from flask import Flask, render_template, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import os
import sys
import json
from typing import Dict, Any, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

app = Flask(__name__,
            static_folder='../static',
            template_folder='../frontend/public')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Enable CORS for development
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# Store active battles
active_battles: Dict[str, Dict[str, Any]] = {}
battle_history: List[Dict[str, Any]] = []

# Store active tournaments
active_tournament: Optional[Dict[str, Any]] = None
tournament_history: List[Dict[str, Any]] = []

# Callback to start battle when client connects
_battle_start_callback = None
_battle_callback_triggered = False


def set_battle_start_callback(callback):
    """Set a callback to be called when the first client connects."""
    global _battle_start_callback
    _battle_start_callback = callback


@app.route('/')
def index():
    """Serve the main dashboard page."""
    return send_from_directory('../frontend/public', 'index.html')


@app.route('/tournament')
@app.route('/tournament.html')
def tournament():
    """Serve the tournament dashboard page."""
    return send_from_directory('../frontend/public', 'tournament.html')


@app.route('/strategic')
@app.route('/strategic-battle')
@app.route('/strategic-battle.html')
def strategic_battle():
    """Serve the strategic battle dashboard page."""
    return send_from_directory('../frontend/public', 'strategic-battle.html')


@app.route('/api/battles/active')
def get_active_battles():
    """Get list of currently active battles."""
    return jsonify({
        'battles': list(active_battles.values()),
        'count': len(active_battles)
    })


@app.route('/api/battles/history')
def get_battle_history():
    """Get battle history."""
    return jsonify({
        'battles': battle_history[-10:],  # Last 10 battles
        'total': len(battle_history)
    })


@app.route('/api/battle/<battle_id>')
def get_battle_details(battle_id):
    """Get details of a specific battle."""
    battle = active_battles.get(battle_id) or \
             next((b for b in battle_history if b['id'] == battle_id), None)

    if battle:
        return jsonify(battle)
    return jsonify({'error': 'Battle not found'}), 404


@app.route('/api/agents')
def get_agents():
    """Get list of available agents including new specialists."""
    agents = [
        # Original GPT Agents
        {
            'name': 'NovaWhale',
            'emoji': '🐋',
            'type': 'Strategic Whale',
            'category': 'original',
            'description': 'Waits for critical moments, massive strikes'
        },
        {
            'name': 'PixelPixie',
            'emoji': '🧚‍♀️',
            'type': 'Budget Cheerleader',
            'category': 'evolving',
            'description': 'Endless enthusiasm, Q-learning optimized rose timing'
        },
        {
            'name': 'GlitchMancer',
            'emoji': '🌀',
            'type': 'Chaotic Wildcard',
            'category': 'evolving',
            'description': 'Burst-mode activations, psychological warfare master'
        },
        {
            'name': 'ShadowPatron',
            'emoji': '👤',
            'type': 'Silent Crisis Intervener',
            'category': 'original',
            'description': 'Observes silently, strikes in crisis'
        },
        {
            'name': 'BoostResponder',
            'emoji': '⚡',
            'type': 'Boost Specialist',
            'category': 'evolving',
            'description': 'Q-learning agent that optimizes boost phase spending'
        },
        # NEW Specialist Agents
        {
            'name': 'DefenseMaster',
            'emoji': '🛡️',
            'type': 'Hammer Specialist',
            'category': 'specialist',
            'description': 'Threat detection, proactive defense, hammer timing'
        },
        {
            'name': 'BudgetOptimizer',
            'emoji': '💰',
            'type': 'ROI Tracker',
            'category': 'specialist',
            'description': 'Efficiency tracking, phase-based spend optimization'
        },
        {
            'name': 'ChaoticTrickster',
            'emoji': '🎪',
            'type': 'Psych Warfare',
            'category': 'specialist',
            'description': 'Bluffs, decoys, fog bursts, strategic pauses'
        },
        {
            'name': 'SynergyCoordinator',
            'emoji': '🤝',
            'type': 'Team Leader',
            'category': 'specialist',
            'description': 'Combo orchestration, whale signals, team synergy'
        }
    ]

    return jsonify({'agents': agents})


# SocketIO Events

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    global _battle_callback_triggered
    print(f'Client connected')
    emit('connection_response', {'status': 'connected'})

    # Trigger battle start callback if set and not yet triggered
    if _battle_start_callback and not _battle_callback_triggered:
        _battle_callback_triggered = True
        print(f'🟢 Starting battle via callback...')
        socketio.start_background_task(_battle_start_callback)


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    print(f'Client disconnected')


@socketio.on('request_battle_update')
def handle_battle_update_request(data):
    """Client requesting battle updates."""
    battle_id = data.get('battle_id')
    if battle_id in active_battles:
        emit('battle_update', active_battles[battle_id])


# Battle Event Handlers (called by battle engine)

def broadcast_battle_start(battle_data: Dict[str, Any]):
    """Broadcast battle start event."""
    battle_id = battle_data['id']
    active_battles[battle_id] = battle_data
    print(f"🔊 Broadcasting battle_start: {battle_id}")
    socketio.emit('battle_start', battle_data)
    print(f"   Emitted to all clients")


def broadcast_battle_tick(battle_id: str, tick_data: Dict[str, Any]):
    """Broadcast battle tick update."""
    if battle_id in active_battles:
        active_battles[battle_id]['current_time'] = tick_data['time']
        active_battles[battle_id]['scores'] = tick_data['scores']
        socketio.emit('battle_tick', {
            'battle_id': battle_id,
            **tick_data
        })


def broadcast_agent_action(battle_id: str, action_data: Dict[str, Any]):
    """Broadcast agent action."""
    socketio.emit('agent_action', {
        'battle_id': battle_id,
        **action_data
    })


def broadcast_battle_end(battle_id: str, result_data: Dict[str, Any]):
    """Broadcast battle end."""
    if battle_id in active_battles:
        battle_data = active_battles[battle_id]
        battle_data['status'] = 'completed'
        battle_data['result'] = result_data

        # Move to history
        battle_history.append(battle_data)
        del active_battles[battle_id]

        socketio.emit('battle_end', {
            'battle_id': battle_id,
            **result_data
        })


# Tournament Broadcast Functions

def broadcast_tournament_start(tournament_data: Dict[str, Any]):
    """Broadcast tournament start."""
    global active_tournament
    active_tournament = tournament_data
    print(f"🔊 Broadcasting tournament_start: {tournament_data['id']}")
    socketio.emit('tournament_start', tournament_data)


def broadcast_tournament_series_update(series_data: Dict[str, Any]):
    """Broadcast tournament series score update."""
    if active_tournament:
        socketio.emit('tournament_series_update', series_data)


def broadcast_tournament_bracket_update(bracket_data: Dict[str, Any]):
    """Broadcast tournament bracket update."""
    if active_tournament:
        socketio.emit('tournament_bracket_update', bracket_data)


def broadcast_tournament_momentum_update(momentum_data: Dict[str, Any]):
    """Broadcast tournament momentum update."""
    if active_tournament:
        socketio.emit('tournament_momentum_update', momentum_data)


def broadcast_tournament_end(tournament_id: str, result_data: Dict[str, Any]):
    """Broadcast tournament end."""
    global active_tournament
    if active_tournament:
        active_tournament['status'] = 'completed'
        active_tournament['result'] = result_data

        # Move to history
        tournament_history.append(active_tournament)
        active_tournament = None

        socketio.emit('tournament_end', {
            'tournament_id': tournament_id,
            **result_data
        })


# Strategic Battle Broadcast Functions

def broadcast_strategic_battle_start(battle_data: Dict[str, Any]):
    """Broadcast strategic battle start with GPT analysis."""
    battle_id = battle_data.get('id', 'strategic_battle')
    active_battles[battle_id] = battle_data
    print(f"🔊 Broadcasting strategic_battle_start: {battle_id}")
    socketio.emit('strategic_battle_start', battle_data)


def broadcast_phase_change(phase_data: Dict[str, Any]):
    """Broadcast phase change event."""
    print(f"🔊 Phase change: {phase_data.get('name')} (x{phase_data.get('multiplier')})")
    socketio.emit('phase_change', phase_data)


def broadcast_boost_condition_update(condition_data: Dict[str, Any]):
    """Broadcast boost condition progress."""
    socketio.emit('boost_condition_update', condition_data)


def broadcast_glove_event(glove_data: Dict[str, Any]):
    """Broadcast glove sent/activated event."""
    print(f"🔊 Glove event: {'ACTIVATED!' if glove_data.get('activated') else 'sent'}")
    socketio.emit('glove_sent', glove_data)


def broadcast_powerup_used(powerup_data: Dict[str, Any]):
    """Broadcast power-up usage."""
    print(f"🔊 Power-up: {powerup_data.get('name')}")
    socketio.emit('powerup_used', powerup_data)


def broadcast_gpt_commentary(commentary: str):
    """Broadcast GPT commentary."""
    socketio.emit('gpt_commentary', {'message': commentary})


def broadcast_strategic_battle_end(result_data: Dict[str, Any]):
    """Broadcast strategic battle end with summary."""
    print(f"🔊 Strategic battle end: {result_data.get('winner')}")
    socketio.emit('battle_end', result_data)


# === NEW FEATURE BROADCAST FUNCTIONS ===

def broadcast_clutch_moment(moment_type: str, data: Dict[str, Any] = None):
    """Broadcast clutch moment activation."""
    print(f"🔥 Clutch moment: {moment_type}")
    socketio.emit('clutch_moment', {
        'type': moment_type,
        **(data or {})
    })


def broadcast_pattern_detected(strategy: str, counter_strategy: Dict[str, Any] = None):
    """Broadcast pattern detection event."""
    print(f"🎯 Pattern detected: {strategy}")
    socketio.emit('pattern_detected', {
        'strategy': strategy,
        'counter_strategy': counter_strategy or {}
    })


def broadcast_combo_executed(combo_type: str, points: int, participants: List[str] = None):
    """Broadcast team combo execution."""
    print(f"💫 Combo executed: {combo_type} (+{points:,})")
    socketio.emit('combo_executed', {
        'combo_type': combo_type,
        'points': points,
        'participants': participants or []
    })


def broadcast_psych_warfare(agent: str, tactic: str, data: Dict[str, Any] = None):
    """Broadcast psychological warfare event."""
    print(f"🎭 Psych warfare: {agent} - {tactic}")
    socketio.emit('psych_warfare', {
        'agent': agent,
        'tactic': tactic,
        **(data or {})
    })


def broadcast_analytics_update(analytics_data: Dict[str, Any]):
    """Broadcast analytics update."""
    socketio.emit('analytics_update', analytics_data)


def broadcast_elimination_bracket_update(bracket_data: Dict[str, Any]):
    """Broadcast 8-team elimination bracket update."""
    print(f"🏆 Bracket update: Round {bracket_data.get('current_round', 1)}")
    socketio.emit('elimination_bracket_update', bracket_data)


def broadcast_match_result(match_id: int, team1: str, team2: str,
                          team1_score: int, team2_score: int, winner: str):
    """Broadcast individual match result."""
    print(f"⚔️ Match {match_id}: {team1} vs {team2} - Winner: {winner}")
    socketio.emit('match_result', {
        'match_id': match_id,
        'team1': team1,
        'team2': team2,
        'team1_score': team1_score,
        'team2_score': team2_score,
        'winner': winner
    })


def broadcast_tournament_champion(team_name: str, emoji: str = '🏆',
                                  record: str = '', point_diff: int = 0):
    """Broadcast tournament champion announcement."""
    print(f"👑 CHAMPION: {emoji} {team_name}")
    socketio.emit('tournament_champion', {
        'team_name': team_name,
        'emoji': emoji,
        'record': record,
        'point_differential': point_diff
    })


def run_server(host='0.0.0.0', port=5000, debug=None):
    """Run the Flask-SocketIO server."""
    print(f"\n{'='*70}")
    print(f"🌐 TikTok Battle Dashboard Server")
    print(f"{'='*70}")
    print(f"Server running at: http://localhost:{port}")
    print(f"Open in browser to watch battles live!")
    print(f"{'='*70}\n")

    if debug is None:
        debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)


if __name__ == '__main__':
    run_server()
