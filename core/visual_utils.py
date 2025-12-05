"""
Visual Utilities - Rich terminal output for TikTok Battle Simulator.

Provides:
- ASCII art banners and frames
- Progress bars (score, time, budget)
- Dramatic announcement frames
- Color utilities
- Battle state visualizations
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
import math


# =============================================================================
# ANSI COLOR CODES
# =============================================================================

class Colors:
    """ANSI color codes for terminal output."""
    # Basic colors
    BLACK = "\033[30m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"

    # Bright/Bold
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    REVERSE = "\033[7m"

    # Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"

    # Special
    RESET = "\033[0m"

    @classmethod
    def colorize(cls, text: str, color: str) -> str:
        """Apply color to text."""
        return f"{color}{text}{cls.RESET}"

    @classmethod
    def rainbow(cls, text: str) -> str:
        """Apply rainbow colors to text."""
        colors = [cls.RED, cls.YELLOW, cls.GREEN, cls.CYAN, cls.BLUE, cls.MAGENTA]
        result = []
        for i, char in enumerate(text):
            if char.strip():
                result.append(f"{colors[i % len(colors)]}{char}")
            else:
                result.append(char)
        return "".join(result) + cls.RESET

    @classmethod
    def gradient(cls, text: str, start_color: str, end_color: str) -> str:
        """Apply gradient (simplified - alternates between two colors)."""
        result = []
        for i, char in enumerate(text):
            color = start_color if i % 2 == 0 else end_color
            result.append(f"{color}{char}")
        return "".join(result) + cls.RESET


# =============================================================================
# PROGRESS BARS
# =============================================================================

class ProgressBar:
    """Configurable progress bar renderer."""

    STYLES = {
        "solid": ("█", "░"),
        "gradient": ("█", "▓", "▒", "░"),
        "arrows": ("►", "─"),
        "dots": ("●", "○"),
        "blocks": ("■", "□"),
        "classic": ("#", "-"),
        "fire": ("🔥", "⬛"),
        "stars": ("★", "☆"),
        "hearts": ("❤️", "🖤"),
        "coins": ("💰", "⬛"),
    }

    def __init__(self, width: int = 30, style: str = "solid"):
        """
        Initialize progress bar.

        Args:
            width: Bar width in characters
            style: Style name from STYLES dict
        """
        self.width = width
        self.style = style
        self.chars = self.STYLES.get(style, self.STYLES["solid"])

    def render(self, progress: float, show_percent: bool = True,
               color: str = Colors.GREEN) -> str:
        """
        Render progress bar.

        Args:
            progress: Progress value between 0.0 and 1.0
            show_percent: Show percentage at end
            color: Color to apply to filled portion
        """
        progress = max(0.0, min(1.0, progress))  # Clamp to 0-1
        filled = int(self.width * progress)
        empty = self.width - filled

        filled_char, empty_char = self.chars[0], self.chars[-1]

        bar = f"{color}{filled_char * filled}{Colors.DIM}{empty_char * empty}{Colors.RESET}"

        if show_percent:
            pct = f" {progress * 100:5.1f}%"
            return f"[{bar}]{pct}"
        return f"[{bar}]"

    def render_dual(self, left_value: float, right_value: float,
                    left_color: str = Colors.GREEN,
                    right_color: str = Colors.RED,
                    left_label: str = "", right_label: str = "") -> str:
        """
        Render dual progress bar (e.g., creator vs opponent).

        Args:
            left_value: Left side score
            right_value: Right side score
            left_color: Color for left side
            right_color: Color for right side
            left_label: Label for left side
            right_label: Label for right side
        """
        total = left_value + right_value
        if total == 0:
            left_pct = 0.5
        else:
            left_pct = left_value / total

        left_chars = int(self.width * left_pct)
        right_chars = self.width - left_chars

        filled_char = self.chars[0]

        left_bar = f"{left_color}{filled_char * left_chars}"
        right_bar = f"{right_color}{filled_char * right_chars}"

        bar = f"{left_bar}{right_bar}{Colors.RESET}"

        if left_label and right_label:
            return f"{left_label} [{bar}] {right_label}"
        return f"[{bar}]"


class BattleProgressBar:
    """Specialized progress bar for battle state visualization."""

    def __init__(self, width: int = 50):
        self.width = width

    def render_score_bar(self, creator_score: int, opponent_score: int,
                         show_scores: bool = True) -> str:
        """Render creator vs opponent score bar."""
        total = creator_score + opponent_score
        if total == 0:
            creator_pct = 0.5
        else:
            creator_pct = creator_score / total

        creator_chars = int(self.width * creator_pct)
        opponent_chars = self.width - creator_chars

        # Use gradient characters for visual appeal
        creator_bar = Colors.GREEN + "█" * creator_chars
        opponent_bar = Colors.RED + "█" * opponent_chars

        bar = f"{creator_bar}{opponent_bar}{Colors.RESET}"

        if show_scores:
            return f"{Colors.GREEN}{creator_score:>8,}{Colors.RESET} [{bar}] {Colors.RED}{opponent_score:<8,}{Colors.RESET}"
        return f"[{bar}]"

    def render_time_bar(self, elapsed: int, total: int,
                        show_time: bool = True) -> str:
        """Render time remaining bar."""
        remaining = total - elapsed
        progress = elapsed / total if total > 0 else 0

        filled = int(self.width * progress)
        empty = self.width - filled

        # Color based on urgency
        if remaining <= 10:
            color = Colors.RED + Colors.BLINK
        elif remaining <= 30:
            color = Colors.YELLOW
        else:
            color = Colors.CYAN

        bar = f"{color}{'▓' * filled}{Colors.DIM}{'░' * empty}{Colors.RESET}"

        if show_time:
            mins = remaining // 60
            secs = remaining % 60
            time_str = f"{mins}:{secs:02d}" if mins > 0 else f"{secs}s"
            return f"⏱️  [{bar}] {time_str} remaining"
        return f"[{bar}]"

    def render_budget_bar(self, remaining: int, total: int,
                          label: str = "Budget") -> str:
        """Render budget remaining bar."""
        progress = remaining / total if total > 0 else 0

        # Color based on budget level
        if progress <= 0.2:
            color = Colors.RED
        elif progress <= 0.4:
            color = Colors.YELLOW
        else:
            color = Colors.GREEN

        filled = int(self.width * progress)
        empty = self.width - filled

        bar = f"{color}{'█' * filled}{Colors.DIM}{'░' * empty}{Colors.RESET}"

        return f"💰 {label}: [{bar}] {remaining:,}/{total:,}"


# =============================================================================
# ASCII ART FRAMES AND BANNERS
# =============================================================================

class ASCIIFrames:
    """ASCII art frames for dramatic announcements."""

    # Box drawing characters
    BOX_DOUBLE = {
        "tl": "╔", "tr": "╗", "bl": "╚", "br": "╝",
        "h": "═", "v": "║"
    }

    BOX_SINGLE = {
        "tl": "┌", "tr": "┐", "bl": "└", "br": "┘",
        "h": "─", "v": "│"
    }

    BOX_BOLD = {
        "tl": "┏", "tr": "┓", "bl": "┗", "br": "┛",
        "h": "━", "v": "┃"
    }

    BOX_ROUNDED = {
        "tl": "╭", "tr": "╮", "bl": "╰", "br": "╯",
        "h": "─", "v": "│"
    }

    @classmethod
    def frame(cls, lines: List[str], width: int = 70,
              box_style: str = "double", color: str = "") -> str:
        """
        Create framed text box.

        Args:
            lines: Lines of text to frame
            width: Total width of frame
            box_style: "double", "single", "bold", or "rounded"
            color: Optional color to apply to frame
        """
        styles = {
            "double": cls.BOX_DOUBLE,
            "single": cls.BOX_SINGLE,
            "bold": cls.BOX_BOLD,
            "rounded": cls.BOX_ROUNDED
        }
        box = styles.get(box_style, cls.BOX_DOUBLE)

        inner_width = width - 2

        result = []
        # Top border
        top = f"{box['tl']}{box['h'] * inner_width}{box['tr']}"
        result.append(f"{color}{top}{Colors.RESET}" if color else top)

        # Content lines
        for line in lines:
            # Center the line
            padding = inner_width - len(line)
            left_pad = padding // 2
            right_pad = padding - left_pad
            padded = f"{' ' * left_pad}{line}{' ' * right_pad}"
            row = f"{box['v']}{padded}{box['v']}"
            result.append(f"{color}{row}{Colors.RESET}" if color else row)

        # Bottom border
        bottom = f"{box['bl']}{box['h'] * inner_width}{box['br']}"
        result.append(f"{color}{bottom}{Colors.RESET}" if color else bottom)

        return "\n".join(result)

    @classmethod
    def banner(cls, text: str, width: int = 70,
               char: str = "═", color: str = "") -> str:
        """Create simple banner with text."""
        padding = (width - len(text) - 4) // 2
        line = f"{char * padding}  {text}  {char * padding}"
        if len(line) < width:
            line += char * (width - len(line))
        if color:
            return f"{color}{line}{Colors.RESET}"
        return line


class DramaticAnnouncements:
    """Pre-built dramatic announcement templates."""

    @staticmethod
    def victory(winner: str = "CREATOR", score_diff: int = 0) -> str:
        """Victory announcement."""
        lines = [
            "",
            "🏆🏆🏆  V I C T O R Y  🏆🏆🏆",
            "",
            f"   {winner.upper()} WINS THE BATTLE!   ",
            "",
            f"   Final Margin: +{score_diff:,} points   " if score_diff else "",
            "",
        ]
        return ASCIIFrames.frame([l for l in lines if l], width=60,
                                  box_style="double", color=Colors.GREEN)

    @staticmethod
    def defeat(winner: str = "OPPONENT", score_diff: int = 0) -> str:
        """Defeat announcement."""
        lines = [
            "",
            "💔💔💔  D E F E A T  💔💔💔",
            "",
            f"   {winner.upper()} WINS THE BATTLE   ",
            "",
            f"   Lost by: {abs(score_diff):,} points   " if score_diff else "",
            "",
        ]
        return ASCIIFrames.frame([l for l in lines if l], width=60,
                                  box_style="double", color=Colors.RED)

    @staticmethod
    def battle_start(duration: int = 180, team_size: int = 4) -> str:
        """Battle start announcement."""
        lines = [
            "",
            "⚔️⚔️⚔️  B A T T L E   S T A R T  ⚔️⚔️⚔️",
            "",
            f"   Duration: {duration} seconds   ",
            f"   Team Size: {team_size} agents   ",
            "",
            "   May the best team win!   ",
            "",
        ]
        return ASCIIFrames.frame(lines, width=60, box_style="double",
                                  color=Colors.CYAN)

    @staticmethod
    def multiplier_activated(multiplier: str = "x5") -> str:
        """Multiplier activation announcement."""
        emojis = {"x2": "⚡", "x3": "⚡⚡", "x5": "💥"}
        emoji = emojis.get(multiplier, "⚡")
        lines = [
            "",
            f"{emoji}{emoji}{emoji}  {multiplier} MULTIPLIER ACTIVE  {emoji}{emoji}{emoji}",
            "",
            "   Every point counts DOUBLE!   " if multiplier == "x2" else
            "   Points TRIPLED!   " if multiplier == "x3" else
            "   MAXIMUM MULTIPLIER!   ",
            "",
        ]
        return ASCIIFrames.frame(lines, width=60, box_style="bold",
                                  color=Colors.YELLOW)

    @staticmethod
    def clutch_moment(moment_type: str = "comeback") -> str:
        """Clutch moment announcement."""
        templates = {
            "comeback_momentum": [
                "",
                "🔥🔥🔥  C O M E B A C K   M O M E N T U M  🔥🔥🔥",
                "",
                "   From the ashes... A PHOENIX RISES!   ",
                "   +15% Glove Probability ACTIVATED   ",
                "",
            ],
            "final_stand": [
                "",
                "⚔️⚔️⚔️  F I N A L   S T A N D  ⚔️⚔️⚔️",
                "",
                "   THIS IS IT! Everything on the line!   ",
                "   +20% Glove Probability ACTIVATED   ",
                "",
            ],
            "threshold_heroics": [
                "",
                "💎💎💎  T H R E S H O L D   H E R O I C S  💎💎💎",
                "",
                "   SO CLOSE! Every coin counts now!   ",
                "   +25% Glove Probability ACTIVATED   ",
                "",
            ],
            "nail_biter": [
                "",
                "😱😱😱  N A I L   B I T E R  😱😱😱",
                "",
                "   The gap is closing...   ",
                "   ANYTHING CAN HAPPEN!   ",
                "",
            ],
        }
        lines = templates.get(moment_type, templates["nail_biter"])
        return ASCIIFrames.frame(lines, width=62, box_style="double",
                                  color=Colors.MAGENTA)

    @staticmethod
    def pattern_detected(strategy: str = "unknown") -> str:
        """Pattern detection announcement."""
        lines = [
            "",
            "🎯🎯🎯  P A T T E R N   D E T E C T E D  🎯🎯🎯",
            "",
            f"   Enemy Strategy Identified: {strategy.upper()}   ",
            "   Counter-measures ENGAGED!   ",
            "",
        ]
        return ASCIIFrames.frame(lines, width=62, box_style="bold",
                                  color=Colors.CYAN)

    @staticmethod
    def psychological_warfare(tactic: str = "bluff") -> str:
        """Psychological warfare announcement."""
        templates = {
            "bluff_detected": [
                "",
                "🎭🎭🎭  B L U F F   D E T E C T E D  🎭🎭🎭",
                "",
                "   Nice try... but we see through the deception!   ",
                "   Counter-bluff INITIATED   ",
                "",
            ],
            "fog_of_war": [
                "",
                "🌫️🌫️🌫️  F O G   O F   W A R  🌫️🌫️🌫️",
                "",
                "   Visibility: ZERO   ",
                "   What are they planning?!   ",
                "",
            ],
            "decoy_launched": [
                "",
                "🎪🎪🎪  D E C O Y   L A U N C H E D  🎪🎪🎪",
                "",
                "   Is it real? Is it fake?   ",
                "   Confusion INTENSIFIES   ",
                "",
            ],
            "strategic_pause": [
                "",
                "🤫🤫🤫  S T R A T E G I C   S I L E N C E  🤫🤫🤫",
                "",
                "   The calm before the storm...   ",
                "   What are they planning?!   ",
                "",
            ],
        }
        lines = templates.get(tactic, templates["bluff_detected"])
        return ASCIIFrames.frame(lines, width=62, box_style="double",
                                  color=Colors.MAGENTA)

    @staticmethod
    def combo_executed(combo_type: str = "wave", points: int = 0) -> str:
        """Combo execution announcement."""
        lines = [
            "",
            f"💫💫💫  C O M B O: {combo_type.upper()}  💫💫💫",
            "",
            "   TEAM SYNERGY ACTIVATED!   ",
            f"   +{points:,} points   " if points else "",
            "",
        ]
        return ASCIIFrames.frame([l for l in lines if l], width=60,
                                  box_style="bold", color=Colors.YELLOW)

    @staticmethod
    def whale_incoming() -> str:
        """Whale gift incoming announcement."""
        lines = [
            "",
            "🐋🐋🐋  W H A L E   I N C O M I N G  🐋🐋🐋",
            "",
            "   MASSIVE GIFT DETECTED!   ",
            "   Brace for IMPACT!   ",
            "",
        ]
        return ASCIIFrames.frame(lines, width=60, box_style="double",
                                  color=Colors.BLUE)

    @staticmethod
    def tournament_champion(team_name: str, emoji: str = "🏆") -> str:
        """Tournament champion announcement."""
        lines = [
            "",
            "👑👑👑  T O U R N A M E N T   C H A M P I O N  👑👑👑",
            "",
            f"   {emoji} {team_name.upper()} {emoji}   ",
            "",
            "   CONGRATULATIONS!   ",
            "",
        ]
        return ASCIIFrames.frame(lines, width=65, box_style="double",
                                  color=Colors.YELLOW)

    @staticmethod
    def round_start(round_name: str = "ROUND 1") -> str:
        """Tournament round start announcement."""
        lines = [
            "",
            f"⚔️  {round_name.upper()}  ⚔️",
            "",
            "   Let the battles begin!   ",
            "",
        ]
        return ASCIIFrames.frame(lines, width=50, box_style="bold",
                                  color=Colors.CYAN)


# =============================================================================
# BATTLE STATE VISUALIZATION
# =============================================================================

class BattleVisualizer:
    """Rich battle state visualization."""

    def __init__(self, width: int = 70):
        self.width = width
        self.score_bar = BattleProgressBar(width=40)

    def render_header(self, battle_name: str = "TikTok Battle",
                      round_num: int = 1) -> str:
        """Render battle header."""
        return ASCIIFrames.banner(
            f"⚔️  {battle_name} - Round {round_num}  ⚔️",
            width=self.width,
            color=Colors.CYAN
        )

    def render_state(self, creator_score: int, opponent_score: int,
                     time_elapsed: int, total_time: int,
                     creator_name: str = "Creator",
                     opponent_name: str = "Opponent") -> str:
        """Render complete battle state."""
        lines = []

        # Score comparison
        lines.append("")
        lines.append(f"   {Colors.BOLD}SCORE{Colors.RESET}")
        lines.append(f"   {self.score_bar.render_score_bar(creator_score, opponent_score)}")
        lines.append("")

        # Time remaining
        lines.append(f"   {self.score_bar.render_time_bar(time_elapsed, total_time)}")
        lines.append("")

        # Determine leader indicator
        if creator_score > opponent_score:
            diff = creator_score - opponent_score
            status = f"{Colors.GREEN}📈 {creator_name} leads by {diff:,}{Colors.RESET}"
        elif opponent_score > creator_score:
            diff = opponent_score - creator_score
            status = f"{Colors.RED}📉 {opponent_name} leads by {diff:,}{Colors.RESET}"
        else:
            status = f"{Colors.YELLOW}⚖️  TIE GAME{Colors.RESET}"

        lines.append(f"   {status}")

        return "\n".join(lines)

    def render_agent_status(self, agents: List[Dict[str, Any]]) -> str:
        """Render agent status panel."""
        lines = [
            "",
            f"   {Colors.BOLD}TEAM STATUS{Colors.RESET}",
            "   " + "─" * 50,
        ]

        for agent in agents:
            emoji = agent.get("emoji", "🤖")
            name = agent.get("name", "Agent")[:15]
            points = agent.get("points", 0)
            gifts = agent.get("gifts", 0)
            status = agent.get("status", "active")

            # Status indicator
            if status == "active":
                indicator = f"{Colors.GREEN}●{Colors.RESET}"
            elif status == "cooldown":
                indicator = f"{Colors.YELLOW}○{Colors.RESET}"
            else:
                indicator = f"{Colors.RED}○{Colors.RESET}"

            lines.append(
                f"   {indicator} {emoji} {name:<15} │ "
                f"💰 {points:>8,} │ 🎁 {gifts:>3}"
            )

        lines.append("   " + "─" * 50)
        return "\n".join(lines)

    def render_mini_timeline(self, events: List[Dict[str, Any]],
                             max_events: int = 5) -> str:
        """Render compact recent events timeline."""
        if not events:
            return ""

        lines = [
            "",
            f"   {Colors.BOLD}RECENT EVENTS{Colors.RESET}",
            "   " + "─" * 40,
        ]

        for event in events[-max_events:]:
            time_str = f"[{event.get('time', 0):>3}s]"
            event_type = event.get("type", "")

            if event_type == "gift":
                icon = "🎁"
                desc = f"{event.get('agent', '?')}: {event.get('gift', '?')}"
            elif event_type == "combo":
                icon = "💫"
                desc = f"COMBO: {event.get('combo_type', '?')}"
            elif event_type == "multiplier":
                icon = "⚡"
                desc = f"{event.get('multiplier', 'x2')} ACTIVATED"
            elif event_type == "clutch":
                icon = "🔥"
                desc = event.get("moment_type", "Clutch Moment")
            else:
                icon = "📝"
                desc = str(event)[:30]

            lines.append(f"   {time_str} {icon} {desc}")

        return "\n".join(lines)


# =============================================================================
# TOURNAMENT BRACKET VISUALIZATION
# =============================================================================

class BracketVisualizer:
    """Enhanced tournament bracket visualization."""

    def __init__(self, width: int = 80):
        self.width = width

    def render_match(self, team1: Dict, team2: Dict,
                     winner: Optional[str] = None) -> str:
        """Render a single match box."""
        t1_name = team1.get("name", "TBD")[:15]
        t1_seed = team1.get("seed", "?")
        t1_emoji = team1.get("emoji", "")

        t2_name = team2.get("name", "TBD")[:15]
        t2_seed = team2.get("seed", "?")
        t2_emoji = team2.get("emoji", "")

        # Determine colors
        if winner == t1_name:
            c1, c2 = Colors.GREEN, Colors.DIM
        elif winner == t2_name:
            c1, c2 = Colors.DIM, Colors.GREEN
        else:
            c1, c2 = Colors.RESET, Colors.RESET

        lines = [
            "┌─────────────────────┐",
            f"│{c1} #{t1_seed} {t1_emoji} {t1_name:<12}{Colors.RESET}│",
            "├─────────────────────┤",
            f"│{c2} #{t2_seed} {t2_emoji} {t2_name:<12}{Colors.RESET}│",
            "└─────────────────────┘",
        ]
        return "\n".join(lines)

    def render_bracket_8_teams(self, matches: List[Dict]) -> str:
        """Render 8-team bracket (3 rounds)."""
        # Simplified ASCII bracket for 8 teams
        lines = []

        lines.append("")
        lines.append(f"{Colors.BOLD}   QUARTERFINALS           SEMIFINALS            FINALS{Colors.RESET}")
        lines.append("")
        lines.append("   ┌──────────────┐")
        lines.append("   │  Match 1     │──────┐")
        lines.append("   └──────────────┘      │")
        lines.append("                         ├──┐")
        lines.append("   ┌──────────────┐      │  │")
        lines.append("   │  Match 2     │──────┘  │")
        lines.append("   └──────────────┘         ├──────┐")
        lines.append("                            │      │")
        lines.append("   ┌──────────────┐         │      │")
        lines.append("   │  Match 3     │──────┐  │      │")
        lines.append("   └──────────────┘      │  │      │")
        lines.append("                         ├──┘      │")
        lines.append("   ┌──────────────┐      │         ├──► 🏆 CHAMPION")
        lines.append("   │  Match 4     │──────┘         │")
        lines.append("   └──────────────┘                │")
        lines.append("                                   │")
        lines.append("")

        return "\n".join(lines)

    def render_standings(self, teams: List[Dict]) -> str:
        """Render team standings table."""
        lines = []
        lines.append("")
        lines.append(ASCIIFrames.banner("STANDINGS", width=60, color=Colors.CYAN))
        lines.append("")
        lines.append(f"   {'Rank':<6} {'Team':<20} {'W-L':<8} {'Pts Diff':<12}")
        lines.append("   " + "─" * 50)

        for i, team in enumerate(teams, 1):
            emoji = team.get("emoji", "")
            name = team.get("name", "?")[:16]
            wins = team.get("wins", 0)
            losses = team.get("losses", 0)
            diff = team.get("point_differential", 0)

            # Rank indicator
            if i == 1:
                rank = "🥇"
            elif i == 2:
                rank = "🥈"
            elif i == 3:
                rank = "🥉"
            else:
                rank = f"#{i}"

            # Color based on elimination status
            if team.get("eliminated"):
                color = Colors.DIM
            else:
                color = Colors.RESET

            diff_str = f"+{diff:,}" if diff >= 0 else f"{diff:,}"
            diff_color = Colors.GREEN if diff > 0 else Colors.RED if diff < 0 else Colors.RESET

            lines.append(
                f"   {color}{rank:<6} {emoji} {name:<17} {wins}-{losses:<5} "
                f"{diff_color}{diff_str:<12}{Colors.RESET}"
            )

        lines.append("   " + "─" * 50)
        return "\n".join(lines)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def clear_screen():
    """Clear terminal screen."""
    print("\033[2J\033[H", end="")


def print_centered(text: str, width: int = 70):
    """Print text centered in terminal."""
    padding = (width - len(text)) // 2
    print(" " * padding + text)


def print_separator(char: str = "═", width: int = 70, color: str = ""):
    """Print separator line."""
    line = char * width
    if color:
        print(f"{color}{line}{Colors.RESET}")
    else:
        print(line)


def animate_text(text: str, delay: float = 0.03):
    """Print text with typewriter effect."""
    import time
    for char in text:
        print(char, end="", flush=True)
        time.sleep(delay)
    print()


# =============================================================================
# DEMO
# =============================================================================

if __name__ == "__main__":
    # Demo the visual utilities
    print("\n" + "=" * 70)
    print("   VISUAL UTILITIES DEMO")
    print("=" * 70)

    # Progress bars
    print("\n📊 PROGRESS BARS\n")

    bar = ProgressBar(width=30, style="solid")
    print(f"   Solid:    {bar.render(0.7)}")

    bar = ProgressBar(width=30, style="blocks")
    print(f"   Blocks:   {bar.render(0.5)}")

    bar = ProgressBar(width=30, style="dots")
    print(f"   Dots:     {bar.render(0.3)}")

    # Battle progress
    print("\n⚔️ BATTLE PROGRESS\n")
    battle_bar = BattleProgressBar(width=40)
    print(f"   {battle_bar.render_score_bar(15000, 12000)}")
    print(f"   {battle_bar.render_time_bar(120, 180)}")
    print(f"   {battle_bar.render_budget_bar(35000, 100000)}")

    # Dramatic announcements
    print("\n🎭 DRAMATIC ANNOUNCEMENTS\n")
    print(DramaticAnnouncements.victory("Creator", 5000))
    print()
    print(DramaticAnnouncements.clutch_moment("final_stand"))
    print()
    print(DramaticAnnouncements.whale_incoming())

    print("\n" + "=" * 70)
    print("   END OF DEMO")
    print("=" * 70 + "\n")
