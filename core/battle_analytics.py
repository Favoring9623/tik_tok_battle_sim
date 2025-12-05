"""
Battle Analytics - Comprehensive battle data collection and analysis.

Tracks:
- Score progression over time
- Agent actions and timing
- Multiplier sessions and impact
- Coordination effectiveness
- Gift patterns and ROI
- Combo tracking
- Clutch moments
- Phase performance breakdown
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import json
from pathlib import Path
from datetime import datetime


@dataclass
class ActionEvent:
    """Records a single action during battle."""
    time: int
    agent: str
    action_type: str
    gift_name: Optional[str] = None
    points: int = 0
    multiplier: float = 1.0
    coordinated: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScoreSnapshot:
    """Score state at a specific time."""
    time: int
    creator_score: int
    opponent_score: int
    score_diff: int
    leader: str
    phase: str


@dataclass
class MultiplierSession:
    """Records a multiplier session."""
    session_type: str  # x2, x3, x5
    start_time: int
    end_time: int
    duration: int
    source: str
    points_during_session: int = 0
    gifts_during_session: int = 0


@dataclass
class ComboEvent:
    """Records a combo execution."""
    time: int
    combo_type: str
    initiator: str
    participants: List[str] = field(default_factory=list)
    total_points: int = 0
    success: bool = True


@dataclass
class ClutchMoment:
    """Records a clutch moment."""
    time: int
    moment_type: str  # comeback, nail_biter, final_surge, etc.
    score_before: int = 0
    score_after: int = 0
    description: str = ""


@dataclass
class TacticEvent:
    """Records a psychological warfare tactic."""
    time: int
    agent: str
    tactic: str  # bluff, decoy, pause, fog_burst
    success: bool = False


class BattleAnalytics:
    """
    Comprehensive analytics system for battle analysis.

    Collects data during battle and provides post-battle insights.
    """

    def __init__(self, battle_duration: int = 180):
        # Timeline data
        self.score_timeline: List[ScoreSnapshot] = []
        self.action_timeline: List[ActionEvent] = []
        self.multiplier_sessions: List[MultiplierSession] = []

        # Agent performance
        self.agent_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "emoji": "",
            "total_donated": 0,
            "total_cost": 0,
            "actions": [],
            "gifts_sent": 0,
            "avg_gift_value": 0,
            "best_gift": {"name": "", "value": 0},
            "timing": {"early": 0, "mid": 0, "late": 0, "final": 0},
            "gifts_by_type": defaultdict(int),
            "combos_participated": 0,
            "tactics_used": defaultdict(int)
        })

        # Coordination tracking
        self.coordination_events: List[Dict[str, Any]] = []
        self.conflicts_prevented: int = 0
        self.dependencies_satisfied: int = 0

        # Battle metadata
        self.battle_start_time: Optional[int] = None
        self.battle_end_time: Optional[int] = None
        self.battle_duration: int = battle_duration
        self.winner: Optional[str] = None
        self.final_scores: Dict[str, int] = {}

        # Gift analytics
        self.gift_distribution: Dict[str, int] = defaultdict(int)
        self.gift_timing: Dict[str, List[int]] = defaultdict(list)
        self.gift_roi: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            "count": 0, "total_points": 0, "total_cost": 0
        })

        # NEW: Combo tracking
        self.combo_events: List[ComboEvent] = []

        # NEW: Clutch moments
        self.clutch_moments: List[ClutchMoment] = []

        # NEW: Tactic tracking
        self.tactic_events: List[TacticEvent] = []

        # NEW: Phase performance
        self.phase_stats: Dict[str, Dict[str, Any]] = {
            "early": {"gifts": 0, "points": 0, "cost": 0, "start": 0, "end": 60},
            "mid": {"gifts": 0, "points": 0, "cost": 0, "start": 60, "end": 120},
            "late": {"gifts": 0, "points": 0, "cost": 0, "start": 120, "end": 150},
            "final": {"gifts": 0, "points": 0, "cost": 0, "start": 150, "end": battle_duration},
            "boost": {"gifts": 0, "points": 0, "cost": 0, "duration": 0},
            "x5": {"gifts": 0, "points": 0, "cost": 0, "duration": 0}
        }

        # NEW: Momentum tracking
        self.largest_lead: int = 0
        self.largest_deficit: int = 0
        self.lead_changes: int = 0
        self.last_leader: Optional[str] = None

        # NEW: Timestamp
        self.start_timestamp = datetime.now()

    def record_battle_start(self, duration: int, agent_count: int):
        """Record battle initialization."""
        self.battle_start_time = 0
        self.battle_duration = duration

    def record_score_snapshot(self, time: int, creator_score: int,
                              opponent_score: int, phase: str):
        """Record score state at this moment."""
        score_diff = creator_score - opponent_score  # Positive = creator winning
        leader = "creator" if creator_score > opponent_score else "opponent" if opponent_score > creator_score else "tie"

        snapshot = ScoreSnapshot(
            time=time,
            creator_score=creator_score,
            opponent_score=opponent_score,
            score_diff=score_diff,
            leader=leader,
            phase=phase
        )
        self.score_timeline.append(snapshot)

        # Track momentum
        if score_diff > self.largest_lead:
            self.largest_lead = score_diff
        if score_diff < self.largest_deficit:
            self.largest_deficit = score_diff

        # Track lead changes
        if self.last_leader and leader != self.last_leader and leader != "tie":
            self.lead_changes += 1
        if leader != "tie":
            self.last_leader = leader

    def register_agent(self, agent_name: str, emoji: str = ""):
        """Register an agent for tracking."""
        if agent_name not in self.agent_stats:
            self.agent_stats[agent_name]  # Creates default
        self.agent_stats[agent_name]["emoji"] = emoji

    def record_action(self, time: int, agent: str, action_type: str,
                     gift_name: Optional[str] = None, points: int = 0,
                     multiplier: float = 1.0, coordinated: bool = False,
                     cost: int = 0, **metadata):
        """Record an agent action."""
        action = ActionEvent(
            time=time,
            agent=agent,
            action_type=action_type,
            gift_name=gift_name,
            points=points,
            multiplier=multiplier,
            coordinated=coordinated,
            metadata=metadata
        )
        self.action_timeline.append(action)

        # Update agent stats
        if points > 0:
            self.agent_stats[agent]["total_donated"] += points
            self.agent_stats[agent]["total_cost"] += cost
            self.agent_stats[agent]["gifts_sent"] += 1
            self.agent_stats[agent]["actions"].append(action)

            # Track best gift
            if points > self.agent_stats[agent]["best_gift"]["value"]:
                self.agent_stats[agent]["best_gift"] = {
                    "name": gift_name or "Unknown",
                    "value": points
                }

            # Track timing
            phase = self._get_phase(time)
            self.agent_stats[agent]["timing"][phase] += 1

            # Gift distribution
            if gift_name:
                self.gift_distribution[gift_name] += 1
                self.gift_timing[gift_name].append(time)
                self.agent_stats[agent]["gifts_by_type"][gift_name] += 1

                # Track gift ROI
                self.gift_roi[gift_name]["count"] += 1
                self.gift_roi[gift_name]["total_points"] += points
                self.gift_roi[gift_name]["total_cost"] += cost

            # Update phase stats
            if phase in self.phase_stats:
                self.phase_stats[phase]["gifts"] += 1
                self.phase_stats[phase]["points"] += points
                self.phase_stats[phase]["cost"] += cost

            # Track boost/x5 separately
            if multiplier >= 5.0:
                self.phase_stats["x5"]["gifts"] += 1
                self.phase_stats["x5"]["points"] += points
                self.phase_stats["x5"]["cost"] += cost
            elif multiplier >= 2.0:
                self.phase_stats["boost"]["gifts"] += 1
                self.phase_stats["boost"]["points"] += points
                self.phase_stats["boost"]["cost"] += cost

    def record_combo(self, time: int, combo_type: str, initiator: str,
                    participants: List[str] = None, total_points: int = 0):
        """Record a combo execution."""
        combo = ComboEvent(
            time=time,
            combo_type=combo_type,
            initiator=initiator,
            participants=participants or [],
            total_points=total_points
        )
        self.combo_events.append(combo)

        # Update agent combo participation
        self.agent_stats[initiator]["combos_participated"] += 1
        for p in (participants or []):
            self.agent_stats[p]["combos_participated"] += 1

    def record_tactic(self, time: int, agent: str, tactic: str, success: bool = False):
        """Record a psychological warfare tactic."""
        event = TacticEvent(time=time, agent=agent, tactic=tactic, success=success)
        self.tactic_events.append(event)
        self.agent_stats[agent]["tactics_used"][tactic] += 1

    def record_clutch_moment(self, time: int, moment_type: str,
                            score_before: int = 0, score_after: int = 0,
                            description: str = ""):
        """Record a clutch moment."""
        moment = ClutchMoment(
            time=time,
            moment_type=moment_type,
            score_before=score_before,
            score_after=score_after,
            description=description
        )
        self.clutch_moments.append(moment)

    def record_multiplier_session(self, session_type: str, start_time: int,
                                  end_time: int, source: str):
        """Record a multiplier session."""
        session = MultiplierSession(
            session_type=session_type,
            start_time=start_time,
            end_time=end_time,
            duration=end_time - start_time,
            source=source
        )
        self.multiplier_sessions.append(session)

    def record_coordination_event(self, event_type: str, agent: str,
                                  action: str, time: int, **details):
        """Record a coordination event."""
        self.coordination_events.append({
            "type": event_type,
            "agent": agent,
            "action": action,
            "time": time,
            **details
        })

        if event_type == "conflict_prevented":
            self.conflicts_prevented += 1
        elif event_type == "dependency_satisfied":
            self.dependencies_satisfied += 1

    def record_battle_end(self, winner: str, creator_score: int, opponent_score: int):
        """Record battle conclusion."""
        self.battle_end_time = self.battle_duration
        self.winner = winner
        self.final_scores = {
            "creator": creator_score,
            "opponent": opponent_score
        }

        # Calculate avg gift values
        for agent, stats in self.agent_stats.items():
            if stats["gifts_sent"] > 0:
                stats["avg_gift_value"] = stats["total_donated"] / stats["gifts_sent"]

    def _get_phase(self, time: int) -> str:
        """Determine battle phase from time."""
        progress = time / self.battle_duration if self.battle_duration > 0 else 0
        if progress <= 0.33:
            return "early"
        elif progress <= 0.67:
            return "mid"
        elif progress <= 0.97:
            return "late"
        else:
            return "final"

    def get_score_progression(self) -> List[Dict[str, Any]]:
        """Get score progression data for charting."""
        return [
            {
                "time": s.time,
                "creator": s.creator_score,
                "opponent": s.opponent_score,
                "diff": s.score_diff,
                "leader": s.leader
            }
            for s in self.score_timeline
        ]

    def get_action_timeline(self) -> List[Dict[str, Any]]:
        """Get chronological action timeline."""
        return [
            {
                "time": a.time,
                "agent": a.agent,
                "action": a.action_type,
                "gift": a.gift_name,
                "points": a.points,
                "multiplier": a.multiplier,
                "coordinated": a.coordinated
            }
            for a in sorted(self.action_timeline, key=lambda x: x.time)
        ]

    def get_agent_performance(self, include_actions: bool = False) -> Dict[str, Dict[str, Any]]:
        """
        Get detailed agent performance metrics.

        Args:
            include_actions: If True, include full action list (not JSON serializable)
        """
        result = {}
        for agent, stats in self.agent_stats.items():
            result[agent] = {
                "total_donated": stats["total_donated"],
                "gifts_sent": stats["gifts_sent"],
                "avg_gift_value": stats["avg_gift_value"],
                "best_gift": stats["best_gift"],
                "timing": stats["timing"]
            }
            if include_actions:
                result[agent]["actions"] = stats["actions"]
        return result

    def get_coordination_summary(self) -> Dict[str, Any]:
        """Get coordination effectiveness summary."""
        return {
            "total_events": len(self.coordination_events),
            "conflicts_prevented": self.conflicts_prevented,
            "dependencies_satisfied": self.dependencies_satisfied,
            "coordination_rate": len([e for e in self.coordination_events if e["type"] in ["approved", "dependency_satisfied"]]) / max(1, len(self.coordination_events)),
            "events": self.coordination_events
        }

    def get_multiplier_analysis(self) -> Dict[str, Any]:
        """Analyze multiplier session effectiveness."""
        if not self.multiplier_sessions:
            return {"sessions": 0, "total_duration": 0}

        total_duration = sum(s.duration for s in self.multiplier_sessions)
        sessions_by_type = defaultdict(int)
        for session in self.multiplier_sessions:
            sessions_by_type[session.session_type] += 1

        return {
            "total_sessions": len(self.multiplier_sessions),
            "total_duration": total_duration,
            "sessions_by_type": dict(sessions_by_type),
            "avg_duration": total_duration / len(self.multiplier_sessions),
            "coverage": (total_duration / self.battle_duration) * 100 if self.battle_duration > 0 else 0
        }

    def get_gift_analysis(self) -> Dict[str, Any]:
        """Analyze gift usage patterns."""
        return {
            "distribution": dict(self.gift_distribution),
            "timing_patterns": {
                gift: {
                    "count": len(times),
                    "first": min(times) if times else 0,
                    "last": max(times) if times else 0,
                    "avg_time": sum(times) / len(times) if times else 0
                }
                for gift, times in self.gift_timing.items()
            },
            "most_used": max(self.gift_distribution.items(), key=lambda x: x[1])[0] if self.gift_distribution else None
        }

    def get_complete_summary(self) -> Dict[str, Any]:
        """Get comprehensive battle summary."""
        return {
            "battle": {
                "duration": self.battle_duration,
                "winner": self.winner,
                "final_scores": self.final_scores,
                "score_diff": self.final_scores.get("opponent", 0) - self.final_scores.get("creator", 0)
            },
            "agents": self.get_agent_performance(),
            "coordination": self.get_coordination_summary(),
            "multipliers": self.get_multiplier_analysis(),
            "gifts": self.get_gift_analysis(),
            "timeline": {
                "snapshots": len(self.score_timeline),
                "actions": len(self.action_timeline)
            }
        }

    def export_to_json(self, filepath: str):
        """Export analytics data to JSON file."""
        data = self.get_complete_summary()
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

    def print_summary(self):
        """Print formatted summary to console."""
        print("\n" + "="*70)
        print("📊 BATTLE ANALYTICS SUMMARY")
        print("="*70)

        # Battle info
        print(f"\n🏆 Battle Result:")
        print(f"   Winner: {self.winner or 'TIE'}")
        print(f"   Duration: {self.battle_duration}s")
        print(f"   Final Score: Creator {self.final_scores.get('creator', 0):,} vs Opponent {self.final_scores.get('opponent', 0):,}")

        # Agent performance
        print(f"\n👥 Agent Performance:")
        for agent, stats in sorted(self.agent_stats.items(), key=lambda x: x[1]["total_donated"], reverse=True):
            print(f"\n   {agent}:")
            print(f"      Total donated: {stats['total_donated']:,} points")
            print(f"      Gifts sent: {stats['gifts_sent']}")
            print(f"      Avg gift value: {stats['avg_gift_value']:,.0f}")
            print(f"      Best gift: {stats['best_gift']['name']} ({stats['best_gift']['value']:,})")
            print(f"      Timing: Early {stats['timing']['early']}, Mid {stats['timing']['mid']}, Late {stats['timing']['late']}, Final {stats['timing']['final']}")

        # Coordination
        coord = self.get_coordination_summary()
        print(f"\n🤝 Coordination:")
        print(f"   Events: {coord['total_events']}")
        print(f"   Conflicts prevented: {coord['conflicts_prevented']}")
        print(f"   Dependencies satisfied: {coord['dependencies_satisfied']}")

        # Multipliers
        mult = self.get_multiplier_analysis()
        if mult["total_sessions"] > 0:
            print(f"\n⚡ Multipliers:")
            print(f"   Sessions: {mult['total_sessions']}")
            print(f"   Total duration: {mult['total_duration']}s")
            print(f"   Coverage: {mult['coverage']:.1f}%")

        print("\n" + "="*70 + "\n")

    # =========================================================================
    # ADVANCED ANALYSIS METHODS
    # =========================================================================

    def get_gift_efficiency_report(self) -> Dict[str, Any]:
        """Get detailed gift efficiency analysis with ROI."""
        total_points = sum(d["total_points"] for d in self.gift_roi.values())
        total_cost = sum(d["total_cost"] for d in self.gift_roi.values())

        report = {
            "total_gifts": sum(d["count"] for d in self.gift_roi.values()),
            "total_points": total_points,
            "total_cost": total_cost,
            "overall_roi": total_points / total_cost if total_cost > 0 else 0,
            "by_gift": {},
            "top_roi_gifts": [],
            "most_used_gifts": []
        }

        # Calculate per-gift ROI
        for gift_name, data in self.gift_roi.items():
            if data["count"] > 0:
                roi = data["total_points"] / data["total_cost"] if data["total_cost"] > 0 else 0
                report["by_gift"][gift_name] = {
                    "count": data["count"],
                    "total_points": data["total_points"],
                    "total_cost": data["total_cost"],
                    "roi": round(roi, 2),
                    "avg_points": data["total_points"] / data["count"]
                }

        # Top ROI gifts
        sorted_by_roi = sorted(
            report["by_gift"].items(),
            key=lambda x: x[1]["roi"],
            reverse=True
        )[:5]
        report["top_roi_gifts"] = [
            {"gift": k, "roi": v["roi"], "count": v["count"]}
            for k, v in sorted_by_roi
        ]

        # Most used gifts
        sorted_by_count = sorted(
            report["by_gift"].items(),
            key=lambda x: x[1]["count"],
            reverse=True
        )[:5]
        report["most_used_gifts"] = [
            {"gift": k, "count": v["count"], "points": v["total_points"]}
            for k, v in sorted_by_count
        ]

        return report

    def get_phase_performance_report(self) -> Dict[str, Any]:
        """Get phase-by-phase performance breakdown."""
        report = {
            "phases": {},
            "best_phase": None,
            "worst_phase": None,
            "multiplier_utilization": {
                "boost_gifts": self.phase_stats["boost"]["gifts"],
                "boost_points": self.phase_stats["boost"]["points"],
                "x5_gifts": self.phase_stats["x5"]["gifts"],
                "x5_points": self.phase_stats["x5"]["points"]
            }
        }

        best_efficiency = 0
        worst_efficiency = float('inf')

        for phase_name in ["early", "mid", "late", "final"]:
            stats = self.phase_stats[phase_name]
            duration = stats["end"] - stats["start"]
            efficiency = stats["points"] / stats["cost"] if stats["cost"] > 0 else 0
            pps = stats["points"] / duration if duration > 0 else 0

            report["phases"][phase_name] = {
                "duration": duration,
                "gifts_sent": stats["gifts"],
                "total_points": stats["points"],
                "total_cost": stats["cost"],
                "efficiency": round(efficiency, 2),
                "points_per_second": round(pps, 2)
            }

            if stats["gifts"] > 0:
                if efficiency > best_efficiency:
                    best_efficiency = efficiency
                    report["best_phase"] = phase_name
                if efficiency < worst_efficiency:
                    worst_efficiency = efficiency
                    report["worst_phase"] = phase_name

        return report

    def get_agent_contribution_report(self) -> Dict[str, Any]:
        """Get agent contribution breakdown."""
        total_points = sum(s["total_donated"] for s in self.agent_stats.values())

        report = {
            "agents": {},
            "mvp": None,
            "most_efficient": None,
            "most_active": None
        }

        max_points = 0
        max_efficiency = 0
        max_gifts = 0

        for agent_name, stats in self.agent_stats.items():
            contrib_pct = (stats["total_donated"] / total_points * 100) if total_points > 0 else 0
            efficiency = stats["total_donated"] / stats["total_cost"] if stats["total_cost"] > 0 else 0

            # Convert defaultdict to regular dict for JSON serialization
            gifts_by_type = dict(stats["gifts_by_type"]) if stats["gifts_by_type"] else {}
            tactics_used = dict(stats["tactics_used"]) if stats["tactics_used"] else {}

            report["agents"][agent_name] = {
                "emoji": stats["emoji"],
                "gifts_sent": stats["gifts_sent"],
                "total_points": stats["total_donated"],
                "total_cost": stats["total_cost"],
                "efficiency": round(efficiency, 2),
                "avg_gift_value": round(stats["avg_gift_value"], 2),
                "contribution_pct": round(contrib_pct, 1),
                "combos_participated": stats["combos_participated"],
                "tactics_used": tactics_used,
                "top_gifts": sorted(gifts_by_type.items(), key=lambda x: x[1], reverse=True)[:3],
                "timing": stats["timing"]
            }

            if stats["total_donated"] > max_points:
                max_points = stats["total_donated"]
                report["mvp"] = agent_name

            if efficiency > max_efficiency and stats["gifts_sent"] >= 3:
                max_efficiency = efficiency
                report["most_efficient"] = agent_name

            if stats["gifts_sent"] > max_gifts:
                max_gifts = stats["gifts_sent"]
                report["most_active"] = agent_name

        return report

    def get_combo_report(self) -> Dict[str, Any]:
        """Get combo analysis."""
        report = {
            "total_combos": len(self.combo_events),
            "combo_breakdown": defaultdict(lambda: {"count": 0, "total_points": 0}),
            "most_effective_combo": None,
            "timeline": []
        }

        max_avg = 0
        for combo in self.combo_events:
            report["combo_breakdown"][combo.combo_type]["count"] += 1
            report["combo_breakdown"][combo.combo_type]["total_points"] += combo.total_points

            report["timeline"].append({
                "time": combo.time,
                "type": combo.combo_type,
                "initiator": combo.initiator,
                "participants": combo.participants
            })

        for combo_type, data in report["combo_breakdown"].items():
            if data["count"] > 0:
                avg = data["total_points"] / data["count"]
                if avg > max_avg:
                    max_avg = avg
                    report["most_effective_combo"] = combo_type

        report["combo_breakdown"] = dict(report["combo_breakdown"])
        return report

    def get_tactic_report(self) -> Dict[str, Any]:
        """Get psychological warfare tactic analysis."""
        report = {
            "total_tactics": len(self.tactic_events),
            "by_tactic": defaultdict(lambda: {"count": 0, "successes": 0}),
            "by_agent": defaultdict(lambda: {"count": 0, "tactics": []})
        }

        for event in self.tactic_events:
            report["by_tactic"][event.tactic]["count"] += 1
            if event.success:
                report["by_tactic"][event.tactic]["successes"] += 1

            report["by_agent"][event.agent]["count"] += 1
            if event.tactic not in report["by_agent"][event.agent]["tactics"]:
                report["by_agent"][event.agent]["tactics"].append(event.tactic)

        report["by_tactic"] = dict(report["by_tactic"])
        report["by_agent"] = dict(report["by_agent"])
        return report

    def get_momentum_report(self) -> Dict[str, Any]:
        """Get momentum and score progression analysis."""
        report = {
            "final_score": self.final_scores,
            "margin": self.final_scores.get("creator", 0) - self.final_scores.get("opponent", 0),
            "won": self.winner == "creator",
            "largest_lead": self.largest_lead,
            "largest_deficit": self.largest_deficit,
            "lead_changes": self.lead_changes,
            "clutch_moments": len(self.clutch_moments),
            "score_progression": []
        }

        # Sample score progression every 30 seconds
        for snap in self.score_timeline:
            if snap.time % 30 == 0 or snap.time == self.battle_duration:
                report["score_progression"].append({
                    "time": snap.time,
                    "creator": snap.creator_score,
                    "opponent": snap.opponent_score,
                    "diff": snap.score_diff
                })

        return report

    def get_timeline(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get battle timeline of key events."""
        events = []

        # Sample gift events
        step = max(1, len(self.action_timeline) // 30)
        for i, action in enumerate(self.action_timeline):
            if i % step == 0 or action.points >= 500:
                events.append({
                    "time": action.time,
                    "type": "gift",
                    "agent": action.agent,
                    "gift": action.gift_name,
                    "points": action.points,
                    "multiplier": action.multiplier
                })

        # Add combo events
        for combo in self.combo_events:
            events.append({
                "time": combo.time,
                "type": "combo",
                "combo_type": combo.combo_type,
                "initiator": combo.initiator
            })

        # Add tactic events
        for tactic in self.tactic_events:
            events.append({
                "time": tactic.time,
                "type": "tactic",
                "agent": tactic.agent,
                "tactic": tactic.tactic
            })

        # Add clutch moments
        for moment in self.clutch_moments:
            events.append({
                "time": moment.time,
                "type": "clutch",
                "moment_type": moment.moment_type,
                "description": moment.description
            })

        # Add multiplier sessions
        for session in self.multiplier_sessions:
            events.append({
                "time": session.start_time,
                "type": "multiplier_start",
                "session_type": session.session_type,
                "source": session.source
            })

        events.sort(key=lambda x: x["time"])
        return events[:limit]

    def get_full_report(self) -> Dict[str, Any]:
        """Get comprehensive battle report."""
        return {
            "summary": {
                "duration": self.battle_duration,
                "winner": self.winner,
                "final_scores": self.final_scores,
                "margin": self.final_scores.get("creator", 0) - self.final_scores.get("opponent", 0),
                "total_gifts": len(self.action_timeline),
                "total_combos": len(self.combo_events),
                "total_tactics": len(self.tactic_events),
                "clutch_moments": len(self.clutch_moments)
            },
            "gift_efficiency": self.get_gift_efficiency_report(),
            "phase_performance": self.get_phase_performance_report(),
            "agent_contributions": self.get_agent_contribution_report(),
            "combos": self.get_combo_report(),
            "tactics": self.get_tactic_report(),
            "momentum": self.get_momentum_report()
        }


# =============================================================================
# ANALYTICS DASHBOARD
# =============================================================================

class AnalyticsDashboard:
    """
    Rich terminal dashboard for displaying battle analytics.
    """

    def __init__(self, analytics: BattleAnalytics):
        self.analytics = analytics
        self.GREEN = "\033[92m"
        self.RED = "\033[91m"
        self.YELLOW = "\033[93m"
        self.BLUE = "\033[94m"
        self.CYAN = "\033[96m"
        self.BOLD = "\033[1m"
        self.RESET = "\033[0m"

    def _color(self, text: str, color: str) -> str:
        """Apply color to text."""
        return f"{color}{text}{self.RESET}"

    def print_header(self, title: str):
        """Print section header."""
        print("\n" + "-" * 70)
        print(f"   {self.BOLD}{title}{self.RESET}")
        print("-" * 70)

    def print_summary(self):
        """Print battle summary."""
        report = self.analytics.get_full_report()
        summary = report["summary"]

        won = summary["winner"] == "creator"
        result = self._color("VICTORY", self.GREEN) if won else self._color("DEFEAT", self.RED)

        print("\n" + "=" * 70)
        print(f"   {self.BOLD}BATTLE ANALYTICS DASHBOARD{self.RESET}")
        print("=" * 70)

        print(f"\n   Result: {result}")
        creator = summary["final_scores"].get("creator", 0)
        opponent = summary["final_scores"].get("opponent", 0)
        print(f"   Final Score: {self._color(f'{creator:,}', self.GREEN)} vs {self._color(f'{opponent:,}', self.RED)}")

        margin = summary["margin"]
        margin_color = self.GREEN if margin > 0 else self.RED
        print(f"   Margin: {self._color(f'{margin:+,}', margin_color)}")

        print(f"\n   Duration: {summary['duration']}s")
        print(f"   Total Gifts: {summary['total_gifts']}")
        print(f"   Combos: {summary['total_combos']}")
        print(f"   Tactics: {summary['total_tactics']}")
        print(f"   Clutch Moments: {summary['clutch_moments']}")

    def print_gift_efficiency(self):
        """Print gift efficiency analysis."""
        report = self.analytics.get_gift_efficiency_report()

        self.print_header("GIFT EFFICIENCY")

        roi = report["overall_roi"]
        roi_color = self.GREEN if roi >= 1.5 else self.YELLOW if roi >= 1.0 else self.RED
        print(f"\n   Overall ROI: {self._color(f'{roi:.2f}x', roi_color)}")
        print(f"   Total Points: {report['total_points']:,}")
        print(f"   Total Cost: {report['total_cost']:,}")

        if report["top_roi_gifts"]:
            print(f"\n   {self.CYAN}Top ROI Gifts:{self.RESET}")
            for i, g in enumerate(report["top_roi_gifts"], 1):
                roi_str = self._color(f"{g['roi']:.2f}x", self.GREEN if g['roi'] >= 2.0 else self.YELLOW)
                print(f"   {i}. {g['gift']}: {roi_str} ({g['count']} sent)")

        if report["most_used_gifts"]:
            print(f"\n   {self.CYAN}Most Used Gifts:{self.RESET}")
            for i, g in enumerate(report["most_used_gifts"], 1):
                print(f"   {i}. {g['gift']}: {g['count']} times ({g['points']:,} pts)")

    def print_phase_performance(self):
        """Print phase performance breakdown."""
        report = self.analytics.get_phase_performance_report()

        self.print_header("PHASE PERFORMANCE")

        if report["best_phase"]:
            print(f"\n   Best Phase: {self._color(report['best_phase'].upper(), self.GREEN)}")
        if report["worst_phase"]:
            print(f"   Worst Phase: {self._color(report['worst_phase'].upper(), self.RED)}")

        print(f"\n   {'Phase':<10} {'Gifts':<8} {'Points':<12} {'PPS':<10} {'Efficiency':<12}")
        print("   " + "-" * 52)

        for phase_name in ["early", "mid", "late", "final"]:
            if phase_name in report["phases"]:
                data = report["phases"][phase_name]
                if data["gifts_sent"] > 0:
                    eff_color = self.GREEN if data["efficiency"] >= 1.5 else self.YELLOW
                    eff_str = f"{data['efficiency']:.2f}x"
                    print(f"   {phase_name:<10} {data['gifts_sent']:<8} {data['total_points']:<12,} "
                          f"{data['points_per_second']:<10.1f} "
                          f"{self._color(eff_str, eff_color)}")

        mult = report["multiplier_utilization"]
        if mult["boost_gifts"] > 0 or mult["x5_gifts"] > 0:
            print(f"\n   {self.CYAN}Multiplier Utilization:{self.RESET}")
            print(f"   - Boost (x2): {mult['boost_gifts']} gifts, {mult['boost_points']:,} pts")
            print(f"   - x5 Glove: {mult['x5_gifts']} gifts, {mult['x5_points']:,} pts")

    def print_agent_contributions(self):
        """Print agent contribution breakdown."""
        report = self.analytics.get_agent_contribution_report()

        self.print_header("AGENT CONTRIBUTIONS")

        if report["mvp"]:
            mvp_data = report["agents"][report["mvp"]]
            emoji = mvp_data.get("emoji", "")
            print(f"\n   MVP: {emoji} {self._color(report['mvp'], self.YELLOW)} "
                  f"({mvp_data['total_points']:,} pts)")

        if report["most_efficient"]:
            eff_data = report["agents"][report["most_efficient"]]
            emoji = eff_data.get("emoji", "")
            print(f"   Most Efficient: {emoji} {report['most_efficient']} "
                  f"({eff_data['efficiency']:.2f}x ROI)")

        print(f"\n   {'Agent':<22} {'Gifts':<8} {'Points':<12} {'Contrib%':<10} {'Efficiency':<10}")
        print("   " + "-" * 62)

        sorted_agents = sorted(
            report["agents"].items(),
            key=lambda x: x[1]["total_points"],
            reverse=True
        )

        for name, data in sorted_agents:
            emoji = data.get("emoji", "") or ""
            display_name = f"{emoji} {name}"[:20]
            print(f"   {display_name:<22} {data['gifts_sent']:<8} {data['total_points']:<12,} "
                  f"{data['contribution_pct']:<10.1f} {data['efficiency']:.2f}x")

            # Show tactics if any
            if data["tactics_used"]:
                tactics_str = ", ".join(f"{k}:{v}" for k, v in data["tactics_used"].items())
                print(f"      {self.CYAN}Tactics:{self.RESET} {tactics_str}")

    def print_combo_analysis(self):
        """Print combo analysis."""
        report = self.analytics.get_combo_report()

        if report["total_combos"] == 0:
            return

        self.print_header("COMBO ANALYSIS")

        print(f"\n   Total Combos: {report['total_combos']}")
        if report["most_effective_combo"]:
            print(f"   Most Effective: {self._color(report['most_effective_combo'].upper(), self.YELLOW)}")

        print(f"\n   Combo Breakdown:")
        for combo_type, data in report["combo_breakdown"].items():
            print(f"   - {combo_type}: {data['count']} times")

    def print_momentum(self):
        """Print momentum analysis."""
        report = self.analytics.get_momentum_report()

        self.print_header("MOMENTUM ANALYSIS")

        lead_str = f"+{report['largest_lead']:,}"
        deficit_str = f"{report['largest_deficit']:,}"
        print(f"\n   Largest Lead: {self._color(lead_str, self.GREEN)}")
        print(f"   Largest Deficit: {self._color(deficit_str, self.RED)}")
        print(f"   Lead Changes: {report['lead_changes']}")

        if report["score_progression"]:
            print(f"\n   Score Progression:")
            for prog in report["score_progression"]:
                diff = prog["diff"]
                bar_len = min(15, max(1, abs(diff) // 2000))
                if diff > 0:
                    bar = self._color("+" * bar_len, self.GREEN)
                else:
                    bar = self._color("-" * bar_len, self.RED)
                print(f"   t={prog['time']:>3}s: {prog['creator']:>7,} vs {prog['opponent']:>7,}  [{bar}]")

    def print_timeline(self, limit: int = 25):
        """Print battle timeline."""
        timeline = self.analytics.get_timeline(limit)

        if not timeline:
            return

        self.print_header("BATTLE TIMELINE")
        print()

        for event in timeline:
            time_str = f"[{event['time']:>3}s]"

            if event["type"] == "gift":
                mult_str = f" x{event['multiplier']:.0f}" if event["multiplier"] > 1 else ""
                print(f"   {time_str} {event['agent']}: {event['gift']} "
                      f"(+{event['points']:,}){mult_str}")

            elif event["type"] == "combo":
                print(f"   {time_str} {self._color('COMBO', self.YELLOW)}: "
                      f"{event['combo_type'].upper()} by {event['initiator']}")

            elif event["type"] == "tactic":
                print(f"   {time_str} {self._color('TACTIC', self.CYAN)}: "
                      f"{event['agent']} used {event['tactic']}")

            elif event["type"] == "clutch":
                print(f"   {time_str} {self._color('CLUTCH', self.RED)}: "
                      f"{event['moment_type']}")

            elif event["type"] == "multiplier_start":
                session_str = f"{event['session_type']} ACTIVATED"
                print(f"   {time_str} {self._color(session_str, self.GREEN)}")

    def print_full_dashboard(self):
        """Print the complete analytics dashboard."""
        self.print_summary()
        self.print_gift_efficiency()
        self.print_phase_performance()
        self.print_agent_contributions()
        self.print_combo_analysis()
        self.print_momentum()
        self.print_timeline()

        print("\n" + "=" * 70)
        print(f"   {self.BOLD}END OF ANALYTICS REPORT{self.RESET}")
        print("=" * 70 + "\n")


# =============================================================================
# STATS EXPORTER
# =============================================================================

class StatsExporter:
    """
    Export battle and agent statistics to CSV and JSON formats.

    Features:
    - Battle analytics export
    - Agent performance export
    - Tournament results export
    - Batch export for all data
    """

    EXPORT_BANNER = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   📊📊📊  S T A T S   E X P O R T E D  📊📊📊                               ║
║                                                                              ║
║   Format: {format}                                                           ║
║   Path: {path}                                                               ║
║   Records: {records}                                                         ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

    def __init__(self, output_dir: str = "data/exports"):
        """Initialize exporter with output directory."""
        self.output_dir = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    def export_battle_analytics(self, analytics: BattleAnalytics,
                                 battle_id: str,
                                 format: str = "json") -> str:
        """
        Export battle analytics to file.

        Args:
            analytics: BattleAnalytics instance
            battle_id: Battle identifier
            format: 'json' or 'csv'

        Returns:
            Path to exported file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report = analytics.get_full_report()

        if format == "json":
            filepath = Path(self.output_dir) / f"battle_{battle_id}_{timestamp}.json"
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2, default=str)

        elif format == "csv":
            filepath = Path(self.output_dir) / f"battle_{battle_id}_{timestamp}.csv"
            self._write_battle_csv(filepath, battle_id, report)

        else:
            raise ValueError(f"Unknown format: {format}")

        print(self.EXPORT_BANNER.format(
            format=format.upper(),
            path=str(filepath),
            records=1
        ))

        return str(filepath)

    def _write_battle_csv(self, filepath: Path, battle_id: str, report: Dict):
        """Write battle data to CSV."""
        import csv

        summary = report.get("summary", {})
        agents = report.get("agent_contributions", {}).get("agents", {})

        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)

            # Header
            writer.writerow([
                "battle_id", "duration", "winner",
                "creator_score", "opponent_score", "margin",
                "total_gifts", "total_combos", "total_tactics",
                "mvp", "most_efficient"
            ])

            # Data row
            writer.writerow([
                battle_id,
                summary.get("duration", 0),
                summary.get("winner", ""),
                summary.get("final_scores", {}).get("creator", 0),
                summary.get("final_scores", {}).get("opponent", 0),
                summary.get("margin", 0),
                summary.get("total_gifts", 0),
                summary.get("total_combos", 0),
                summary.get("total_tactics", 0),
                report.get("agent_contributions", {}).get("mvp", ""),
                report.get("agent_contributions", {}).get("most_efficient", "")
            ])

            # Agent breakdown
            writer.writerow([])
            writer.writerow(["Agent Performance"])
            writer.writerow([
                "agent", "gifts_sent", "total_points", "efficiency",
                "contribution_pct", "avg_gift_value"
            ])

            for agent, data in agents.items():
                writer.writerow([
                    agent,
                    data.get("gifts_sent", 0),
                    data.get("total_points", 0),
                    data.get("efficiency", 0),
                    data.get("contribution_pct", 0),
                    data.get("avg_gift_value", 0)
                ])

    def export_agent_performance(self, db, agent_name: str,
                                  format: str = "json") -> str:
        """
        Export agent performance history.

        Args:
            db: BattleHistoryDB instance
            agent_name: Agent to export
            format: 'json' or 'csv'

        Returns:
            Path to exported file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stats = db.get_agent_stats(agent_name)
        learning_state = db.load_agent_learning_state(agent_name)

        data = {
            "agent_name": agent_name,
            "exported_at": datetime.now().isoformat(),
            "aggregate_stats": stats,
            "learning_state": learning_state
        }

        if format == "json":
            filepath = Path(self.output_dir) / f"agent_{agent_name}_{timestamp}.json"
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)

        elif format == "csv":
            filepath = Path(self.output_dir) / f"agent_{agent_name}_{timestamp}.csv"
            self._write_agent_csv(filepath, agent_name, stats, learning_state)

        else:
            raise ValueError(f"Unknown format: {format}")

        print(self.EXPORT_BANNER.format(
            format=format.upper(),
            path=str(filepath),
            records=stats.get("total_battles", 0)
        ))

        return str(filepath)

    def _write_agent_csv(self, filepath: Path, agent_name: str,
                          stats: Dict, learning_state: Dict):
        """Write agent data to CSV."""
        import csv

        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)

            # Summary
            writer.writerow(["Agent Performance Summary"])
            writer.writerow(["agent", "total_battles", "wins", "win_rate",
                           "avg_points", "total_points", "glove_success_rate"])
            writer.writerow([
                agent_name,
                stats.get("total_battles", 0),
                stats.get("wins", 0),
                f"{stats.get('win_rate', 0) * 100:.1f}%",
                int(stats.get("avg_points", 0)),
                int(stats.get("total_points", 0)),
                f"{stats.get('glove_success_rate', 0) * 100:.1f}%"
            ])

            # Learning state
            if learning_state:
                writer.writerow([])
                writer.writerow(["Learning State"])
                writer.writerow(["epsilon", "updated_at"])
                writer.writerow([
                    learning_state.get("epsilon", 0),
                    learning_state.get("updated_at", "")
                ])

    def export_tournament_results(self, tournament_stats: Dict,
                                   tournament_id: str,
                                   format: str = "json") -> str:
        """
        Export tournament results.

        Args:
            tournament_stats: Stats from TournamentManager
            tournament_id: Tournament identifier
            format: 'json' or 'csv'

        Returns:
            Path to exported file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        data = {
            "tournament_id": tournament_id,
            "exported_at": datetime.now().isoformat(),
            **tournament_stats
        }

        if format == "json":
            filepath = Path(self.output_dir) / f"tournament_{tournament_id}_{timestamp}.json"
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)

        elif format == "csv":
            filepath = Path(self.output_dir) / f"tournament_{tournament_id}_{timestamp}.csv"
            self._write_tournament_csv(filepath, tournament_id, tournament_stats)

        else:
            raise ValueError(f"Unknown format: {format}")

        num_battles = len(tournament_stats.get("battles", []))
        print(self.EXPORT_BANNER.format(
            format=format.upper(),
            path=str(filepath),
            records=num_battles
        ))

        return str(filepath)

    def _write_tournament_csv(self, filepath: Path, tournament_id: str,
                               stats: Dict):
        """Write tournament data to CSV."""
        import csv

        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)

            # Summary
            writer.writerow(["Tournament Summary"])
            writer.writerow(["tournament_id", "format", "winner",
                           "creator_wins", "opponent_wins", "total_battles"])
            writer.writerow([
                tournament_id,
                stats.get("format", ""),
                stats.get("tournament_winner", ""),
                stats.get("creator_wins", 0),
                stats.get("opponent_wins", 0),
                stats.get("total_battles", 0)
            ])

            # Battles
            writer.writerow([])
            writer.writerow(["Battle Results"])
            writer.writerow(["battle_num", "winner", "creator_score",
                           "opponent_score", "score_diff", "top_contributor"])

            for battle in stats.get("battles", []):
                writer.writerow([
                    battle.get("number", 0),
                    battle.get("winner", ""),
                    battle.get("creator_score", 0),
                    battle.get("opponent_score", 0),
                    battle.get("score_diff", 0),
                    battle.get("top_contributor", "")
                ])

    def export_all_stats(self, db, format: str = "json") -> List[str]:
        """
        Batch export all available data.

        Args:
            db: BattleHistoryDB instance
            format: 'json' or 'csv'

        Returns:
            List of exported file paths
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        exported_files = []

        # Export all battles
        battles = db.get_recent_battles(limit=100)
        if battles:
            filepath = Path(self.output_dir) / f"all_battles_{timestamp}.{format}"
            if format == "json":
                with open(filepath, 'w') as f:
                    json.dump({"battles": battles, "count": len(battles)}, f, indent=2)
            elif format == "csv":
                self._write_all_battles_csv(filepath, battles)
            exported_files.append(str(filepath))

        # Export all agent stats
        all_agent_stats = db.get_all_agent_stats()
        if all_agent_stats:
            filepath = Path(self.output_dir) / f"all_agents_{timestamp}.{format}"
            if format == "json":
                with open(filepath, 'w') as f:
                    json.dump(all_agent_stats, f, indent=2)
            elif format == "csv":
                self._write_all_agents_csv(filepath, all_agent_stats)
            exported_files.append(str(filepath))

        print(f"\n📦 Batch export complete: {len(exported_files)} files exported to {self.output_dir}")
        for fp in exported_files:
            print(f"   - {Path(fp).name}")

        return exported_files

    def _write_all_battles_csv(self, filepath: Path, battles: List[Dict]):
        """Write all battles to CSV."""
        import csv

        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["battle_id", "timestamp", "duration", "winner",
                           "creator_score", "opponent_score", "margin"])

            for battle in battles:
                writer.writerow([
                    battle.get("battle_id", ""),
                    battle.get("timestamp", ""),
                    battle.get("duration", 0),
                    battle.get("winner", ""),
                    battle.get("creator_score", 0),
                    battle.get("opponent_score", 0),
                    battle.get("margin", 0)
                ])

    def _write_all_agents_csv(self, filepath: Path, agents: Dict):
        """Write all agent stats to CSV."""
        import csv

        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["agent_name", "agent_type", "total_battles",
                           "total_wins", "win_rate", "epsilon", "updated_at"])

            for name, stats in agents.items():
                writer.writerow([
                    name,
                    stats.get("agent_type", ""),
                    stats.get("total_battles", 0),
                    stats.get("total_wins", 0),
                    f"{stats.get('win_rate', 0) * 100:.1f}%",
                    stats.get("epsilon", 0),
                    stats.get("updated_at", "")
                ])

    @staticmethod
    def list_exports(output_dir: str = "data/exports") -> List[Dict]:
        """List available export files."""
        exports = []

        if not Path(output_dir).exists():
            return exports

        for filepath in Path(output_dir).iterdir():
            if filepath.suffix in ['.json', '.csv']:
                stat = filepath.stat()
                exports.append({
                    "filename": filepath.name,
                    "path": str(filepath),
                    "format": filepath.suffix[1:].upper(),
                    "size_kb": round(stat.st_size / 1024, 1),
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                })

        exports.sort(key=lambda x: x["modified"], reverse=True)
        return exports

    @staticmethod
    def print_exports(output_dir: str = "data/exports"):
        """Print formatted list of exports."""
        exports = StatsExporter.list_exports(output_dir)

        print("\n" + "=" * 80)
        print("   📊 AVAILABLE EXPORTS")
        print("=" * 80)

        if not exports:
            print(f"   No exports found in {output_dir}")
        else:
            print(f"\n   {'#':<4}{'Filename':<40}{'Format':<8}{'Size':<10}{'Modified':<20}")
            print("   " + "-" * 75)

            for i, exp in enumerate(exports, 1):
                print(f"   {i:<4}{exp['filename'][:38]:<40}{exp['format']:<8}"
                      f"{exp['size_kb']:<10.1f}{exp['modified'][:19]:<20}")

        print("=" * 80 + "\n")
