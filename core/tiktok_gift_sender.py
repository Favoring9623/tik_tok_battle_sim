"""
TikTok Live Gift Sender - Browser Automation
=============================================

Uses Playwright to automate gift sending on TikTok Live.
Requires user to log in manually on first use (session is saved).

WARNING: This may violate TikTok's Terms of Service.
Use at your own risk.
"""

import asyncio
import json
import logging
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, Callable, List, Dict, Any
from enum import Enum

try:
    from playwright.async_api import async_playwright, Browser, Page, BrowserContext
except ImportError:
    print("Playwright not installed. Run: pip install playwright && playwright install chromium")
    raise

logger = logging.getLogger("TikTokGiftSender")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(message)s')

# Session storage path
SESSION_PATH = Path(__file__).parent.parent / "data" / "tiktok_session"


class GiftType(Enum):
    """Common TikTok gifts with their panel positions."""
    ROSE = "Rose"
    FEST_POP = "Fest Pop"
    ICE_CREAM = "Ice Cream Cone"
    DOUGHNUT = "Doughnut"
    FEST_GEAR = "Fest Gear"
    FEST_CHEERS = "Fest Cheers"
    FEST_PARTY = "Fest Party"


@dataclass
class SendResult:
    """Result of a gift send attempt."""
    success: bool
    gift_name: str
    quantity: int
    error: Optional[str] = None
    timestamp: float = field(default_factory=time.time)


@dataclass
class SenderSession:
    """Tracks a gift sending session."""
    target_username: str
    gift_type: str
    total_quantity: int
    sent: int = 0
    failed: int = 0
    start_time: float = field(default_factory=time.time)
    status: str = "pending"  # pending, running, paused, completed, error

    @property
    def progress(self) -> float:
        if self.total_quantity == 0:
            return 0.0
        return (self.sent / self.total_quantity) * 100

    @property
    def remaining(self) -> int:
        return self.total_quantity - self.sent


