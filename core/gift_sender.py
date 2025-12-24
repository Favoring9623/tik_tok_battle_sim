#!/usr/bin/env python3
"""
Universal TikTok Gift Sender
Supports all gift types with automatic detection
"""

import asyncio
import sys
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from playwright.async_api import async_playwright, Page, BrowserContext

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Gift locations: "bar" = bottom bar, "panel" = More panel
GIFT_LOCATIONS = {
    # Bottom bar gifts (always visible)
    "Rose": "bar",
    "Fest Cheers": "bar",
    "Fest Party": "bar",
    # Panel gifts (need to click "More")
    "Fest Pop": "panel",
    "Money Gun": "panel",
    "Private Jet": "panel",
    "Flying Jets": "panel",
    "Pyramids": "panel",
    "Interstellar": "panel",
    "Cheeky Wiggly": "panel",
    "Treasure Chest": "panel",
    "I'm Ready!": "panel",
}


@dataclass
class GiftSendResult:
    """Result of a gift sending operation"""
    success: bool
    sent: int
    failed: int
    gift_name: str
    streamer: str
    cps: float
    message: str = ""


class TikTokGiftSender:
    """Universal TikTok gift sender with support for all gift types"""

    def __init__(self, session_path: str = None):
        if session_path is None:
            # Use absolute path relative to project root
            import os
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            session_path = os.path.join(project_root, "data/tiktok_session/state.json")
        self.session_path = session_path
        self._playwright = None
        self._browser = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._current_streamer: Optional[str] = None
        self._is_connected = False

    async def connect(self, headless: bool = False):
        """Initialize browser and load session"""
        if self._is_connected:
            return

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=headless,
            slow_mo=0
        )
        self._context = await self._browser.new_context(
            storage_state=self.session_path,
            viewport={"width": 1280, "height": 800},
        )
        self._page = await self._context.new_page()
        self._is_connected = True
        logger.info("Browser connected")

    async def disconnect(self):
        """Close browser and save session"""
        if not self._is_connected:
            return

        try:
            await self._context.storage_state(path=self.session_path)
            await self._browser.close()
            await self._playwright.stop()
        except Exception as e:
            logger.warning(f"Error during disconnect: {e}")

        self._is_connected = False
        self._current_streamer = None
        logger.info("Browser disconnected")

    async def go_to_stream(self, username: str) -> bool:
        """Navigate to a streamer's live"""
        username = username.lstrip("@")

        if self._current_streamer == username:
            return True

        try:
            await self._page.goto(f"https://www.tiktok.com/@{username}/live")
            await asyncio.sleep(4)

            # Check if live is active - wait a bit more for page to load
            await asyncio.sleep(1)
            no_live = await self._page.locator('text="No LIVE"').count()
            if no_live > 0:
                logger.error(f"@{username} is not live")
                return False

            self._current_streamer = username
            logger.info(f"Connected to @{username}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to @{username}: {e}")
            return False

    async def _open_gift_panel(self) -> bool:
        """Open the 'More' gift panel"""
        try:
            more_btn = self._page.locator('text="More"').last
            if await more_btn.count() > 0:
                await more_btn.click()
                await asyncio.sleep(1)
                return True
        except Exception as e:
            logger.debug(f"Panel may already be open: {e}")
        return False

    async def _find_gift_position(self, gift_name: str) -> Optional[Dict[str, float]]:
        """Find a gift's click position by name"""

        # Check if we need to open the panel
        location = GIFT_LOCATIONS.get(gift_name, "panel")
        if location == "panel":
            await self._open_gift_panel()

        # Find the gift by text
        result = await self._page.evaluate(f"""
            () => {{
                const walker = document.createTreeWalker(
                    document.body, NodeFilter.SHOW_TEXT, null, false
                );
                while (walker.nextNode()) {{
                    const node = walker.currentNode;
                    if (node.textContent.trim() === '{gift_name}') {{
                        let el = node.parentElement;
                        for (let i = 0; i < 5; i++) {{
                            if (el && el.className?.includes?.('flex') &&
                                el.className?.includes?.('items-center')) {{
                                const img = el.querySelector('img');
                                if (img) {{
                                    const r = img.getBoundingClientRect();
                                    return {{
                                        x: r.x + r.width/2,
                                        y: r.y + r.height/2,
                                        found: true
                                    }};
                                }}
                            }}
                            el = el?.parentElement;
                        }}
                    }}
                }}
                return {{found: false}};
            }}
        """)

        if result.get('found'):
            return {'x': result['x'], 'y': result['y']}
        return None

    async def _find_send_button(self) -> Optional[Dict[str, float]]:
        """Find the Send button position"""
        result = await self._page.evaluate("""
            () => {
                const walker = document.createTreeWalker(
                    document.body, NodeFilter.SHOW_TEXT, null, false
                );
                while (walker.nextNode()) {
                    if (walker.currentNode.textContent.trim() === 'Send') {
                        let el = walker.currentNode.parentElement;
                        if (el && el.offsetParent) {
                            const r = el.getBoundingClientRect();
                            return {x: r.x + r.width/2, y: r.y + r.height/2, found: true};
                        }
                    }
                }
                return {found: false};
            }
        """)

        if result.get('found'):
            return {'x': result['x'], 'y': result['y']}
        return None

    async def send_gifts(
        self,
        username: str,
        gift_name: str,
        quantity: int,
        cps: float = 6.0,
        progress_callback=None
    ) -> GiftSendResult:
        """
        Send gifts to a streamer

        Args:
            username: Streamer's username (with or without @)
            gift_name: Name of the gift (e.g., "Rose", "Fest Pop")
            quantity: Number of gifts to send
            cps: Clicks per second (1-12 recommended)
            progress_callback: Optional callback(sent, total, failed)

        Returns:
            GiftSendResult with statistics
        """
        username = username.lstrip("@")

        # Connect to stream
        if not await self.go_to_stream(username):
            return GiftSendResult(
                success=False, sent=0, failed=0,
                gift_name=gift_name, streamer=username, cps=cps,
                message=f"@{username} is not live"
            )

        # Find gift position
        gift_pos = await self._find_gift_position(gift_name)
        if not gift_pos:
            return GiftSendResult(
                success=False, sent=0, failed=0,
                gift_name=gift_name, streamer=username, cps=cps,
                message=f"Gift '{gift_name}' not found"
            )

        logger.info(f"Gift '{gift_name}' found at ({gift_pos['x']:.0f}, {gift_pos['y']:.0f})")

        # Select gift and find Send button (must click gift first to show Send)
        await self._page.mouse.click(gift_pos['x'], gift_pos['y'])
        await asyncio.sleep(0.5)  # Wait for Send button to appear

        send_pos = await self._find_send_button()
        if not send_pos:
            return GiftSendResult(
                success=False, sent=0, failed=0,
                gift_name=gift_name, streamer=username, cps=cps,
                message="Send button not found"
            )

        logger.info(f"Send button at ({send_pos['x']:.0f}, {send_pos['y']:.0f})")

        # Send gifts
        delay = 1.0 / cps
        sent = 0
        failed = 0
        reselect_every = 100

        for i in range(quantity):
            try:
                # Re-select gift periodically
                if i > 0 and i % reselect_every == 0:
                    await self._page.mouse.click(gift_pos['x'], gift_pos['y'])
                    await asyncio.sleep(0.15)
                    # Update send button position
                    new_send = await self._find_send_button()
                    if new_send:
                        send_pos = new_send

                # Click Send
                await self._page.mouse.click(send_pos['x'], send_pos['y'])
                sent += 1

            except Exception as e:
                failed += 1
                logger.debug(f"Click error: {e}")

            # Progress callback
            if progress_callback and (i + 1) % 10 == 0:
                progress_callback(sent, quantity, failed)

            await asyncio.sleep(delay)

        return GiftSendResult(
            success=True,
            sent=sent,
            failed=failed,
            gift_name=gift_name,
            streamer=username,
            cps=cps,
            message=f"Sent {sent}/{quantity} {gift_name} to @{username}"
        )


