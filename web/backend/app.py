"""
TikTok Battle Simulator - Web Dashboard Backend

Flask + SocketIO server for real-time battle visualization.
"""

from flask import Flask, render_template, jsonify, send_from_directory, request, session, redirect, url_for, Blueprint
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import os
import sys
import json
import asyncio
import threading
import yaml
from typing import Dict, Any, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

# Import live battle components
try:
    from core.tiktok_live_connector import (
        TikTokLiveConnector,
        LiveGiftEvent,
        TIKTOK_LIVE_AVAILABLE
    )
    from core.live_battle_engine import LiveBattleEngine, BattleMode
except ImportError:
    TIKTOK_LIVE_AVAILABLE = False

# Import live tournament engine
try:
    from core.live_tournament_engine import (
        LiveTournamentEngine,
        TournamentFormat,
        TournamentState,
        RoundResult
    )
    TOURNAMENT_AVAILABLE = True
except ImportError:
    TOURNAMENT_AVAILABLE = False

# Import AI vs Live engine
try:
    from core.ai_vs_live_engine import (
        AIvsLiveEngine,
        AIBattleMode,
        TournamentFormat as AITournamentFormat
    )
    AI_VS_LIVE_AVAILABLE = True
except ImportError:
    AI_VS_LIVE_AVAILABLE = False

from web.backend.auth import (
    login_required, admin_required, authenticate_user,
    create_user, init_default_admin, get_user_count
)

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

# Store active live battles
active_live_battles: Dict[str, Any] = {}
live_battle_engine: Optional[Any] = None
live_battle_loop: Optional[asyncio.AbstractEventLoop] = None

# Store active tournament
active_tournament_engine: Optional[Any] = None
tournament_loop: Optional[asyncio.AbstractEventLoop] = None

# Store active AI vs Live battle
ai_vs_live_engine: Optional[Any] = None
ai_vs_live_loop: Optional[asyncio.AbstractEventLoop] = None

# Store active Battle Platform
battle_platform: Optional[Any] = None
battle_platform_loop: Optional[asyncio.AbstractEventLoop] = None

# Import Battle Platform
try:
    from core.battle_platform import (
        TikTokBattlePlatform,
        PlatformConfig,
        PlatformMode,
        PlatformStats
    )
    from core.ai_battle_controller import AIStrategy
    BATTLE_PLATFORM_AVAILABLE = True
except ImportError:
    BATTLE_PLATFORM_AVAILABLE = False

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


@app.route('/live')
@app.route('/live.html')
def live_battle():
    """Serve the live TikTok battle dashboard page."""
    return send_from_directory('../frontend/public', 'live.html')


@app.route('/live-tournament')
@app.route('/live-tournament.html')
def live_tournament():
    """Serve the live tournament dashboard page."""
    return send_from_directory('../frontend/public', 'live-tournament.html')


@app.route('/ai-vs-live')
@app.route('/ai-vs-live.html')
def ai_vs_live():
    """Serve the AI vs Live battle dashboard page."""
    return send_from_directory('../frontend/public', 'ai-vs-live.html')


@app.route('/ai-battle')
@app.route('/ai-battle.html')
def ai_battle_page():
    """Serve the AI Battle Controller dashboard page."""
    return send_from_directory('../frontend/public', 'ai-battle.html')


@app.route('/gift-sender')
@app.route('/gift-sender.html')
def gift_sender_page():
    """Serve the Gift Sender dashboard page."""
    return send_from_directory('../frontend/public', 'gift-sender.html')


@app.route('/control-center')
@app.route('/control-center.html')
def control_center_page():
    """Serve the unified Control Center dashboard page."""
    return send_from_directory('../frontend/public', 'control-center.html')


@app.route('/api/health')
def health_check():
    """Health check endpoint for deployment."""
    return jsonify({
        'status': 'healthy',
        'service': 'TikTok Battle Simulator',
        'version': '2.0.0'
    })


@app.route('/api/live/status')
def get_live_status():
    """Get live battle system status."""
    return jsonify({
        'tiktok_live_available': TIKTOK_LIVE_AVAILABLE,
        'active_battle': live_battle_engine is not None,
        'battle_state': live_battle_engine.get_state() if live_battle_engine else None
    })


@app.route('/api/ai-vs-live/status')
def get_ai_vs_live_status():
    """Get AI vs Live battle system status."""
    return jsonify({
        'ai_vs_live_available': AI_VS_LIVE_AVAILABLE,
        'tiktok_live_available': TIKTOK_LIVE_AVAILABLE,
        'active_battle': ai_vs_live_engine is not None,
        'battle_state': ai_vs_live_engine.get_stats() if ai_vs_live_engine else None
    })


@app.route('/api/battle-platform/status')
def get_battle_platform_status():
    """Get Battle Platform status."""
    return jsonify({
        'battle_platform_available': BATTLE_PLATFORM_AVAILABLE,
        'active': battle_platform is not None,
        'stats': battle_platform.get_stats() if battle_platform else None
    })


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


# =============================================================================
# Live TikTok Battle Socket.IO Events
# =============================================================================

