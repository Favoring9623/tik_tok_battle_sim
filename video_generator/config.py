"""
Video Generator Configuration
"""
from dataclasses import dataclass
from typing import Tuple

# === VIDEO SPECS ===
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
VIDEO_FPS = 30
VIDEO_CODEC = "libx264"
VIDEO_BITRATE = "8000k"
AUDIO_CODEC = "aac"
AUDIO_BITRATE = "128k"
MAX_FILE_SIZE_MB = 50

# === COLORS (TikTok Brand) ===
@dataclass
class Colors:
    PRIMARY = "#00F2EA"      # TikTok cyan
    SECONDARY = "#FF0050"    # TikTok red
    BACKGROUND = "#121212"   # Dark background
    BACKGROUND_ALT = "#1a1a1a"
    TEXT = "#FFFFFF"
    TEXT_MUTED = "#888888"
    ACCENT = "#25F4EE"
    SUCCESS = "#00D26A"
    WARNING = "#FFD93D"
    ERROR = "#FF6B6B"

# === FONTS ===
@dataclass
class Fonts:
    TITLE = "Montserrat-Bold"
    SUBTITLE = "Montserrat-SemiBold"
    BODY = "Inter-Regular"
    MONO = "JetBrainsMono-Regular"

@dataclass
class FontSizes:
    H1 = 72
    H2 = 48
    H3 = 36
    BODY = 24
    CAPTION = 18
    SMALL = 14

# === SCENE DURATIONS (seconds) ===
@dataclass
class SceneDurations:
    INTRO = 15
    DASHBOARD = 15
    OAUTH = 30
    START_BATTLE = 30
    GIFT_TRACKING = 60
    ANALYTICS = 30
    WINNER = 20
    CLOSING = 25

# === ANIMATION TIMINGS (seconds) ===
@dataclass
class AnimationTimings:
    FADE_IN = 0.5
    FADE_OUT = 0.5
    SLIDE_IN = 0.4
    SLIDE_OUT = 0.4
    BOUNCE = 0.3
    SCALE = 0.3
    TYPING_CHAR = 0.05  # Per character

# === SCENE DEFINITIONS ===
SCENES = [
    {
        "id": "intro",
        "name": "Introduction",
        "duration": SceneDurations.INTRO,
        "scope": None,
        "elements": [
            {"type": "background", "style": "gradient"},
            {"type": "logo", "animation": "fade_in"},
            {"type": "title", "text": "TikTok Battle Simulator", "animation": "slide_up"},
            {"type": "subtitle", "text": "Real-time Battle Analytics", "animation": "fade_in", "delay": 1.0},
        ]
    },
    {
        "id": "dashboard",
        "name": "Dashboard Overview",
        "duration": SceneDurations.DASHBOARD,
        "scope": None,
        "elements": [
            {"type": "browser_frame", "url": "https://orionlabs.live"},
            {"type": "screenshot", "source": "dashboard.png", "animation": "pan_down"},
            {"type": "callout", "text": "Real-time tracking", "position": "bottom_right"},
        ]
    },
    {
        "id": "oauth",
        "name": "TikTok OAuth Login",
        "duration": SceneDurations.OAUTH,
        "scope": "user.info.basic",
        "elements": [
            {"type": "browser_frame", "url": "https://orionlabs.live/login"},
            {"type": "click", "target": "login_button"},
            {"type": "screenshot", "source": "oauth_consent.png", "duration": 5},
            {"type": "click", "target": "authorize_button"},
            {"type": "screenshot", "source": "profile_loaded.png"},
        ]
    },
    {
        "id": "start_battle",
        "name": "Start Battle",
        "duration": SceneDurations.START_BATTLE,
        "scope": "live.room.info",
        "elements": [
            {"type": "browser_frame", "url": "https://orionlabs.live/battle"},
            {"type": "typing", "target": "creator1_input", "text": "@streamer_one"},
            {"type": "typing", "target": "creator2_input", "text": "@streamer_two"},
            {"type": "click", "target": "start_button"},
            {"type": "status", "text": "Connected", "style": "success"},
        ]
    },
    {
        "id": "gift_tracking",
        "name": "Live Gift Tracking",
        "duration": SceneDurations.GIFT_TRACKING,
        "scope": "live.gift.info",
        "elements": [
            {"type": "battle_screen"},
            {"type": "gift_event", "gift": "Rose", "value": 1, "sender": "@viewer1", "side": "left"},
            {"type": "gift_event", "gift": "Galaxy", "value": 1000, "sender": "@whale", "side": "right"},
            {"type": "gift_event", "gift": "Lion", "value": 29999, "sender": "@big_spender", "side": "left"},
            {"type": "score_update"},
            {"type": "leaderboard_update"},
        ]
    },
    {
        "id": "analytics",
        "name": "Battle Analytics",
        "duration": SceneDurations.ANALYTICS,
        "scope": None,
        "elements": [
            {"type": "browser_frame", "url": "https://orionlabs.live/analytics"},
            {"type": "chart", "chart_type": "line", "animation": "draw"},
            {"type": "stats_card", "label": "Win Rate", "value": "68%"},
            {"type": "stats_card", "label": "Total Gifts", "value": "247"},
        ]
    },
    {
        "id": "winner",
        "name": "Winner Announcement",
        "duration": SceneDurations.WINNER,
        "scope": None,
        "elements": [
            {"type": "overlay", "style": "victory"},
            {"type": "confetti"},
            {"type": "winner_card", "winner": "@streamer_one", "score": "156,780"},
        ]
    },
    {
        "id": "closing",
        "name": "Closing",
        "duration": SceneDurations.CLOSING,
        "scope": None,
        "elements": [
            {"type": "browser_frame", "url": "https://orionlabs.live/privacy"},
            {"type": "scroll", "direction": "down", "duration": 10},
            {"type": "logo", "animation": "fade_in"},
            {"type": "text", "text": "orionlabs.live", "style": "url"},
            {"type": "fade_out"},
        ]
    },
]

# === GIFTS DATA (for animation) ===
GIFTS = {
    "Rose": {"value": 1, "color": "#FF69B4", "icon": "rose.png"},
    "Galaxy": {"value": 1000, "color": "#9B59B6", "icon": "galaxy.png"},
    "Lion": {"value": 29999, "color": "#F1C40F", "icon": "lion.png"},
    "TikTok Universe": {"value": 44999, "color": "#00F2EA", "icon": "universe.png"},
    "Dragon": {"value": 10000, "color": "#E74C3C", "icon": "dragon.png"},
}

# === PATHS ===
ASSETS_DIR = "video_generator/assets"
OUTPUT_DIR = "video_generator/output"
SCENES_DIR = "video_generator/scenes"

def get_total_duration() -> int:
    """Calculate total video duration in seconds."""
    return sum(scene["duration"] for scene in SCENES)

def get_scene_by_id(scene_id: str) -> dict:
    """Get scene config by ID."""
    for scene in SCENES:
        if scene["id"] == scene_id:
            return scene
    return None
