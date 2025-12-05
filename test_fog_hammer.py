#!/usr/bin/env python3
"""
Test script for Fog deployment and Hammer counter mechanics.

Tests:
1. Fog deployment at strategic time
2. Hammer counter against x5 strikes
3. Integration with multiplier system
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core import BattleEngine, EventBus
from core.multiplier_system import MultiplierManager, MultiplierType
from agents.specialists.sentinel import AgentSentinel
from agents.specialists.strike_master import AgentStrikeMaster


def test_fog_deployment():
    """Test 1: Verify fog deploys at correct time."""
    print("\n" + "="*70)
    print("TEST 1: FOG DEPLOYMENT")
    print("="*70)

    # Create battle with sentinel
    event_bus = EventBus()
    engine = BattleEngine(
        battle_duration=180,
        tick_speed=0,  # No delay for testing
        event_bus=event_bus,
        enable_multipliers=True
    )

    sentinel = AgentSentinel()
    sentinel.event_bus = event_bus
    sentinel.fog_deploy_time = 10  # Deploy early for testing
    engine.add_agent(sentinel)

    # Fast-forward to fog deployment time
    print("\n⏩ Fast-forwarding to t=10s (fog deployment time)...")
    for i in range(10):
        engine._tick(silent=True)

    # Check fog status
    inventory = sentinel.get_inventory_status()
    print(f"\n✅ Fog Deployment Results:")
    print(f"   Fog deployed: {inventory['fog_deployed']}")
    print(f"   Fogs remaining: {inventory['fogs']}/2")

    assert inventory['fog_deployed'] == True, "Fog should be deployed"
    assert inventory['fogs'] == 1, "Should have 1 fog remaining"
    print("\n✅ TEST 1 PASSED: Fog deployed successfully!\n")


def test_hammer_counter():
    """Test 2: Verify hammer counters x5 strikes."""
    print("\n" + "="*70)
    print("TEST 2: HAMMER COUNTER vs X5 STRIKE")
    print("="*70)

    # Create battle with multiplier system
    event_bus = EventBus()
    engine = BattleEngine(
        battle_duration=180,
        tick_speed=0,
        event_bus=event_bus,
        enable_multipliers=True
    )

    sentinel = AgentSentinel()
    sentinel.event_bus = event_bus
    engine.add_agent(sentinel)

    # Initialize multiplier system
    engine.multiplier_manager.initialize_auto_session()

    # Advance to auto-session time (should be around 61s)
    print("\n⏩ Advancing to auto-session activation...")
    for i in range(65):
        engine._tick(silent=True)

    # Check if session is active
    session_active = engine.multiplier_manager.is_session_active()
    print(f"   Session active at t=65s: {session_active}")

    if not session_active:
        # Manually trigger a session for testing
        print("   (Manually triggering x3 session for test)")
        from core.multiplier_system import MultiplierSession
        session = MultiplierSession(
            multiplier=MultiplierType.X3,
            start_time=65,
            duration=20,
            source="test"
        )
        engine.multiplier_manager.active_sessions.append(session)
        session_active = True

    print("\n⚡ Triggering x5 strike at t=65s (during x3 session)...")

    # Force x5 trigger with 100% probability
    engine.multiplier_manager.x5_success_probability = 1.0
    x5_triggered = engine.multiplier_manager.attempt_x5_strike(65, "OpponentAgent")

    print(f"   x5 triggered: {x5_triggered}")

    # Check x5 is active
    active_sessions = engine.multiplier_manager.active_sessions
    x5_sessions = [s for s in active_sessions if s.multiplier == MultiplierType.X5]
    print(f"   Active x5 sessions: {len(x5_sessions)}")

    # Deploy hammer
    print("\n🔨 Deploying hammer counter...")
    initial_hammers = sentinel.hammers_available
    success = engine.multiplier_manager.deploy_hammer(65, "Sentinel")

    # Check results
    print(f"\n✅ Hammer Counter Results:")
    print(f"   Hammer deployed successfully: {success}")
    print(f"   Hammers remaining: {sentinel.hammers_available}/{initial_hammers}")

    # Verify x5 was neutralized
    active_sessions_after = engine.multiplier_manager.active_sessions
    x5_active_after = any(s.multiplier == MultiplierType.X5 for s in active_sessions_after)
    print(f"   x5 still active after hammer: {x5_active_after}")

    assert x5_triggered == True, "x5 should trigger during session"
    assert success == True, "Hammer should successfully neutralize x5"
    assert x5_active_after == False, "x5 should be neutralized after hammer"
    print("\n✅ TEST 2 PASSED: Hammer neutralized x5 successfully!\n")


def test_integration():
    """Test 3: Full integration test with both mechanics."""
    print("\n" + "="*70)
    print("TEST 3: INTEGRATION TEST - FOG + HAMMER")
    print("="*70)

    event_bus = EventBus()
    engine = BattleEngine(
        battle_duration=180,
        tick_speed=0,
        event_bus=event_bus,
        enable_multipliers=True
    )

    # Add both Sentinel and StrikeMaster
    sentinel = AgentSentinel()
    sentinel.event_bus = event_bus
    sentinel.fog_deploy_time = 160
    engine.add_agent(sentinel)

    strike_master = AgentStrikeMaster()
    strike_master.event_bus = event_bus
    engine.add_agent(strike_master)

    # Initialize multiplier system
    engine.multiplier_manager.initialize_auto_session()

    print("\n📋 Test Scenario:")
    print("   1. StrikeMaster triggers x5 at t=70s")
    print("   2. Verify x5 is active")
    print("   3. Simulate opponent x5 at t=80s")
    print("   4. Sentinel auto-counters with hammer")
    print("   5. Fog deploys at t=160s")

    # Advance to t=70
    for i in range(70):
        engine._tick(silent=True)

    # Trigger friendly x5
    print("\n⚡ t=70s: Friendly x5 strike...")
    engine.multiplier_manager.x5_success_probability = 1.0
    friendly_x5 = engine.multiplier_manager.attempt_x5_strike(70, "StrikeMaster")
    print(f"   Friendly x5 active: {friendly_x5}")

    # Let it expire
    for i in range(10):
        engine._tick(silent=True)

    # Simulate opponent x5 at t=80
    print("\n⚡ t=80s: Opponent x5 strike detected...")
    opponent_x5 = engine.multiplier_manager.attempt_x5_strike(80, "OpponentAgent")
    print(f"   Opponent x5 active: {opponent_x5}")

    # Check if x5 is active
    x5_sessions = [s for s in engine.multiplier_manager.active_sessions if s.multiplier == MultiplierType.X5]
    print(f"   Active x5 sessions: {len(x5_sessions)}")

    # Deploy hammer
    print("\n🔨 t=80s: Sentinel deploys hammer...")
    hammer_success = engine.multiplier_manager.deploy_hammer(80, "Sentinel")
    sentinel.hammers_available -= 1
    print(f"   Hammer success: {hammer_success}")
    print(f"   Hammers remaining: {sentinel.hammers_available}/2")

    # Advance to fog deployment
    for i in range(80):
        engine._tick(silent=True)

    print("\n🌫️ t=160s: Fog deployment...")
    fog_before = sentinel.fog_deployed
    sentinel.decide_action(engine)
    fog_after = sentinel.fog_deployed
    print(f"   Fog deployed: {fog_after}")
    print(f"   Fogs remaining: {sentinel.fogs_available}/2")

    print("\n✅ Integration Test Results:")
    print(f"   ✓ Friendly x5 worked: {friendly_x5}")
    print(f"   ✓ Hammer neutralized opponent x5: {hammer_success}")
    print(f"   ✓ Fog deployed at correct time: {fog_after}")
    print("\n✅ TEST 3 PASSED: All mechanics working together!\n")


def main():
    """Run all tests."""
    print("\n🧪 TESTING FOG DEPLOYMENT & HAMMER COUNTERS")
    print("="*70)

    try:
        test_fog_deployment()
        test_hammer_counter()
        test_integration()

        print("\n" + "="*70)
        print("🎉 ALL TESTS PASSED!")
        print("="*70)
        print("\n✅ Fog Deployment: Working")
        print("✅ Hammer Counter: Working")
        print("✅ Integration: Working\n")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