@socketio.on('start_live_battle')
def handle_start_live_battle(data):
    """Handle request to start a live TikTok battle."""
    global live_battle_engine, live_battle_loop

    if not TIKTOK_LIVE_AVAILABLE:
        emit('live_error', {'error': 'TikTokLive library not installed. Run: pip install TikTokLive'})
        return

    if live_battle_engine is not None:
        emit('live_error', {'error': 'A live battle is already running'})
        return

    creator = data.get('creator', '').lstrip('@')
    opponent = data.get('opponent', '').lstrip('@')
    duration = int(data.get('duration', 300))

    if not creator or not opponent:
        emit('live_error', {'error': 'Both creator and opponent usernames are required'})
        return

    print(f"\n{'='*60}")
    print(f"🔴 LIVE BATTLE STARTING")
    print(f"   @{creator} vs @{opponent}")
    print(f"   Duration: {duration}s")
    print(f"{'='*60}\n")

    # Create engine
    live_battle_engine = LiveBattleEngine(
        creator_username=creator,
        opponent_username=opponent,
        battle_duration=duration,
        mode=BattleMode.LIVE
    )

    # Register callbacks for Socket.IO broadcasting
    def on_gift(event, creator_score, opponent_score):
        socketio.emit('live_gift', {
            'team': event.team,
            'username': event.username,
            'gift_name': event.gift_name,
            'gift_id': event.gift_id,
            'repeat_count': event.repeat_count,
            'total_coins': event.total_coins,
            'total_points': event.total_points,
            'creator_score': creator_score,
            'opponent_score': opponent_score
        })

    def on_phase_change(phase, multiplier):
        socketio.emit('live_phase_change', {
            'phase': phase,
            'multiplier': multiplier
        })

    def on_score_update(creator_score, opponent_score):
        state = live_battle_engine.get_state()
        socketio.emit('live_score_update', {
            'creator_score': creator_score,
            'opponent_score': opponent_score,
            'time_remaining': state['time_remaining'],
            'current_phase': state['current_phase'],
            'current_multiplier': state['current_multiplier']
        })

    def on_battle_end(winner, result):
        global live_battle_engine
        socketio.emit('live_battle_ended', {
            'winner': winner,
            'creator_score': result['creator_score'],
            'opponent_score': result['opponent_score'],
            'creator_username': result['creator_username'],
            'opponent_username': result['opponent_username'],
            'top_creator_gifters': result['top_creator_gifters'],
            'top_opponent_gifters': result['top_opponent_gifters']
        })
        live_battle_engine = None

    # Add connection status callback
    def on_connection_change():
        state = live_battle_engine.get_state()
        socketio.emit('live_connection_status', {
            'team': 'creator',
            'username': creator,
            'connected': state['creator_connected']
        })
        socketio.emit('live_connection_status', {
            'team': 'opponent',
            'username': opponent,
            'connected': state['opponent_connected']
        })
        # Also update top gifters periodically
        socketio.emit('live_top_gifters', {
            'creator': dict(sorted(
                live_battle_engine.state.top_creator_gifters.items(),
                key=lambda x: x[1], reverse=True
            )[:5]) if live_battle_engine.state.top_creator_gifters else {},
            'opponent': dict(sorted(
                live_battle_engine.state.top_opponent_gifters.items(),
                key=lambda x: x[1], reverse=True
            )[:5]) if live_battle_engine.state.top_opponent_gifters else {}
        })

    live_battle_engine.on_gift(on_gift)
    live_battle_engine.on_phase_change(on_phase_change)
    live_battle_engine.on_score_update(on_score_update)
    live_battle_engine.on_battle_end(on_battle_end)

    # Monkey-patch connection handlers to broadcast status
    original_on_connect = live_battle_engine._on_connect
    def patched_on_connect(team, unique_id):
        original_on_connect(team, unique_id)
        on_connection_change()
    live_battle_engine._on_connect = patched_on_connect

    original_on_disconnect = live_battle_engine._on_disconnect
    def patched_on_disconnect(team, unique_id):
        original_on_disconnect(team, unique_id)
        on_connection_change()
    live_battle_engine._on_disconnect = patched_on_disconnect

    # Emit battle started confirmation
    emit('live_battle_started', {
        'creator': creator,
        'opponent': opponent,
        'duration': duration
    })

    # Start the battle in a background thread
    def run_live_battle():
        global live_battle_engine, live_battle_loop
        live_battle_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(live_battle_loop)

        try:
            live_battle_loop.run_until_complete(live_battle_engine.start_live_battle())
        except Exception as e:
            print(f"Live battle error: {e}")
            socketio.emit('live_error', {'error': str(e)})
        finally:
            live_battle_loop.close()
            live_battle_loop = None

    # Start in background thread
    battle_thread = threading.Thread(target=run_live_battle, daemon=True)
    battle_thread.start()


@socketio.on('stop_live_battle')
def handle_stop_live_battle():
    """Handle request to stop a live battle."""
    global live_battle_engine, live_battle_loop

    if live_battle_engine is None:
        emit('live_error', {'error': 'No live battle is running'})
        return

    print(f"\n⏹️  Stopping live battle...")

    # Stop the battle
    if live_battle_loop and live_battle_loop.is_running():
        future = asyncio.run_coroutine_threadsafe(
            live_battle_engine.stop_battle(),
            live_battle_loop
        )
        try:
            future.result(timeout=5)
        except Exception as e:
            print(f"Error stopping battle: {e}")

    live_battle_engine = None
    emit('live_battle_stopped', {'status': 'stopped'})


@socketio.on('get_live_state')
def handle_get_live_state():
    """Get current live battle state."""
    if live_battle_engine:
        state = live_battle_engine.get_state()
        emit('live_state', state)
    else:
        emit('live_state', None)


# =============================================================================
# LIVE TOURNAMENT SOCKET.IO HANDLERS
# =============================================================================

