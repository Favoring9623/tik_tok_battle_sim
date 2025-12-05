"""
Web Battle Demo - Battle with Real-time Web Dashboard Streaming

Watch your GPT battles in a beautiful web interface!

Usage:
    1. Terminal 1: python3 demo_web_battle.py server
       (Starts the web dashboard server)

    2. Terminal 2: Open http://localhost:5000 in your browser

    3. Terminal 3: python3 demo_web_battle.py battle
       (Runs a battle that streams to the dashboard)

Or run everything with:
    python3 demo_web_battle.py
"""

import sys
import os
import time
import threading
from multiprocessing import Process

# Add web backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'web/backend'))

from core.battle_engine import BattleEngine
from agents.personas.gpt_personas import create_gpt_persona_team


def run_web_server():
    """Run the Flask-SocketIO web server."""
    from web.backend.app import run_server
    print("\n🌐 Starting Web Dashboard Server...")
    run_server(host='0.0.0.0', port=5000, debug=False)


def run_streamed_battle():
    """Run a battle that streams to the web dashboard."""
    print("\n" + "="*70)
    print("🎭 STREAMING BATTLE TO WEB DASHBOARD")
    print("="*70 + "\n")

    print("📡 Connecting to web dashboard...")
    time.sleep(2)  # Give server time to start

    # Import after server is ready
    from web.backend.app import (
        broadcast_battle_start,
        broadcast_battle_tick,
        broadcast_agent_action,
        broadcast_battle_end,
        socketio
    )

    print("✅ Connected to dashboard at http://localhost:5000\n")

    # Create battle
    print("🎬 Creating battle with GPT persona agents...\n")
    engine = BattleEngine(
        battle_duration=60,
        tick_speed=0.2,  # Slightly slower for web viewing
        enable_multipliers=True,
        enable_analytics=True
    )

    # Add GPT persona team
    agents = create_gpt_persona_team()
    for agent in agents:
        engine.add_agent(agent)
        print(f"   ✓ {agent.emoji} {agent.name}")

    print(f"\n{'='*70}")
    print("🚀 BATTLE START - Watch in browser!")
    print(f"{'='*70}\n")

    # Broadcast battle start
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
    broadcast_battle_start(battle_data)

    # Custom tick handler to broadcast
    original_tick = engine._tick

    def web_tick(silent=False):
        original_tick(silent)
        current_time = engine.time_manager.current_time

        # Broadcast tick update
        current_mult = engine.multiplier_manager.get_current_multiplier()
        tick_data = {
            'time': current_time,
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
        broadcast_battle_tick(battle_id, tick_data)

    engine._tick = web_tick

    # Wrap agent actions to broadcast
    for agent in agents:
        def make_wrapped_send_gift(agent_ref, original_method):
            def wrapped_send_gift(battle, gift_type, points):
                # Call original
                original_method(battle, gift_type, points)

                # Broadcast action
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

    # Broadcast battle end
    winner = engine.analytics.winner
    final_scores = engine.analytics.final_scores
    performance = engine.analytics.get_agent_performance()

    result_data = {
        'winner': winner,
        'final_scores': final_scores,
        'duration': engine.time_manager.current_time,
        'agent_performance': performance
    }
    broadcast_battle_end(battle_id, result_data)

    print(f"\n{'='*70}")
    print("✅ BATTLE COMPLETE!")
    print(f"{'='*70}")
    print(f"\n🏆 Winner: {winner.upper()}")
    print(f"📊 Final Score: Creator {final_scores['creator']:,} vs Opponent {final_scores['opponent']:,}")
    print(f"\n💡 Check the web dashboard for detailed analytics!\n")


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        command = sys.argv[1]

        if command == 'server':
            # Just run server
            run_web_server()

        elif command == 'battle':
            # Just run battle (assumes server is already running)
            run_streamed_battle()

        else:
            print(f"Unknown command: {command}")
            print("Usage: python3 demo_web_battle.py [server|battle]")
            sys.exit(1)

    else:
        # Run both server and battle
        print("\n" + "="*70)
        print("🌐 TikTok Battle Web Dashboard Demo")
        print("="*70)
        print("\n📋 Starting in combined mode:")
        print("   1. Web server at http://localhost:5000")
        print("   2. Battle streaming to dashboard")
        print("\n⏳ Starting server...")

        # Start server in separate process
        server_process = Process(target=run_web_server)
        server_process.start()

        # Wait for server to start
        print("⏳ Waiting for server to initialize (5 seconds)...")
        time.sleep(5)

        print("\n🌐 Server ready! Open http://localhost:5000 in your browser")
        print("⏳ Waiting for browser connection...")
        print("   (Open the URL above, then press Enter when you see 🟢 Connected)\n")
        input("Press Enter when browser is connected and ready...")
        print("\n⏳ Starting battle in 2 seconds...\n")
        time.sleep(2)

        try:
            # Run battle in main process
            run_streamed_battle()

            # Keep server running
            print("\n✨ Battle complete! Server still running.")
            print("📺 Keep the browser open to see the results.")
            print("🛑 Press Ctrl+C to stop the server.\n")

            server_process.join()

        except KeyboardInterrupt:
            print("\n\n🛑 Shutting down...")
            server_process.terminate()
            server_process.join()
            print("✅ Goodbye!\n")


if __name__ == '__main__':
    main()
