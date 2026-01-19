"""
Animations - Reusable animation functions for video generation
"""
from typing import Callable, Tuple
import math

try:
    from moviepy.editor import VideoClip
    from moviepy.video.fx.all import fadein, fadeout
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

from ..config import AnimationTimings, VIDEO_WIDTH, VIDEO_HEIGHT


class Animations:
    """Collection of reusable animations."""

    @staticmethod
    def fade_in(clip: 'VideoClip', duration: float = None) -> 'VideoClip':
        """Apply fade in effect."""
        duration = duration or AnimationTimings.FADE_IN
        return clip.fx(fadein, duration)

    @staticmethod
    def fade_out(clip: 'VideoClip', duration: float = None) -> 'VideoClip':
        """Apply fade out effect."""
        duration = duration or AnimationTimings.FADE_OUT
        return clip.fx(fadeout, duration)

    @staticmethod
    def slide_up(start_y: int = 100, duration: float = None) -> Callable:
        """
        Create slide up position function.

        Returns a position function for use with set_position().
        """
        duration = duration or AnimationTimings.SLIDE_IN

        def position_func(t):
            if t < duration:
                progress = ease_out_cubic(t / duration)
                y_offset = int(start_y * (1 - progress))
                return ("center", VIDEO_HEIGHT // 2 + y_offset)
            return ("center", "center")

        return position_func

    @staticmethod
    def slide_down(start_y: int = -100, duration: float = None) -> Callable:
        """Create slide down position function."""
        duration = duration or AnimationTimings.SLIDE_IN

        def position_func(t):
            if t < duration:
                progress = ease_out_cubic(t / duration)
                y_offset = int(start_y * (1 - progress))
                return ("center", VIDEO_HEIGHT // 2 + y_offset)
            return ("center", "center")

        return position_func

    @staticmethod
    def slide_left(start_x: int = 100, duration: float = None) -> Callable:
        """Create slide from right to center."""
        duration = duration or AnimationTimings.SLIDE_IN

        def position_func(t):
            if t < duration:
                progress = ease_out_cubic(t / duration)
                x_offset = int(start_x * (1 - progress))
                return (VIDEO_WIDTH // 2 + x_offset, "center")
            return ("center", "center")

        return position_func

    @staticmethod
    def slide_right(start_x: int = -100, duration: float = None) -> Callable:
        """Create slide from left to center."""
        duration = duration or AnimationTimings.SLIDE_IN

        def position_func(t):
            if t < duration:
                progress = ease_out_cubic(t / duration)
                x_offset = int(start_x * (1 - progress))
                return (VIDEO_WIDTH // 2 + x_offset, "center")
            return ("center", "center")

        return position_func

    @staticmethod
    def bounce(scale_from: float = 0.5, duration: float = None) -> Callable:
        """Create bounce scale effect."""
        duration = duration or AnimationTimings.BOUNCE

        def scale_func(t):
            if t < duration:
                progress = t / duration
                # Overshoot then settle
                if progress < 0.6:
                    return scale_from + (1.2 - scale_from) * (progress / 0.6)
                else:
                    return 1.2 - 0.2 * ((progress - 0.6) / 0.4)
            return 1.0

        return scale_func

    @staticmethod
    def pulse(min_scale: float = 0.95, max_scale: float = 1.05, period: float = 1.0) -> Callable:
        """Create continuous pulse effect."""
        def scale_func(t):
            phase = (t % period) / period
            return min_scale + (max_scale - min_scale) * (0.5 + 0.5 * math.sin(phase * 2 * math.pi))

        return scale_func

    @staticmethod
    def typewriter(text: str, char_duration: float = None) -> Callable:
        """
        Create typewriter text reveal effect.

        Returns a function that gives visible text at time t.
        """
        char_duration = char_duration or AnimationTimings.TYPING_CHAR

        def text_func(t):
            chars_visible = int(t / char_duration)
            return text[:chars_visible]

        return text_func

    @staticmethod
    def count_up(start: int, end: int, duration: float) -> Callable:
        """Create counting number animation."""
        def count_func(t):
            if t >= duration:
                return end
            progress = ease_out_cubic(t / duration)
            return int(start + (end - start) * progress)

        return count_func


# === Easing Functions ===

def ease_linear(t: float) -> float:
    """Linear easing."""
    return t

def ease_in_quad(t: float) -> float:
    """Quadratic ease in."""
    return t * t

def ease_out_quad(t: float) -> float:
    """Quadratic ease out."""
    return t * (2 - t)

def ease_in_out_quad(t: float) -> float:
    """Quadratic ease in-out."""
    return 2 * t * t if t < 0.5 else -1 + (4 - 2 * t) * t

def ease_in_cubic(t: float) -> float:
    """Cubic ease in."""
    return t * t * t

def ease_out_cubic(t: float) -> float:
    """Cubic ease out."""
    t -= 1
    return t * t * t + 1

def ease_in_out_cubic(t: float) -> float:
    """Cubic ease in-out."""
    if t < 0.5:
        return 4 * t * t * t
    t = 2 * t - 2
    return 0.5 * t * t * t + 1

def ease_out_bounce(t: float) -> float:
    """Bounce ease out."""
    if t < 1 / 2.75:
        return 7.5625 * t * t
    elif t < 2 / 2.75:
        t -= 1.5 / 2.75
        return 7.5625 * t * t + 0.75
    elif t < 2.5 / 2.75:
        t -= 2.25 / 2.75
        return 7.5625 * t * t + 0.9375
    else:
        t -= 2.625 / 2.75
        return 7.5625 * t * t + 0.984375

def ease_out_elastic(t: float) -> float:
    """Elastic ease out."""
    if t == 0 or t == 1:
        return t
    return math.pow(2, -10 * t) * math.sin((t - 0.075) * (2 * math.pi) / 0.3) + 1