@socketio.on('start_tournament')
def handle_start_tournament(data):
    """Handle request to start a live TikTok tournament."""
    global active_tournament_engine, tournament_loop

    if not TIKTOK_LIVE_AVAILABLE:
        emit('tournament_error', {'error': 'TikTokLive library not installed. Run: pip install TikTokLive'})
        return

    if not TOURNAMENT_AVAILABLE:
        emit('tournament_error', {'error': 'Tournament engine not available'})
        return

    if active_tournament_engine is not None:
        emit('tournament_error', {'error': 'A tournament is already running'})
        return

    creator = data.get('creator', '').lstrip('@')
    opponent = data.get('opponent', '').lstrip('@')
    format_str = data.get('format', 'bo3').lower()
    round_duration = int(data.get('round_duration', 120))
    break_duration = int(data.get('break_duration', 20))

    if not creator or not opponent:
        emit('tournament_error', {'error': 'Both creator and opponent usernames are required'})
        return

    # Parse format
    format_map = {
        'bo3': TournamentFormat.BEST_OF_3,
        'bo5': TournamentFormat.BEST_OF_5,
        'bo7': TournamentFormat.BEST_OF_7,
    }
    tournament_format = format_map.get(format_str, TournamentFormat.BEST_OF_3)

    print(f"\n{'='*60}")
    print(f"🏆 LIVE TOURNAMENT STARTING - Best of {tournament_format.value}")
    print(f"   @{creator} vs @{opponent}")
    print(f"   Round Duration: {round_duration}s | Break: {break_duration}s")
    print(f"{'='*60}\n")

    # Create tournament engine
    active_tournament_engine = LiveTournamentEngine(
        creator_username=creator,
        opponent_username=opponent,
        format=tournament_format,
        round_duration=round_duration,
        break_duration=break_duration
    )

    # Register callbacks for Socket.IO broadcasting
    def on_round_start(round_num, stats):
        socketio.emit('tournament_round_start', {
            'round': round_num,
            'series_score': stats['series_score'],
            'creator_wins': stats['creator_wins'],
            'opponent_wins': stats['opponent_wins'],
            'wins_needed': stats['wins_needed']
        })

    def on_gift(event, round_num, creator_score, opponent_score):
        socketio.emit('tournament_gift', {
            'round': round_num,
            'team': event.team,
            'username': event.username,
            'gift_name': event.gift_name,
            'gift_id': event.gift_id,
            'repeat_count': event.repeat_count,
            'total_coins': event.total_coins,
            'total_points': event.total_points,
            'creator_score': creator_score,
            'opponent_score': opponent_score
        })

    def on_score_update(round_num, creator_score, opponent_score, time_remaining):
        socketio.emit('tournament_score_update', {
            'round': round_num,
            'creator_score': creator_score,
            'opponent_score': opponent_score,
            'time_remaining': time_remaining
        })

    def on_round_end(result, stats):
        socketio.emit('tournament_round_end', {
            'round': result.round_number,
            'winner': result.winner,
            'creator_score': result.creator_score,
            'opponent_score': result.opponent_score,
            'top_gifter': result.top_gifter,
            'top_gift_amount': result.top_gift_amount,
            'gift_count': result.gift_count,
            'series_score': stats['series_score'],
            'creator_wins': stats['creator_wins'],
            'opponent_wins': stats['opponent_wins']
        })

    def on_break_start(next_round, break_seconds):
        socketio.emit('tournament_break_start', {
            'next_round': next_round,
            'break_seconds': break_seconds
        })

    def on_tournament_end(winner, stats):
        global active_tournament_engine
        socketio.emit('tournament_ended', {
            'winner': winner,
            'series_score': stats['series_score'],
            'rounds_played': stats['rounds_played'],
            'total_creator_score': stats['total_creator_score'],
            'total_opponent_score': stats['total_opponent_score'],
            'total_gifts': stats['total_gifts'],
            'total_coins': stats['total_coins'],
            'rounds': stats['rounds']
        })
        active_tournament_engine = None

    active_tournament_engine.on_round_start(on_round_start)
    active_tournament_engine.on_gift(on_gift)
    active_tournament_engine.on_score_update(on_score_update)
    active_tournament_engine.on_round_end(on_round_end)
    active_tournament_engine.on_break_start(on_break_start)
    active_tournament_engine.on_tournament_end(on_tournament_end)

    # Emit tournament started confirmation
    emit('tournament_started', {
        'creator': creator,
        'opponent': opponent,
        'format': format_str,
        'format_value': tournament_format.value,
        'round_duration': round_duration,
        'break_duration': break_duration,
        'wins_needed': (tournament_format.value // 2) + 1
    })

    # Start the tournament in a background thread
    def run_tournament():
        global active_tournament_engine, tournament_loop
        tournament_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(tournament_loop)

        try:
            tournament_loop.run_until_complete(active_tournament_engine.start())
        except Exception as e:
            print(f"Tournament error: {e}")
            socketio.emit('tournament_error', {'error': str(e)})
        finally:
            tournament_loop.close()
            tournament_loop = None

    # Start in background thread
    tournament_thread = threading.Thread(target=run_tournament, daemon=True)
    tournament_thread.start()


@socketio.on('stop_tournament')
def handle_stop_tournament():
    """Handle request to stop a live tournament."""
    global active_tournament_engine, tournament_loop

    if active_tournament_engine is None:
        emit('tournament_error', {'error': 'No tournament is running'})
        return

    print(f"\n⏹️  Stopping tournament...")

    # Stop the tournament
    if tournament_loop and tournament_loop.is_running():
        future = asyncio.run_coroutine_threadsafe(
            active_tournament_engine.stop(),
            tournament_loop
        )
        try:
            future.result(timeout=5)
        except Exception as e:
            print(f"Error stopping tournament: {e}")

    active_tournament_engine = None
    emit('tournament_stopped', {'status': 'stopped'})


@socketio.on('get_tournament_state')
def handle_get_tournament_state():
    """Get current tournament state."""
    if active_tournament_engine:
        stats = active_tournament_engine.get_stats()
        emit('tournament_state', stats)
    else:
        emit('tournament_state', None)


# =============================================================================
# AI vs LIVE BATTLE SOCKET.IO HANDLERS
# =============================================================================

@socketio.on('start_ai_vs_live')
def handle_start_ai_vs_live(data):
    """Handle request to start an AI vs Live battle."""
    global ai_vs_live_engine, ai_vs_live_loop

    if not AI_VS_LIVE_AVAILABLE:
        emit('ai_vs_live_error', {'error': 'AI vs Live engine not available'})
        return

    if ai_vs_live_engine is not None:
        emit('ai_vs_live_error', {'error': 'An AI vs Live battle is already running'})
        return

    target = data.get('target', '').lstrip('@')
    mode = data.get('mode', 'simulation')  # 'simulation' or 'live'
    format_str = data.get('format', 'bo1').lower()
    duration = int(data.get('duration', 300))
    budget = int(data.get('budget', 50000))
    team = data.get('team', None)

    if not target:
        emit('ai_vs_live_error', {'error': 'Target streamer username is required'})
        return

    # Parse format
    format_map = {
        'bo1': AITournamentFormat.BEST_OF_1,
        'bo3': AITournamentFormat.BEST_OF_3,
        'bo5': AITournamentFormat.BEST_OF_5,
        'bo7': AITournamentFormat.BEST_OF_7,
    }
    tournament_format = format_map.get(format_str, AITournamentFormat.BEST_OF_1)

    # Parse mode
    battle_mode = AIBattleMode.SIMULATION if mode == 'simulation' else AIBattleMode.TOURNAMENT

    print(f"\n{'='*60}")
    print(f"🤖 AI vs LIVE BATTLE STARTING")
    print(f"   Target: @{target}")
    print(f"   Mode: {battle_mode.value}")
    print(f"   Format: Best of {tournament_format.value}")
    print(f"   Duration: {duration}s per round")
    print(f"   Budget: {budget:,} coins")
    print(f"{'='*60}\n")

    # Create engine
    ai_vs_live_engine = AIvsLiveEngine(
        target_streamer=target,
        ai_team=team.split(',') if team else None,
        mode=battle_mode,
        round_duration=duration,
        tournament_format=tournament_format,
        ai_budget_per_round=budget
    )

    # Register callbacks for Socket.IO broadcasting
    def on_ai_gift(gift_data, ai_score, live_score):
        socketio.emit('ai_vs_live_ai_gift', {
            'agent': gift_data['agent'],
            'emoji': gift_data['emoji'],
            'gift_name': gift_data['gift_name'],
            'points': gift_data['points'],
            'multiplier': gift_data.get('multiplier', 1.0),
            'ai_score': ai_score,
            'live_score': live_score
        })

    def on_live_gift(event, live_score, ai_score):
        socketio.emit('ai_vs_live_live_gift', {
            'username': event.username,
            'gift_name': event.gift_name,
            'repeat_count': event.repeat_count,
            'total_coins': event.total_coins,
            'total_points': event.total_points,
            'ai_score': ai_score,
            'live_score': live_score
        })

    def on_score_update(ai_score, live_score, time_remaining, round_num):
        socketio.emit('ai_vs_live_score_update', {
            'ai_score': ai_score,
            'live_score': live_score,
            'time_remaining': time_remaining,
            'round': round_num
        })

    def on_round_end(result, stats):
        socketio.emit('ai_vs_live_round_end', {
            'round': result.round_number,
            'winner': result.winner,
            'ai_score': result.ai_score,
            'live_score': result.live_score,
            'ai_gifts': result.ai_gifts,
            'live_gifts': result.live_gifts,
            'top_ai_agent': result.top_ai_agent,
            'top_live_gifter': result.top_live_gifter,
            'ai_wins': stats['ai_wins'],
            'live_wins': stats['live_wins']
        })

    def on_battle_end(winner, stats):
        global ai_vs_live_engine
        socketio.emit('ai_vs_live_battle_end', {
            'winner': winner,
            'series_score': stats['series_score'],
            'total_ai_score': stats['total_ai_score'],
            'total_live_score': stats['total_live_score'],
            'ai_team': stats['ai_team'],
            'rounds': stats['rounds'],
            'target_streamer': stats['target_streamer']
        })
        ai_vs_live_engine = None

    def on_connection(connected, username):
        socketio.emit('ai_vs_live_connection', {
            'connected': connected,
            'username': username
        })

    ai_vs_live_engine.on_ai_gift(on_ai_gift)
    ai_vs_live_engine.on_live_gift(on_live_gift)
    ai_vs_live_engine.on_score_update(on_score_update)
    ai_vs_live_engine.on_round_end(on_round_end)
    ai_vs_live_engine.on_battle_end(on_battle_end)
    ai_vs_live_engine.on_connection(on_connection)

    # Emit battle started confirmation
    emit('ai_vs_live_started', {
        'target': target,
        'mode': battle_mode.value,
        'format': format_str,
        'format_value': tournament_format.value,
        'duration': duration,
        'budget': budget,
        'wins_needed': (tournament_format.value // 2) + 1
    })

    # Start the battle in a background thread
    def run_ai_vs_live():
        global ai_vs_live_engine, ai_vs_live_loop
        ai_vs_live_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(ai_vs_live_loop)

        try:
            ai_vs_live_loop.run_until_complete(ai_vs_live_engine.start_battle())
        except Exception as e:
            print(f"AI vs Live battle error: {e}")
            socketio.emit('ai_vs_live_error', {'error': str(e)})
        finally:
            ai_vs_live_loop.close()
            ai_vs_live_loop = None

    # Start in background thread
    battle_thread = threading.Thread(target=run_ai_vs_live, daemon=True)
    battle_thread.start()


@socketio.on('stop_ai_vs_live')
def handle_stop_ai_vs_live():
    """Handle request to stop an AI vs Live battle."""
    global ai_vs_live_engine, ai_vs_live_loop

    if ai_vs_live_engine is None:
        emit('ai_vs_live_error', {'error': 'No AI vs Live battle is running'})
        return

    print(f"\n⏹️  Stopping AI vs Live battle...")

    # Stop the battle
    if ai_vs_live_loop and ai_vs_live_loop.is_running():
        future = asyncio.run_coroutine_threadsafe(
            ai_vs_live_engine.stop(),
            ai_vs_live_loop
        )
        try:
            future.result(timeout=5)
        except Exception as e:
            print(f"Error stopping AI vs Live battle: {e}")

    ai_vs_live_engine = None
    emit('ai_vs_live_stopped', {'status': 'stopped'})


@socketio.on('get_ai_vs_live_state')
def handle_get_ai_vs_live_state():
    """Get current AI vs Live battle state."""
    if ai_vs_live_engine:
        stats = ai_vs_live_engine.get_stats()
        emit('ai_vs_live_state', stats)
    else:
        emit('ai_vs_live_state', None)


# =============================================================================
# BATTLE PLATFORM SOCKET.IO HANDLERS
# =============================================================================

@socketio.on('start_battle_platform')
def handle_start_battle_platform(data):
    """Handle request to start Battle Platform AI support."""
    global battle_platform, battle_platform_loop

    if not BATTLE_PLATFORM_AVAILABLE:
        emit('platform_error', {'error': 'Battle Platform not available'})
        return

    if battle_platform is not None:
        emit('platform_error', {'error': 'Battle Platform is already running'})
        return

    target = data.get('target', '').lstrip('@')
    strategy = data.get('strategy', 'smart')
    mode = data.get('mode', 'supporter')
    duration = int(data.get('duration', 300))
    gift = data.get('gift', 'Fest Pop')
    max_per_minute = int(data.get('max_per_minute', 500))

    if not target:
        emit('platform_error', {'error': 'Target streamer username is required'})
        return

    # Parse strategy
    try:
        ai_strategy = AIStrategy(strategy.lower())
    except:
        ai_strategy = AIStrategy.SMART

    # Parse mode
    mode_map = {
        'observer': PlatformMode.OBSERVER,
        'supporter': PlatformMode.SUPPORTER,
        'manual': PlatformMode.MANUAL,
        'hybrid': PlatformMode.HYBRID
    }
    platform_mode = mode_map.get(mode.lower(), PlatformMode.SUPPORTER)

    print(f"\n{'='*60}")
    print(f"🤖 BATTLE PLATFORM STARTING")
    print(f"   Target: @{target}")
    print(f"   Strategy: {ai_strategy.value}")
    print(f"   Mode: {platform_mode.value}")
    print(f"   Duration: {duration}s")
    print(f"{'='*60}\n")

    # Create config
    config = PlatformConfig(
        mode=platform_mode,
        target_streamer=target,
        ai_strategy=ai_strategy,
        default_gift=gift,
        max_gifts_per_minute=max_per_minute,
        ai_enabled=(platform_mode != PlatformMode.OBSERVER)
    )

    # Create platform
    battle_platform = TikTokBattlePlatform(config)

    # Register callbacks for Socket.IO broadcasting
    def on_score_update(score):
        socketio.emit('platform_score', {
            'our_score': score.our_score,
            'opponent_score': score.opponent_score,
            'gap': score.gap,
            'gap_percentage': score.gap_percentage,
            'time_remaining': score.time_remaining,
            'battle_active': score.battle_active
        })

    def on_decision(decision, score):
        socketio.emit('platform_decision', {
            'should_send': decision.should_send,
            'gift_name': decision.gift_name,
            'quantity': decision.quantity,
            'urgency': decision.urgency,
            'reason': decision.reason,
            'cps': decision.cps,
            'score': {
                'our_score': score.our_score,
                'opponent_score': score.opponent_score,
                'gap': score.gap
            }
        })

    def on_gift_sent(result):
        socketio.emit('platform_gift_sent', {
            'success': result.success,
            'sent': result.sent,
            'failed': result.failed,
            'gift_name': result.gift_name,
            'message': result.message
        })

    def on_battle_end(result):
        socketio.emit('platform_battle_end', result)

    battle_platform.on_score_update(on_score_update)
    battle_platform.on_decision(on_decision)
    battle_platform.on_gift_sent(on_gift_sent)
    battle_platform.on_battle_end(on_battle_end)

    # Emit started confirmation
    emit('platform_started', {
        'target': target,
        'strategy': ai_strategy.value,
        'mode': platform_mode.value,
        'duration': duration,
        'gift': gift
    })

    # Start in background thread
    def run_platform():
        global battle_platform, battle_platform_loop
        battle_platform_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(battle_platform_loop)

        try:
            battle_platform_loop.run_until_complete(battle_platform.connect())
            battle_platform_loop.run_until_complete(battle_platform.go_to_stream(target))
            battle_platform_loop.run_until_complete(battle_platform.run_ai_battle(duration))
        except Exception as e:
            print(f"Battle Platform error: {e}")
            socketio.emit('platform_error', {'error': str(e)})
        finally:
            if battle_platform:
                battle_platform_loop.run_until_complete(battle_platform.disconnect())
            battle_platform_loop.close()
            battle_platform_loop = None
            battle_platform = None
            socketio.emit('platform_stopped', {'status': 'completed'})

    platform_thread = threading.Thread(target=run_platform, daemon=True)
    platform_thread.start()


@socketio.on('stop_battle_platform')
def handle_stop_battle_platform():
    """Handle request to stop Battle Platform."""
    global battle_platform

    if battle_platform is None:
        emit('platform_error', {'error': 'No Battle Platform is running'})
        return

    print(f"\n⏹️  Stopping Battle Platform...")
    battle_platform.stop()
    emit('platform_stopped', {'status': 'stopped'})


@socketio.on('platform_set_strategy')
def handle_platform_set_strategy(data):
    """Change Battle Platform strategy."""
    if battle_platform is None:
        emit('platform_error', {'error': 'No Battle Platform is running'})
        return

    strategy = data.get('strategy', 'smart')
    try:
        ai_strategy = AIStrategy(strategy.lower())
        battle_platform.set_strategy(ai_strategy)
        emit('platform_strategy_changed', {'strategy': ai_strategy.value})
    except:
        emit('platform_error', {'error': f'Invalid strategy: {strategy}'})


@socketio.on('platform_pause')
def handle_platform_pause():
    """Pause Battle Platform."""
    if battle_platform:
        battle_platform.pause()
        emit('platform_paused', {'status': 'paused'})


@socketio.on('platform_resume')
def handle_platform_resume():
    """Resume Battle Platform."""
    if battle_platform:
        battle_platform.resume()
        emit('platform_resumed', {'status': 'resumed'})


@socketio.on('get_platform_state')
def handle_get_platform_state():
    """Get current Battle Platform state."""
    if battle_platform:
        emit('platform_state', battle_platform.get_stats())
    else:
        emit('platform_state', None)


# Live Battle Broadcast Functions

def broadcast_live_connection_status(team: str, username: str, connected: bool):
    """Broadcast live stream connection status."""
    print(f"{'✅' if connected else '❌'} {team.upper()} @{username}: {'Connected' if connected else 'Disconnected'}")
    socketio.emit('live_connection_status', {
        'team': team,
        'username': username,
        'connected': connected
    })


def broadcast_live_top_gifters(creator_gifters: Dict[str, int], opponent_gifters: Dict[str, int]):
    """Broadcast top gifters update."""
    socketio.emit('live_top_gifters', {
        'creator': dict(sorted(creator_gifters.items(), key=lambda x: x[1], reverse=True)[:5]),
        'opponent': dict(sorted(opponent_gifters.items(), key=lambda x: x[1], reverse=True)[:5])
    })


# =============================================================================
# AUDIENCE VOTING & INTERACTION
# =============================================================================

# Audience state
audience_state = {
    'viewers': {},  # viewer_id -> {vote, connected}
    'votes': {'creator': 0, 'opponent': 0},
    'powerup_cooldowns': {},  # powerup -> timestamp
    'total_viewers': 0
}


@app.route('/audience')
@app.route('/audience.html')
def audience_page():
    """Serve the audience participation page."""
    return send_from_directory('../frontend/public', 'audience.html')


@app.route('/host')
@app.route('/host.html')
def host_page():
    """Serve the host controls page."""
    return send_from_directory('../frontend/public', 'host.html')


@socketio.on('viewer_join')
def handle_viewer_join(data):
    """Handle viewer joining the audience."""
    viewer_id = data.get('viewer_id')
    if viewer_id:
        audience_state['viewers'][viewer_id] = {'vote': None, 'connected': True}
        audience_state['total_viewers'] = len([v for v in audience_state['viewers'].values() if v['connected']])

        # Send current state to new viewer
        emit('vote_update', audience_state['votes'])
        emit('viewer_count', {'count': audience_state['total_viewers']})

        # Broadcast updated viewer count
        socketio.emit('viewer_count', {'count': audience_state['total_viewers']})


@socketio.on('audience_vote')
def handle_audience_vote(data):
    """Handle audience vote for a team."""
    viewer_id = data.get('viewer_id')
    vote = data.get('vote')

    if not viewer_id or vote not in ['creator', 'opponent']:
        return

    # Check if already voted
    if viewer_id in audience_state['viewers'] and audience_state['viewers'][viewer_id]['vote']:
        emit('vote_error', {'error': 'Already voted'})
        return

    # Record vote
    if viewer_id not in audience_state['viewers']:
        audience_state['viewers'][viewer_id] = {'vote': None, 'connected': True}

    audience_state['viewers'][viewer_id]['vote'] = vote
    audience_state['votes'][vote] += 1

    # Broadcast updated votes
    socketio.emit('vote_update', audience_state['votes'])

    print(f"🗳️ Vote: {vote.upper()} (Creator: {audience_state['votes']['creator']}, Opponent: {audience_state['votes']['opponent']})")


@socketio.on('audience_powerup')
def handle_audience_powerup(data):
    """Handle audience-triggered power-up."""
    import time

    viewer_id = data.get('viewer_id')
    powerup = data.get('powerup')

    valid_powerups = ['score_boost', 'freeze', 'double_points', 'random']
    if powerup not in valid_powerups:
        return

    # Check cooldown (30 seconds)
    cooldown_key = f"{viewer_id}_{powerup}"
    current_time = time.time()

    if cooldown_key in audience_state['powerup_cooldowns']:
        if current_time - audience_state['powerup_cooldowns'][cooldown_key] < 30:
            remaining = 30 - (current_time - audience_state['powerup_cooldowns'][cooldown_key])
            emit('powerup_cooldown', {'powerup': powerup, 'seconds': int(remaining)})
            return

    # Record cooldown
    audience_state['powerup_cooldowns'][cooldown_key] = current_time

    # Broadcast power-up event
    powerup_names = {
        'score_boost': 'Score Boost',
        'freeze': 'Freeze',
        'double_points': 'Double Points',
        'random': 'Random Effect'
    }

    socketio.emit('powerup_triggered', {
        'powerup': powerup_names.get(powerup, powerup),
        'triggered_by': f'Viewer',
        'type': powerup
    })

    # Also emit as regular power_up for OBS overlays
    socketio.emit('power_up', {
        'power_up': powerup_names.get(powerup, powerup),
        'source': 'audience'
    })

    print(f"⚡ Audience Power-up: {powerup_names.get(powerup, powerup)}")

    # Send cooldown to triggering viewer
    emit('powerup_cooldown', {'powerup': powerup, 'seconds': 30})


@app.route('/api/audience/votes')
def get_audience_votes():
    """Get current audience vote counts."""
    return jsonify({
        'votes': audience_state['votes'],
        'total_viewers': audience_state['total_viewers']
    })


@app.route('/api/audience/reset', methods=['POST'])
def reset_audience_votes():
    """Reset audience votes (for new battle)."""
    audience_state['votes'] = {'creator': 0, 'opponent': 0}
    for viewer_id in audience_state['viewers']:
        audience_state['viewers'][viewer_id]['vote'] = None

    socketio.emit('vote_update', audience_state['votes'])
    return jsonify({'status': 'reset'})


# =============================================================================
# Database API Endpoints
# =============================================================================

try:
    from core.database import BattleRepository, TournamentRepository, ReplayRepository, LeaderboardRepository, init_database
    DATABASE_AVAILABLE = True
    init_database()
except ImportError:
    DATABASE_AVAILABLE = False
    ReplayRepository = None
    LeaderboardRepository = None


@app.route('/api/db/battles')
def get_db_battles():
    """Get battle history from database."""
    if not DATABASE_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 503

    limit = int(request.args.get('limit', 20))
    battles = BattleRepository.get_recent_battles(limit)
    return jsonify({'battles': battles})


@app.route('/api/db/battles/<battle_id>')
def get_db_battle(battle_id):
    """Get specific battle from database."""
    if not DATABASE_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 503

    battle = BattleRepository.get_battle(battle_id)
    if battle:
        events = BattleRepository.get_battle_events(battle_id)
        battle['events'] = events
        return jsonify(battle)
    return jsonify({'error': 'Battle not found'}), 404


@app.route('/api/db/statistics')
def get_db_statistics():
    """Get overall battle statistics."""
    if not DATABASE_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 503

    stats = BattleRepository.get_statistics()
    return jsonify(stats)


@app.route('/api/db/tournaments')
def get_db_tournaments():
    """Get tournament history from database."""
    if not DATABASE_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 503

    limit = int(request.args.get('limit', 10))
    tournaments = TournamentRepository.get_recent_tournaments(limit)
    return jsonify({'tournaments': tournaments})


@app.route('/api/db/tournaments/<tournament_id>')
def get_db_tournament(tournament_id):
    """Get specific tournament from database."""
    if not DATABASE_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 503

    tournament = TournamentRepository.get_tournament(tournament_id)
    if tournament:
        return jsonify(tournament)
    return jsonify({'error': 'Tournament not found'}), 404


# =============================================================================
# Analytics API Endpoints
# =============================================================================

@app.route('/analytics')
@app.route('/analytics.html')
def analytics_dashboard():
    """Serve the analytics dashboard page."""
    return send_from_directory('../frontend/public', 'analytics.html')


@app.route('/api/analytics/overview')
def get_analytics_overview():
    """Get comprehensive analytics overview."""
    if not DATABASE_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 503

    stats = BattleRepository.get_advanced_statistics()
    return jsonify(stats)


@app.route('/api/analytics/agents')
def get_analytics_agents():
    """Get agent performance statistics."""
    if not DATABASE_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 503

    agents = BattleRepository.get_agent_statistics()
    return jsonify({'agents': agents})


@app.route('/api/analytics/distribution')
def get_analytics_distribution():
    """Get score distribution data."""
    if not DATABASE_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 503

    distribution = BattleRepository.get_score_distribution()
    return jsonify(distribution)


@app.route('/api/analytics/timeline/<battle_id>')
def get_battle_timeline(battle_id):
    """Get score timeline for a specific battle."""
    if not DATABASE_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 503

    timeline = BattleRepository.get_battle_timeline(battle_id)
    return jsonify({'timeline': timeline})


# =============================================================================
# Replay API Endpoints
# =============================================================================

@app.route('/replay')
@app.route('/replay.html')
def replay_dashboard():
    """Serve the replay dashboard page."""
    return send_from_directory('../frontend/public', 'replay.html')


# =============================================================================
# OBS STREAMING INTEGRATION ROUTES
# =============================================================================

@app.route('/obs')
@app.route('/obs/')
def obs_index():
    """Redirect to OBS overlay."""
    return send_from_directory('../frontend/public/obs', 'overlay.html')


@app.route('/obs/overlay')
@app.route('/obs/overlay.html')
def obs_overlay():
    """Serve the full OBS overlay with scores, timer, and gifts."""
    return send_from_directory('../frontend/public/obs', 'overlay.html')


@app.route('/obs/scores')
@app.route('/obs/scores.html')
def obs_scores():
    """Serve the minimal score widget for OBS."""
    return send_from_directory('../frontend/public/obs', 'scores.html')


@app.route('/obs/alerts')
@app.route('/obs/alerts.html')
def obs_alerts():
    """Serve the gift alerts overlay for OBS."""
    return send_from_directory('../frontend/public/obs', 'alerts.html')


@app.route('/obs/setup')
@app.route('/obs/setup.html')
def obs_setup():
    """Serve the OBS setup and configuration page."""
    return send_from_directory('../frontend/public/obs', 'setup.html')


@app.route('/api/replay/list')
def get_replay_list():
    """Get list of battles available for replay."""
    if not DATABASE_AVAILABLE or not ReplayRepository:
        return jsonify({'error': 'Database not available'}), 503

    limit = int(request.args.get('limit', 20))
    replays = ReplayRepository.get_replay_list(limit)
    return jsonify({'replays': replays})


@app.route('/api/replay/<battle_id>')
def get_replay_data(battle_id):
    """Get full replay data for a battle."""
    if not DATABASE_AVAILABLE or not ReplayRepository:
        return jsonify({'error': 'Database not available'}), 503

    replay = ReplayRepository.get_replay_data(battle_id)
    if replay:
        return jsonify(replay)
    return jsonify({'error': 'Replay not found'}), 404


@app.route('/api/replay/<battle_id>/state')
def get_replay_state_at_time(battle_id):
    """Get reconstructed state at a specific time for seeking."""
    if not DATABASE_AVAILABLE or not ReplayRepository:
        return jsonify({'error': 'Database not available'}), 503

    target_time = float(request.args.get('time', 0))
    state = ReplayRepository.get_state_at_time(battle_id, target_time)
    return jsonify(state)


@app.route('/api/replay/<battle_id>/events')
def get_replay_events_range(battle_id):
    """Get events in a time range for partial loading."""
    if not DATABASE_AVAILABLE or not ReplayRepository:
        return jsonify({'error': 'Database not available'}), 503

    start_time = float(request.args.get('start', 0))
    end_time = float(request.args.get('end', 9999))
    events = ReplayRepository.get_replay_events_range(battle_id, start_time, end_time)
    return jsonify({'events': events})


# =============================================================================
# LEADERBOARD API ENDPOINTS
# =============================================================================

@app.route('/leaderboard')
@app.route('/leaderboard.html')
def leaderboard_page():
    """Serve the leaderboard page."""
    return send_from_directory('../frontend/public', 'leaderboard.html')


@app.route('/api/leaderboard/agents')
def get_leaderboard_agents():
    """Get top agents leaderboard."""
    if not DATABASE_AVAILABLE or not LeaderboardRepository:
        return jsonify({'error': 'Database not available'}), 503

    limit = int(request.args.get('limit', 20))
    sort_by = request.args.get('sort', 'total_points')
    agents = LeaderboardRepository.get_top_agents(limit, sort_by)
    return jsonify({'agents': agents})


@app.route('/api/leaderboard/gifters')
def get_leaderboard_gifters():
    """Get top gifters leaderboard."""
    if not DATABASE_AVAILABLE or not LeaderboardRepository:
        return jsonify({'error': 'Database not available'}), 503

    limit = int(request.args.get('limit', 20))
    sort_by = request.args.get('sort', 'total_coins')
    gifters = LeaderboardRepository.get_top_gifters(limit, sort_by)
    return jsonify({'gifters': gifters})


@app.route('/api/leaderboard/summary')
def get_leaderboard_summary():
    """Get leaderboard summary stats."""
    if not DATABASE_AVAILABLE or not LeaderboardRepository:
        return jsonify({'error': 'Database not available'}), 503

    summary = LeaderboardRepository.get_leaderboard_summary()
    return jsonify(summary)


@app.route('/api/leaderboard/agent/<agent_name>')
def get_agent_rank(agent_name):
    """Get specific agent's rank and stats."""
    if not DATABASE_AVAILABLE or not LeaderboardRepository:
        return jsonify({'error': 'Database not available'}), 503

    agent = LeaderboardRepository.get_agent_rank(agent_name)
    if agent:
        return jsonify(agent)
    return jsonify({'error': 'Agent not found'}), 404


@app.route('/api/leaderboard/gifter/<username>')
def get_gifter_rank(username):
    """Get specific gifter's rank and stats."""
    if not DATABASE_AVAILABLE or not LeaderboardRepository:
        return jsonify({'error': 'Database not available'}), 503

    gifter = LeaderboardRepository.get_gifter_rank(username)
    if gifter:
        return jsonify(gifter)
    return jsonify({'error': 'Gifter not found'}), 404


# =============================================================================
# Authentication Routes
# =============================================================================

@app.route('/login', methods=['GET'])
def login_page():
    """Serve login page."""
    if 'user_id' in session:
        return redirect(url_for('index'))
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login - TikTok Battle Simulator</title>
        <style>
            body { font-family: -apple-system, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; margin: 0; }
            .login-box { background: white; padding: 40px; border-radius: 12px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); max-width: 400px; width: 100%; }
            h1 { margin: 0 0 30px; color: #1f2937; text-align: center; }
            input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #d1d5db; border-radius: 8px; box-sizing: border-box; font-size: 16px; }
            button { width: 100%; padding: 12px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; margin-top: 20px; }
            button:hover { opacity: 0.9; }
            .error { color: #ef4444; text-align: center; margin-top: 15px; }
        </style>
    </head>
    <body>
        <div class="login-box">
            <h1>TikTok Battle Simulator</h1>
            <form method="POST" action="/login">
                <input type="text" name="username" placeholder="Username" required>
                <input type="password" name="password" placeholder="Password" required>
                <button type="submit">Login</button>
            </form>
        </div>
    </body>
    </html>
    '''


@app.route('/login', methods=['POST'])
def login():
    """Handle login form submission."""
    username = request.form.get('username')
    password = request.form.get('password')

    user = authenticate_user(username, password)
    if user:
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['is_admin'] = user['is_admin']
        return redirect(url_for('index'))

    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login - TikTok Battle Simulator</title>
        <style>
            body { font-family: -apple-system, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; margin: 0; }
            .login-box { background: white; padding: 40px; border-radius: 12px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); max-width: 400px; width: 100%; }
            h1 { margin: 0 0 30px; color: #1f2937; text-align: center; }
            input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #d1d5db; border-radius: 8px; box-sizing: border-box; font-size: 16px; }
            button { width: 100%; padding: 12px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; margin-top: 20px; }
            button:hover { opacity: 0.9; }
            .error { color: #ef4444; text-align: center; margin-top: 15px; }
        </style>
    </head>
    <body>
        <div class="login-box">
            <h1>TikTok Battle Simulator</h1>
            <form method="POST" action="/login">
                <input type="text" name="username" placeholder="Username" required>
                <input type="password" name="password" placeholder="Password" required>
                <button type="submit">Login</button>
            </form>
            <p class="error">Invalid username or password</p>
        </div>
    </body>
    </html>
    '''


@app.route('/logout')
def logout():
    """Handle logout."""
    session.clear()
    return redirect(url_for('login_page'))


@app.route('/api/auth/status')
def auth_status():
    """Check authentication status."""
    auth_enabled = os.environ.get('AUTH_ENABLED', 'false').lower() == 'true'
    if 'user_id' in session:
        return jsonify({
            'authenticated': True,
            'username': session.get('username'),
            'is_admin': session.get('is_admin', False),
            'auth_enabled': auth_enabled
        })
    return jsonify({
        'authenticated': False,
        'auth_enabled': auth_enabled
    })


# =============================================================================
# API v1 - Versioned Public API
# =============================================================================

api_v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1')


@api_v1.route('/battles/active')
def api_v1_active_battles():
    """API v1: Get active battles."""
    return jsonify({
        'battles': list(active_battles.values()),
        'count': len(active_battles)
    })


@api_v1.route('/battles/history')
def api_v1_battle_history():
    """API v1: Get battle history."""
    limit = min(int(request.args.get('limit', 20)), 100)
    offset = int(request.args.get('offset', 0))

    if DATABASE_AVAILABLE:
        battles = BattleRepository.get_recent_battles(limit)
        return jsonify({'battles': battles[offset:offset+limit], 'total': len(battles)})
    return jsonify({'battles': battle_history[offset:offset+limit], 'total': len(battle_history)})


@api_v1.route('/battles/<battle_id>')
def api_v1_battle_details(battle_id):
    """API v1: Get battle details."""
    battle = active_battles.get(battle_id)
    if not battle and DATABASE_AVAILABLE:
        battle = BattleRepository.get_battle(battle_id)
    if battle:
        return jsonify(battle)
    return jsonify({'error': {'code': 'BATTLE_NOT_FOUND', 'message': 'Battle not found', 'status': 404}}), 404


@api_v1.route('/live/status')
def api_v1_live_status():
    """API v1: Get live battle status."""
    return jsonify({
        'tiktok_live_available': TIKTOK_LIVE_AVAILABLE,
        'active_battle': live_battle_engine is not None,
        'battle_state': live_battle_engine.get_state() if live_battle_engine else None
    })


@api_v1.route('/analytics/overview')
def api_v1_analytics_overview():
    """API v1: Get analytics overview."""
    if DATABASE_AVAILABLE:
        return jsonify(BattleRepository.get_advanced_statistics())
    return jsonify({'error': {'code': 'DATABASE_UNAVAILABLE', 'message': 'Database not available', 'status': 503}}), 503


@api_v1.route('/analytics/agents')
def api_v1_analytics_agents():
    """API v1: Get agent statistics."""
    if DATABASE_AVAILABLE:
        return jsonify({'agents': BattleRepository.get_agent_statistics()})
    return jsonify({'error': {'code': 'DATABASE_UNAVAILABLE', 'message': 'Database not available', 'status': 503}}), 503


@api_v1.route('/analytics/distribution')
def api_v1_analytics_distribution():
    """API v1: Get score distribution."""
    if DATABASE_AVAILABLE:
        return jsonify(BattleRepository.get_score_distribution())
    return jsonify({'error': {'code': 'DATABASE_UNAVAILABLE', 'message': 'Database not available', 'status': 503}}), 503


@api_v1.route('/leaderboard/agents')
def api_v1_leaderboard_agents():
    """API v1: Get top agents."""
    if DATABASE_AVAILABLE and LeaderboardRepository:
        limit = min(int(request.args.get('limit', 20)), 100)
        sort_by = request.args.get('sort', 'total_points')
        return jsonify({'agents': LeaderboardRepository.get_top_agents(limit, sort_by)})
    return jsonify({'error': {'code': 'DATABASE_UNAVAILABLE', 'message': 'Database not available', 'status': 503}}), 503


@api_v1.route('/leaderboard/gifters')
def api_v1_leaderboard_gifters():
    """API v1: Get top gifters."""
    if DATABASE_AVAILABLE and LeaderboardRepository:
        limit = min(int(request.args.get('limit', 20)), 100)
        sort_by = request.args.get('sort', 'total_coins')
        return jsonify({'gifters': LeaderboardRepository.get_top_gifters(limit, sort_by)})
    return jsonify({'error': {'code': 'DATABASE_UNAVAILABLE', 'message': 'Database not available', 'status': 503}}), 503


@api_v1.route('/leaderboard/summary')
def api_v1_leaderboard_summary():
    """API v1: Get leaderboard summary."""
    if DATABASE_AVAILABLE and LeaderboardRepository:
        return jsonify(LeaderboardRepository.get_leaderboard_summary())
    return jsonify({'error': {'code': 'DATABASE_UNAVAILABLE', 'message': 'Database not available', 'status': 503}}), 503


@api_v1.route('/replay/list')
def api_v1_replay_list():
    """API v1: Get replay list."""
    if DATABASE_AVAILABLE and ReplayRepository:
        limit = min(int(request.args.get('limit', 20)), 100)
        return jsonify({'replays': ReplayRepository.get_replay_list(limit)})
    return jsonify({'error': {'code': 'DATABASE_UNAVAILABLE', 'message': 'Database not available', 'status': 503}}), 503


@api_v1.route('/replay/<battle_id>')
def api_v1_replay_data(battle_id):
    """API v1: Get replay data."""
    if DATABASE_AVAILABLE and ReplayRepository:
        replay = ReplayRepository.get_replay_data(battle_id)
        if replay:
            return jsonify(replay)
        return jsonify({'error': {'code': 'REPLAY_NOT_FOUND', 'message': 'Replay not found', 'status': 404}}), 404
    return jsonify({'error': {'code': 'DATABASE_UNAVAILABLE', 'message': 'Database not available', 'status': 503}}), 503


@api_v1.route('/audience/votes')
def api_v1_audience_votes():
    """API v1: Get audience votes."""
    return jsonify({
        'votes': audience_state['votes'],
        'total_viewers': audience_state['total_viewers']
    })


# Register API v1 blueprint
app.register_blueprint(api_v1)


# =============================================================================
# API Documentation / Swagger UI
# =============================================================================

@app.route('/docs')
@app.route('/docs/')
@app.route('/api/docs')
def api_docs():
    """Serve Swagger UI for API documentation."""
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>TikTok Battle Simulator - API Documentation</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
    <style>
        body { margin: 0; background: #fafafa; }
        .swagger-ui .topbar { display: none; }
        .swagger-ui .info { margin: 20px 0; }
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script>
        window.onload = function() {
            SwaggerUIBundle({
                url: "/api/openapi.yaml",
                dom_id: '#swagger-ui',
                presets: [SwaggerUIBundle.presets.apis, SwaggerUIBundle.SwaggerUIStandalonePreset],
                layout: "BaseLayout",
                deepLinking: true,
                docExpansion: "list"
            });
        };
    </script>
</body>
</html>
'''


@app.route('/api/openapi.yaml')
@app.route('/api/openapi.json')
def api_openapi_spec():
    """Serve OpenAPI specification."""
    spec_path = os.path.join(os.path.dirname(__file__), '../../docs/api/openapi.yaml')
    try:
        with open(spec_path, 'r') as f:
            spec = yaml.safe_load(f)
        if request.path.endswith('.json'):
            return jsonify(spec)
        return app.response_class(
            response=yaml.dump(spec),
            status=200,
            mimetype='application/x-yaml'
        )
    except Exception as e:
        return jsonify({'error': f'Could not load OpenAPI spec: {e}'}), 500


@app.route('/api')
@app.route('/api/')
def api_info():
    """API information endpoint."""
    return jsonify({
        'name': 'TikTok Battle Simulator API',
        'version': '1.0.0',
        'documentation': '/docs',
        'openapi_spec': '/api/openapi.yaml',
        'endpoints': {
            'v1': '/api/v1'
        },
        'websocket': {
            'url': 'ws://localhost:5000',
            'events': ['battle_start', 'battle_tick', 'battle_end', 'gift_sent', 'phase_change']
        }
    })


# =============================================================================
# Legal Pages (Required for TikTok Developer Portal)
# =============================================================================

@app.route('/privacy')
@app.route('/privacy-policy')
def privacy_policy():
    """Serve Privacy Policy page."""
    import markdown
    policy_path = os.path.join(os.path.dirname(__file__), '../../docs/legal/PRIVACY_POLICY.md')
    try:
        with open(policy_path, 'r') as f:
            content = f.read()
        html_content = markdown.markdown(content, extensions=['tables', 'fenced_code'])
        return f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Privacy Policy - TikTok Battle Simulator</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 40px 20px; line-height: 1.6; color: #1f2937; background: #f9fafb; }}
        h1 {{ color: #111827; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; }}
        h2 {{ color: #374151; margin-top: 30px; }}
        h3 {{ color: #4b5563; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #d1d5db; padding: 12px; text-align: left; }}
        th {{ background: #f3f4f6; font-weight: 600; }}
        a {{ color: #2563eb; }}
        hr {{ border: none; border-top: 1px solid #e5e7eb; margin: 30px 0; }}
        .back-link {{ display: inline-block; margin-bottom: 20px; color: #6b7280; text-decoration: none; }}
        .back-link:hover {{ color: #374151; }}
    </style>
</head>
<body>
    <a href="/" class="back-link">&larr; Back to App</a>
    {html_content}
</body>
</html>
'''
    except Exception as e:
        return f'<h1>Privacy Policy</h1><p>Error loading content: {e}</p>', 500


@app.route('/terms')
@app.route('/terms-of-service')
def terms_of_service():
    """Serve Terms of Service page."""
    import markdown
    tos_path = os.path.join(os.path.dirname(__file__), '../../docs/legal/TERMS_OF_SERVICE.md')
    try:
        with open(tos_path, 'r') as f:
            content = f.read()
        html_content = markdown.markdown(content, extensions=['tables', 'fenced_code'])
        return f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Terms of Service - TikTok Battle Simulator</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 40px 20px; line-height: 1.6; color: #1f2937; background: #f9fafb; }}
        h1 {{ color: #111827; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; }}
        h2 {{ color: #374151; margin-top: 30px; }}
        h3 {{ color: #4b5563; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #d1d5db; padding: 12px; text-align: left; }}
        th {{ background: #f3f4f6; font-weight: 600; }}
        a {{ color: #2563eb; }}
        hr {{ border: none; border-top: 1px solid #e5e7eb; margin: 30px 0; }}
        .back-link {{ display: inline-block; margin-bottom: 20px; color: #6b7280; text-decoration: none; }}
        .back-link:hover {{ color: #374151; }}
    </style>
</head>
<body>
    <a href="/" class="back-link">&larr; Back to App</a>
    {html_content}
</body>
</html>
'''
    except Exception as e:
        return f'<h1>Terms of Service</h1><p>Error loading content: {e}</p>', 500


# =============================================================================
# Server Runner
# =============================================================================

def run_server(host='0.0.0.0', port=5000, debug=None):
    """Run the Flask-SocketIO server."""
    # Initialize default admin if auth is enabled
    if os.environ.get('AUTH_ENABLED', 'false').lower() == 'true':
        init_default_admin()

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
