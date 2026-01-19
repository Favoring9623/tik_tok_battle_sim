"""
Scene Renderer - Generates video frames for each scene
"""
from typing import List, Optional, Callable
from dataclasses import dataclass
import os

try:
    from moviepy.editor import (
        VideoClip, ColorClip, TextClip, ImageClip,
        CompositeVideoClip, concatenate_videoclips
    )
    from moviepy.video.fx.all import fadein, fadeout, resize
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    print("MoviePy not installed. Run: pip install moviepy")

from ..config import (
    VIDEO_WIDTH, VIDEO_HEIGHT, VIDEO_FPS,
    Colors, Fonts, FontSizes, AnimationTimings,
    SCENES, get_scene_by_id
)


@dataclass
class Element:
    """Rendered element in a scene."""
    clip: any
    start_time: float = 0
    duration: float = None
    position: tuple = ("center", "center")
    z_index: int = 0


class SceneRenderer:
    """Renders individual scenes as video clips."""

    def __init__(self):
        if not MOVIEPY_AVAILABLE:
            raise RuntimeError("MoviePy is required for video generation")

        self.width = VIDEO_WIDTH
        self.height = VIDEO_HEIGHT
        self.fps = VIDEO_FPS

    def render_scene(self, scene_id: str) -> Optional[VideoClip]:
        """Render a scene by ID."""
        scene = get_scene_by_id(scene_id)
        if not scene:
            print(f"Scene '{scene_id}' not found")
            return None

        print(f"Rendering scene: {scene['name']} ({scene['duration']}s)")

        # Create background
        bg = self._create_background(scene)

        # Render elements
        elements = []
        current_time = 0

        for element_config in scene.get("elements", []):
            element = self._render_element(element_config, scene["duration"])
            if element:
                element.start_time = current_time + element_config.get("delay", 0)
                elements.append(element)

        # Composite all elements
        clips = [bg]
        for elem in sorted(elements, key=lambda e: e.z_index):
            clip = elem.clip.set_start(elem.start_time)
            if elem.position:
                clip = clip.set_position(elem.position)
            clips.append(clip)

        return CompositeVideoClip(clips, size=(self.width, self.height)).set_duration(scene["duration"])

    def _create_background(self, scene: dict) -> VideoClip:
        """Create background clip for scene."""
        bg_config = next(
            (e for e in scene.get("elements", []) if e.get("type") == "background"),
            {"style": "solid"}
        )

        style = bg_config.get("style", "solid")

        if style == "gradient":
            return self._create_gradient_background(scene["duration"])
        else:
            return ColorClip(
                size=(self.width, self.height),
                color=self._hex_to_rgb(Colors.BACKGROUND)
            ).set_duration(scene["duration"])

    def _create_gradient_background(self, duration: float) -> VideoClip:
        """Create a gradient background."""
        # For simplicity, use a solid dark color
        # A real gradient would require custom frame generation
        return ColorClip(
            size=(self.width, self.height),
            color=self._hex_to_rgb(Colors.BACKGROUND)
        ).set_duration(duration)

    def _render_element(self, config: dict, scene_duration: float) -> Optional[Element]:
        """Render a single element based on config."""
        elem_type = config.get("type")

        if elem_type == "background":
            return None  # Handled separately

        elif elem_type == "title":
            return self._render_text(
                config.get("text", ""),
                FontSizes.H1,
                config.get("animation"),
                scene_duration
            )

        elif elem_type == "subtitle":
            return self._render_text(
                config.get("text", ""),
                FontSizes.H2,
                config.get("animation"),
                scene_duration,
                color=Colors.TEXT_MUTED
            )

        elif elem_type == "text":
            return self._render_text(
                config.get("text", ""),
                FontSizes.BODY,
                config.get("animation"),
                scene_duration
            )

        elif elem_type == "logo":
            return self._render_logo(config, scene_duration)

        elif elem_type == "browser_frame":
            return self._render_browser_frame(config, scene_duration)

        elif elem_type == "screenshot":
            return self._render_screenshot(config, scene_duration)

        elif elem_type == "callout":
            return self._render_callout(config, scene_duration)

        return None

    def _render_text(
        self,
        text: str,
        font_size: int,
        animation: str = None,
        duration: float = 5,
        color: str = None
    ) -> Element:
        """Render text element with optional animation."""
        color = color or Colors.TEXT

        clip = TextClip(
            text,
            fontsize=font_size,
            color=color,
            font=Fonts.TITLE
        ).set_duration(duration)

        # Apply animation
        if animation == "fade_in":
            clip = clip.fx(fadein, AnimationTimings.FADE_IN)
        elif animation == "slide_up":
            clip = self._apply_slide_up(clip)

        return Element(clip=clip, position=("center", "center"))

    def _render_logo(self, config: dict, duration: float) -> Element:
        """Render logo element."""
        # Create a simple text logo for now
        clip = TextClip(
            "ORION",
            fontsize=FontSizes.H1,
            color=Colors.PRIMARY,
            font=Fonts.TITLE
        ).set_duration(duration)

        animation = config.get("animation")
        if animation == "fade_in":
            clip = clip.fx(fadein, AnimationTimings.FADE_IN)

        return Element(clip=clip, position=("center", "center"))

    def _render_browser_frame(self, config: dict, duration: float) -> Element:
        """Render browser frame with URL bar."""
        url = config.get("url", "https://orionlabs.live")

        # Create URL bar text
        url_clip = TextClip(
            f"  {url}",
            fontsize=FontSizes.CAPTION,
            color=Colors.TEXT,
            font=Fonts.MONO,
            bg_color=Colors.BACKGROUND_ALT
        ).set_duration(duration)

        return Element(clip=url_clip, position=("center", 50))

    def _render_screenshot(self, config: dict, duration: float) -> Element:
        """Render screenshot image."""
        source = config.get("source", "")
        # Placeholder - would load actual image
        clip = ColorClip(
            size=(self.width - 100, self.height - 200),
            color=self._hex_to_rgb(Colors.BACKGROUND_ALT)
        ).set_duration(duration)

        return Element(clip=clip, position=("center", "center"))

    def _render_callout(self, config: dict, duration: float) -> Element:
        """Render callout text box."""
        text = config.get("text", "")
        position = config.get("position", "bottom_right")

        clip = TextClip(
            f" {text} ",
            fontsize=FontSizes.BODY,
            color=Colors.TEXT,
            font=Fonts.BODY,
            bg_color=Colors.PRIMARY
        ).set_duration(duration).fx(fadein, 0.3)

        # Convert position name to coordinates
        pos = self._get_position_coords(position)

        return Element(clip=clip, position=pos)

    def _apply_slide_up(self, clip: VideoClip) -> VideoClip:
        """Apply slide up animation."""
        def position_func(t):
            if t < AnimationTimings.SLIDE_IN:
                progress = t / AnimationTimings.SLIDE_IN
                y_offset = int(100 * (1 - progress))
                return ("center", self.height // 2 + y_offset)
            return ("center", "center")

        return clip.set_position(position_func)

    def _get_position_coords(self, position_name: str) -> tuple:
        """Convert position name to coordinates."""
        positions = {
            "center": ("center", "center"),
            "top": ("center", 100),
            "bottom": ("center", self.height - 100),
            "top_left": (50, 50),
            "top_right": (self.width - 300, 50),
            "bottom_left": (50, self.height - 100),
            "bottom_right": (self.width - 300, self.height - 100),
        }
        return positions.get(position_name, ("center", "center"))

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> tuple:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


class VideoCompositor:
    """Assembles all scenes into final video."""

    def __init__(self):
        self.renderer = SceneRenderer()

    def compose_all_scenes(self) -> VideoClip:
        """Render and compose all scenes."""
        clips = []

        for scene in SCENES:
            clip = self.renderer.render_scene(scene["id"])
            if clip:
                clips.append(clip)
                print(f"  Added: {scene['name']} ({clip.duration}s)")

        if not clips:
            raise ValueError("No scenes rendered")

        print(f"\nTotal scenes: {len(clips)}")
        return concatenate_videoclips(clips, method="compose")

    def export(self, output_path: str, clip: VideoClip = None):
        """Export final video."""
        if clip is None:
            clip = self.compose_all_scenes()

        print(f"\nExporting to: {output_path}")
        clip.write_videofile(
            output_path,
            fps=VIDEO_FPS,
            codec="libx264",
            audio=False,
            preset="medium",
            bitrate="8000k"
        )
        print("Export complete!")


if __name__ == "__main__":
    # Test render
    renderer = SceneRenderer()
    clip = renderer.render_scene("intro")
    if clip:
        print(f"Intro scene rendered: {clip.duration}s")
