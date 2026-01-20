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

# === FONTS (System fonts) ===
@dataclass
class Fonts:
    TITLE = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    SUBTITLE = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    BODY = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"

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
        "duration": 8,
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
        "duration": 10,
        "scope": None,
        "elements": [
            {"type": "browser_frame", "url": "https://orionlabs.live"},
            {"type": "screenshot", "source": "captures/01_intro/dashboard_main.png"},
            {"type": "callout", "text": "Real-time tracking", "position": "bottom_right"},
        ]
    },
    {
        "id": "oauth",
        "name": "TikTok OAuth Login",
        "duration": 15,
        "scope": "user.info.basic",
        "elements": [
            {"type": "browser_frame", "url": "https://orionlabs.live/login"},
            {"type": "screenshot", "source": "captures/02_login/before_login.png"},
            {"type": "callout", "text": "Secure OAuth Login", "position": "top_right"},
        ]
    },
    {
        "id": "live_tracking",
        "name": "Live Battle Tracking",
        "duration": 12,
        "scope": "live.room.info",
        "elements": [
            {"type": "browser_frame", "url": "https://orionlabs.live/live"},
            {"type": "screenshot", "source": "captures/live/live_tracking.png"},
            {"type": "callout", "text": "Enter Streamer ID", "position": "bottom_right"},
        ]
    },
    {
        "id": "strategic_battle",
        "name": "Strategic Battle Dashboard",
        "duration": 15,
        "scope": "live.room.info",
        "elements": [
            {"type": "browser_frame", "url": "https://orionlabs.live/strategic-battle"},
            {"type": "screenshot", "source": "captures/strategic/strategic_battle.png"},
            {"type": "callout", "text": "AI-Powered Strategy", "position": "top_right"},
        ]
    },
    {
        "id": "tournament",
        "name": "Tournament Simulation",
        "duration": 12,
        "scope": None,
        "elements": [
            {"type": "browser_frame", "url": "https://orionlabs.live/tournament"},
            {"type": "screenshot", "source": "captures/tournament/tournament_main.png"},
            {"type": "callout", "text": "8-Team Brackets", "position": "bottom_right"},
        ]
    },
    {
        "id": "gift_tracking",
        "name": "Live Gift Tracking",
        "duration": 20,
        "scope": "live.gift.info",
        "elements": [
            {"type": "browser_frame", "url": "https://orionlabs.live/battle"},
            {"type": "screenshot", "source": "captures/live_gifts/battle_live_score.png"},
            {"type": "callout", "text": "88,956 vs 58,370 - LIVE", "position": "top_right"},
        ]
    },
    {
        "id": "gift_panel",
        "name": "Gift Panel",
        "duration": 10,
        "scope": "live.gift.info",
        "elements": [
            {"type": "screenshot", "source": "captures/live_gifts/gift_panel.png"},
            {"type": "callout", "text": "Send Gifts Live", "position": "bottom_right"},
        ]
    },
    {
        "id": "all_gifts",
        "name": "Gift Catalog",
        "duration": 8,
        "scope": "live.gift.info",
        "elements": [
            {"type": "screenshot", "source": "captures/live_gifts/all_gifts_catalog.png"},
            {"type": "callout", "text": "All TikTok Gifts", "position": "top_right"},
        ]
    },
    {
        "id": "analytics",
        "name": "Battle Analytics",
        "duration": 12,
        "scope": None,
        "elements": [
            {"type": "browser_frame", "url": "https://orionlabs.live/analytics"},
            {"type": "screenshot", "source": "captures/05_analytics/analytics_main.png"},
            {"type": "callout", "text": "Performance Analytics", "position": "bottom_right"},
        ]
    },
    {
        "id": "leaderboard",
        "name": "Leaderboards",
        "duration": 10,
        "scope": None,
        "elements": [
            {"type": "browser_frame", "url": "https://orionlabs.live/leaderboard"},
            {"type": "screenshot", "source": "captures/06_leaderboards/leaderboard_main.png"},
            {"type": "callout", "text": "Top Gifters", "position": "top_right"},
        ]
    },
    {
        "id": "obs_overlay",
        "name": "OBS Integration",
        "duration": 10,
        "scope": None,
        "elements": [
            {"type": "browser_frame", "url": "https://orionlabs.live/overlay"},
            {"type": "screenshot", "source": "captures/07_obs/obs_overlay.png"},
            {"type": "callout", "text": "Stream Overlay", "position": "bottom_right"},
        ]
    },
    {
        "id": "control_center",
        "name": "Control Center",
        "duration": 10,
        "scope": None,
        "elements": [
            {"type": "browser_frame", "url": "https://orionlabs.live/control-center"},
            {"type": "screenshot", "source": "captures/control_center/control_center.png"},
            {"type": "callout", "text": "Admin Dashboard", "position": "top_right"},
        ]
    },
    {
        "id": "live_battle_demo",
        "name": "Live Strategic Battle",
        "duration": 30,
        "scope": "live.gift.info",
        "elements": [
            {"type": "browser_frame", "url": "https://orionlabs.live/demo"},
            {"type": "screenshot", "source": "captures/demo_battle/demo_battle.png"},
            {"type": "callout", "text": "AI vs AI Battle Demo", "position": "top_right"},
        ]
    },
    {
        "id": "closing",
        "name": "Closing",
        "duration": 15,
        "scope": None,
        "elements": [
            {"type": "browser_frame", "url": "https://orionlabs.live/privacy"},
            {"type": "screenshot", "source": "captures/09_privacy/privacy_page.png"},
            {"type": "logo", "animation": "fade_in", "delay": 8},
            {"type": "text", "text": "orionlabs.live", "style": "url", "delay": 10},
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
