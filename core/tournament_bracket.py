"""
Tournament Bracket Visualization

ASCII art bracket display for Best of 3/5 tournaments.
Shows current series progress and battle results.
"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass

# Import visual utilities
from .visual_utils import (
    Colors, ProgressBar, ASCIIFrames, DramaticAnnouncements,
    BracketVisualizer as VisualBracket, print_separator
)


@dataclass
class BracketBattle:
    """Single battle representation in bracket."""
    battle_num: int
    creator_score: Optional[int] = None
    opponent_score: Optional[int] = None
    winner: Optional[str] = None  # "creator" or "opponent"
    completed: bool = False


class TournamentBracket:
    """
    Visual bracket display for Best of 3/5 tournaments.

    Shows:
    - Current series score
    - Each battle result
    - Series winner
    - Visual progress indicators
    """

    def __init__(self, format_name: str = "BEST_OF_3", battles_to_win: int = 2):
        """
        Initialize tournament bracket.

        Args:
            format_name: "BEST_OF_3" or "BEST_OF_5"
            battles_to_win: Number of wins needed (2 for BO3, 3 for BO5)
        """
        self.format_name = format_name
        self.battles_to_win = battles_to_win
        self.max_battles = battles_to_win * 2 - 1  # 3 for BO3, 5 for BO5

        # Track battles
        self.battles: List[BracketBattle] = []
        self.creator_wins = 0
        self.opponent_wins = 0
        self.series_winner: Optional[str] = None

    def add_battle_result(self, battle_num: int, creator_score: int,
                         opponent_score: int, winner: str):
        """
        Add a completed battle to the bracket.

        Args:
            battle_num: Battle number (1-indexed)
            creator_score: Creator final score
            opponent_score: Opponent final score
            winner: "creator" or "opponent"
        """
        battle = BracketBattle(
            battle_num=battle_num,
            creator_score=creator_score,
            opponent_score=opponent_score,
            winner=winner,
            completed=True
        )
        self.battles.append(battle)

        # Update wins
        if winner == "creator":
            self.creator_wins += 1
        else:
            self.opponent_wins += 1

        # Check for series win
        if self.creator_wins >= self.battles_to_win:
            self.series_winner = "creator"
        elif self.opponent_wins >= self.battles_to_win:
            self.series_winner = "opponent"

    def print_bracket(self):
        """Print enhanced ASCII art tournament bracket with rich visuals."""
        width = 70

        # Create dramatic header
        header_lines = [
            "",
            f"🏆  {self.format_name}  🏆",
            "TOURNAMENT BRACKET",
            "",
        ]
        print(ASCIIFrames.frame(header_lines, width=width, box_style="double",
                                color=Colors.CYAN))

        # Series progress visualization
        print(f"\n   {Colors.BOLD}SERIES SCORE{Colors.RESET}")
        print("   " + "─" * 60)

        # Progress bar for each side
        bar = ProgressBar(width=20, style="stars")
        creator_progress = self.creator_wins / self.battles_to_win
        opponent_progress = self.opponent_wins / self.battles_to_win

        creator_bar = bar.render(creator_progress, show_percent=False, color=Colors.GREEN)
        opponent_bar = bar.render(opponent_progress, show_percent=False, color=Colors.RED)

        print(f"   {Colors.GREEN}CREATOR{Colors.RESET}  {creator_bar}  {self.creator_wins}/{self.battles_to_win} wins")
        print(f"   {Colors.RED}OPPONENT{Colors.RESET} {opponent_bar}  {self.opponent_wins}/{self.battles_to_win} wins")
        print("   " + "─" * 60)

        # Series status
        if self.series_winner:
            print()
            if self.series_winner == "creator":
                print(DramaticAnnouncements.victory("CREATOR", 0))
            else:
                print(DramaticAnnouncements.defeat("OPPONENT", 0))
        else:
            print(f"\n   {Colors.YELLOW}First to {self.battles_to_win} wins advances!{Colors.RESET}\n")

        # Battle results with visual enhancement
        print(f"\n   {Colors.BOLD}BATTLE RESULTS{Colors.RESET}")
        print("   ╔" + "═" * 58 + "╗")

        for i in range(1, self.max_battles + 1):
            self._print_battle_line_enhanced(i)

        print("   ╚" + "═" * 58 + "╝\n")

    def _print_battle_line_enhanced(self, battle_num: int):
        """Print an enhanced single battle line."""
        battle = next((b for b in self.battles if b.battle_num == battle_num), None)

        if battle and battle.completed:
            # Completed battle with bars
            total = battle.creator_score + battle.opponent_score
            c_pct = battle.creator_score / total if total > 0 else 0.5

            bar_width = 20
            c_bars = int(c_pct * bar_width)
            o_bars = bar_width - c_bars

            if battle.winner == "creator":
                c_icon = f"{Colors.GREEN}✓{Colors.RESET}"
                o_icon = f"{Colors.RED}✗{Colors.RESET}"
                c_color = Colors.GREEN
                o_color = Colors.DIM
            else:
                c_icon = f"{Colors.RED}✗{Colors.RESET}"
                o_icon = f"{Colors.GREEN}✓{Colors.RESET}"
                c_color = Colors.DIM
                o_color = Colors.GREEN

            score_bar = f"{c_color}{'█' * c_bars}{o_color}{'█' * o_bars}{Colors.RESET}"

            print(f"   ║  Battle {battle_num} {c_icon}  "
                  f"[{score_bar}]  "
                  f"{battle.creator_score:>6,} vs {battle.opponent_score:<6,}  {o_icon}  ║")
        else:
            if self.series_winner:
                print(f"   ║  Battle {battle_num}     "
                      f"{Colors.DIM}────── Not Played ──────{Colors.RESET}"
                      f"                        ║")
            else:
                print(f"   ║  Battle {battle_num}     "
                      f"{Colors.YELLOW}────── Upcoming ────────{Colors.RESET}"
                      f"                        ║")

    def _format_wins(self, wins: int) -> str:
        """Format win count with visual indicators."""
        stars = "⭐" * wins
        empty = "☆" * (self.battles_to_win - wins)
        return f"{wins} WINS {stars}{empty}"

    def _print_battle_line(self, battle_num: int):
        """Print a single battle line in the bracket."""
        # Find battle if it exists
        battle = next((b for b in self.battles if b.battle_num == battle_num), None)

        if battle and battle.completed:
            # Completed battle
            creator_icon = "✅" if battle.winner == "creator" else "❌"
            opponent_icon = "✅" if battle.winner == "opponent" else "❌"

            print(f"  Battle {battle_num}:  "
                  f"{creator_icon} Creator {battle.creator_score:>6,}  "
                  f"│  "
                  f"Opponent {battle.opponent_score:>6,} {opponent_icon}")
        else:
            # Not yet played
            if self.series_winner:
                # Series already over, this battle won't be played
                print(f"  Battle {battle_num}:  {'─' * 20}  │  {'─' * 20}  (Not played)")
            else:
                # Upcoming battle
                print(f"  Battle {battle_num}:  {'·' * 20}  │  {'·' * 20}  (Upcoming)")

    def print_compact_bracket(self):
        """Print a more compact bracket view."""
        print(f"\n🏆 {self.format_name}: "
              f"Creator {self.creator_wins} - {self.opponent_wins} Opponent "
              f"(First to {self.battles_to_win})")

        # One-line battle results
        results = []
        for battle in self.battles:
            if battle.completed:
                winner_mark = "C" if battle.winner == "creator" else "O"
                results.append(f"[{battle.battle_num}:{winner_mark}]")

        if results:
            print(f"   Battles: {' '.join(results)}")

        if self.series_winner:
            print(f"   🏆 {self.series_winner.upper()} WINS!\n")
        else:
            print()

    def get_bracket_state(self) -> Dict[str, Any]:
        """
        Get bracket state as dictionary for JSON serialization.

        Returns:
            Dictionary with complete bracket state
        """
        return {
            "format": self.format_name,
            "battles_to_win": self.battles_to_win,
            "max_battles": self.max_battles,
            "creator_wins": self.creator_wins,
            "opponent_wins": self.opponent_wins,
            "series_winner": self.series_winner,
            "battles": [
                {
                    "battle_num": b.battle_num,
                    "creator_score": b.creator_score,
                    "opponent_score": b.opponent_score,
                    "winner": b.winner,
                    "completed": b.completed
                }
                for b in self.battles
            ]
        }


class BracketVisualizer:
    """
    Advanced bracket visualizations with ASCII art.
    """

    @staticmethod
    def print_series_progress_bar(creator_wins: int, opponent_wins: int,
                                  battles_to_win: int):
        """
        Print visual progress bar showing series status.

        Args:
            creator_wins: Creator win count
            opponent_wins: Opponent win count
            battles_to_win: Wins needed to win series
        """
        width = 50
        print("\nSeries Progress:")

        # Creator progress
        creator_progress = int((creator_wins / battles_to_win) * (width / 2))
        opponent_progress = int((opponent_wins / battles_to_win) * (width / 2))

        creator_bar = "█" * creator_progress + "░" * (width // 2 - creator_progress)
        opponent_bar = "░" * (width // 2 - opponent_progress) + "█" * opponent_progress

        print(f"Creator   [{creator_bar}] {creator_wins}/{battles_to_win}")
        print(f"Opponent  [{opponent_bar}] {opponent_wins}/{battles_to_win}")
        print()

    @staticmethod
    def print_battle_timeline(battles: List[BracketBattle]):
        """
        Print horizontal timeline of battle results.

        Args:
            battles: List of completed battles
        """
        if not battles:
            return

        print("\nBattle Timeline:")
        print("─" * 70)

        # Timeline header
        timeline = "  "
        for battle in battles:
            timeline += f"Battle {battle.battle_num}     "
        print(timeline)

        # Winner indicators
        winners = "  "
        for battle in battles:
            if battle.winner == "creator":
                winners += "    🔵       "
            else:
                winners += "    🔴       "
        print(winners)

        # Legend
        print("  🔵 = Creator Win  |  🔴 = Opponent Win")
        print("─" * 70 + "\n")

    @staticmethod
    def print_score_comparison(battles: List[BracketBattle]):
        """
        Print score comparison across all battles.

        Args:
            battles: List of completed battles
        """
        if not battles:
            return

        print("\nScore Comparison:")
        print("─" * 70)

        for battle in battles:
            if not battle.completed:
                continue

            # Calculate bar lengths (max 30 chars each side)
            max_score = max(battle.creator_score, battle.opponent_score)
            creator_bar_len = int((battle.creator_score / max_score) * 30) if max_score > 0 else 0
            opponent_bar_len = int((battle.opponent_score / max_score) * 30) if max_score > 0 else 0

            # Build bars
            creator_bar = "█" * creator_bar_len
            opponent_bar = "█" * opponent_bar_len

            # Print
            print(f"Battle {battle.battle_num}:")
            print(f"  Creator   {creator_bar:>30} {battle.creator_score:>7,}")
            print(f"  Opponent  {opponent_bar:>30} {battle.opponent_score:>7,}")
            print()

        print("─" * 70 + "\n")


# =============================================================================
# MULTI-TEAM TOURNAMENT SYSTEM
# =============================================================================

@dataclass
class TournamentTeam:
    """Represents a team/participant in the tournament."""
    name: str
    seed: int
    emoji: str = ""
    wins: int = 0
    losses: int = 0
    points_scored: int = 0
    points_allowed: int = 0
    eliminated: bool = False

    @property
    def point_differential(self) -> int:
        return self.points_scored - self.points_allowed

    @property
    def win_rate(self) -> float:
        total = self.wins + self.losses
        return self.wins / total if total > 0 else 0.0


@dataclass
class TournamentMatch:
    """Single match in the tournament bracket."""
    match_id: int
    round_num: int
    team1: Optional['TournamentTeam'] = None
    team2: Optional['TournamentTeam'] = None
    team1_score: int = 0
    team2_score: int = 0
    winner: Optional['TournamentTeam'] = None
    completed: bool = False
    next_match_id: Optional[int] = None  # Winner advances here


class EliminationTournament:
    """
    Full elimination tournament system.

    Supports:
    - 4, 8, 16, 32 team brackets
    - Single or double elimination
    - Seeding based on rankings
    - Round-by-round progression
    - Championship finals
    """

    def __init__(self, teams: List['TournamentTeam'],
                 elimination_type: str = "single",
                 championship_best_of: int = 3):
        """
        Initialize tournament.

        Args:
            teams: List of TournamentTeam objects
            elimination_type: "single" or "double"
            championship_best_of: 1, 3, or 5 for finals
        """
        self.original_teams = teams
        self.elimination_type = elimination_type
        self.championship_best_of = championship_best_of

        # Validate team count (must be power of 2)
        valid_sizes = [2, 4, 8, 16, 32]
        if len(teams) not in valid_sizes:
            # Pad with byes if needed
            target_size = min(s for s in valid_sizes if s >= len(teams))
            while len(teams) < target_size:
                bye_team = TournamentTeam(
                    name="BYE", seed=999, emoji="⬜", eliminated=True
                )
                teams.append(bye_team)

        self.teams = sorted(teams, key=lambda t: t.seed)
        self.num_teams = len(self.teams)
        self.num_rounds = self._calculate_rounds()

        # Match tracking
        self.matches: Dict[int, TournamentMatch] = {}
        self.current_round = 1
        self.champion: Optional[TournamentTeam] = None

        # Round names
        self.round_names = self._get_round_names()

        # Initialize bracket
        self._setup_bracket()

    def _calculate_rounds(self) -> int:
        """Calculate number of rounds needed."""
        import math
        return int(math.log2(self.num_teams))

    def _get_round_names(self) -> Dict[int, str]:
        """Get display names for each round."""
        names = {}
        total = self.num_rounds

        for r in range(1, total + 1):
            remaining = total - r + 1
            if remaining == 1:
                names[r] = "🏆 GRAND FINALS"
            elif remaining == 2:
                names[r] = "SEMIFINALS"
            elif remaining == 3:
                names[r] = "QUARTERFINALS"
            else:
                names[r] = f"ROUND {r}"

        return names

    def _setup_bracket(self):
        """Setup initial bracket with seeded matchups."""
        # Create seeded pairings (1v8, 4v5, 3v6, 2v7 pattern)
        pairings = self._create_seeded_pairings()

        # Calculate total matches: n-1 for single elimination
        total_matches = self.num_teams - 1

        # Build match structure from end to beginning
        # For 8 teams: matches 5,6 feed to 7 (finals), matches 1-4 feed to 5,6

        match_id = 1

        # Round 1 matches (quarterfinals for 8 teams)
        round1_count = self.num_teams // 2
        for i in range(round1_count):
            # Next match for this pairing
            next_match_id = round1_count + 1 + (i // 2) if self.num_rounds > 1 else None

            match = TournamentMatch(
                match_id=match_id,
                round_num=1,
                team1=pairings[i][0] if i < len(pairings) else None,
                team2=pairings[i][1] if i < len(pairings) else None,
                next_match_id=next_match_id
            )

            # Auto-advance if BYE
            if match.team2 and match.team2.name == "BYE":
                match.winner = match.team1
                match.completed = True
                match.team1_score = 1
                match.team2_score = 0
            elif match.team1 and match.team1.name == "BYE":
                match.winner = match.team2
                match.completed = True
                match.team1_score = 0
                match.team2_score = 1

            self.matches[match_id] = match
            match_id += 1

        # Create later round matches
        current_match_count = round1_count // 2
        for round_num in range(2, self.num_rounds + 1):
            round_start = match_id
            for i in range(current_match_count):
                # Next match (if not finals)
                if round_num < self.num_rounds:
                    next_match_id = round_start + current_match_count + (i // 2)
                else:
                    next_match_id = None

                match = TournamentMatch(
                    match_id=match_id,
                    round_num=round_num,
                    next_match_id=next_match_id
                )
                self.matches[match_id] = match
                match_id += 1

            current_match_count //= 2

    def _create_seeded_pairings(self) -> List[tuple]:
        """Create seeded pairings (1v8, 4v5, 3v6, 2v7 for 8 teams)."""
        n = self.num_teams
        teams = self.teams.copy()

        # Standard bracket seeding
        pairings = []
        for i in range(n // 2):
            if i % 2 == 0:
                pairings.append((teams[i], teams[n - 1 - i]))
            else:
                pairings.append((teams[n - 1 - i], teams[i]))

        # Reorder for proper bracket flow
        # This ensures top seeds are on opposite sides
        ordered = []
        if n == 4:
            ordered = [pairings[0], pairings[1]]
        elif n == 8:
            ordered = [pairings[0], pairings[3], pairings[2], pairings[1]]
        elif n == 16:
            # More complex reordering for 16 teams
            indices = [0, 7, 4, 3, 2, 5, 6, 1]
            ordered = [pairings[i] for i in indices]
        else:
            ordered = pairings  # Default for other sizes

        return ordered

    def record_match_result(self, match_id: int, team1_score: int, team2_score: int):
        """
        Record the result of a match.

        Args:
            match_id: ID of the match
            team1_score: Score for team 1
            team2_score: Score for team 2
        """
        if match_id not in self.matches:
            raise ValueError(f"Match {match_id} not found")

        match = self.matches[match_id]
        if match.completed:
            raise ValueError(f"Match {match_id} already completed")

        if not match.team1 or not match.team2:
            raise ValueError(f"Match {match_id} teams not yet determined")

        match.team1_score = team1_score
        match.team2_score = team2_score
        match.completed = True

        # Determine winner
        if team1_score > team2_score:
            match.winner = match.team1
            match.team1.wins += 1
            match.team2.losses += 1
            match.team2.eliminated = True
        else:
            match.winner = match.team2
            match.team2.wins += 1
            match.team1.losses += 1
            match.team1.eliminated = True

        # Update point totals
        match.team1.points_scored += team1_score
        match.team1.points_allowed += team2_score
        match.team2.points_scored += team2_score
        match.team2.points_allowed += team1_score

        # Advance winner to next match
        if match.next_match_id:
            next_match = self.matches[match.next_match_id]
            if next_match.team1 is None:
                next_match.team1 = match.winner
            else:
                next_match.team2 = match.winner
        else:
            # This was the final - we have a champion!
            self.champion = match.winner

        # Update current round
        self._update_current_round()

    def _update_current_round(self):
        """Update current round based on completed matches."""
        for round_num in range(1, self.num_rounds + 1):
            round_matches = [m for m in self.matches.values() if m.round_num == round_num]
            if not all(m.completed for m in round_matches):
                self.current_round = round_num
                return
        self.current_round = self.num_rounds + 1  # Tournament complete

    def get_current_matches(self) -> List[TournamentMatch]:
        """Get matches available to play in current round."""
        return [
            m for m in self.matches.values()
            if m.round_num == self.current_round
            and not m.completed
            and m.team1 is not None
            and m.team2 is not None
            and m.team1.name != "BYE"
            and m.team2.name != "BYE"
        ]

    def get_round_matches(self, round_num: int) -> List[TournamentMatch]:
        """Get all matches in a specific round."""
        return sorted(
            [m for m in self.matches.values() if m.round_num == round_num],
            key=lambda m: m.match_id
        )

    def is_complete(self) -> bool:
        """Check if tournament is complete."""
        return self.champion is not None

    def print_bracket(self):
        """Print enhanced full tournament bracket."""
        width = 80

        # Create dramatic header
        header_lines = [
            "",
            f"🏆 {self.num_teams}-TEAM ELIMINATION 🏆",
            f"{self.elimination_type.upper()} ELIMINATION",
            "",
        ]
        print(ASCIIFrames.frame(header_lines, width=width, box_style="double",
                                color=Colors.CYAN))

        if self.champion:
            print()
            print(DramaticAnnouncements.tournament_champion(
                self.champion.name, self.champion.emoji
            ))
            print()

        # Print each round with enhanced visuals
        for round_num in range(1, self.num_rounds + 1):
            self._print_round_enhanced(round_num)

        print("═" * width + "\n")

    def _print_round(self, round_num: int):
        """Print a single round of matches."""
        matches = self.get_round_matches(round_num)
        round_name = self.round_names.get(round_num, f"ROUND {round_num}")

        print(f"\n{'-' * 40}")
        print(f"  {round_name}")
        print(f"{'-' * 40}")

        for match in matches:
            self._print_match(match)

    def _print_round_enhanced(self, round_num: int):
        """Print an enhanced single round of matches."""
        matches = self.get_round_matches(round_num)
        round_name = self.round_names.get(round_num, f"ROUND {round_num}")

        # Color based on round importance
        if "FINALS" in round_name:
            color = Colors.YELLOW
        elif "SEMI" in round_name:
            color = Colors.CYAN
        else:
            color = Colors.WHITE

        print(f"\n   {color}{'─' * 60}{Colors.RESET}")
        print(f"   {color}{Colors.BOLD}  {round_name}  {Colors.RESET}")
        print(f"   {color}{'─' * 60}{Colors.RESET}")

        for match in matches:
            self._print_match_enhanced(match)

    def _print_match(self, match: TournamentMatch):
        """Print a single match."""
        if match.team1 is None or match.team2 is None:
            print(f"  Match {match.match_id}: TBD vs TBD")
            return

        t1 = match.team1
        t2 = match.team2

        if match.completed:
            # Show completed match
            w1 = "✓" if match.winner == t1 else " "
            w2 = "✓" if match.winner == t2 else " "
            print(f"  Match {match.match_id}: "
                  f"[{w1}] ({t1.seed}) {t1.emoji} {t1.name:<15} {match.team1_score:>6,}"
                  f"  vs  "
                  f"{match.team2_score:>6,} {t2.emoji} {t2.name:<15} ({t2.seed}) [{w2}]")
        else:
            # Show upcoming match
            print(f"  Match {match.match_id}: "
                  f"    ({t1.seed}) {t1.emoji} {t1.name:<15}"
                  f"  vs  "
                  f"{t2.emoji} {t2.name:<15} ({t2.seed})")

    def _print_match_enhanced(self, match: TournamentMatch):
        """Print an enhanced single match with visual elements."""
        if match.team1 is None or match.team2 is None:
            print(f"   ║  Match {match.match_id}: {Colors.DIM}TBD vs TBD{Colors.RESET}")
            return

        t1 = match.team1
        t2 = match.team2

        if match.completed:
            # Create score bar
            total = match.team1_score + match.team2_score
            t1_pct = match.team1_score / total if total > 0 else 0.5

            bar_width = 20
            t1_bars = int(t1_pct * bar_width)
            t2_bars = bar_width - t1_bars

            if match.winner == t1:
                t1_color = Colors.GREEN
                t2_color = Colors.DIM
                t1_mark = f"{Colors.GREEN}✓{Colors.RESET}"
                t2_mark = f"{Colors.RED}✗{Colors.RESET}"
            else:
                t1_color = Colors.DIM
                t2_color = Colors.GREEN
                t1_mark = f"{Colors.RED}✗{Colors.RESET}"
                t2_mark = f"{Colors.GREEN}✓{Colors.RESET}"

            score_bar = f"{t1_color}{'█' * t1_bars}{t2_color}{'█' * t2_bars}{Colors.RESET}"

            print(f"   ║")
            print(f"   ║  Match {match.match_id}:")
            print(f"   ║    {t1_mark} #{t1.seed} {t1.emoji} {t1.name:<14} {t1_color}{match.team1_score:>7,}{Colors.RESET}")
            print(f"   ║       [{score_bar}]")
            print(f"   ║    {t2_mark} #{t2.seed} {t2.emoji} {t2.name:<14} {t2_color}{match.team2_score:>7,}{Colors.RESET}")
        else:
            # Upcoming match
            print(f"   ║")
            print(f"   ║  Match {match.match_id}: {Colors.YELLOW}UPCOMING{Colors.RESET}")
            print(f"   ║    #{t1.seed} {t1.emoji} {t1.name}")
            print(f"   ║       {Colors.DIM}vs{Colors.RESET}")
            print(f"   ║    #{t2.seed} {t2.emoji} {t2.name}")

    def print_standings(self):
        """Print enhanced current standings/rankings."""
        # Header
        header_lines = [
            "",
            "📊 TOURNAMENT STANDINGS",
            "",
        ]
        print(ASCIIFrames.frame(header_lines, width=65, box_style="bold",
                                color=Colors.CYAN))

        # Sort by: eliminated last, then by wins, then by point diff
        sorted_teams = sorted(
            [t for t in self.teams if t.name != "BYE"],
            key=lambda t: (not t.eliminated, t.wins, t.point_differential),
            reverse=True
        )

        print(f"\n   {Colors.BOLD}{'Rank':<6} {'Team':<20} {'W-L':<8} {'Diff':>10} {'Status':<12}{Colors.RESET}")
        print("   " + "─" * 56)

        for i, team in enumerate(sorted_teams, 1):
            # Rank medal
            if team == self.champion:
                rank = "🏆"
            elif i == 2:
                rank = "🥈"
            elif i == 3:
                rank = "🥉"
            else:
                rank = f"#{i}"

            # Status with color
            if team == self.champion:
                status = f"{Colors.YELLOW}CHAMPION{Colors.RESET}"
            elif team.eliminated:
                status = f"{Colors.DIM}Eliminated{Colors.RESET}"
            else:
                status = f"{Colors.GREEN}Active{Colors.RESET}"

            # Point differential with color
            diff = team.point_differential
            if diff > 0:
                diff_str = f"{Colors.GREEN}+{diff:,}{Colors.RESET}"
            elif diff < 0:
                diff_str = f"{Colors.RED}{diff:,}{Colors.RESET}"
            else:
                diff_str = f"{Colors.DIM}0{Colors.RESET}"

            # Team name with color based on status
            if team == self.champion:
                name_color = Colors.YELLOW
            elif team.eliminated:
                name_color = Colors.DIM
            else:
                name_color = Colors.RESET

            print(f"   {rank:<6} {team.emoji} {name_color}{team.name:<17}{Colors.RESET} "
                  f"{team.wins}-{team.losses:<5} {diff_str:>15} {status}")

        print("   " + "─" * 56 + "\n")

    def print_upcoming(self):
        """Print upcoming matches."""
        upcoming = self.get_current_matches()

        if not upcoming:
            if self.champion:
                print("\n  🏆 Tournament Complete!")
            else:
                print("\n  No matches currently available.")
            return

        round_name = self.round_names.get(self.current_round, f"ROUND {self.current_round}")
        print(f"\n  UPCOMING - {round_name}:")
        print("  " + "-" * 40)

        for match in upcoming:
            t1 = match.team1
            t2 = match.team2
            print(f"  Match {match.match_id}: "
                  f"({t1.seed}) {t1.emoji} {t1.name} vs {t2.emoji} {t2.name} ({t2.seed})")
        print()


class TournamentRunner:
    """
    Runs a complete tournament with simulated battles.
    """

    def __init__(self, tournament: EliminationTournament):
        self.tournament = tournament
        self.battle_history: List[Dict] = []

    def simulate_match(self, match: TournamentMatch) -> tuple:
        """
        Simulate a battle between two teams.
        Returns (team1_score, team2_score).

        Override this method for actual battle simulation.
        """
        import random

        # Base scores on seed (higher seed = slight advantage)
        t1_base = 5000 + (50 - match.team1.seed) * 200
        t2_base = 5000 + (50 - match.team2.seed) * 200

        # Add randomness
        t1_score = max(1000, t1_base + random.randint(-3000, 5000))
        t2_score = max(1000, t2_base + random.randint(-3000, 5000))

        # Ensure no ties
        if t1_score == t2_score:
            t1_score += random.choice([-100, 100])

        return t1_score, t2_score

    def run_round(self, verbose: bool = True):
        """Run all matches in the current round with enhanced visuals."""
        matches = self.tournament.get_current_matches()

        if not matches:
            if verbose:
                print("No matches to play in current round.")
            return

        round_name = self.tournament.round_names.get(
            self.tournament.current_round,
            f"ROUND {self.tournament.current_round}"
        )

        if verbose:
            print(DramaticAnnouncements.round_start(round_name))
            print()

        for match in matches:
            t1_score, t2_score = self.simulate_match(match)
            t1 = match.team1
            t2 = match.team2
            winner = t1 if t1_score > t2_score else t2
            loser = t2 if t1_score > t2_score else t1

            self.tournament.record_match_result(match.match_id, t1_score, t2_score)

            if verbose:
                # Create visual score comparison
                total = t1_score + t2_score
                t1_pct = t1_score / total if total > 0 else 0.5

                bar_width = 25
                t1_bars = int(t1_pct * bar_width)
                t2_bars = bar_width - t1_bars

                w_color = Colors.GREEN
                l_color = Colors.DIM

                if t1_score > t2_score:
                    t1_c, t2_c = w_color, l_color
                else:
                    t1_c, t2_c = l_color, w_color

                print(f"   ┌{'─' * 50}┐")
                print(f"   │  Match {match.match_id}: {t1.emoji} {t1.name} vs {t2.emoji} {t2.name}")
                print(f"   │  ")
                print(f"   │  {t1_c}{t1.emoji} {t1_score:>8,}{Colors.RESET}  "
                      f"[{t1_c}{'█' * t1_bars}{t2_c}{'█' * t2_bars}{Colors.RESET}]  "
                      f"{t2_c}{t2_score:<8,} {t2.emoji}{Colors.RESET}")
                print(f"   │  ")
                print(f"   │  {Colors.GREEN}► Winner: {winner.emoji} {winner.name}{Colors.RESET}")
                print(f"   └{'─' * 50}┘")
                print()

            self.battle_history.append({
                "match_id": match.match_id,
                "round": self.tournament.current_round - 1,  # Just completed
                "team1": match.team1.name,
                "team2": match.team2.name,
                "team1_score": t1_score,
                "team2_score": t2_score,
                "winner": match.winner.name
            })

    def run_tournament(self, verbose: bool = True):
        """Run the complete tournament with enhanced visuals."""
        if verbose:
            # Dramatic tournament start
            start_lines = [
                "",
                "🏆🏆🏆  T O U R N A M E N T   S T A R T  🏆🏆🏆",
                "",
                f"   {self.tournament.num_teams} Teams Ready to Battle   ",
                "",
                "   May the best team win!   ",
                "",
            ]
            print(ASCIIFrames.frame(start_lines, width=65, box_style="double",
                                    color=Colors.YELLOW))
            print()
            self.tournament.print_bracket()

        while not self.tournament.is_complete():
            self.run_round(verbose)

        if verbose:
            # Dramatic tournament complete
            print()
            print(DramaticAnnouncements.tournament_champion(
                self.tournament.champion.name,
                self.tournament.champion.emoji
            ))
            print()
            self.tournament.print_bracket()
            self.tournament.print_standings()


# =============================================================================
# ROUND ROBIN TOURNAMENT SYSTEM
# =============================================================================

@dataclass
class RoundRobinStanding:
    """Team standing in round robin tournament."""
    team: TournamentTeam
    matches_played: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    points_for: int = 0
    points_against: int = 0
    match_points: int = 0  # 3 for win, 1 for draw, 0 for loss

    @property
    def point_differential(self) -> int:
        return self.points_for - self.points_against

    @property
    def win_rate(self) -> float:
        if self.matches_played == 0:
            return 0.0
        return self.wins / self.matches_played

    def __lt__(self, other: 'RoundRobinStanding') -> bool:
        """Comparison for sorting (tiebreakers)."""
        # 1. Match points
        if self.match_points != other.match_points:
            return self.match_points > other.match_points
        # 2. Point differential
        if self.point_differential != other.point_differential:
            return self.point_differential > other.point_differential
        # 3. Points scored
        return self.points_for > other.points_for


@dataclass
class RoundRobinMatch:
    """Match in round robin format."""
    match_id: int
    matchday: int
    home_team: TournamentTeam
    away_team: TournamentTeam
    home_score: int = 0
    away_score: int = 0
    winner: Optional[TournamentTeam] = None  # None if draw
    completed: bool = False


class RoundRobinTournament:
    """
    Round Robin Tournament - Every team plays every other team.

    Features:
    - Automatic fixture generation (circle algorithm)
    - Points-based standings (3W/1D/0L)
    - Multiple tiebreakers (points, differential, scored)
    - Optional double round robin (home/away)
    - Matchday organization
    """

    # Dramatic announcement banners
    ROUND_ROBIN_START = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   🔄🔄🔄  R O U N D   R O B I N   T O U R N A M E N T  🔄🔄🔄               ║
║                                                                              ║
║   Every team faces every opponent!                                           ║
║   {num_teams} teams  |  {total_matches} matches  |  {matchdays} matchdays               ║
║                                                                              ║
║   Points: 3 WIN  |  1 DRAW  |  0 LOSS                                        ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

    MATCHDAY_BANNER = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   📅  M A T C H D A Y   {day}   O F   {total}  📅                            ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

    FINAL_STANDINGS_BANNER = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   🏆🏆🏆  R O U N D   R O B I N   C O M P L E T E !  🏆🏆🏆                  ║
║                                                                              ║
║   CHAMPION: {emoji} {champion}                                               ║
║   Record: {wins}W - {draws}D - {losses}L  |  {points} points                 ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

    def __init__(self, teams: List[TournamentTeam],
                 double_round_robin: bool = False,
                 points_for_win: int = 3,
                 points_for_draw: int = 1,
                 points_for_loss: int = 0,
                 allow_draws: bool = False):
        """
        Initialize round robin tournament.

        Args:
            teams: List of participating teams
            double_round_robin: If True, each pair plays twice (home/away)
            points_for_win/draw/loss: Point values for results
            allow_draws: If False, ties go to overtime/tiebreaker
        """
        self.teams = teams
        self.num_teams = len(teams)
        self.double_round_robin = double_round_robin
        self.points_win = points_for_win
        self.points_draw = points_for_draw
        self.points_loss = points_for_loss
        self.allow_draws = allow_draws

        # Pad with bye if odd number of teams
        self._has_bye = False
        if self.num_teams % 2 == 1:
            self._has_bye = True
            bye_team = TournamentTeam(name="BYE", seed=999, emoji="⬜")
            self.teams = teams + [bye_team]
            self.num_teams += 1

        # Calculate totals
        self.total_matchdays = (self.num_teams - 1) * (2 if double_round_robin else 1)
        self.matches_per_day = self.num_teams // 2
        self.total_matches = (self.num_teams * (self.num_teams - 1)) // 2
        if double_round_robin:
            self.total_matches *= 2

        # Initialize fixtures and standings
        self.fixtures: List[RoundRobinMatch] = []
        self.standings: Dict[str, RoundRobinStanding] = {}
        self.current_matchday = 1
        self.is_complete = False
        self.champion: Optional[TournamentTeam] = None

        self._initialize_standings()
        self._generate_fixtures()

    def _initialize_standings(self):
        """Initialize standings for all teams."""
        for team in self.teams:
            if team.name != "BYE":
                self.standings[team.name] = RoundRobinStanding(team=team)

    def _generate_fixtures(self):
        """Generate all fixtures using circle algorithm."""
        teams = self.teams.copy()
        n = len(teams)
        fixtures = []
        match_id = 1

        # Circle algorithm
        for matchday in range(1, n):
            day_matches = []
            for i in range(n // 2):
                home = teams[i]
                away = teams[n - 1 - i]
                if home.name != "BYE" and away.name != "BYE":
                    day_matches.append(RoundRobinMatch(
                        match_id=match_id,
                        matchday=matchday,
                        home_team=home,
                        away_team=away
                    ))
                    match_id += 1
            fixtures.extend(day_matches)

            # Rotate teams (keep first team fixed)
            teams = [teams[0]] + [teams[-1]] + teams[1:-1]

        self.fixtures = fixtures

        # Add reverse fixtures for double round robin
        if self.double_round_robin:
            reverse_fixtures = []
            for f in fixtures:
                reverse_fixtures.append(RoundRobinMatch(
                    match_id=match_id,
                    matchday=f.matchday + (n - 1),
                    home_team=f.away_team,  # Swap home/away
                    away_team=f.home_team
                ))
                match_id += 1
            self.fixtures.extend(reverse_fixtures)

    def record_match_result(self, match_id: int, home_score: int, away_score: int):
        """Record match result and update standings."""
        match = next((m for m in self.fixtures if m.match_id == match_id), None)
        if not match:
            raise ValueError(f"Match {match_id} not found")
        if match.completed:
            raise ValueError(f"Match {match_id} already completed")

        match.home_score = home_score
        match.away_score = away_score
        match.completed = True

        home = self.standings[match.home_team.name]
        away = self.standings[match.away_team.name]

        # Update stats
        home.matches_played += 1
        away.matches_played += 1
        home.points_for += home_score
        away.points_for += away_score
        home.points_against += away_score
        away.points_against += home_score

        # Determine result
        if home_score > away_score:
            match.winner = match.home_team
            home.wins += 1
            home.match_points += self.points_win
            away.losses += 1
            away.match_points += self.points_loss
        elif away_score > home_score:
            match.winner = match.away_team
            away.wins += 1
            away.match_points += self.points_win
            home.losses += 1
            home.match_points += self.points_loss
        else:
            # Draw
            home.draws += 1
            away.draws += 1
            home.match_points += self.points_draw
            away.match_points += self.points_draw

        # Update current matchday
        self._update_matchday()

        # Check completion
        if all(m.completed for m in self.fixtures):
            self.is_complete = True
            standings = self.get_standings()
            if standings:
                self.champion = standings[0].team

    def _update_matchday(self):
        """Update current matchday based on completed matches."""
        for day in range(1, self.total_matchdays + 1):
            day_matches = [m for m in self.fixtures if m.matchday == day]
            if not all(m.completed for m in day_matches):
                self.current_matchday = day
                return
        self.current_matchday = self.total_matchdays + 1

    def get_standings(self) -> List[RoundRobinStanding]:
        """Get sorted standings with all tiebreakers applied."""
        standings = list(self.standings.values())
        standings.sort()  # Uses __lt__ for tiebreakers
        return standings

    def get_matchday_fixtures(self, matchday: int) -> List[RoundRobinMatch]:
        """Get fixtures for a specific matchday."""
        return [m for m in self.fixtures if m.matchday == matchday]

    def get_current_fixtures(self) -> List[RoundRobinMatch]:
        """Get fixtures for current matchday."""
        return [m for m in self.fixtures
                if m.matchday == self.current_matchday and not m.completed]

    def print_tournament_start(self):
        """Print tournament start banner."""
        print(self.ROUND_ROBIN_START.format(
            num_teams=self.num_teams - (1 if self._has_bye else 0),
            total_matches=len([m for m in self.fixtures]),
            matchdays=self.total_matchdays
        ))

    def print_matchday_header(self, matchday: int):
        """Print matchday header."""
        print(self.MATCHDAY_BANNER.format(
            day=matchday,
            total=self.total_matchdays
        ))

    def print_standings(self):
        """Print formatted round robin standings table."""
        standings = self.get_standings()
        leader_points = standings[0].match_points if standings else 0

        print("\n" + "=" * 80)
        print(f"   {'🏆 ROUND ROBIN STANDINGS':^74}")
        print("=" * 80)

        # Header
        print(f"\n   {'Rank':<6}{'Team':<20}{'P':<4}{'W':<4}{'D':<4}{'L':<4}"
              f"{'PF':<9}{'PA':<9}{'Diff':<9}{'Pts':<6}")
        print("   " + "-" * 74)

        for i, s in enumerate(standings, 1):
            # Rank emoji
            if i == 1:
                rank = "🥇"
            elif i == 2:
                rank = "🥈"
            elif i == 3:
                rank = "🥉"
            else:
                rank = f"#{i}"

            # Point differential with color
            diff = s.point_differential
            if diff > 0:
                diff_str = f"{Colors.GREEN}+{diff:,}{Colors.RESET}"
            elif diff < 0:
                diff_str = f"{Colors.RED}{diff:,}{Colors.RESET}"
            else:
                diff_str = f"{Colors.DIM}0{Colors.RESET}"

            # Points color (leader highlighted)
            pts_color = Colors.YELLOW if i == 1 else Colors.RESET

            print(f"   {rank:<6}{s.team.emoji} {s.team.name:<17}{s.matches_played:<4}"
                  f"{s.wins:<4}{s.draws:<4}{s.losses:<4}"
                  f"{s.points_for:<9,}{s.points_against:<9,}{diff_str:<18}"
                  f"{pts_color}{s.match_points:<6}{Colors.RESET}")

        print("   " + "-" * 74)

        # Games back from leader
        if len(standings) > 1:
            print(f"\n   Games Back from Leader:")
            for i, s in enumerate(standings[1:], 2):
                gb = (leader_points - s.match_points) / 3
                print(f"   {s.team.emoji} {s.team.name}: {gb:.1f} GB")
        print()

    def print_matchday_results(self, matchday: int):
        """Print results for a specific matchday."""
        matches = self.get_matchday_fixtures(matchday)
        completed = [m for m in matches if m.completed]

        if not completed:
            return

        print(f"\n   MATCHDAY {matchday} RESULTS:")
        print("   " + "-" * 50)

        for match in completed:
            home = match.home_team
            away = match.away_team

            if match.winner == home:
                h_color = Colors.GREEN
                a_color = Colors.DIM
                result = "W"
            elif match.winner == away:
                h_color = Colors.DIM
                a_color = Colors.GREEN
                result = "L"
            else:
                h_color = Colors.YELLOW
                a_color = Colors.YELLOW
                result = "D"

            print(f"   {h_color}{home.emoji} {home.name:<15}{Colors.RESET} "
                  f"{match.home_score:>5,} - {match.away_score:<5,} "
                  f"{a_color}{away.emoji} {away.name:<15}{Colors.RESET}")

        print("   " + "-" * 50 + "\n")

    def print_final_standings(self):
        """Print final standings with champion announcement."""
        if not self.is_complete:
            self.print_standings()
            return

        standings = self.get_standings()
        champ = standings[0]

        print(self.FINAL_STANDINGS_BANNER.format(
            emoji=champ.team.emoji,
            champion=champ.team.name.upper(),
            wins=champ.wins,
            draws=champ.draws,
            losses=champ.losses,
            points=champ.match_points
        ))

        self.print_standings()


class RoundRobinRunner:
    """Runs a complete round robin tournament with simulated battles."""

    def __init__(self, tournament: RoundRobinTournament):
        self.tournament = tournament
        self.match_history: List[Dict] = []

    def simulate_match(self, match: RoundRobinMatch) -> tuple:
        """
        Simulate a match between two teams.
        Returns (home_score, away_score).
        """
        import random

        # Base scores on seed
        h_base = 5000 + (50 - match.home_team.seed) * 200
        a_base = 5000 + (50 - match.away_team.seed) * 200

        # Add randomness
        h_score = max(1000, h_base + random.randint(-3000, 5000))
        a_score = max(1000, a_base + random.randint(-3000, 5000))

        # Home advantage
        h_score += random.randint(0, 500)

        # Ensure no ties if draws not allowed
        if not self.tournament.allow_draws and h_score == a_score:
            h_score += random.choice([-100, 100])

        return h_score, a_score

    def run_matchday(self, matchday: int, verbose: bool = True):
        """Run all matches in a matchday."""
        matches = self.tournament.get_matchday_fixtures(matchday)
        unplayed = [m for m in matches if not m.completed]

        if not unplayed:
            return

        if verbose:
            self.tournament.print_matchday_header(matchday)

        for match in unplayed:
            h_score, a_score = self.simulate_match(match)
            self.tournament.record_match_result(match.match_id, h_score, a_score)

            self.match_history.append({
                "matchday": matchday,
                "home": match.home_team.name,
                "away": match.away_team.name,
                "home_score": h_score,
                "away_score": a_score,
                "winner": match.winner.name if match.winner else "Draw"
            })

        if verbose:
            self.tournament.print_matchday_results(matchday)

    def run_tournament(self, verbose: bool = True):
        """Run the complete round robin tournament."""
        if verbose:
            self.tournament.print_tournament_start()
            self.tournament.print_standings()

        for matchday in range(1, self.tournament.total_matchdays + 1):
            self.run_matchday(matchday, verbose)
            if verbose:
                self.tournament.print_standings()

        if verbose:
            self.tournament.print_final_standings()


# =============================================================================
# DOUBLE ELIMINATION TOURNAMENT SYSTEM
# =============================================================================

@dataclass
class DoubleElimMatch:
    """Match in double elimination format with bracket tracking."""
    match_id: int
    bracket: str  # 'winners', 'losers', 'grand_final'
    round_num: int
    team1: Optional[TournamentTeam] = None
    team2: Optional[TournamentTeam] = None
    team1_score: int = 0
    team2_score: int = 0
    winner: Optional[TournamentTeam] = None
    loser: Optional[TournamentTeam] = None
    completed: bool = False
    winners_next_match_id: Optional[int] = None  # Winner advances here
    losers_next_match_id: Optional[int] = None   # Loser goes here (from winners)


class DoubleEliminationTournament:
    """
    Double Elimination Tournament - Two chances to compete!

    Features:
    - Winners bracket (upper bracket)
    - Losers bracket (lower bracket)
    - Grand finals with potential bracket reset
    - Dramatic "dropped to losers" announcements
    - Visual double bracket display
    """

    # Dramatic announcement banners
    DOUBLE_ELIM_START = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   ⚔️⚔️⚔️  D O U B L E   E L I M I N A T I O N  ⚔️⚔️⚔️                        ║
║                                                                              ║
║   {num_teams} teams  |  Winners + Losers Brackets  |  Grand Finals           ║
║                                                                              ║
║   🏆 LOSE ONCE: Dropped to Losers Bracket                                    ║
║   💀 LOSE TWICE: Eliminated!                                                 ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

    DROPPED_TO_LOSERS = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   ⬇️⬇️⬇️  D R O P P E D   T O   L O S E R S !  ⬇️⬇️⬇️                        ║
║                                                                              ║
║                      {emoji} {team}                                          ║
║                                                                              ║
║   💪 ONE LIFE LEFT - WIN OR GO HOME! 💪                                      ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

    ELIMINATED_BANNER = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   💀💀💀  E L I M I N A T E D !  💀💀💀                                      ║
║                                                                              ║
║                      {emoji} {team}                                          ║
║                                                                              ║
║   Two losses - Tournament over for this team!                                ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

    GRAND_FINALS_BANNER = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   🏆🏆🏆  G R A N D   F I N A L S  🏆🏆🏆                                     ║
║                                                                              ║
║   👑 WINNERS CHAMP: {w_emoji} {winners_champ}                                ║
║   🔥 LOSERS CHAMP:  {l_emoji} {losers_champ}                                 ║
║                                                                              ║
║   {condition}                                                                ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

    BRACKET_RESET_BANNER = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   🔄🔄🔄  B R A C K E T   R E S E T !  🔄🔄🔄                                 ║
║                                                                              ║
║   The Losers Champion has defeated the Winners Champion!                     ║
║   Both teams now have ONE LOSS!                                              ║
║                                                                              ║
║   ⚡ THIS IS FOR EVERYTHING! ⚡                                               ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

    CHAMPION_BANNER = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   👑👑👑  T O U R N A M E N T   C H A M P I O N  👑👑👑                       ║
║                                                                              ║
║                    {emoji} {champion}                                        ║
║                                                                              ║
║   Record: {wins}W - {losses}L  |  Point Diff: +{diff:,}                      ║
║   {path}                                                                     ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

    def __init__(self, teams: List[TournamentTeam],
                 grand_finals_best_of: int = 1):
        """
        Initialize double elimination tournament.

        Args:
            teams: List of participating teams
            grand_finals_best_of: Games in grand finals (1, 3, or 5)
        """
        self.original_teams = teams[:]
        self.grand_finals_best_of = grand_finals_best_of

        # Validate and pad to power of 2
        valid_sizes = [2, 4, 8, 16, 32]
        if len(teams) not in valid_sizes:
            target_size = min(s for s in valid_sizes if s >= len(teams))
            while len(teams) < target_size:
                bye_team = TournamentTeam(
                    name="BYE", seed=999, emoji="⬜", eliminated=True
                )
                teams.append(bye_team)

        self.teams = sorted(teams, key=lambda t: t.seed)
        self.num_teams = len(self.teams)
        self.winners_rounds = self._calculate_rounds()
        self.losers_rounds = (self.winners_rounds - 1) * 2  # Losers has more rounds

        # Match tracking
        self.winners_matches: Dict[int, DoubleElimMatch] = {}
        self.losers_matches: Dict[int, DoubleElimMatch] = {}
        self.grand_final_match: Optional[DoubleElimMatch] = None
        self.bracket_reset_match: Optional[DoubleElimMatch] = None

        # State tracking
        self.current_phase = "winners"  # 'winners', 'losers', 'grand_finals', 'bracket_reset'
        self.champion: Optional[TournamentTeam] = None
        self.winners_champion: Optional[TournamentTeam] = None
        self.losers_champion: Optional[TournamentTeam] = None
        self.match_counter = 0

        # Team status tracking
        self.teams_in_winners: List[TournamentTeam] = []
        self.teams_in_losers: List[TournamentTeam] = []
        self.eliminated_teams: List[TournamentTeam] = []

        # Setup brackets
        self._setup_double_bracket()

    def _calculate_rounds(self) -> int:
        """Calculate number of winners bracket rounds."""
        import math
        return int(math.log2(self.num_teams))

    def _next_match_id(self) -> int:
        """Get next match ID."""
        self.match_counter += 1
        return self.match_counter

    def _setup_double_bracket(self):
        """Setup both winners and losers brackets."""
        self._setup_winners_bracket()
        self._setup_losers_bracket()
        self._setup_grand_finals()

    def _create_seeded_pairings(self) -> List[tuple]:
        """Create seeded pairings for first round."""
        n = self.num_teams
        teams = self.teams.copy()

        pairings = []
        for i in range(n // 2):
            if i % 2 == 0:
                pairings.append((teams[i], teams[n - 1 - i]))
            else:
                pairings.append((teams[n - 1 - i], teams[i]))

        # Reorder for bracket flow
        if n == 8:
            pairings = [pairings[0], pairings[3], pairings[2], pairings[1]]
        elif n == 16:
            indices = [0, 7, 4, 3, 2, 5, 6, 1]
            pairings = [pairings[i] for i in indices]

        return pairings

    def _setup_winners_bracket(self):
        """Setup winners bracket matches."""
        pairings = self._create_seeded_pairings()
        round1_count = self.num_teams // 2

        # Create winners bracket rounds
        for round_num in range(1, self.winners_rounds + 1):
            matches_in_round = self.num_teams // (2 ** round_num)

            for i in range(matches_in_round):
                match_id = self._next_match_id()

                # First round gets the seeded pairings
                if round_num == 1:
                    team1 = pairings[i][0] if i < len(pairings) else None
                    team2 = pairings[i][1] if i < len(pairings) else None
                else:
                    team1 = None
                    team2 = None

                match = DoubleElimMatch(
                    match_id=match_id,
                    bracket='winners',
                    round_num=round_num,
                    team1=team1,
                    team2=team2
                )

                # Auto-advance BYE matches
                if team1 and team2:
                    if team2.name == "BYE":
                        match.winner = team1
                        match.loser = team2
                        match.completed = True
                        match.team1_score = 1
                        self.teams_in_winners.append(team1)
                    elif team1.name == "BYE":
                        match.winner = team2
                        match.loser = team1
                        match.completed = True
                        match.team2_score = 1
                        self.teams_in_winners.append(team2)
                    else:
                        self.teams_in_winners.extend([team1, team2])

                self.winners_matches[match_id] = match

        # Link winners bracket matches
        self._link_winners_bracket()

    def _link_winners_bracket(self):
        """Link winners bracket matches for advancement."""
        for round_num in range(1, self.winners_rounds):
            current_round = [m for m in self.winners_matches.values()
                           if m.round_num == round_num]
            next_round = [m for m in self.winners_matches.values()
                         if m.round_num == round_num + 1]

            current_round.sort(key=lambda m: m.match_id)
            next_round.sort(key=lambda m: m.match_id)

            for i, match in enumerate(current_round):
                if next_round:
                    match.winners_next_match_id = next_round[i // 2].match_id

    def _setup_losers_bracket(self):
        """Setup losers bracket with proper routing."""
        # For 8 teams: (W = winners losers go here, L = losers bracket matches)
        # Losers R1: 2 matches (W R1 losers play each other)
        # Losers R2: 2 matches (L R1 winners vs W R2 losers)
        # Losers R3: 1 match (L R2 winners play each other)
        # Losers R4: 1 match (L R3 winner vs W Finals loser)

        # Track which losers match gets teams from winners bracket
        self.winners_loser_routing: Dict[int, int] = {}  # winners match -> losers match
        self.losers_bracket_structure: List[List[int]] = []  # rounds of losers matches

        # Calculate losers bracket structure
        # For n teams: losers bracket has 2*(log2(n)-1) rounds
        num_losers_rounds = 2 * (self.winners_rounds - 1)

        # Matches per losers round (alternating pattern)
        # R1: n/4, R2: n/4, R3: n/8, R4: n/8, etc.
        matches_per_round = []
        current_matches = self.num_teams // 4
        for r in range(num_losers_rounds):
            matches_per_round.append(current_matches)
            if r % 2 == 1:  # Reduce after every other round
                current_matches = max(1, current_matches // 2)

        # Create losers matches round by round
        round_num = 1
        for num_matches in matches_per_round:
            round_matches = []
            for i in range(num_matches):
                match_id = self._next_match_id()
                match = DoubleElimMatch(
                    match_id=match_id,
                    bracket='losers',
                    round_num=round_num
                )
                self.losers_matches[match_id] = match
                round_matches.append(match_id)
            self.losers_bracket_structure.append(round_matches)
            round_num += 1

        # Link losers bracket matches for advancement
        self._link_losers_bracket()

        # Setup routing from winners bracket losers to losers bracket
        self._setup_winners_to_losers_routing()

    def _link_losers_bracket(self):
        """Link losers bracket matches for winner advancement."""
        if len(self.losers_bracket_structure) < 2:
            return

        for round_idx in range(len(self.losers_bracket_structure) - 1):
            current_round_ids = self.losers_bracket_structure[round_idx]
            next_round_ids = self.losers_bracket_structure[round_idx + 1]

            for i, match_id in enumerate(current_round_ids):
                match = self.losers_matches[match_id]
                if next_round_ids:
                    # Winners advance to next losers round
                    next_idx = i // 2 if len(next_round_ids) < len(current_round_ids) else i
                    if next_idx < len(next_round_ids):
                        match.winners_next_match_id = next_round_ids[next_idx]

    def _setup_winners_to_losers_routing(self):
        """Setup routing from winners bracket losers to losers bracket."""
        if not self.losers_bracket_structure:
            return

        # Winners R1 losers -> Losers R1
        winners_r1 = [m for m in self.winners_matches.values() if m.round_num == 1]
        winners_r1.sort(key=lambda m: m.match_id)

        if self.losers_bracket_structure:
            losers_r1_ids = self.losers_bracket_structure[0]
            for i, w_match in enumerate(winners_r1):
                if i // 2 < len(losers_r1_ids):
                    w_match.losers_next_match_id = losers_r1_ids[i // 2]

        # Winners R2+ losers -> Losers R2, R4, R6, etc. (odd indices in structure)
        for w_round in range(2, self.winners_rounds + 1):
            winners_round = [m for m in self.winners_matches.values() if m.round_num == w_round]
            winners_round.sort(key=lambda m: m.match_id)

            # Map to corresponding losers round (R2 losers -> L Round 2, R3 losers -> L Round 4)
            losers_round_idx = (w_round - 1) * 2 - 1  # 2->1, 3->3, 4->5
            if 0 <= losers_round_idx < len(self.losers_bracket_structure):
                losers_round_ids = self.losers_bracket_structure[losers_round_idx]
                for i, w_match in enumerate(winners_round):
                    if i < len(losers_round_ids):
                        w_match.losers_next_match_id = losers_round_ids[i]

    def _setup_grand_finals(self):
        """Setup grand finals match."""
        match_id = self._next_match_id()
        self.grand_final_match = DoubleElimMatch(
            match_id=match_id,
            bracket='grand_final',
            round_num=1
        )

    def _drop_to_losers(self, team: TournamentTeam, verbose: bool = True):
        """Move a team from winners to losers bracket."""
        if team in self.teams_in_winners:
            self.teams_in_winners.remove(team)
        self.teams_in_losers.append(team)

        if verbose and team.name != "BYE":
            print(self.DROPPED_TO_LOSERS.format(
                emoji=team.emoji,
                team=team.name.upper()
            ))

    def _eliminate(self, team: TournamentTeam, verbose: bool = True):
        """Eliminate a team from the tournament."""
        if team in self.teams_in_losers:
            self.teams_in_losers.remove(team)
        self.eliminated_teams.append(team)
        team.eliminated = True

        if verbose and team.name != "BYE":
            print(self.ELIMINATED_BANNER.format(
                emoji=team.emoji,
                team=team.name.upper()
            ))

    def record_match_result(self, match_id: int, team1_score: int, team2_score: int,
                           verbose: bool = True):
        """
        Record match result and handle bracket advancement.

        Args:
            match_id: ID of the match
            team1_score: Score for team 1
            team2_score: Score for team 2
            verbose: Print dramatic announcements
        """
        # Find the match
        match = None
        if match_id in self.winners_matches:
            match = self.winners_matches[match_id]
        elif match_id in self.losers_matches:
            match = self.losers_matches[match_id]
        elif self.grand_final_match and match_id == self.grand_final_match.match_id:
            match = self.grand_final_match
        elif self.bracket_reset_match and match_id == self.bracket_reset_match.match_id:
            match = self.bracket_reset_match

        if not match:
            raise ValueError(f"Match {match_id} not found")
        if match.completed:
            raise ValueError(f"Match {match_id} already completed")
        if not match.team1 or not match.team2:
            raise ValueError(f"Match {match_id} teams not determined")

        # Record scores
        match.team1_score = team1_score
        match.team2_score = team2_score
        match.completed = True

        # Determine winner/loser
        if team1_score > team2_score:
            match.winner = match.team1
            match.loser = match.team2
        else:
            match.winner = match.team2
            match.loser = match.team1

        # Update team stats
        match.winner.wins += 1
        match.loser.losses += 1
        match.team1.points_scored += team1_score
        match.team1.points_allowed += team2_score
        match.team2.points_scored += team2_score
        match.team2.points_allowed += team1_score

        # Handle bracket-specific logic
        if match.bracket == 'winners':
            self._handle_winners_result(match, verbose)
        elif match.bracket == 'losers':
            self._handle_losers_result(match, verbose)
        elif match.bracket == 'grand_final':
            self._handle_grand_final_result(match, verbose)
        elif match.bracket == 'bracket_reset':
            self._handle_bracket_reset_result(match, verbose)

    def _handle_winners_result(self, match: DoubleElimMatch, verbose: bool):
        """Handle winners bracket match result."""
        # Loser drops to losers bracket
        self._drop_to_losers(match.loser, verbose)

        # Route loser to their losers bracket match
        if match.losers_next_match_id and match.losers_next_match_id in self.losers_matches:
            losers_match = self.losers_matches[match.losers_next_match_id]
            if losers_match.team1 is None:
                losers_match.team1 = match.loser
            else:
                losers_match.team2 = match.loser

        # Winner advances in winners bracket
        if match.winners_next_match_id:
            next_match = self.winners_matches[match.winners_next_match_id]
            if next_match.team1 is None:
                next_match.team1 = match.winner
            else:
                next_match.team2 = match.winner
        else:
            # This was winners finals
            self.winners_champion = match.winner
            if verbose:
                print(f"\n   👑 WINNERS BRACKET CHAMPION: {match.winner.emoji} {match.winner.name}!\n")
            # Check if we can setup grand finals
            self._check_grand_finals_ready()

    def _handle_losers_result(self, match: DoubleElimMatch, verbose: bool):
        """Handle losers bracket match result."""
        # Loser is eliminated
        self._eliminate(match.loser, verbose)

        # Winner advances in losers bracket
        if match.winners_next_match_id and match.winners_next_match_id in self.losers_matches:
            next_match = self.losers_matches[match.winners_next_match_id]
            if next_match.team1 is None:
                next_match.team1 = match.winner
            else:
                next_match.team2 = match.winner
        else:
            # This was losers finals - crown losers champion
            self.losers_champion = match.winner
            if verbose:
                print(f"\n   🔥 LOSERS BRACKET CHAMPION: {match.winner.emoji} {match.winner.name}!\n")
            # Check if we can setup grand finals
            self._check_grand_finals_ready()

    def _check_grand_finals_ready(self):
        """Check if both champions are ready for grand finals."""
        if self.winners_champion and self.losers_champion and self.grand_final_match:
            if not self.grand_final_match.team1:
                self.grand_final_match.team1 = self.winners_champion
                self.grand_final_match.team2 = self.losers_champion
                self.current_phase = "grand_finals"

    def _handle_grand_final_result(self, match: DoubleElimMatch, verbose: bool):
        """Handle grand finals result."""
        if match.winner == self.winners_champion:
            # Winners champ wins - they're the champion!
            self.champion = match.winner
            if verbose:
                path = "Undefeated through Winners Bracket!" if match.winner.losses == 0 else ""
                print(self.CHAMPION_BANNER.format(
                    emoji=match.winner.emoji,
                    champion=match.winner.name.upper(),
                    wins=match.winner.wins,
                    losses=match.winner.losses,
                    diff=match.winner.point_differential,
                    path=path
                ))
        else:
            # Losers champ wins - BRACKET RESET!
            if verbose:
                print(self.BRACKET_RESET_BANNER)

            # Create bracket reset match
            reset_id = self._next_match_id()
            self.bracket_reset_match = DoubleElimMatch(
                match_id=reset_id,
                bracket='bracket_reset',
                round_num=2,
                team1=self.winners_champion,
                team2=self.losers_champion
            )
            self.current_phase = "bracket_reset"

    def _handle_bracket_reset_result(self, match: DoubleElimMatch, verbose: bool):
        """Handle bracket reset result."""
        self.champion = match.winner
        if verbose:
            path = "Won through Losers Bracket!" if match.winner == self.losers_champion else "Survived Bracket Reset!"
            print(self.CHAMPION_BANNER.format(
                emoji=match.winner.emoji,
                champion=match.winner.name.upper(),
                wins=match.winner.wins,
                losses=match.winner.losses,
                diff=match.winner.point_differential,
                path=path
            ))

    def get_current_matches(self) -> List[DoubleElimMatch]:
        """Get matches available to play."""
        available = []

        # Check winners bracket
        for match in self.winners_matches.values():
            if (not match.completed and match.team1 and match.team2
                and match.team1.name != "BYE" and match.team2.name != "BYE"):
                available.append(match)

        # Check losers bracket if relevant
        if len(available) == 0:
            for match in self.losers_matches.values():
                if (not match.completed and match.team1 and match.team2
                    and match.team1.name != "BYE" and match.team2.name != "BYE"):
                    available.append(match)

        # Check grand finals
        if len(available) == 0 and self.grand_final_match:
            if (not self.grand_final_match.completed
                and self.grand_final_match.team1
                and self.grand_final_match.team2):
                available.append(self.grand_final_match)

        # Check bracket reset
        if len(available) == 0 and self.bracket_reset_match:
            if not self.bracket_reset_match.completed:
                available.append(self.bracket_reset_match)

        return available

    def is_complete(self) -> bool:
        """Check if tournament is complete."""
        return self.champion is not None

    def _setup_grand_finals_matchup(self):
        """Setup the grand finals matchup when both champions are determined."""
        if self.winners_champion and self.losers_champion and self.grand_final_match:
            self.grand_final_match.team1 = self.winners_champion
            self.grand_final_match.team2 = self.losers_champion
            self.current_phase = "grand_finals"

    def print_bracket(self):
        """Print the full double elimination bracket."""
        print("\n" + "=" * 80)
        print(f"   {'⚔️ DOUBLE ELIMINATION BRACKET ⚔️':^74}")
        print("=" * 80)

        # WINNERS BRACKET
        print(f"\n   {Colors.GREEN}{'═' * 35} WINNERS BRACKET {'═' * 34}{Colors.RESET}")

        for round_num in range(1, self.winners_rounds + 1):
            round_matches = [m for m in self.winners_matches.values()
                           if m.round_num == round_num]
            round_matches.sort(key=lambda m: m.match_id)

            round_name = self._get_winners_round_name(round_num)
            print(f"\n   {Colors.CYAN}{round_name}{Colors.RESET}")
            print("   " + "-" * 50)

            for match in round_matches:
                self._print_match(match)

        # LOSERS BRACKET
        print(f"\n   {Colors.RED}{'═' * 35} LOSERS BRACKET {'═' * 35}{Colors.RESET}")

        losers_by_round = {}
        for match in self.losers_matches.values():
            if match.round_num not in losers_by_round:
                losers_by_round[match.round_num] = []
            losers_by_round[match.round_num].append(match)

        for round_num in sorted(losers_by_round.keys()):
            round_matches = losers_by_round[round_num]
            round_matches.sort(key=lambda m: m.match_id)

            print(f"\n   {Colors.YELLOW}Losers Round {round_num}{Colors.RESET}")
            print("   " + "-" * 50)

            for match in round_matches:
                self._print_match(match)

        # GRAND FINALS
        print(f"\n   {Colors.YELLOW}{'═' * 35} GRAND FINALS {'═' * 36}{Colors.RESET}")

        if self.grand_final_match:
            print(f"\n   {Colors.BOLD}Grand Finals{Colors.RESET}")
            print("   " + "-" * 50)
            self._print_match(self.grand_final_match)

        if self.bracket_reset_match:
            print(f"\n   {Colors.BOLD}🔄 BRACKET RESET{Colors.RESET}")
            print("   " + "-" * 50)
            self._print_match(self.bracket_reset_match)

        print("\n" + "=" * 80)

    def _get_winners_round_name(self, round_num: int) -> str:
        """Get display name for winners bracket round."""
        remaining = self.winners_rounds - round_num + 1
        if remaining == 1:
            return "WINNERS FINALS"
        elif remaining == 2:
            return "WINNERS SEMIFINALS"
        elif remaining == 3:
            return "WINNERS QUARTERFINALS"
        else:
            return f"WINNERS ROUND {round_num}"

    def _print_match(self, match: DoubleElimMatch):
        """Print a single match."""
        if not match.team1 or not match.team2:
            print(f"   Match {match.match_id}: TBD vs TBD")
            return

        t1, t2 = match.team1, match.team2

        if match.completed:
            w_mark = "✓" if match.winner == t1 else " "
            l_mark = "✓" if match.winner == t2 else " "
            t1_c = Colors.GREEN if match.winner == t1 else Colors.DIM
            t2_c = Colors.GREEN if match.winner == t2 else Colors.DIM

            print(f"   M{match.match_id}: [{w_mark}] {t1.emoji} {t1_c}{t1.name:<14}{Colors.RESET} "
                  f"{match.team1_score:>6,} - {match.team2_score:<6,} "
                  f"{t2_c}{t2.name:<14}{Colors.RESET} {t2.emoji} [{l_mark}]")
        else:
            print(f"   M{match.match_id}: {t1.emoji} {t1.name:<14} vs "
                  f"{t2.name:<14} {t2.emoji}  {Colors.YELLOW}[UPCOMING]{Colors.RESET}")

    def print_standings(self):
        """Print current standings."""
        print("\n" + "=" * 70)
        print(f"   {'📊 DOUBLE ELIMINATION STANDINGS':^64}")
        print("=" * 70)

        # Active in Winners
        if self.teams_in_winners:
            active = [t for t in self.teams_in_winners if t.name != "BYE"]
            print(f"\n   {Colors.GREEN}Active in Winners Bracket:{Colors.RESET}")
            for t in active:
                print(f"      {t.emoji} {t.name} ({t.wins}-{t.losses})")

        # Active in Losers
        if self.teams_in_losers:
            active = [t for t in self.teams_in_losers if t.name != "BYE" and not t.eliminated]
            if active:
                print(f"\n   {Colors.YELLOW}Active in Losers Bracket:{Colors.RESET}")
                for t in active:
                    print(f"      {t.emoji} {t.name} ({t.wins}-{t.losses}) ⚠️ 1 LIFE LEFT")

        # Eliminated
        if self.eliminated_teams:
            elim = [t for t in self.eliminated_teams if t.name != "BYE"]
            if elim:
                print(f"\n   {Colors.DIM}Eliminated:{Colors.RESET}")
                for t in elim:
                    print(f"      {Colors.DIM}{t.emoji} {t.name} ({t.wins}-{t.losses}){Colors.RESET}")

        # Champion
        if self.champion:
            print(f"\n   {Colors.YELLOW}🏆 CHAMPION: {self.champion.emoji} {self.champion.name}{Colors.RESET}")

        print("\n" + "=" * 70)


class DoubleEliminationRunner:
    """Runs a complete double elimination tournament with simulated battles."""

    def __init__(self, tournament: DoubleEliminationTournament):
        self.tournament = tournament
        self.match_history: List[Dict] = []

    def simulate_match(self, match: DoubleElimMatch) -> tuple:
        """Simulate a match between two teams."""
        import random

        # Base on seed with advantage
        t1_base = 5000 + (50 - match.team1.seed) * 200
        t2_base = 5000 + (50 - match.team2.seed) * 200

        # Losers bracket hunger bonus
        if match.bracket == 'losers':
            # Teams fighting for survival get a boost
            t1_base += 1000
            t2_base += 1000

        # Grand finals pressure
        if match.bracket in ['grand_final', 'bracket_reset']:
            t1_base += 2000
            t2_base += 2000

        # Add randomness
        t1_score = max(1000, t1_base + random.randint(-3000, 5000))
        t2_score = max(1000, t2_base + random.randint(-3000, 5000))

        # No ties
        if t1_score == t2_score:
            t1_score += random.choice([-100, 100])

        return t1_score, t2_score

    def run_match(self, match: DoubleElimMatch, verbose: bool = True):
        """Run a single match."""
        t1_score, t2_score = self.simulate_match(match)

        self.tournament.record_match_result(match.match_id, t1_score, t2_score, verbose)

        if verbose:
            winner = match.winner
            print(f"   ┌{'─' * 50}┐")
            print(f"   │  Match {match.match_id} ({match.bracket.upper()})")
            print(f"   │  {match.team1.emoji} {match.team1.name} vs {match.team2.emoji} {match.team2.name}")
            print(f"   │  Score: {t1_score:,} - {t2_score:,}")
            print(f"   │  {Colors.GREEN}► Winner: {winner.emoji} {winner.name}{Colors.RESET}")
            print(f"   └{'─' * 50}┘\n")

        self.match_history.append({
            "match_id": match.match_id,
            "bracket": match.bracket,
            "team1": match.team1.name,
            "team2": match.team2.name,
            "team1_score": t1_score,
            "team2_score": t2_score,
            "winner": match.winner.name
        })

    def run_tournament(self, verbose: bool = True):
        """Run the complete double elimination tournament."""
        if verbose:
            print(self.tournament.DOUBLE_ELIM_START.format(
                num_teams=self.tournament.num_teams
            ))
            self.tournament.print_bracket()

        max_iterations = 100  # Safety limit
        iteration = 0

        while not self.tournament.is_complete() and iteration < max_iterations:
            iteration += 1
            matches = self.tournament.get_current_matches()

            if not matches:
                # Try to setup grand finals
                self.tournament._setup_grand_finals_matchup()
                matches = self.tournament.get_current_matches()

                if not matches:
                    break

            for match in matches:
                self.run_match(match, verbose)

        if verbose:
            self.tournament.print_bracket()
            self.tournament.print_standings()
