"""
Battle Visualizer - ASCII Charts and Visual Analytics

Provides visual representations of battle data:
- Score progression charts
- Action timeline visualization
- Agent performance comparisons
- Multiplier session timelines
"""

from typing import List, Dict, Any, Tuple
from .battle_analytics import BattleAnalytics


class BattleVisualizer:
    """
    Creates visual representations of battle analytics data.

    Uses ASCII art and formatting to display charts and timelines
    without requiring external graphing libraries.
    """

    @staticmethod
    def create_score_chart(analytics: BattleAnalytics, width: int = 60, height: int = 15) -> str:
        """
        Create ASCII chart of score progression.

        Args:
            analytics: BattleAnalytics instance with data
            width: Chart width in characters
            height: Chart height in lines

        Returns:
            Multi-line string with ASCII chart
        """
        progression = analytics.get_score_progression()
        if not progression:
            return "No score data available"

        lines = []
        lines.append("\n📈 SCORE PROGRESSION CHART")
        lines.append("=" * (width + 10))

        # Get score ranges
        max_score = max(
            max(p['creator'] for p in progression),
            max(p['opponent'] for p in progression)
        )
        min_score = 0

        # Create chart
        for row in range(height):
            # Calculate score value for this row (top to bottom)
            score_value = int(max_score - (row * max_score / height))
            line = f"{score_value:6,} |"

            # Sample points across the timeline
            for col in range(width):
                # Map column to time index
                time_idx = int(col * len(progression) / width)
                if time_idx >= len(progression):
                    time_idx = len(progression) - 1

                point = progression[time_idx]
                creator = point['creator']
                opponent = point['opponent']

                # Determine what to plot
                creator_here = abs(creator - score_value) < (max_score / height)
                opponent_here = abs(opponent - score_value) < (max_score / height)

                if creator_here and opponent_here:
                    line += "X"  # Both lines overlap
                elif creator_here:
                    line += "█"  # Creator line
                elif opponent_here:
                    line += "░"  # Opponent line
                else:
                    line += " "

            lines.append(line)

        # Add time axis
        lines.append(" " * 7 + "+" + "-" * width)
        time_labels = "       0s"
        time_labels += " " * (width - 20) + f"{progression[-1]['time']}s"
        lines.append(time_labels)

        # Add legend
        lines.append("\n  Legend: █ Creator  ░ Opponent  X Both")
        lines.append("=" * (width + 10) + "\n")

        return "\n".join(lines)

    @staticmethod
    def create_action_timeline(analytics: BattleAnalytics, width: int = 70) -> str:
        """
        Create visual timeline of major actions.

        Args:
            analytics: BattleAnalytics instance
            width: Timeline width in characters

        Returns:
            Multi-line string with timeline
        """
        timeline = analytics.get_action_timeline()
        if not timeline:
            return "No actions recorded"

        lines = []
        lines.append("\n⏱️  ACTION TIMELINE")
        lines.append("=" * width)

        battle_duration = analytics.battle_duration

        # Create timeline bar
        timeline_bar = [" "] * width

        # Mark actions on timeline
        for action in timeline:
            time_pos = int((action['time'] / battle_duration) * width)
            if time_pos >= width:
                time_pos = width - 1

            # Use different symbols for different agents
            if "Kinetik" in action['agent']:
                timeline_bar[time_pos] = "🎯"
            elif "Strike" in action['agent']:
                timeline_bar[time_pos] = "⚡"
            elif "Activator" in action['agent']:
                timeline_bar[time_pos] = "📊"
            elif "Sentinel" in action['agent']:
                timeline_bar[time_pos] = "🛡️"
            else:
                timeline_bar[time_pos] = "●"

        # Print timeline
        lines.append("0s |" + "".join(timeline_bar) + f"| {battle_duration}s")

        # Add action details
        lines.append("\nKEY ACTIONS:")
        for action in timeline[:10]:  # Show first 10
            emoji = "🎁"
            lines.append(
                f"  [{action['time']:3d}s] {emoji} {action['agent']}: "
                f"{action['gift'] or 'Unknown'} ({action['points']:,} pts)"
            )

        if len(timeline) > 10:
            lines.append(f"  ... and {len(timeline) - 10} more actions")

        lines.append("=" * width + "\n")
        return "\n".join(lines)

    @staticmethod
    def create_agent_comparison(analytics: BattleAnalytics) -> str:
        """
        Create bar chart comparing agent performance.

        Args:
            analytics: BattleAnalytics instance

        Returns:
            Multi-line string with comparison chart
        """
        performance = analytics.get_agent_performance()
        if not performance:
            return "No agent data available"

        lines = []
        lines.append("\n👥 AGENT PERFORMANCE COMPARISON")
        lines.append("=" * 70)

        # Sort by total donated
        sorted_agents = sorted(
            performance.items(),
            key=lambda x: x[1]['total_donated'],
            reverse=True
        )

        max_donated = max(p[1]['total_donated'] for p in sorted_agents) if sorted_agents else 1

        for agent, stats in sorted_agents:
            donated = stats['total_donated']
            bar_width = int((donated / max_donated) * 40) if max_donated > 0 else 0
            bar = "█" * bar_width

            lines.append(f"\n{agent:15s} {donated:8,} pts")
            lines.append(f"                {bar}")
            lines.append(
                f"                Gifts: {stats['gifts_sent']} | "
                f"Avg: {stats['avg_gift_value']:,.0f} | "
                f"Best: {stats['best_gift']['name']}"
            )

        lines.append("\n" + "=" * 70 + "\n")
        return "\n".join(lines)

    @staticmethod
    def create_multiplier_timeline(analytics: BattleAnalytics, width: int = 70) -> str:
        """
        Create visual timeline of multiplier sessions.

        Args:
            analytics: BattleAnalytics instance
            width: Timeline width

        Returns:
            Multi-line string with multiplier timeline
        """
        sessions = analytics.multiplier_sessions
        if not sessions:
            return "No multiplier sessions recorded"

        lines = []
        lines.append("\n⚡ MULTIPLIER SESSION TIMELINE")
        lines.append("=" * width)

        battle_duration = analytics.battle_duration

        # Create timeline representation
        timeline = [" "] * width

        # Mark each session
        for session in sessions:
            start_pos = int((session.start_time / battle_duration) * width)
            end_pos = int((session.end_time / battle_duration) * width)

            # Fill session duration
            symbol = "▓" if session.session_type == "x3" else "▒"
            for pos in range(start_pos, min(end_pos + 1, width)):
                timeline[pos] = symbol

        # Print timeline
        lines.append("0s |" + "".join(timeline) + f"| {battle_duration}s")

        # Add legend
        lines.append("\n  ▓ = x3 session   ▒ = x2 session")

        # Session details
        lines.append("\nSESSION DETAILS:")
        for i, session in enumerate(sessions, 1):
            lines.append(
                f"  {i}. {session.session_type} @ {session.start_time}s-{session.end_time}s "
                f"({session.duration}s, {session.source})"
            )

        # Summary
        mult_analysis = analytics.get_multiplier_analysis()
        lines.append(f"\nTotal coverage: {mult_analysis['coverage']:.1f}% of battle")
        lines.append("=" * width + "\n")

        return "\n".join(lines)

    @staticmethod
    def create_complete_report(analytics: BattleAnalytics) -> str:
        """
        Create complete visual analytics report.

        Args:
            analytics: BattleAnalytics instance

        Returns:
            Complete multi-page report as string
        """
        report = []

        report.append("\n" + "=" * 70)
        report.append("📊 COMPLETE BATTLE ANALYTICS REPORT")
        report.append("=" * 70)

        # Battle summary
        summary = analytics.get_complete_summary()
        battle = summary['battle']
        report.append(f"\n🏆 BATTLE SUMMARY")
        report.append(f"   Winner: {battle['winner'].upper()}")
        report.append(f"   Duration: {battle['duration']}s")
        report.append(f"   Final: Creator {battle['final_scores']['creator']:,} vs "
                     f"Opponent {battle['final_scores']['opponent']:,}")
        report.append(f"   Margin: {abs(battle['score_diff']):,} points")

        # Visual charts
        report.append(BattleVisualizer.create_score_chart(analytics))
        report.append(BattleVisualizer.create_agent_comparison(analytics))
        report.append(BattleVisualizer.create_action_timeline(analytics))
        report.append(BattleVisualizer.create_multiplier_timeline(analytics))

        # Data summary
        report.append("\n📈 DATA COLLECTED:")
        report.append(f"   Score snapshots: {len(analytics.score_timeline)}")
        report.append(f"   Actions tracked: {len(analytics.action_timeline)}")
        report.append(f"   Agents analyzed: {len(analytics.agent_stats)}")
        report.append(f"   Multiplier sessions: {len(analytics.multiplier_sessions)}")

        report.append("\n" + "=" * 70)
        report.append("✅ End of Report")
        report.append("=" * 70 + "\n")

        return "\n".join(report)
