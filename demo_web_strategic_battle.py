"""
Web Strategic Battle Demo

Streams a complete strategic battle to the web dashboard with:
- Real-time phase transitions
- GPT-4 commentary
- Agent evolution stats
- Power-up activations
- Glove mechanics visualization
"""

import sys
import os
import time

# Ensure we can import from project root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from core.battle_engine import BattleEngine
from core.advanced_phase_system import AdvancedPhaseManager, PowerUpType
from core.battle_history import BattleHistoryDB, generate_battle_id
from core.budget_system import BudgetManager, BudgetIntelligence
from agents.evolving_agents import create_mixed_strategic_team, reset_evolving_team, learn_from_battle_results
from agents.gpt_strategic_agents import GPTStrategicNarrator
from agents.opponent_ai import OpponentAI


def run_web_strategic_battle():
    """Run strategic battle with web streaming."""

    # Import web backend
    from web.backend.app import (
        socketio, run_server, set_battle_start_callback,
        broadcast_strategic_battle_start,
        broadcast_battle_tick,
        broadcast_agent_action,
        broadcast_phase_change,
        broadcast_boost_condition_update,
        broadcast_glove_event,
        broadcast_powerup_used,
        broadcast_gpt_commentary,
        broadcast_strategic_battle_end
    )

    def run_battle_after_connect():
        """Run the strategic battle after client connects."""
        time.sleep(2)  # Wait for client to be ready

        print("\n" + "🌐"*35)
        print("WEB STRATEGIC BATTLE STARTING")
        print("🌐"*35 + "\n")

        # Initialize components
        battle_id = generate_battle_id()
        db = BattleHistoryDB("data/web_battle_history.db")

        # Create GPT narrator
        gpt_narrator = GPTStrategicNarrator()

        # Create phase manager (300 seconds = 5 minutes)
        # ENIGMA MODE: Boost #2 details hidden until dramatic reveal!
        phase_manager = AdvancedPhaseManager(battle_duration=300, enigma_mode=True)

        # Creator power-ups: Glove (x2), Hammer, Fog, Time Bonus
        phase_manager.add_power_up(PowerUpType.GLOVE, "creator")
        phase_manager.add_power_up(PowerUpType.GLOVE, "creator")  # 2 gloves available
        phase_manager.add_power_up(PowerUpType.HAMMER, "creator")
        phase_manager.add_power_up(PowerUpType.FOG, "creator")
        phase_manager.add_power_up(PowerUpType.TIME_BONUS, "creator")

        # Opponent power-ups: Glove (x2), Hammer
        phase_manager.add_power_up(PowerUpType.GLOVE, "opponent")
        phase_manager.add_power_up(PowerUpType.GLOVE, "opponent")
        phase_manager.add_power_up(PowerUpType.HAMMER, "opponent")

        # Create budget manager with random starting budgets
        budget_manager = BudgetManager()
        print(f"\n💰 BUDGET ALLOCATED:")
        print(f"   Creator: {budget_manager.creator_starting:,} coins")
        print(f"   Opponent: {budget_manager.opponent_starting:,} coins\n")

        # Create budget intelligence for adaptive strategy
        budget_intelligence = BudgetIntelligence(budget_manager, team="creator")

        # Create smart opponent AI (medium difficulty) with budget awareness
        opponent_ai = OpponentAI(phase_manager, difficulty="medium", budget_manager=budget_manager)

        # Create mixed strategic team (strategic + persona agents)
        team = create_mixed_strategic_team(phase_manager, db=db, budget_intelligence=budget_intelligence)

        # Give all agents access to budget manager
        for agent in team:
            agent.budget_manager = budget_manager
            agent.team = "creator"  # All agents donate to creator

        # Get GPT pre-battle analysis
        gpt_analysis = ""
        if gpt_narrator.enabled:
            try:
                gpt_analysis = gpt_narrator.generate_pre_battle_analysis(team, 180)
            except Exception as e:
                gpt_analysis = f"Strategic battle with evolving agents beginning..."

        # Broadcast battle start with boost and budget info
        boost1_status = phase_manager.get_boost1_status()
        boost2_status = phase_manager.get_boost2_status()
        broadcast_strategic_battle_start({
            'id': battle_id,
            'duration': 300,
            'gpt_analysis': gpt_analysis,
            'agents': [{'name': a.name, 'emoji': a.emoji, 'type': a.agent_type} for a in team],
            'boost1_will_trigger': boost1_status['will_trigger'],
            'boost1_trigger_time': boost1_status['trigger_time'],
            'boost1_multiplier': boost1_status['multiplier'],
            'boost2_will_trigger': boost2_status['will_trigger'],
            'boost2_trigger_time': boost2_status['trigger_time'],
            'boost2_threshold': boost2_status['threshold'],
            'boost2_multiplier': boost2_status['multiplier'],
            # Budget info
            'creator_budget': budget_manager.creator_starting,
            'opponent_budget': budget_manager.opponent_starting
        })

        # Create battle engine (300 seconds = 5 minutes)
        engine = BattleEngine(
            battle_duration=300,
            tick_speed=0.5,  # Half speed for better visualization
            enable_multipliers=False,
            enable_analytics=True
        )

        # Add agents
        for agent in team:
            engine.add_agent(agent)

        # Track state for broadcasts
        last_phase_name = None
        last_roses = 0
        last_points = 0
        gloves_sent = 0
        gloves_activated = 0
        last_glove_active = False

        # Track Boost #1 for budget intelligence analysis
        boost1_started = False
        boost1_scores_before = {'creator': 0, 'opponent': 0}

        # Wrap tick for broadcasting
        original_tick = engine._tick

        def wrapped_tick(silent):
            nonlocal last_phase_name, last_roses, last_points, gloves_sent, gloves_activated, last_glove_active

            # Call original tick
            original_tick(silent)

            current_time = engine.time_manager.current_time
            time_remaining = engine.time_manager.time_remaining()

            # Update phase manager
            phase_manager.update(current_time)

            # Sync scores for glove bonus calculations
            phase_manager.update_scores(
                engine.score_tracker.creator_score,
                engine.score_tracker.opponent_score
            )

            # Sync engine duration with phase manager (for time bonus)
            if engine.time_manager.battle_duration != phase_manager.battle_duration:
                engine.time_manager.battle_duration = phase_manager.battle_duration
                print(f"⏱️  Engine synced to new duration: {phase_manager.battle_duration}s")

            # Smart opponent AI decisions
            opponent_result = opponent_ai.update(
                current_time,
                engine.score_tracker.creator_score,
                engine.score_tracker.opponent_score
            )

            # Apply opponent gift to score
            if opponent_result["gift_sent"]:
                engine.score_tracker.opponent_score += opponent_result["gift_points"]

            # Broadcast opponent power-up usage
            if opponent_result["power_up_used"]:
                if opponent_result["power_up_used"] == "GLOVE":
                    broadcast_glove_event({
                        'total_sent': opponent_ai.gloves_used,
                        'total_activated': opponent_ai.gloves_used,
                        'activated': phase_manager.active_glove_owner == "opponent",
                        'team': 'opponent'
                    })

            # Get budget status
            creator_budget_status = budget_manager.get_status("creator")
            opponent_budget_status = budget_manager.get_status("opponent")

            # Broadcast tick with budget info
            broadcast_battle_tick(battle_id, {
                'time': current_time,
                'duration': phase_manager.battle_duration,  # May change with time bonus
                'creator_score': engine.score_tracker.creator_score,
                'opponent_score': engine.score_tracker.opponent_score,
                'scores': {
                    'creator': engine.score_tracker.creator_score,
                    'opponent': engine.score_tracker.opponent_score
                },
                # Budget info
                'creator_budget': creator_budget_status['current'],
                'opponent_budget': opponent_budget_status['current'],
                'creator_budget_tier': creator_budget_status['tier'],
                'opponent_budget_tier': opponent_budget_status['tier'],
                'creator_budget_pct': creator_budget_status['percentage'],
                'opponent_budget_pct': opponent_budget_status['percentage']
            })

            # Check for phase changes
            phase_info = phase_manager.get_phase_info()
            current_phase = phase_info.get('name', '')

            if current_phase != last_phase_name:
                last_phase_name = current_phase

                # Get GPT commentary for phase change
                gpt_comment = ""
                if gpt_narrator.enabled:
                    try:
                        score_diff = abs(
                            engine.score_tracker.creator_score -
                            engine.score_tracker.opponent_score
                        )
                        gpt_comment = gpt_narrator.comment_on_phase_transition(
                            current_phase,
                            phase_info.get('multiplier', 1.0),
                            current_time,
                            score_diff
                        )
                    except:
                        pass

                # Use base_multiplier for phase display (without glove stacking)
                base_mult = phase_info.get('base_multiplier', 1.0)
                broadcast_phase_change({
                    'name': current_phase,
                    'multiplier': base_mult,
                    'time_remaining': time_remaining,
                    'gpt_commentary': gpt_comment
                })

            # Check boost #1 and #2 status
            boost1_status = phase_manager.get_boost1_status()
            boost2_status = phase_manager.get_boost2_status()
            creator_points = boost2_status['creator_points']
            opponent_points = boost2_status['opponent_points']

            # === BOOST #1 INTELLIGENCE ANALYSIS ===
            nonlocal boost1_started, boost1_scores_before

            # Detect Boost #1 start - save scores
            if boost1_status['active'] and not boost1_started:
                boost1_started = True
                boost1_scores_before = {
                    'creator': engine.score_tracker.creator_score,
                    'opponent': engine.score_tracker.opponent_score
                }
                print(f"🧠 Budget Intelligence: Tracking Boost #1 start - Creator: {boost1_scores_before['creator']:,}, Opponent: {boost1_scores_before['opponent']:,}")

            # Detect Boost #1 end - analyze response
            if boost1_started and not boost1_status['active'] and not budget_intelligence.boost1_completed:
                budget_intelligence.analyze_boost1_response(
                    our_score_before=boost1_scores_before['creator'],
                    our_score_after=engine.score_tracker.creator_score,
                    opponent_score_before=boost1_scores_before['opponent'],
                    opponent_score_after=engine.score_tracker.opponent_score
                )
                print(f"🧠 Budget Intelligence: Boost #1 ended - Creator gained {engine.score_tracker.creator_score - boost1_scores_before['creator']:,}, Opponent gained {engine.score_tracker.opponent_score - boost1_scores_before['opponent']:,}")

            # Detect Boost #2 end - release reserved budget
            if boost2_status['active'] and not budget_intelligence.boost2_completed:
                pass  # Wait for boost to end
            elif phase_manager.boost2_triggered and not boost2_status['active'] and not budget_intelligence.boost2_completed:
                budget_intelligence.mark_boost2_complete()

            # Broadcast boost status updates (every tick for enigma mode timing)
            # Always send for early warning tracking, not just when points change
            should_broadcast = (
                creator_points != last_roses or
                opponent_points != last_points or
                current_time % 5 == 0  # Also broadcast every 5 seconds for enigma timing
            )
            if should_broadcast:
                last_roses = creator_points
                last_points = opponent_points
                broadcast_boost_condition_update({
                    # Boost #1 info
                    'boost1_will_trigger': boost1_status['will_trigger'],
                    'boost1_trigger_time': boost1_status['trigger_time'],
                    'boost1_active': boost1_status['active'],
                    'boost1_multiplier': boost1_status['multiplier'],
                    # Boost #2 info - ENIGMA MODE (frontend hides details until reveal)
                    'boost2_will_trigger': boost2_status['will_trigger'],
                    'boost2_trigger_time': boost2_status['trigger_time'],
                    'boost2_triggered': phase_manager.boost2_triggered,  # Whether Boost #2 has been triggered (past threshold window)
                    'threshold_window_active': boost2_status['threshold_window_active'],
                    'threshold': boost2_status['threshold'],
                    'boost2_active': boost2_status['active'],
                    'boost2_multiplier': boost2_status['multiplier'],
                    'creator_points': creator_points,
                    'opponent_points': opponent_points,
                    'creator_progress': boost2_status['creator_progress'],
                    'opponent_progress': boost2_status['opponent_progress'],
                    'creator_qualified': boost2_status['creator_qualified'],
                    'opponent_qualified': boost2_status['opponent_qualified'],
                    # Current time for enigma mode timing calculations
                    'current_time': current_time,
                    # Final 30 seconds info
                    'in_final_30s': phase_manager.is_in_final_30s(current_time),
                    # Glove active state
                    'glove_active': phase_manager.active_glove_x5
                })

            # Check for glove state changes
            glove_active = phase_manager.active_glove_x5
            if glove_active != last_glove_active:
                last_glove_active = glove_active
                glove_status = phase_manager.get_active_glove_status(current_time)
                socketio.emit('glove_state', {
                    'active': glove_status['active'],
                    'owner': glove_status['owner'],
                    'time_remaining': glove_status['time_remaining'],
                    'bonuses': glove_status['bonuses'],
                    'base_chance': glove_status['base_chance'],
                    'final_chance': glove_status['final_chance']
                })
            # Also send periodic updates while glove is active (for countdown)
            elif glove_active:
                glove_status = phase_manager.get_active_glove_status(current_time)
                socketio.emit('glove_countdown', {
                    'time_remaining': glove_status['time_remaining'],
                    'owner': glove_status['owner']
                })

            # Check for fog deactivation
            if hasattr(phase_manager, '_fog_was_active'):
                if phase_manager._fog_was_active and not phase_manager.fog_active:
                    # Fog just ended, broadcast clear
                    socketio.emit('fog_clear', {})
                    phase_manager._fog_was_active = False

            if phase_manager.fog_active:
                phase_manager._fog_was_active = True

            # Yield to event loop
            socketio.sleep(0)

        engine._tick = wrapped_tick

        # Override agent send_gift to broadcast
        for agent in team:
            original_send_gift = agent.send_gift

            def make_broadcast_send_gift(ag, orig_send):
                def broadcast_send_gift(battle, gift_name, points):
                    # Call original and capture result (MUST return for counters!)
                    result = orig_send(battle, gift_name, points)

                    # Only broadcast/track if gift was actually sent
                    if result:
                        # Record gift for Boost #2 tracking
                        current_time = battle.time_manager.current_time
                        phase_manager.record_gift(gift_name, points, "creator", current_time)

                        # Broadcast
                        broadcast_agent_action(battle_id, {
                            'agent_name': ag.name,
                            'emoji': ag.emoji,
                            'gift_name': gift_name,
                            'points': points,
                            'win_rate': ag.learning_agent.get_win_rate() if hasattr(ag, 'learning_agent') else 0
                        })

                        # Check for glove
                        if 'GLOVE' in gift_name.upper():
                            nonlocal gloves_sent
                            gloves_sent += 1
                            # Check if it activated (40% chance during boost or last 30s)
                            activated = False
                            if phase_manager.active_glove_x5:
                                activated = True
                                nonlocal gloves_activated
                                gloves_activated += 1

                            broadcast_glove_event({
                                'total_sent': gloves_sent,
                                'total_activated': gloves_activated,
                                'activated': activated
                            })

                    # CRITICAL: Return the result so callers can track success!
                    return result

                return broadcast_send_gift

            agent.send_gift = make_broadcast_send_gift(agent, original_send_gift)

        # Override phase manager power-up use
        original_use_powerup = phase_manager.use_power_up
        gloves_used_count = 0

        def broadcast_use_powerup(powerup_type, team_name, current_time):
            nonlocal gloves_used_count
            result = original_use_powerup(powerup_type, team_name, current_time)

            if result:
                if powerup_type == PowerUpType.GLOVE:
                    gloves_used_count += 1
                    info = {
                        'name': f'Glove {gloves_used_count}',
                        'emoji': '🥊',
                        'type': f'Glove{gloves_used_count}'
                    }
                else:
                    powerup_info = {
                        PowerUpType.HAMMER: {'name': 'Hammer', 'emoji': '🔨', 'type': 'Hammer'},
                        PowerUpType.FOG: {'name': 'Fog', 'emoji': '🌫️', 'type': 'Fog'},
                        PowerUpType.TIME_BONUS: {'name': 'Time Bonus', 'emoji': '⏱️', 'type': 'Time'}
                    }
                    info = powerup_info.get(powerup_type, {'name': 'Unknown', 'emoji': '❓', 'type': 'Unknown'})
                # broadcast_powerup_used already prints
                broadcast_powerup_used(info)

                # Show glove effect for glove power-ups
                if powerup_type == PowerUpType.GLOVE:
                    broadcast_glove_event({
                        'total_sent': gloves_used_count,
                        'total_activated': gloves_used_count,  # Power-ups always activate
                        'activated': True
                    })

            return result

        phase_manager.use_power_up = broadcast_use_powerup

        # Run battle
        print("🚀 Starting strategic battle...")
        try:
            engine.run(silent=True)
        except Exception as e:
            print(f"Battle error: {e}")

        # Get results safely
        try:
            winner = engine.analytics.winner or 'creator'
            final_scores = engine.analytics.final_scores or {
                'creator': engine.score_tracker.creator_score,
                'opponent': engine.score_tracker.opponent_score
            }
        except:
            winner = 'creator' if engine.score_tracker.creator_score > engine.score_tracker.opponent_score else 'opponent'
            final_scores = {
                'creator': engine.score_tracker.creator_score,
                'opponent': engine.score_tracker.opponent_score
            }

        phase_analytics = phase_manager.get_analytics()

        # Get GPT summary
        gpt_summary = ""
        if gpt_narrator.enabled:
            try:
                gpt_summary = gpt_narrator.generate_battle_summary(
                    winner,
                    final_scores,
                    phase_analytics
                )
            except:
                pass

        # Get budget analytics
        budget_analytics = budget_manager.get_analytics()
        creator_budget_final = budget_manager.get_status("creator")
        opponent_budget_final = budget_manager.get_status("opponent")

        # Broadcast end with budget info
        broadcast_strategic_battle_end({
            'winner': winner,
            'creator_score': final_scores['creator'],
            'opponent_score': final_scores['opponent'],
            'gpt_summary': gpt_summary,
            'analytics': phase_analytics,
            'budget_analytics': budget_analytics,
            'creator_budget_remaining': creator_budget_final['current'],
            'opponent_budget_remaining': opponent_budget_final['current']
        })

        # Learn from battle
        battle_stats = {
            'points_donated': sum(
                engine.analytics.get_agent_performance().get(a.name, {}).get('total_donated', 0)
                for a in team
            ),
            'boost2_triggered': phase_analytics.get('boost2_triggered', False),
            'boost2_qualified': phase_analytics.get('boost2_creator_qualified', False),
            'gloves_activated': gloves_activated,
            # Budget learning data
            'creator_budget_efficiency': budget_analytics['creator']['efficiency'],
            'opponent_budget_efficiency': budget_analytics['opponent']['efficiency'],
            'budget_advantage': budget_manager.creator_starting - budget_manager.opponent_starting
        }

        # IMPORTANT: Learn BEFORE reset (so agents can see their battle stats)
        learn_from_battle_results(team, winner == 'creator', battle_stats)
        reset_evolving_team(team)  # Reset for next battle

        print(f"\n🏁 Battle complete! Winner: {winner.upper()}")
        print(f"   Creator: {final_scores['creator']:,}")
        print(f"   Opponent: {final_scores['opponent']:,}")
        print(f"\n💰 Budget Summary:")
        print(f"   Creator: {budget_manager.creator_starting:,} → {creator_budget_final['current']:,} (spent {budget_analytics['creator']['total_spent']:,})")
        print(f"   Opponent: {budget_manager.opponent_starting:,} → {opponent_budget_final['current']:,} (spent {budget_analytics['opponent']['total_spent']:,})")

        db.close()

    # Set callback and start server
    set_battle_start_callback(run_battle_after_connect)

    print("\n" + "="*70)
    print("🌐 WEB STRATEGIC BATTLE SERVER")
    print("="*70)
    print("\nOpen in browser: http://localhost:5000/strategic")
    print("Battle will start when you open the page!")
    print("="*70 + "\n")

    run_server(port=5000, debug=False)


if __name__ == '__main__':
    run_web_strategic_battle()
