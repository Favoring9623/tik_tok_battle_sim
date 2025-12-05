#!/usr/bin/env python3
"""
Demo: Advanced Analytics System

Showcases the comprehensive analytics dashboard including:
- Gift efficiency tracking and ROI analysis
- Phase performance breakdown
- Agent contribution metrics
- Combo and tactic tracking
- Momentum analysis
- Battle timeline/replay
"""

import sys
import random
from core.advanced_phase_system import AdvancedPhaseManager, PowerUpType
from core.battle_analytics import BattleAnalytics, AnalyticsDashboard
from core.gift_catalog import get_gift_catalog

# Import agents
from agents.specialists import (
    DefenseMaster,
    BudgetOptimizer,
    ChaoticTrickster,
    SynergyCoordinator,
    AgentKinetik
)


class AnalyticsBattleSimulator:
    """
    Battle simulator with full analytics tracking.
    """

    def __init__(self, duration: int = 120):
        self.duration = duration
        self.phase_manager = AdvancedPhaseManager(battle_duration=duration)
        self.analytics = BattleAnalytics(battle_duration=duration)
        self.gift_catalog = get_gift_catalog()

        # Scores
        self.creator_score = 0
        self.opponent_score = 0

        # Setup phase manager
        self.phase_manager.add_power_up(PowerUpType.HAMMER, "creator")
        self.phase_manager.add_power_up(PowerUpType.FOG, "creator")

    def run_battle(self, team):
        """Run a full battle with analytics tracking."""
        print("\n" + "=" * 70)
        print("   BATTLE WITH ANALYTICS TRACKING")
        print("=" * 70)

        # Register agents
        for agent in team:
            self.analytics.register_agent(agent.name, agent.emoji)
            agent.budget_manager = None  # No budget restrictions for demo

        # Record battle start
        self.analytics.record_battle_start(self.duration, len(team))

        # Mock battle object
        class MockBattle:
            def __init__(self, sim):
                self.sim = sim
                self.time_manager = MockTimeManager(sim)
                self.score_tracker = MockScoreTracker(sim)

        class MockTimeManager:
            def __init__(self, sim):
                self.sim = sim
                self.current_time = 0

            def time_remaining(self):
                return self.sim.duration - self.current_time

        class MockScoreTracker:
            def __init__(self, sim):
                self.sim = sim

            @property
            def creator_score(self):
                return self.sim.creator_score

            @property
            def opponent_score(self):
                return self.sim.opponent_score

            def add_creator_points(self, points):
                self.sim.creator_score += points

        battle = MockBattle(self)

        # Run simulation
        for t in range(0, self.duration, 3):  # Every 3 seconds
            battle.time_manager.current_time = t

            # Update phase manager
            self.phase_manager.update(t)

            # Get current multiplier
            multiplier = self.phase_manager.get_current_multiplier()
            phase = self._get_phase_name(t)

            # Each agent acts
            for agent in team:
                if random.random() < 0.4:  # 40% chance to act
                    gift = self._select_gift(agent, multiplier)
                    if gift:
                        effective_points = int(gift.coins * multiplier)
                        self.creator_score += effective_points

                        # Record action
                        self.analytics.record_action(
                            time=t,
                            agent=agent.name,
                            action_type="gift",
                            gift_name=gift.name,
                            points=effective_points,
                            multiplier=multiplier,
                            cost=gift.coins  # coins is the cost
                        )

                        # Print gift
                        mult_str = f" x{multiplier:.0f}" if multiplier > 1 else ""
                        print(f"   t={t:>3}s {agent.emoji} {agent.name}: {gift.name} (+{effective_points:,}){mult_str}")

            # Simulate opponent
            if random.random() < 0.3:
                opp_gift = random.randint(50, 500)
                self.opponent_score += opp_gift

            # Record score snapshot
            self.analytics.record_score_snapshot(t, self.creator_score, self.opponent_score, phase)

            # Simulate combos
            if t > 30 and random.random() < 0.15:
                combo_types = ["triple_threat", "boost_blitz", "wave_attack", "final_push"]
                combo = random.choice(combo_types)
                self.analytics.record_combo(t, combo, team[0].name if team else "Unknown")
                print(f"   t={t:>3}s COMBO: {combo.upper()}")

            # Simulate tactics
            if random.random() < 0.1:
                tactics = ["bluff", "decoy", "pause", "fog_burst"]
                tactic = random.choice(tactics)
                agent = random.choice(team) if team else None
                if agent:
                    self.analytics.record_tactic(t, agent.name, tactic)
                    print(f"   t={t:>3}s TACTIC: {agent.name} used {tactic}")

            # Simulate clutch moments
            if t > self.duration - 30 and abs(self.creator_score - self.opponent_score) < 3000:
                if random.random() < 0.2:
                    self.analytics.record_clutch_moment(t, "nail_biter", self.creator_score, self.creator_score)

        # Final score snapshot
        self.analytics.record_score_snapshot(
            self.duration, self.creator_score, self.opponent_score, "final"
        )

        # Determine winner
        winner = "creator" if self.creator_score > self.opponent_score else "opponent"
        self.analytics.record_battle_end(winner, self.creator_score, self.opponent_score)

        print(f"\n   FINAL: Creator {self.creator_score:,} vs Opponent {self.opponent_score:,}")
        print(f"   RESULT: {'VICTORY!' if winner == 'creator' else 'DEFEAT'}")

        return self.analytics

    def _get_phase_name(self, time: int) -> str:
        """Get phase name based on time."""
        if time < 60:
            return "early"
        elif time < 120:
            return "mid"
        elif time < 150:
            return "late"
        else:
            return "final"

    def _select_gift(self, agent, multiplier):
        """Select a gift based on agent type and multiplier."""
        if multiplier >= 2.0:
            # Big gifts during multiplier
            gift_names = ["Galaxy", "Confetti", "Shooting Star", "Sports Car"]
        else:
            # Normal gifts
            gift_names = ["Doughnut", "Heart", "Rose", "Butterfly", "Confetti"]

        for name in gift_names:
            gift = self.gift_catalog.get_gift(name)
            if gift:
                return gift
        return None


