"""
Web Tournament Demo - Tournament Streaming to Dashboard

Runs a full tournament with real-time streaming to the web dashboard.

Features:
- Tournament bracket visualization
- Series momentum tracking
- Live battle updates
- Tournament statistics

Usage:
    python3 demo_web_tournament.py

    Then open http://localhost:5000/tournament.html in your browser
"""

import sys
import os
import uuid

# Add web backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'web/backend'))

from core.battle_engine import BattleEngine
from core.tournament_system import TournamentManager, TournamentFormat
from core.tournament_bracket import TournamentBracket
from core.tournament_momentum import MomentumTracker
from agents.personas import NovaWhale, PixelPixie, GlitchMancer


def run_tournament_after_delay(delay=3):
    """Run tournament after a delay to let server start and browser connect."""
    from web.backend.app import socketio

    print(f"\n⏳ Tournament will start in {delay} seconds...")
    print("📺 Open http://localhost:5000/tournament.html NOW and wait for 🟢 Connected\n")

    socketio.sleep(delay)

    print("\n" + "="*70)
    print("🏆 STARTING TOURNAMENT - BEST OF 3")
    print("="*70 + "\n")

    # Import broadcast functions
    from web.backend.app import (
        broadcast_tournament_start,
        broadcast_tournament_series_update,
        broadcast_tournament_bracket_update,
        broadcast_tournament_momentum_update,
        broadcast_tournament_end,
        broadcast_battle_start,
        broadcast_battle_tick,
        broadcast_agent_action,
        broadcast_battle_end
    )

    # Initialize tournament systems
    tournament = TournamentManager(
        format=TournamentFormat.BEST_OF_3,
        total_budget=250000,
        battle_duration=60
    )

    bracket = TournamentBracket(
        format_name="BEST_OF_3",
        battles_to_win=2
    )

    momentum = MomentumTracker(battles_to_win=2)

    # Create tournament ID
    tournament_id = str(uuid.uuid4())

    # Start tournament
    tournament.start_tournament()

    # Broadcast tournament start
    tournament_data = {
        'id': tournament_id,
        'format': 'BEST_OF_3',
        'battles_to_win': 2,
        'creator_wins': 0,
        'opponent_wins': 0,
        'status': 'active'
    }

    print("🔊 Broadcasting tournament start...")
    broadcast_tournament_start(tournament_data)
    socketio.sleep(2)

    battle_num = 0

    # Run battles until tournament complete
    while tournament.can_continue():
        battle_num += 1

        print(f"\n{'='*70}")
        print(f"⚔️  BATTLE {battle_num} STARTING")
        print(f"{'='*70}\n")

        # Show series status
        print(f"📊 Series: Creator {tournament.creator_wins} - {tournament.opponent_wins} Opponent")

        # Create battle engine
        engine = BattleEngine(
            battle_duration=tournament.battle_duration,
            tick_speed=0.2,
            enable_multipliers=True,
            enable_analytics=True
        )

        # Add creator team agents
        engine.add_agent(NovaWhale())
        engine.add_agent(PixelPixie())

        # Add opponent team agent
        engine.add_agent(GlitchMancer())

        # Create battle ID and data
        battle_id = str(uuid.uuid4())
        agents = [NovaWhale(), PixelPixie(), GlitchMancer()]

        battle_data = {
            'id': battle_id,
            'status': 'active',
            'duration': tournament.battle_duration,
            'agents': [
                {
                    'name': agent.name,
                    'emoji': agent.emoji,
                    'total_donated': 0,
                    'gifts_sent': 0
                } for agent in agents
            ],
            'current_time': 0,
            'scores': {'creator': 0, 'opponent': 0}
        }

        # Broadcast battle start
        print(f"🔊 Broadcasting battle {battle_num} start...")
        broadcast_battle_start(battle_data)

        # Wrap tick for streaming
        original_tick = engine._tick

        def web_tick(silent=False):
            original_tick(silent)
            current_mult = engine.multiplier_manager.get_current_multiplier()
            tick_data = {
                'time': engine.time_manager.current_time,
                'scores': {
                    'creator': engine.score_tracker.creator_score,
                    'opponent': engine.score_tracker.opponent_score
                },
                'leader': engine.score_tracker.get_leader() or 'tied',
                'time_remaining': engine.time_manager.time_remaining(),
                'multiplier': {
                    'active': current_mult.value > 1.0,
                    'value': current_mult.value,
                    'type': current_mult.name
                }
            }

            # Debug output every 10 seconds
            if int(engine.time_manager.current_time) % 10 == 0 and engine.time_manager.current_time > 0:
                print(f"   📊 {engine.time_manager.current_time}s - Creator {tick_data['scores']['creator']:,} vs Opponent {tick_data['scores']['opponent']:,}")

            broadcast_battle_tick(battle_id, tick_data)
            socketio.sleep(0)  # Yield to event loop

        engine._tick = web_tick

        # Wrap agent actions
        for agent in agents:
            def make_wrapped_send_gift(agent_ref, original_method):
                def wrapped_send_gift(battle, gift_type, points):
                    original_method(battle, gift_type, points)
                    action_data = {
                        'agent_name': agent_ref.name,
                        'agent_emoji': agent_ref.emoji,
                        'action_type': 'gift',
                        'gift_type': gift_type,
                        'points': points,
                        'timestamp': engine.time_manager.current_time
                    }
                    broadcast_agent_action(battle_id, action_data)
                return wrapped_send_gift

            agent.send_gift = make_wrapped_send_gift(agent, agent.send_gift)

        # Run battle
        engine.run(silent=False)

        # Get results
        winner = engine.analytics.winner
        creator_score = engine.analytics.final_scores['creator']
        opponent_score = engine.analytics.final_scores['opponent']
        agent_performance = engine.analytics.get_agent_performance()

        # Broadcast battle end
        result_data = {
            'winner': winner,
            'final_scores': engine.analytics.final_scores,
            'duration': engine.time_manager.current_time,
            'agent_performance': agent_performance
        }
        broadcast_battle_end(battle_id, result_data)

        print(f"\n🏁 Battle {battle_num} Complete: {winner.upper()} wins!")
        print(f"   Creator: {creator_score:,} | Opponent: {opponent_score:,}")

        # Record in tournament systems
        tournament.record_battle_result(
            winner=winner,
            creator_score=creator_score,
            opponent_score=opponent_score,
            budget_spent_this_battle=0,
            agent_performance=agent_performance
        )

        bracket.add_battle_result(
            battle_num=battle_num,
            creator_score=creator_score,
            opponent_score=opponent_score,
            winner=winner
        )

        momentum.record_battle(
            battle_num=battle_num,
            winner=winner,
            creator_score=creator_score,
            opponent_score=opponent_score
        )

        # Broadcast tournament updates
        series_data = {
            'creator_wins': tournament.creator_wins,
            'opponent_wins': tournament.opponent_wins,
            'battle_num': battle_num
        }
        print(f"🔊 Broadcasting series update: {tournament.creator_wins}-{tournament.opponent_wins}")
        broadcast_tournament_series_update(series_data)

        # Broadcast bracket update
        bracket_data = {
            'battles': [
                {
                    'battle_num': b.battle_num,
                    'creator_score': b.creator_score,
                    'opponent_score': b.opponent_score,
                    'winner': b.winner
                }
                for b in bracket.battles
            ]
        }
        print(f"🔊 Broadcasting bracket update")
        broadcast_tournament_bracket_update(bracket_data)

        # Broadcast momentum update
        momentum_data = momentum.get_momentum_state()
        print(f"🔊 Broadcasting momentum update")
        broadcast_tournament_momentum_update(momentum_data)

        socketio.sleep(3)  # Pause between battles

    # Tournament complete
    print("\n" + "🏆"*35)
    print("TOURNAMENT COMPLETE!")
    print("🏆"*35 + "\n")

    tournament_winner = tournament.tournament_winner
    print(f"🏆 WINNER: {tournament_winner.upper()}")
    print(f"📊 Series: Creator {tournament.creator_wins} - {tournament.opponent_wins} Opponent")

    # Broadcast tournament end
    tournament_result = {
        'winner': tournament_winner,
        'creator_wins': tournament.creator_wins,
        'opponent_wins': tournament.opponent_wins,
        'total_battles': battle_num
    }
    print(f"🔊 Broadcasting tournament end")
    broadcast_tournament_end(tournament_id, tournament_result)

    print("\n💡 Check the browser for full tournament visualization!\n")


def main():
    """Main entry point."""
    print("\n" + "="*70)
    print("🏆 TikTok Tournament Web Dashboard")
    print("="*70)
    print("\n✨ Starting server and tournament in same process")
    print("📺 Open http://localhost:5000/tournament.html in your browser NOW!\n")

    # Import app components
    from web.backend.app import set_battle_start_callback

    # Set callback to start tournament when first client connects
    def delayed_tournament():
        run_tournament_after_delay(delay=3)

    set_battle_start_callback(delayed_tournament)
    print("⚙️  Tournament will start when you connect to the dashboard\n")

    # Run Flask server in main thread (blocking)
    print("🌐 Starting Flask server...\n")
    from web.backend.app import run_server

    try:
        run_server(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down...")
        print("✅ Goodbye!\n")


if __name__ == '__main__':
    main()