async def main():
    """CLI interface"""
    if len(sys.argv) < 4:
        print("""
Usage: python gift_sender.py <username> <quantity> <gift_name> [cps]

Examples:
  python gift_sender.py @christ9817 100 "Fest Pop" 6.0
  python gift_sender.py nunu.d10 200 "Rose" 10.0
  python gift_sender.py @streamer 50 "Fest Cheers" 8.0

Available gifts:
  Bar:   Rose, Fest Cheers, Fest Party
  Panel: Fest Pop, Money Gun, Private Jet, Pyramids, etc.
        """)
        return

    username = sys.argv[1]
    quantity = int(sys.argv[2])
    gift_name = sys.argv[3]
    cps = float(sys.argv[4]) if len(sys.argv) > 4 else 6.0

    print(f"""
╔══════════════════════════════════════════════════════════════════════╗
║   🎁 UNIVERSAL GIFT SENDER                                           ║
╠══════════════════════════════════════════════════════════════════════╣
║   Streamer: {username:<20}  Gift: {gift_name:<20} ║
║   Quantité: {quantity:<15,}  Vitesse: {cps} CPS                      ║
╚══════════════════════════════════════════════════════════════════════╝
    """)

    sender = TikTokGiftSender()

    def progress(sent, total, failed):
        pct = sent / total * 100
        bar = "█" * int(pct / 2.5) + "░" * (40 - int(pct / 2.5))
        print(f"\r  [{bar}] {pct:>5.1f}% | {sent:,}/{total:,} | Échecs: {failed}", end="", flush=True)

    try:
        await sender.connect(headless=False)
        result = await sender.send_gifts(
            username=username,
            gift_name=gift_name,
            quantity=quantity,
            cps=cps,
            progress_callback=progress
        )

        print(f"\n\n{'═' * 60}")
        print("📊 RÉSULTAT")
        print("═" * 60)
        print(f"   {'✅' if result.success else '❌'} {result.message}")
        print(f"   Envoyés: {result.sent:,}")
        print(f"   Échecs: {result.failed}")
        if result.sent + result.failed > 0:
            print(f"   Taux réussite: {result.sent/(result.sent+result.failed)*100:.1f}%")
        print("═" * 60)

    finally:
        await sender.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
