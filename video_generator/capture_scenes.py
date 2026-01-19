"""
Scene Capture Script - Captures screenshots and video clips for demo video
Uses Playwright to automate browser interactions
"""
import asyncio
import os
from playwright.async_api import async_playwright

# Output directory for captured assets
OUTPUT_DIR = "video_generator/assets/captures"
BASE_URL = "http://localhost:5000"

# Scene definitions with capture instructions
SCENES = [
    {
        "id": "01_intro",
        "name": "Introduction & Website",
        "actions": [
            {"type": "goto", "url": "/"},
            {"type": "wait", "ms": 1000},
            {"type": "screenshot", "name": "dashboard_main"},
            {"type": "scroll", "y": 300},
            {"type": "wait", "ms": 500},
            {"type": "screenshot", "name": "dashboard_scroll"},
        ]
    },
    {
        "id": "02_login",
        "name": "TikTok Login",
        "actions": [
            {"type": "goto", "url": "/"},
            {"type": "wait", "ms": 500},
            {"type": "screenshot", "name": "before_login"},
            # OAuth flow would be captured manually or simulated
        ]
    },
    {
        "id": "03_start_battle",
        "name": "Starting a Live Battle",
        "actions": [
            {"type": "goto", "url": "/"},
            {"type": "wait", "ms": 1000},
            {"type": "screenshot", "name": "battle_setup"},
        ]
    },
    {
        "id": "04_gift_tracking",
        "name": "Live Gift Tracking",
        "actions": [
            {"type": "goto", "url": "/"},
            {"type": "wait", "ms": 1000},
            {"type": "screenshot", "name": "gift_tracking_main"},
        ]
    },
    {
        "id": "05_analytics",
        "name": "Battle Analytics",
        "actions": [
            {"type": "goto", "url": "/analytics"},
            {"type": "wait", "ms": 1000},
            {"type": "screenshot", "name": "analytics_main"},
        ]
    },
    {
        "id": "06_leaderboards",
        "name": "Leaderboards",
        "actions": [
            {"type": "goto", "url": "/leaderboard"},
            {"type": "wait", "ms": 1000},
            {"type": "screenshot", "name": "leaderboard_main"},
        ]
    },
    {
        "id": "07_obs",
        "name": "OBS Integration",
        "actions": [
            {"type": "goto", "url": "/overlay"},
            {"type": "wait", "ms": 1000},
            {"type": "screenshot", "name": "obs_overlay"},
        ]
    },
    {
        "id": "08_conclusion",
        "name": "Battle Conclusion",
        "actions": [
            {"type": "goto", "url": "/"},
            {"type": "wait", "ms": 500},
            {"type": "screenshot", "name": "battle_end"},
        ]
    },
    {
        "id": "09_privacy",
        "name": "Closing & Privacy",
        "actions": [
            {"type": "goto", "url": "/privacy"},
            {"type": "wait", "ms": 1000},
            {"type": "screenshot", "name": "privacy_page"},
        ]
    },
]


async def capture_scene(page, scene: dict, output_dir: str):
    """Capture a single scene."""
    scene_dir = os.path.join(output_dir, scene["id"])
    os.makedirs(scene_dir, exist_ok=True)

    print(f"\n📹 Capturing: {scene['name']}")

    for i, action in enumerate(scene["actions"]):
        action_type = action["type"]

        if action_type == "goto":
            url = BASE_URL + action["url"]
            print(f"  → Navigating to {url}")
            try:
                await page.goto(url, wait_until="networkidle", timeout=10000)
            except Exception as e:
                print(f"  ⚠ Navigation timeout, continuing: {e}")
                await page.goto(url, wait_until="domcontentloaded", timeout=5000)

        elif action_type == "wait":
            await asyncio.sleep(action["ms"] / 1000)

        elif action_type == "screenshot":
            path = os.path.join(scene_dir, f"{action['name']}.png")
            await page.screenshot(path=path, full_page=False)
            print(f"  📸 Screenshot: {action['name']}.png")

        elif action_type == "scroll":
            await page.evaluate(f"window.scrollBy(0, {action['y']})")

        elif action_type == "click":
            try:
                await page.click(action["selector"], timeout=3000)
            except:
                print(f"  ⚠ Could not click: {action['selector']}")

        elif action_type == "type":
            await page.fill(action["selector"], action["text"])

        elif action_type == "video":
            # Start video recording for this segment
            video_path = os.path.join(scene_dir, f"{action['name']}.webm")
            print(f"  🎥 Recording: {action['name']}.webm")


async def capture_all_scenes():
    """Capture all scenes."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1,
        )
        page = await context.new_page()

        print("=" * 60)
        print("🎬 Scene Capture - TikTok Battle Simulator Demo")
        print("=" * 60)

        for scene in SCENES:
            try:
                await capture_scene(page, scene, OUTPUT_DIR)
            except Exception as e:
                print(f"  ❌ Error capturing {scene['name']}: {e}")

        await browser.close()

    print("\n" + "=" * 60)
    print("✅ Capture complete!")
    print(f"📁 Assets saved to: {OUTPUT_DIR}")
    print("=" * 60)


async def capture_single_scene(scene_id: str):
    """Capture a single scene by ID."""
    scene = next((s for s in SCENES if s["id"] == scene_id), None)
    if not scene:
        print(f"Scene '{scene_id}' not found")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1,
        )
        page = await context.new_page()

        await capture_scene(page, scene, OUTPUT_DIR)

        await browser.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # Capture specific scene
        asyncio.run(capture_single_scene(sys.argv[1]))
    else:
        # Capture all scenes
        asyncio.run(capture_all_scenes())
