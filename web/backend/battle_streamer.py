"""
Battle Streamer - Streams battle events to web dashboard

Integrates with BattleEngine to capture and broadcast events in real-time.
"""

import uuid
from typing import Optional, Dict, Any
from datetime import datetime


class BattleStreamer:
    """
    Streams battle events to the web dashboard.

    Usage:
        streamer = BattleStreamer()
        engine = BattleEngine(battle_duration=60)
        engine.add_event_listener(streamer)
        engine.run()
    """

    def __init__(self, broadcast_callback=None):
        """
        Initialize battle streamer.

        Args:
            broadcast_callback: Optional callback for broadcasting events
                              (useful for testing without SocketIO)
        """
        self.broadcast = broadcast_callback
        self.battle_id = None
        self.battle_data = {}
        self.events = []

    def on_battle_start(self, battle):
        """Called when battle starts."""
        self.battle_id = str(uuid.uuid4())
        self.battle_data = {
            'id': self.battle_id,
            'status': 'active',
            'duration': battle.time_manager.duration,
            'start_time': datetime.now().isoformat(),
            'agents': [],
            'current_time': 0,
            'scores': {
                'creator': 0,
                'opponent': 0
            },
            'multiplier': {
                'active': False,
                'type': None,
                'value': 1.0
            }
        }

        # Collect agent info
        for agent in battle.agents:
            self.battle_data['agents'].append({
                'name': agent.name,
                'emoji': agent.emoji,
                'total_donated': 0,
                'gifts_sent': 0,
                'emotion': 'CALM'
            })

        if self.broadcast:
            from web.backend.app import broadcast_battle_start
            broadcast_battle_start(self.battle_data)

    def on_tick(self, battle, current_time):
        """Called every tick."""
        tick_data = {
            'time': current_time,
            'scores': {
                'creator': battle.score_tracker.creator_score,
                'opponent': battle.score_tracker.opponent_score
            },
            'leader': battle.score_tracker.get_leader() or 'tied',
            'time_remaining': battle.time_manager.time_remaining()
        }

        # Check multiplier status
        current_mult = battle.multiplier_system.get_current_multiplier()
        tick_data['multiplier'] = {
            'active': current_mult.value > 1.0,
            'value': current_mult.value,
            'type': current_mult.name
        }

        if self.broadcast:
            from web.backend.app import broadcast_battle_tick
            broadcast_battle_tick(self.battle_id, tick_data)

    def on_agent_action(self, agent, action_type, details):
        """Called when agent performs action."""
        action_data = {
            'agent_name': agent.name,
            'agent_emoji': agent.emoji,
            'action_type': action_type,  # 'gift', 'message', 'item_use'
            'timestamp': self.battle_data.get('current_time', 0),
            **details
        }

        self.events.append(action_data)

        if self.broadcast:
            from web.backend.app import broadcast_agent_action
            broadcast_agent_action(self.battle_id, action_data)

    def on_battle_end(self, battle):
        """Called when battle ends."""
        # Get final analytics
        winner = battle.analytics.winner
        final_scores = battle.analytics.final_scores
        performance = battle.analytics.get_agent_performance()

        result_data = {
            'winner': winner,
            'final_scores': final_scores,
            'duration': battle.time_manager.current_time,
            'end_time': datetime.now().isoformat(),
            'agent_performance': performance,
            'total_events': len(self.events)
        }

        if self.broadcast:
            from web.backend.app import broadcast_battle_end
            broadcast_battle_end(self.battle_id, result_data)

        return result_data


def create_streamed_battle(battle_engine, enable_broadcast=True):
    """
    Create a battle engine with streaming enabled.

    Args:
        battle_engine: BattleEngine instance
        enable_broadcast: Whether to broadcast to web dashboard

    Returns:
        Tuple of (engine, streamer)
    """
    streamer = BattleStreamer(broadcast_callback=enable_broadcast)

    # Hook into battle engine events
    # Note: This requires adding event listener support to BattleEngine
    # For now, we'll create a wrapper

    return battle_engine, streamer
