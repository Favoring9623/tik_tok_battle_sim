"""
Final Video Assembly - Concatenates all pre-rendered clips into demo video
"""
import os
from moviepy import VideoFileClip, concatenate_videoclips

OUTPUT_DIR = "video_generator/output"

# Scene order for final video (matching config.py SCENES order)
SCENE_ORDER = [
    "intro_cinematic",  # 12s - Warner Bros style intro
    "dashboard",        # 10s
    "oauth",            # 15s
    "live_tracking",    # 12s
    "strategic_battle", # 15s
    "tournament",       # 12s
    "gift_tracking",    # 20s
    "gift_panel",       # 10s
    "all_gifts",        # 8s
    "analytics",        # 12s
    "leaderboard",      # 10s
    # "obs_overlay",    # REMOVED - transparent background renders as blank
    "control_center",   # 10s
    "live_battle_demo", # 30s - Final live strategic battle
    "closing",          # 15s
]


def assemble_video(output_filename="demo_video_final.mp4"):
    """Assemble all clips into final demo video."""
    print("=" * 60)
    print("Assembling Final Demo Video")
    print("=" * 60)

    clips = []
    total_duration = 0

    for scene_name in SCENE_ORDER:
        clip_path = os.path.join(OUTPUT_DIR, f"{scene_name}.mp4")

        if not os.path.exists(clip_path):
            print(f"  WARNING: Missing clip {scene_name}.mp4")
            continue

        clip = VideoFileClip(clip_path)
        clips.append(clip)
        total_duration += clip.duration
        print(f"  + {scene_name}.mp4 ({clip.duration:.1f}s)")

    if not clips:
        print("ERROR: No clips found!")
        return None

    print("-" * 60)
    print(f"Total clips: {len(clips)}")
    print(f"Total duration: {total_duration:.1f}s ({total_duration/60:.1f} min)")
    print()

    # Concatenate all clips
    print("Concatenating clips...")
    final = concatenate_videoclips(clips, method="compose")

    # Export
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    print(f"Exporting to: {output_path}")

    final.write_videofile(
        output_path,
        fps=30,
        codec="libx264",
        audio=False,
        preset="medium",
        bitrate="8000k",
        ffmpeg_params=["-pix_fmt", "yuv420p"]  # Ensure compatibility
    )

    # Close clips to free memory
    for clip in clips:
        clip.close()
    final.close()

    # Check file size
    if os.path.exists(output_path):
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print()
        print("=" * 60)
        print(f"Final video: {output_path}")
        print(f"Duration: {total_duration:.1f}s")
        print(f"File size: {size_mb:.1f} MB")

        if size_mb > 50:
            print()
            print("WARNING: File exceeds 50MB TikTok limit!")
            print("Compressing...")
            compress_video(output_path)
        else:
            print("File size OK for TikTok submission")
        print("=" * 60)

    return output_path


def compress_video(input_path, target_mb=45):
    """Compress video to target size."""
    import subprocess

    output_path = input_path.replace(".mp4", "_compressed.mp4")

    # Get duration
    clip = VideoFileClip(input_path)
    duration = clip.duration
    clip.close()

    # Calculate target bitrate (bits per second)
    target_bits = target_mb * 8 * 1024 * 1024
    target_bitrate = int(target_bits / duration)
    bitrate_k = f"{target_bitrate // 1000}k"

    print(f"Target bitrate: {bitrate_k}")

    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        "-c:v", "libx264",
        "-b:v", bitrate_k,
        "-preset", "slow",
        "-c:a", "copy",
        output_path
    ]

    subprocess.run(cmd, capture_output=True)

    if os.path.exists(output_path):
        size_mb = os.path.getsize(output_path) / (1024 * 1024)
        print(f"Compressed: {output_path} ({size_mb:.1f} MB)")
        return output_path

    return None


if __name__ == "__main__":
    assemble_video()
