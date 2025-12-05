#!/usr/bin/env python3
"""
Battle Analyzer - Deep dive into battle data.

Analyzes patterns, correlations, and insights from multiple battles.
"""

import json
from pathlib import Path
from collections import defaultdict, Counter
import statistics


class BattleAnalyzer:
    """Analyze battle data to extract insights."""

    def __init__(self, data_file="data/battles/test_results.json"):
        self.data_file = Path(data_file)
        self.data = None
        self.battles = []

    def load_data(self):
        """Load battle data from JSON."""
        if not self.data_file.exists():
            print(f"❌ Data file not found: {self.data_file}")
            print(f"   Run test_suite.py first to generate battle data.")
            return False

        with open(self.data_file, 'r') as f:
            self.data = json.load(f)
            self.battles = self.data.get("battles", [])

        print(f"✅ Loaded {len(self.battles)} battles from {self.data_file}")
        return True

    def analyze_win_factors(self):
        """Identify what factors correlate with winning."""
        print("\n" + "="*70)
        print("🎯 WIN FACTOR ANALYSIS")
        print("="*70)

        wins = [b for b in self.battles if b["results"]["winner"] == "creator"]
        losses = [b for b in self.battles if b["results"]["winner"] == "opponent"]

        if not wins or not losses:
            print("   ⚠️ Need both wins and losses to compare.")
            return

        # Compare metrics
        metrics = {
            "Gifts Sent": ("statistics", "total_gifts"),
            "Messages": ("statistics", "total_messages"),
            "Emotion Changes": ("statistics", "emotion_changes"),
        }

        print("\nAverage values in winning vs. losing battles:\n")
        print(f"{'Metric':<20} {'Wins':>12} {'Losses':>12} {'Difference':>12}")
        print("-" * 60)

        for metric_name, (category, key) in metrics.items():
            win_vals = [b[category][key] for b in wins]
            loss_vals = [b[category][key] for b in losses]

            win_avg = statistics.mean(win_vals) if win_vals else 0
            loss_avg = statistics.mean(loss_vals) if loss_vals else 0
            diff = win_avg - loss_avg

            print(f"{metric_name:<20} {win_avg:>12.1f} {loss_avg:>12.1f} {diff:>+12.1f}")

    def analyze_agent_effectiveness(self):
        """Which agents contribute most to wins?"""
        print("\n" + "="*70)
        print("🤖 AGENT EFFECTIVENESS ANALYSIS")
        print("="*70)

        # Track agent performance
        agent_stats = defaultdict(lambda: {"total_points": 0, "battles": 0, "wins": 0})

        for battle in self.battles:
            winner = battle["results"]["winner"]
            for agent_name, points in battle["results"]["agent_contributions"].items():
                agent_stats[agent_name]["total_points"] += points
                agent_stats[agent_name]["battles"] += 1
                if winner == "creator":
                    agent_stats[agent_name]["wins"] += 1

        print("\nAgent Performance:\n")
        print(f"{'Agent':<15} {'Battles':>8} {'Wins':>8} {'Win %':>8} {'Avg Pts':>12} {'Total':>12}")
        print("-" * 70)

        for agent_name in sorted(agent_stats.keys()):
            stats = agent_stats[agent_name]
            battles = stats["battles"]
            wins = stats["wins"]
            win_pct = (wins / battles * 100) if battles > 0 else 0
            avg_pts = stats["total_points"] / battles if battles > 0 else 0
            total = stats["total_points"]

            print(f"{agent_name:<15} {battles:>8} {wins:>8} {win_pct:>7.1f}% {avg_pts:>12,.0f} {total:>12,}")

    def analyze_emotional_patterns(self):
        """What emotional patterns emerge?"""
        print("\n" + "="*70)
        print("💭 EMOTIONAL PATTERN ANALYSIS")
        print("="*70)

        # Track emotions per agent
        agent_emotions = defaultdict(Counter)

        for battle in self.battles:
            for emotion_event in battle["timeline"]["emotional_arc"]:
                agent = emotion_event["agent"]
                emotion = emotion_event["emotion"]
                agent_emotions[agent][emotion] += 1

        print("\nMost Common Emotions by Agent:\n")

        for agent_name in sorted(agent_emotions.keys()):
            emotions = agent_emotions[agent_name]
            total = sum(emotions.values())

            print(f"{agent_name}:")
            for emotion, count in emotions.most_common(3):
                pct = count / total * 100 if total > 0 else 0
                print(f"   {emotion:<12} {count:>3} times ({pct:>5.1f}%)")
            print()

    def analyze_timing_patterns(self):
        """When do agents typically act?"""
        print("\n" + "="*70)
        print("⏰ TIMING PATTERN ANALYSIS")
        print("="*70)

        # Track gift timing
        time_buckets = defaultdict(lambda: defaultdict(int))  # {agent: {bucket: count}}

        for battle in self.battles:
            for gift in battle["timeline"]["gifts"]:
                agent = gift["agent"]
                time = int(gift["time"])

                # Bucket into phases
                if time < 20:
                    bucket = "Early (0-20s)"
                elif time < 40:
                    bucket = "Mid (20-40s)"
                elif time < 55:
                    bucket = "Late (40-55s)"
                else:
                    bucket = "Final (55-60s)"

                time_buckets[agent][bucket] += 1

        print("\nGift Distribution by Battle Phase:\n")
        print(f"{'Agent':<15} {'Early':>10} {'Mid':>10} {'Late':>10} {'Final':>10}")
        print("-" * 60)

        for agent_name in sorted(time_buckets.keys()):
            buckets = time_buckets[agent_name]
            print(f"{agent_name:<15} "
                  f"{buckets.get('Early (0-20s)', 0):>10} "
                  f"{buckets.get('Mid (20-40s)', 0):>10} "
                  f"{buckets.get('Late (40-55s)', 0):>10} "
                  f"{buckets.get('Final (55-60s)', 0):>10}")

    def analyze_team_compositions(self):
        """Which team compositions work best?"""
        print("\n" + "="*70)
        print("👥 TEAM COMPOSITION ANALYSIS")
        print("="*70)

        # Group battles by team composition
        team_performance = defaultdict(lambda: {"wins": 0, "total": 0, "avg_score": []})

        for battle in self.battles:
            team = tuple(sorted(battle["config"]["agents"]))
            team_str = ", ".join(team)

            team_performance[team_str]["total"] += 1
            team_performance[team_str]["avg_score"].append(battle["results"]["creator_score"])

            if battle["results"]["winner"] == "creator":
                team_performance[team_str]["wins"] += 1

        print("\nTeam Composition Win Rates:\n")
        print(f"{'Team':<50} {'Battles':>8} {'Wins':>8} {'Win %':>8} {'Avg Score':>12}")
        print("-" * 95)

        for team, stats in sorted(team_performance.items(),
                                  key=lambda x: x[1]["wins"]/x[1]["total"] if x[1]["total"] > 0 else 0,
                                  reverse=True):
            total = stats["total"]
            wins = stats["wins"]
            win_pct = (wins / total * 100) if total > 0 else 0
            avg_score = statistics.mean(stats["avg_score"]) if stats["avg_score"] else 0

            # Truncate long team names
            team_display = team if len(team) <= 47 else team[:44] + "..."

            print(f"{team_display:<50} {total:>8} {wins:>8} {win_pct:>7.1f}% {avg_score:>12,.0f}")

    def find_interesting_battles(self):
        """Identify the most interesting battles."""
        print("\n" + "="*70)
        print("✨ MOST INTERESTING BATTLES")
        print("="*70)

        # Score battles by "interestingness"
        interesting_scores = []

        for battle in self.battles:
            score = 0

            # More messages = more drama
            score += battle["statistics"]["total_messages"] * 2

            # More emotion changes = more dynamic
            score += battle["statistics"]["emotion_changes"]

            # Close battles are exciting
            margin = battle["results"]["margin"]
            creator_score = battle["results"]["creator_score"]
            opponent_score = battle["results"]["opponent_score"]
            total = creator_score + opponent_score

            if total > 0:
                closeness = 1 - (margin / total)  # 0 = blowout, 1 = tie
                score += closeness * 50  # Weight closeness highly

            interesting_scores.append((score, battle))

        # Top 5 most interesting
        interesting_scores.sort(reverse=True, key=lambda x: x[0])

        print("\nTop 5 Most Interesting Battles:\n")

        for i, (score, battle) in enumerate(interesting_scores[:5], 1):
            print(f"{i}. {battle['battle_id']}")
            print(f"   Winner: {battle['results']['winner'].upper()}")
            print(f"   Score: {battle['results']['creator_score']} vs {battle['results']['opponent_score']}")
            print(f"   Messages: {battle['statistics']['total_messages']}, "
                  f"Emotions: {battle['statistics']['emotion_changes']}")
            print(f"   Interestingness Score: {score:.1f}\n")

    def generate_insights_report(self):
        """Generate a comprehensive insights report."""
        print("\n" + "="*70)
        print("💡 KEY INSIGHTS & RECOMMENDATIONS")
        print("="*70 + "\n")

        insights = []

        # Win rate analysis
        wins = sum(1 for b in self.battles if b["results"]["winner"] == "creator")
        win_rate = wins / len(self.battles) if self.battles else 0

        if win_rate > 0.7:
            insights.append("⚠️  Creator wins too often - battles may not be suspenseful enough")
        elif win_rate < 0.3:
            insights.append("⚠️  Creator loses too often - agents may need more power")
        else:
            insights.append("✅ Win rate is balanced - battles are competitive")

        # Message frequency
        avg_messages = statistics.mean([b["statistics"]["total_messages"] for b in self.battles])
        if avg_messages < 10:
            insights.append("💬 Low message count - agents could be more talkative for drama")
        elif avg_messages > 40:
            insights.append("💬 High message count - good narrative/theatrical value")

        # Emotion dynamics
        avg_emotions = statistics.mean([b["statistics"]["emotion_changes"] for b in self.battles])
        if avg_emotions < 20:
            insights.append("😐 Low emotion changes - agents may feel static")
        elif avg_emotions > 50:
            insights.append("🎭 High emotion variance - agents feel alive and reactive")

        for insight in insights:
            print(f"   {insight}")

        print("\n" + "="*70 + "\n")


def main():
    """Run comprehensive battle analysis."""

    print("=" * 70)
    print("📊 TikTok Battle Analyzer - Deep Dive Analysis")
    print("=" * 70)

    analyzer = BattleAnalyzer()

    if not analyzer.load_data():
        return

    # Run all analyses
    analyzer.analyze_win_factors()
    analyzer.analyze_agent_effectiveness()
    analyzer.analyze_emotional_patterns()
    analyzer.analyze_timing_patterns()
    analyzer.analyze_team_compositions()
    analyzer.find_interesting_battles()
    analyzer.generate_insights_report()

    print("✨ Analysis complete!\n")


if __name__ == "__main__":
    main()