class TikTokGiftSender:
    """
    Automated TikTok Live gift sender using browser automation.

    Usage:
        async with TikTokGiftSender() as sender:
            # First time: will open browser for login
            await sender.login()

            # Navigate to a live stream
            await sender.go_to_live("@username")

            # Send gifts
            await sender.send_gift("Fest Pop", quantity=100)
    """

    def __init__(
        self,
        headless: bool = False,  # Set True for invisible mode
        slow_mo: int = 100,      # Milliseconds delay between actions
        on_gift_sent: Optional[Callable[[SendResult], None]] = None,
        on_progress: Optional[Callable[[SenderSession], None]] = None,
    ):
        self.headless = headless
        self.slow_mo = slow_mo
        self._on_gift_sent = on_gift_sent
        self._on_progress = on_progress

        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None

        self._running = False
        self._paused = False
        self._current_session: Optional[SenderSession] = None

        # Ensure session directory exists
        SESSION_PATH.mkdir(parents=True, exist_ok=True)

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, *args):
        await self.close()

    async def start(self):
        """Start the browser."""
        logger.info("🚀 Starting browser...")
        self._playwright = await async_playwright().start()

        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
            slow_mo=self.slow_mo,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
            ]
        )

        # Try to load existing session
        if (SESSION_PATH / "state.json").exists():
            logger.info("📂 Loading saved session...")
            self._context = await self._browser.new_context(
                storage_state=str(SESSION_PATH / "state.json"),
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
        else:
            logger.info("🆕 Creating new session...")
            self._context = await self._browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )

        self._page = await self._context.new_page()

        # Block unnecessary resources for speed
        await self._page.route("**/*.{png,jpg,jpeg,gif,svg,ico}", lambda route: route.abort())

        logger.info("✅ Browser started")

    async def close(self):
        """Close the browser and save session."""
        if self._context:
            # Save session state
            await self._context.storage_state(path=str(SESSION_PATH / "state.json"))
            logger.info("💾 Session saved")

        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

        logger.info("🔌 Browser closed")

    async def login(self, timeout: int = 120):
        """
        Open TikTok login page and wait for user to log in.
        Session will be saved for future use.
        """
        logger.info("🔐 Opening TikTok login page...")
        await self._page.goto("https://www.tiktok.com/login")

        # Wait for user to complete login
        logger.info(f"⏳ Please log in manually in the browser window (timeout: {timeout}s)...")

        try:
            # Wait for navigation away from login page
            await self._page.wait_for_url(
                lambda url: "/login" not in url and "tiktok.com" in url,
                timeout=timeout * 1000
            )

            # Additional wait to ensure session is established
            await asyncio.sleep(2)

            # Save session
            await self._context.storage_state(path=str(SESSION_PATH / "state.json"))

            logger.info("✅ Login successful! Session saved.")
            return True

        except Exception as e:
            logger.error(f"❌ Login timeout or error: {e}")
            return False

    async def is_logged_in(self) -> bool:
        """Check if user is currently logged in."""
        await self._page.goto("https://www.tiktok.com")
        await asyncio.sleep(2)

        # Check for login button (if present, not logged in)
        login_btn = await self._page.query_selector('[data-e2e="top-login-button"]')
        return login_btn is None

    async def go_to_live(self, username: str) -> bool:
        """
        Navigate to a user's live stream.

        Args:
            username: TikTok username (with or without @)

        Returns:
            True if live stream found, False otherwise
        """
        username = username.lstrip("@")
        live_url = f"https://www.tiktok.com/@{username}/live"

        logger.info(f"🔴 Navigating to @{username}'s live stream...")
        await self._page.goto(live_url)

        # Wait for page load
        await asyncio.sleep(3)

        # Check if live is active
        page_content = await self._page.content()

        if "currently unavailable" in page_content.lower() or "isn't hosting" in page_content.lower():
            logger.warning(f"⚠️ @{username} is not live")
            return False

        logger.info(f"✅ Connected to @{username}'s live stream")
        return True

    async def open_gift_panel(self) -> bool:
        """Open the gift panel on the live stream page."""
        try:
            # New TikTok Live UI: gift bar is already visible at bottom
            # Check if gifts are already visible
            await asyncio.sleep(2)

            # Look for gift items in the bottom bar
            gift_items = await self._page.query_selector_all('div[class*="flex-col"][class*="items-center"][class*="w-\\[106px\\]"]')
            if gift_items and len(gift_items) > 0:
                logger.info(f"🎁 Gift bar already visible ({len(gift_items)} gifts)")
                return True

            # Alternative: look for text-based gift names
            common_gifts = ['Rose', 'Fest Pop', 'Fest Party', 'Fest Cheers']
            for gift_name in common_gifts:
                el = await self._page.query_selector(f'text="{gift_name}"')
                if el and await el.is_visible():
                    logger.info(f"🎁 Gift bar visible (found {gift_name})")
                    return True

            # Try clicking "More" to expand gift panel if it exists
            more_btn = await self._page.query_selector('text="More"')
            if more_btn and await more_btn.is_visible():
                await more_btn.click()
                logger.info("🎁 Clicked 'More' to expand gifts")
                await asyncio.sleep(1)
                return True

            # Fallback: look for any gift-related elements
            elements = await self._page.query_selector_all('[class*="gift" i]')
            if elements:
                logger.info(f"🎁 Found {len(elements)} gift-related elements")
                return True

            logger.warning("⚠️ Gift panel might not be visible")
            return True  # Continue anyway, might still work

        except Exception as e:
            logger.error(f"❌ Error checking gift panel: {e}")
            return False

    async def select_gift(self, gift_name: str) -> bool:
        """
        Select a specific gift from the panel.

        Args:
            gift_name: Name of the gift (e.g., "Rose", "Fest Pop")
        """
        try:
            # New TikTok UI: gifts are in horizontal bar at bottom
            # Each gift has the name visible, click on the gift container

            # Method 1: Find by exact text using get_by_text
            try:
                gift_locator = self._page.get_by_text(gift_name, exact=True)
                if await gift_locator.count() > 0:
                    await gift_locator.first.click()
                    logger.info(f"🎁 Selected gift: {gift_name}")
                    await asyncio.sleep(0.3)
                    return True
            except Exception as e:
                logger.debug(f"Method 1 failed: {e}")

            # Method 2: Find gift container by partial text match
            try:
                containers = await self._page.query_selector_all('div[class*="flex-col"][class*="items-center"]')
                for container in containers:
                    try:
                        text = await container.inner_text()
                        if gift_name.lower() in text.lower():
                            await container.click()
                            logger.info(f"🎁 Selected gift container: {gift_name}")
                            await asyncio.sleep(0.3)
                            return True
                    except:
                        continue
            except Exception as e:
                logger.debug(f"Method 2 failed: {e}")

            # Method 3: Use CSS selector with text content
            try:
                # Find element containing text
                el = await self._page.query_selector(f'//*[contains(text(), "{gift_name}")]')
                if el and await el.is_visible():
                    await el.click()
                    logger.info(f"🎁 Clicked on (xpath): {gift_name}")
                    await asyncio.sleep(0.3)
                    return True
            except Exception as e:
                logger.debug(f"Method 3 failed: {e}")

            # Method 4: Click More to find the gift in expanded panel
            try:
                more_locator = self._page.get_by_text("More", exact=True)
                if await more_locator.count() > 0 and await more_locator.first.is_visible():
                    await more_locator.first.click()
                    await asyncio.sleep(1)

                    # Now search again in expanded panel
                    gift_locator = self._page.get_by_text(gift_name, exact=False)
                    if await gift_locator.count() > 0:
                        await gift_locator.first.click()
                        logger.info(f"🎁 Selected gift from expanded panel: {gift_name}")
                        return True
            except Exception as e:
                logger.debug(f"Method 4 failed: {e}")

            logger.warning(f"⚠️ Gift not found: {gift_name}")
            return False

        except Exception as e:
            logger.error(f"❌ Error selecting gift: {e}")
            return False

    async def click_send(self) -> bool:
        """Click the send button to send the selected gift."""
        try:
            # New TikTok UI: Multiple ways to send

            # Method 1: Look for red heart/send button (commonly on right side)
            heart_selectors = [
                'svg[class*="heart" i]',
                '[class*="heart" i][class*="button" i]',
                'button[class*="send" i]',
                '[data-e2e="live-send-gift"]',
            ]

            for selector in heart_selectors:
                try:
                    btn = await self._page.query_selector(selector)
                    if btn and await btn.is_visible():
                        await btn.click()
                        logger.debug("Clicked heart/send button")
                        return True
                except:
                    continue

            # Method 2: Look for "Send" or "Envoyer" text
            send_texts = ['Send', 'Envoyer', 'Enviar', '发送']
            for text in send_texts:
                try:
                    btn = await self._page.locator(f'button:has-text("{text}")').first
                    if btn and await btn.is_visible():
                        await btn.click()
                        logger.debug(f"Clicked '{text}' button")
                        return True
                except:
                    continue

            # Method 3: In new TikTok UI, clicking on gift might send it directly
            # Just return True if gift was already clicked in select_gift
            logger.debug("Assuming gift sent on selection (new UI)")
            return True

        except Exception as e:
            logger.error(f"❌ Error clicking send: {e}")
            return False

    async def send_gift(
        self,
        gift_name: str = "Fest Pop",
        quantity: int = 1,
        delay_ms: int = 500,
    ) -> SenderSession:
        """
        Send multiple gifts automatically.

        In the new TikTok UI, clicking on a gift in the bar sends it directly.
        No separate "send" button needed.

        Args:
            gift_name: Name of the gift to send
            quantity: Number of gifts to send
            delay_ms: Delay between each send in milliseconds

        Returns:
            SenderSession with results
        """
        session = SenderSession(
            target_username=self._page.url.split("@")[1].split("/")[0] if "@" in self._page.url else "unknown",
            gift_type=gift_name,
            total_quantity=quantity,
            status="running"
        )
        self._current_session = session
        self._running = True
        self._paused = False

        logger.info(f"🚀 Starting to send {quantity}x {gift_name}...")

        # Verify gift panel is visible
        if not await self.open_gift_panel():
            session.status = "error"
            return session

        # Send loop - in new TikTok UI, clicking the gift sends it directly
        for i in range(quantity):
            if not self._running:
                session.status = "cancelled"
                break

            while self._paused:
                await asyncio.sleep(0.1)
                if not self._running:
                    break

            try:
                # Click on the gift to send it (new UI sends on click)
                success = await self._click_gift_to_send(gift_name)

                if success:
                    session.sent += 1
                    result = SendResult(True, gift_name, 1)
                else:
                    session.failed += 1
                    result = SendResult(False, gift_name, 1, "Send failed")

                if self._on_gift_sent:
                    self._on_gift_sent(result)

                if self._on_progress and session.sent % 10 == 0:
                    self._on_progress(session)

                # Progress log
                if session.sent % 50 == 0:
                    logger.info(f"📊 Progress: {session.sent}/{quantity} ({session.progress:.1f}%)")

            except Exception as e:
                session.failed += 1
                logger.warning(f"⚠️ Send error: {e}")

            # Delay between sends
            await asyncio.sleep(delay_ms / 1000)

        if session.status == "running":
            session.status = "completed"

        logger.info(f"✅ Session complete: {session.sent}/{quantity} sent, {session.failed} failed")
        return session

    async def _click_gift_to_send(self, gift_name: str) -> bool:
        """
        Click on a gift to send it (new TikTok UI).
        Clicking the gift icon directly sends 1 gift.
        Uses JavaScript for reliability with rapid clicks.
        """
        try:
            # Use JavaScript directly - most reliable for rapid clicks
            result = await self._page.evaluate(f"""
                () => {{
                    // Find the gift element by text content
                    const walker = document.createTreeWalker(
                        document.body,
                        NodeFilter.SHOW_TEXT,
                        null,
                        false
                    );

                    while (walker.nextNode()) {{
                        const node = walker.currentNode;
                        if (node.textContent.trim() === '{gift_name}') {{
                            // Get the clickable parent element
                            let el = node.parentElement;
                            // Walk up to find clickable container (max 5 levels)
                            for (let i = 0; i < 5 && el; i++) {{
                                if (el.offsetParent !== null) {{
                                    el.click();
                                    return true;
                                }}
                                el = el.parentElement;
                            }}
                        }}
                    }}

                    // Fallback: direct element search
                    const elements = document.querySelectorAll('div, span, button');
                    for (const el of elements) {{
                        if (el.textContent && el.textContent.trim() === '{gift_name}' && el.offsetParent !== null) {{
                            el.click();
                            return true;
                        }}
                    }}
                    return false;
                }}
            """)
            return result

        except Exception as e:
            logger.debug(f"Click gift error: {e}")
            return False

    async def send_burst(
        self,
        gift_name: str = "Fest Pop",
        quantity: int = 100,
        clicks_per_second: float = 5.0,
    ) -> SenderSession:
        """
        Send gifts as fast as possible (burst mode).

        Args:
            gift_name: Gift to send
            quantity: Total quantity
            clicks_per_second: Target CPS (limited by TikTok)
        """
        delay_ms = int(1000 / clicks_per_second)
        return await self.send_gift(gift_name, quantity, delay_ms)

    def pause(self):
        """Pause the current sending session."""
        self._paused = True
        if self._current_session:
            self._current_session.status = "paused"
        logger.info("⏸️ Paused")

    def resume(self):
        """Resume the current sending session."""
        self._paused = False
        if self._current_session:
            self._current_session.status = "running"
        logger.info("▶️ Resumed")

    def stop(self):
        """Stop the current sending session."""
        self._running = False
        logger.info("⏹️ Stopped")


