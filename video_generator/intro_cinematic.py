"""
Cinematic Intro Generator - Warner Bros style introduction
Creates a dramatic entrance into the TikTok Battle Live universe
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

try:
    from moviepy import (
        VideoClip, ColorClip, TextClip, ImageClip,
        CompositeVideoClip, concatenate_videoclips, AudioFileClip
    )
    from moviepy import vfx
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    print("MoviePy required: pip install moviepy")

# === CONFIG ===
WIDTH = 1920
HEIGHT = 1080
FPS = 30
DURATION = 12  # seconds

# Colors
DARK_BG = (8, 8, 12)
TIKTOK_CYAN = (0, 242, 234)
TIKTOK_RED = (255, 0, 80)
GOLD = (255, 215, 0)
WHITE = (255, 255, 255)

# Fonts
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def create_particle_frame(t, num_particles=100):
    """Create a frame with floating particles/stars."""
    img = Image.new('RGBA', (WIDTH, HEIGHT), (*DARK_BG, 255))
    draw = ImageDraw.Draw(img)

    np.random.seed(42)  # Consistent particles

    for i in range(num_particles):
        # Particle properties
        base_x = np.random.randint(0, WIDTH)
        base_y = np.random.randint(0, HEIGHT)
        size = np.random.randint(1, 4)
        speed = np.random.uniform(0.5, 2)

        # Animate upward drift
        y = (base_y - t * speed * 30) % HEIGHT
        x = base_x + np.sin(t * 2 + i) * 10

        # Twinkle effect
        alpha = int(128 + 127 * np.sin(t * 3 + i))

        # Color variation (cyan/white/gold)
        colors = [TIKTOK_CYAN, WHITE, GOLD, TIKTOK_RED]
        color = colors[i % len(colors)]

        draw.ellipse(
            [x - size, y - size, x + size, y + size],
            fill=(*color, alpha)
        )

    return np.array(img)


def create_glow_text(text, font_size, color, glow_color, glow_radius=10):
    """Create text with glow effect."""
    # Create larger canvas for glow
    padding = glow_radius * 4
    font = ImageFont.truetype(FONT_PATH, font_size)

    # Get text size
    dummy = Image.new('RGBA', (1, 1))
    draw = ImageDraw.Draw(dummy)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # Create image with padding
    img_width = text_width + padding * 2
    img_height = text_height + padding * 2
    img = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw glow layer
    glow_img = Image.new('RGBA', (img_width, img_height), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_img)
    glow_draw.text((padding, padding), text, font=font, fill=(*glow_color, 255))
    glow_img = glow_img.filter(ImageFilter.GaussianBlur(glow_radius))

    # Composite glow
    img = Image.alpha_composite(img, glow_img)

    # Draw main text
    draw = ImageDraw.Draw(img)
    draw.text((padding, padding), text, font=font, fill=(*color, 255))

    return img


def create_logo_frame(t, phase="build"):
    """Create animated logo frame."""
    img = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Logo text
    logo_text = "ORION"
    subtitle = "BATTLE SYSTEMS"
    tagline = "TikTok Live Battle Simulator"

    # Animation phases
    if phase == "build":
        # Fade in with scale
        progress = min(t / 2, 1)
        alpha = int(255 * progress)
        scale = 0.5 + 0.5 * progress
    elif phase == "hold":
        alpha = 255
        scale = 1.0
    elif phase == "pulse":
        alpha = 255
        scale = 1.0 + 0.05 * np.sin(t * 4)
    else:
        alpha = 255
        scale = 1.0

    # Main logo with glow
    font_size = int(120 * scale)
    try:
        font = ImageFont.truetype(FONT_PATH, font_size)
        small_font = ImageFont.truetype(FONT_PATH, int(36 * scale))
        tag_font = ImageFont.truetype(FONT_PATH, int(28 * scale))
    except:
        return np.array(img)

    # Center position
    bbox = draw.textbbox((0, 0), logo_text, font=font)
    text_width = bbox[2] - bbox[0]
    x = (WIDTH - text_width) // 2
    y = HEIGHT // 2 - 80

    # Draw glow effect
    for offset in range(20, 0, -5):
        glow_alpha = int(alpha * (20 - offset) / 60)
        glow_color = (*TIKTOK_CYAN, glow_alpha)
        draw.text((x, y), logo_text, font=font, fill=glow_color)

    # Main text with gradient effect (cyan to red)
    draw.text((x - 2, y), logo_text, font=font, fill=(*TIKTOK_RED, alpha))
    draw.text((x + 2, y), logo_text, font=font, fill=(*TIKTOK_CYAN, alpha))
    draw.text((x, y), logo_text, font=font, fill=(*WHITE, alpha))

    # Subtitle
    if t > 1.5:
        sub_alpha = int(255 * min((t - 1.5) / 1, 1))
        bbox = draw.textbbox((0, 0), subtitle, font=small_font)
        sub_width = bbox[2] - bbox[0]
        draw.text(
            ((WIDTH - sub_width) // 2, y + 130),
            subtitle,
            font=small_font,
            fill=(*GOLD, sub_alpha)
        )

    # Tagline
    if t > 2.5:
        tag_alpha = int(255 * min((t - 2.5) / 1, 1))
        bbox = draw.textbbox((0, 0), tagline, font=tag_font)
        tag_width = bbox[2] - bbox[0]
        draw.text(
            ((WIDTH - tag_width) // 2, y + 180),
            tagline,
            font=tag_font,
            fill=(*WHITE, tag_alpha)
        )

    return np.array(img)


def create_light_rays(t):
    """Create dramatic light ray effect."""
    img = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    center_x = WIDTH // 2
    center_y = HEIGHT // 2

    num_rays = 12
    for i in range(num_rays):
        angle = (i / num_rays) * 2 * np.pi + t * 0.5
        length = 800 + 200 * np.sin(t * 2 + i)

        end_x = center_x + np.cos(angle) * length
        end_y = center_y + np.sin(angle) * length

        # Ray alpha pulsing
        alpha = int(30 + 20 * np.sin(t * 3 + i))

        # Draw ray as polygon
        width = 100
        perp_angle = angle + np.pi / 2
        dx = np.cos(perp_angle) * width
        dy = np.sin(perp_angle) * width

        points = [
            (center_x - dx/4, center_y - dy/4),
            (center_x + dx/4, center_y + dy/4),
            (end_x + dx, end_y + dy),
            (end_x - dx, end_y - dy),
        ]

        color = TIKTOK_CYAN if i % 2 == 0 else TIKTOK_RED
        draw.polygon(points, fill=(*color, alpha))

    # Apply blur
    img = img.filter(ImageFilter.GaussianBlur(30))

    return np.array(img)


def create_vignette():
    """Create vignette overlay."""
    img = Image.new('RGBA', (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    center_x, center_y = WIDTH // 2, HEIGHT // 2
    max_dist = np.sqrt(center_x**2 + center_y**2)

    # Radial gradient
    for y in range(0, HEIGHT, 4):
        for x in range(0, WIDTH, 4):
            dist = np.sqrt((x - center_x)**2 + (y - center_y)**2)
            alpha = int(200 * (dist / max_dist) ** 1.5)
            alpha = min(alpha, 220)
            draw.rectangle([x, y, x+4, y+4], fill=(0, 0, 0, alpha))

    return img


def make_frame(t):
    """Generate a single frame of the cinematic intro."""
    # Base dark background
    frame = np.full((HEIGHT, WIDTH, 3), DARK_BG, dtype=np.uint8)

    # Convert to PIL for compositing
    base = Image.fromarray(frame).convert('RGBA')

    # Phase timing
    if t < 1:
        # Fade from black with particles appearing
        fade = t
        phase = "build"
    elif t < 3:
        # Light rays appear
        fade = 1
        phase = "build"
    elif t < 8:
        # Full logo display with pulse
        fade = 1
        phase = "pulse"
    elif t < 10:
        # Hold
        fade = 1
        phase = "hold"
    else:
        # Fade out
        fade = max(0, 1 - (t - 10) / 2)
        phase = "hold"

    # Add light rays (subtle)
    if t > 1:
        rays = Image.fromarray(create_light_rays(t))
        ray_alpha = min((t - 1) / 2, 1) * fade
        rays.putalpha(Image.fromarray(
            (np.array(rays.split()[3]) * ray_alpha).astype(np.uint8)
        ))
        base = Image.alpha_composite(base, rays)

    # Add particles
    particles = Image.fromarray(create_particle_frame(t, num_particles=80))
    particle_alpha = fade
    particles.putalpha(Image.fromarray(
        (np.array(particles.split()[3]) * particle_alpha).astype(np.uint8)
    ))
    base = Image.alpha_composite(base, particles)

    # Add logo
    if t > 0.5:
        logo = Image.fromarray(create_logo_frame(t - 0.5, phase))
        logo_alpha = min((t - 0.5) / 1, 1) * fade
        logo.putalpha(Image.fromarray(
            (np.array(logo.split()[3]) * logo_alpha).astype(np.uint8)
        ))
        base = Image.alpha_composite(base, logo)

    # Add vignette
    vignette = create_vignette()
    base = Image.alpha_composite(base, vignette)

    # Apply overall fade
    if fade < 1:
        dark = Image.new('RGBA', (WIDTH, HEIGHT), (*DARK_BG, int(255 * (1 - fade))))
        base = Image.alpha_composite(base, dark)

    return np.array(base.convert('RGB'))


def generate_cinematic_intro(output_path="video_generator/output/intro_cinematic.mp4"):
    """Generate the full cinematic intro video."""
    if not MOVIEPY_AVAILABLE:
        print("MoviePy is required")
        return

    print("=" * 60)
    print("🎬 Generating Cinematic Intro")
    print("=" * 60)
    print(f"Resolution: {WIDTH}x{HEIGHT}")
    print(f"Duration: {DURATION}s")
    print(f"FPS: {FPS}")
    print()

    # Create video clip from frame function
    clip = VideoClip(make_frame, duration=DURATION)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Export
    print("Rendering frames...")
    clip.write_videofile(
        output_path,
        fps=FPS,
        codec="libx264",
        audio=False,
        preset="medium",
        bitrate="8000k"
    )

    print()
    print("=" * 60)
    print(f"✅ Cinematic intro saved: {output_path}")
    print("=" * 60)

    return output_path


if __name__ == "__main__":
    generate_cinematic_intro()
