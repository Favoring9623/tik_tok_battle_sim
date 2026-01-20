"""
Video Generator CLI - Generate demo videos for TikTok Developer Portal

Usage:
    python -m video_generator.generate                    # Generate full video
    python -m video_generator.generate --scene intro      # Generate single scene
    python -m video_generator.generate --preview intro    # Preview scene (no export)
    python -m video_generator.generate --list             # List all scenes
"""
import argparse
import os
import sys

# Check dependencies
try:
    from moviepy import VideoClip
    MOVIEPY_OK = True
except ImportError:
    MOVIEPY_OK = False
    print("ERROR: MoviePy not installed")
    print("Install with: pip install moviepy")

from .config import SCENES, get_scene_by_id, get_total_duration, OUTPUT_DIR
from .core.renderer import SceneRenderer, VideoCompositor


def list_scenes():
    """Print all available scenes."""
    print("\n Available Scenes:")
    print("-" * 60)
    total = 0
    for scene in SCENES:
        scope = scene.get("scope") or "-"
        print(f"  {scene['id']:<15} {scene['name']:<25} {scene['duration']:>3}s  [{scope}]")
        total += scene["duration"]
    print("-" * 60)
    print(f"  {'TOTAL':<15} {'':<25} {total:>3}s")
    print()


def generate_scene(scene_id: str, output_path: str = None, preview: bool = False):
    """Generate a single scene."""
    if not MOVIEPY_OK:
        return

    renderer = SceneRenderer()
    clip = renderer.render_scene(scene_id)

    if clip is None:
        print(f"Failed to render scene: {scene_id}")
        return

    print(f"Scene '{scene_id}' rendered: {clip.duration}s")

    if preview:
        print("Preview mode - displaying...")
        clip.preview(fps=15)
    elif output_path:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        print(f"Exporting to: {output_path}")
        clip.write_videofile(output_path, fps=30, codec="libx264", audio=False)
        print("Done!")


def generate_full_video(output_path: str):
    """Generate the complete demo video."""
    if not MOVIEPY_OK:
        return

    print("\n Generating Full Demo Video")
    print("=" * 60)

    compositor = VideoCompositor()

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    # Compose and export
    compositor.export(output_path)

    # Check file size
    if os.path.exists(output_path):
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"\nFile size: {size_mb:.1f} MB")
        if size_mb > 50:
            print("WARNING: File exceeds 50MB TikTok limit!")
            print("Run compression: python -m video_generator.compress")


def main():
    parser = argparse.ArgumentParser(
        description="Generate demo videos for TikTok Developer Portal"
    )
    parser.add_argument(
        "--scene", "-s",
        help="Generate specific scene by ID"
    )
    parser.add_argument(
        "--preview", "-p",
        help="Preview scene without exporting"
    )
    parser.add_argument(
        "--output", "-o",
        default="video_generator/output/demo_video.mp4",
        help="Output file path"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all available scenes"
    )

    args = parser.parse_args()

    if args.list:
        list_scenes()
        return

    if args.preview:
        generate_scene(args.preview, preview=True)
        return

    if args.scene:
        output = f"video_generator/output/{args.scene}.mp4"
        generate_scene(args.scene, output_path=output)
        return

    # Generate full video
    generate_full_video(args.output)


if __name__ == "__main__":
    main()
