"""
Simple Web Battle Demo - Everything in one process

This version runs the server and battle in the same process using threading,
so WebSocket events work properly!

Usage:
    python3 demo_web_battle_simple.py

    Then open http://localhost:5000 in your browser
"""

import sys
import os
import time
import threading

# Add web backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'web/backend'))

from core.battle_engine import BattleEngine
from agents.personas.gpt_personas import create_gpt_persona_team


def run_battle_after_delay(delay=8):
    """Run battle after a delay to let server start and browser connect."""
    from web.backend.app import socketio

    print(f"\n⏳ Battle will start in {delay} seconds...")
    print("📺 Open http://localhost:5000 NOW and wait for 🟢 Connected\n")

    socketio.sleep(delay)  # Use socketio.sleep for eventlet/gevent compatibility

    print("\n" + "="*70)
    print("🎭 STARTING STREAMED BATTLE")
    print("="*70 + "\n")

    # Import here to use the same socketio instance
    from web.backend.app import (
        broadcast_battle_start,
        broadcast_battle_tick,
        broadcast_agent_action,
        broadcast_battle_end
    )

    # Create battle
    print("🎬 Creating battle...\n")
    engine = BattleEngine(
        battle_duration=60,
        tick_speed=0.2,
        enable_multipliers=True,
        enable_analytics=True
    )

    # Add agents
    agents = create_gpt_persona_team()
    for agent in agents:
        engine.add_agent(agent)
        print(f"   ✓ {agent.emoji} {agent.name}")

    print(f"\n{'='*70}")
    print("🚀 BATTLE START - Watch in browser!")
    print(f"{'='*70}\n")

    # Create battle ID and data
    import uuid
    battle_id = str(uuid.uuid4())
    battle_data = {
        'id': battle_id,
        'status': 'active',
        'duration': 60,
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

    # Broadcast start
    print("🔊 Broadcasting battle start...")
    broadcast_battle_start(battle_data)

    # Import socketio for sleep
    from web.backend.app import socketio

    # Wrap tick
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

        # Debug output every 5 seconds
        if int(engine.time_manager.current_time) % 5 == 0 and engine.time_manager.current_time > 0:
            print(f"   📊 {engine.time_manager.current_time}s - Broadcasting: Creator {tick_data['scores']['creator']:,} vs Opponent {tick_data['scores']['opponent']:,}")

        broadcast_battle_tick(battle_id, tick_data)

        # CRITICAL: Allow Flask to process the event!
        socketio.sleep(0)

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
                print(f"   🎁 {agent_ref.emoji} {agent_ref.name} sent {gift_type} (+{points} pts)")
                broadcast_agent_action(battle_id, action_data)
            return wrapped_send_gift

        agent.send_gift = make_wrapped_send_gift(agent, agent.send_gift)

    # Run battle
    engine.run(silent=False)

    # Broadcast end
    result_data = {
        'winner': engine.analytics.winner,
        'final_scores': engine.analytics.final_scores,
        'duration': engine.time_manager.current_time,
        'agent_performance': engine.analytics.get_agent_performance()
    }
    broadcast_battle_end(battle_id, result_data)

    print(f"\n{'='*70}")
    print("✅ BATTLE COMPLETE!")
    print(f"{'='*70}")
    print(f"🏆 Winner: {engine.analytics.winner.upper()}")
    print(f"📊 Score: {engine.analytics.final_scores}")
    print("\n💡 Check the browser for full visualization!\n")


def main():
    """Main entry point."""
    print("\n" + "="*70)
    print("🌐 TikTok Battle Web Dashboard - Simple Mode")
    print("="*70)
    print("\n✨ Starting server and battle in same process")
    print("📺 Open http://localhost:5000 in your browser NOW!\n")

    # Import app components
    from web.backend.app import set_battle_start_callback

    # Set callback to start battle when first client connects
    def delayed_battle():
        run_battle_after_delay(delay=3)

    set_battle_start_callback(delayed_battle)
    print("⚙️  Battle will start when you connect to the dashboard\n")

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