# ============================================================
# CLI Interface
# ============================================================

async def interactive_mode():
    """Run the gift sender in interactive mode."""
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║           🎁 TikTok Live Gift Sender - Interactive Mode              ║
╠══════════════════════════════════════════════════════════════════════╣
║  ⚠️  WARNING: This may violate TikTok's Terms of Service            ║
║  Use at your own risk. Your account may be suspended.                ║
╚══════════════════════════════════════════════════════════════════════╝
    """)

    async with TikTokGiftSender(headless=False, slow_mo=50) as sender:
        # Check login status
        print("\n🔍 Checking login status...")

        if not await sender.is_logged_in():
            print("\n❌ Not logged in. Opening login page...")
            print("📱 Please log in using your TikTok account.")
            print("   You can use QR code, phone, or email login.")

            logged_in = await sender.login(timeout=180)
            if not logged_in:
                print("❌ Login failed or timed out.")
                return
        else:
            print("✅ Already logged in!")

        # Main menu loop
        while True:
            print("\n" + "=" * 50)
            print("📋 MENU")
            print("=" * 50)
            print("1. Go to a live stream")
            print("2. Send gifts (manual quantity)")
            print("3. Send burst (auto-clicker)")
            print("4. Exit")

            choice = input("\nChoose option (1-4): ").strip()

            if choice == "1":
                username = input("Enter username (e.g., @liznogalh): ").strip()
                if await sender.go_to_live(username):
                    print("✅ Connected to live stream!")
                else:
                    print("❌ Could not connect (user may not be live)")

            elif choice == "2":
                gift = input("Gift name (default: Fest Pop): ").strip() or "Fest Pop"
                qty = int(input("Quantity (default: 10): ").strip() or "10")

                print(f"\n🚀 Sending {qty}x {gift}...")
                session = await sender.send_gift(gift, qty, delay_ms=500)
                print(f"✅ Done! Sent: {session.sent}, Failed: {session.failed}")

            elif choice == "3":
                gift = input("Gift name (default: Fest Pop): ").strip() or "Fest Pop"
                qty = int(input("Quantity (default: 100): ").strip() or "100")
                cps = float(input("Clicks per second (default: 5): ").strip() or "5")

                print(f"\n🚀 Burst mode: {qty}x {gift} @ {cps} CPS...")
                session = await sender.send_burst(gift, qty, cps)
                print(f"✅ Done! Sent: {session.sent}, Failed: {session.failed}")

            elif choice == "4":
                print("\n👋 Goodbye!")
                break

            else:
                print("❌ Invalid option")


async def quick_test():
    """Quick test to verify setup."""
    print("🧪 Running quick test...")

    async with TikTokGiftSender(headless=False) as sender:
        print("✅ Browser started successfully")

        # Go to TikTok
        await sender._page.goto("https://www.tiktok.com")
        print("✅ TikTok loaded")

        # Check login
        logged_in = await sender.is_logged_in()
        print(f"{'✅' if logged_in else '❌'} Login status: {'Logged in' if logged_in else 'Not logged in'}")

        await asyncio.sleep(3)
        print("✅ Test complete")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        asyncio.run(quick_test())
    else:
        asyncio.run(interactive_mode())