def main():
    print("\n" + "=" * 70)
    print("   ADVANCED ANALYTICS DEMO")
    print("   Showcasing battle analytics and dashboard")
    print("=" * 70)

    # Create phase manager and team
    pm = AdvancedPhaseManager(battle_duration=120)
    pm.add_power_up(PowerUpType.HAMMER, "creator")
    pm.add_power_up(PowerUpType.FOG, "creator")

    team = [
        DefenseMaster(phase_manager=pm),
        BudgetOptimizer(phase_manager=pm),
        ChaoticTrickster(phase_manager=pm),
        SynergyCoordinator(phase_manager=pm),
        AgentKinetik()
    ]

    # Run battle with analytics
    simulator = AnalyticsBattleSimulator(duration=120)
    analytics = simulator.run_battle(team)

    # Show dashboard
    print("\n\n")
    dashboard = AnalyticsDashboard(analytics)
    dashboard.print_full_dashboard()

    # Export to JSON
    print("   Exporting analytics to battle_analytics_report.json...")
    analytics.export_to_json("battle_analytics_report.json")
    print("   Done!\n")

    # Show individual reports
    print("\n" + "=" * 70)
    print("   INDIVIDUAL REPORTS (Raw Data)")
    print("=" * 70)

    print("\n--- Gift Efficiency Report ---")
    eff_report = analytics.get_gift_efficiency_report()
    print(f"   Overall ROI: {eff_report['overall_roi']:.2f}x")
    print(f"   Total Gifts: {eff_report['total_gifts']}")
    print(f"   Top ROI Gift: {eff_report['top_roi_gifts'][0]['gift'] if eff_report['top_roi_gifts'] else 'N/A'}")

    print("\n--- Phase Performance Report ---")
    phase_report = analytics.get_phase_performance_report()
    print(f"   Best Phase: {phase_report['best_phase']}")
    print(f"   Worst Phase: {phase_report['worst_phase']}")

    print("\n--- Agent Contribution Report ---")
    agent_report = analytics.get_agent_contribution_report()
    print(f"   MVP: {agent_report['mvp']}")
    print(f"   Most Active: {agent_report['most_active']}")
    print(f"   Most Efficient: {agent_report['most_efficient']}")

    print("\n--- Momentum Report ---")
    momentum = analytics.get_momentum_report()
    print(f"   Largest Lead: +{momentum['largest_lead']:,}")
    print(f"   Largest Deficit: {momentum['largest_deficit']:,}")
    print(f"   Lead Changes: {momentum['lead_changes']}")

    print("\n" + "=" * 70)
    print("   DEMO COMPLETE")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
