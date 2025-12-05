"""
Pre-built agent personas for TikTok battle simulations.

Each agent has a unique:
- Personality and behavior pattern
- Gift-giving strategy
- Communication style
- Emotional range
"""

from .nova_whale import NovaWhale
from .pixel_pixie import PixelPixie
from .glitch_mancer import GlitchMancer
from .shadow_patron import ShadowPatron
from .dramatron import Dramatron

__all__ = [
    "NovaWhale",
    "PixelPixie",
    "GlitchMancer",
    "ShadowPatron",
    "Dramatron",
]
