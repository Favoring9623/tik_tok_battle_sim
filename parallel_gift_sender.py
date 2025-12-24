#!/usr/bin/env python3
"""
Parallel Gift Sender - Multi-browser simultaneous gift sending
Achieves 50-60+ CPS by running multiple browser instances in parallel
"""

import asyncio
import sys
import time
from dataclasses import dataclass, field
from typing import List, Optional
from playwright.async_api import async_playwright, Browser, Page

@dataclass
class WorkerStats:
    """Stats for a single worker"""
    worker_id: int
    sent: int = 0
    failed: int = 0
    target: int = 0
    status: str = "idle"

@dataclass
class ParallelStats:
    """Combined stats for all workers"""
    workers: List[WorkerStats] = field(default_factory=list)
    start_time: float = 0
    total_target: int = 0

    @property
    def total_sent(self) -> int:
        return sum(w.sent for w in self.workers)

    @property
    def total_failed(self) -> int:
        return sum(w.failed for w in self.workers)

    @property
    def elapsed(self) -> float:
        return time.time() - self.start_time if self.start_time else 0

    @property
    def effective_cps(self) -> float:
        return self.total_sent / self.elapsed if self.elapsed > 0 else 0


async def worker_send_gifts(
    worker_id: int,
    username: str,
    gift_name: str,
    quantity: int,
    cps: float,
    session_path: str,
    stats: WorkerStats,
    display_lock: asyncio.Lock
) -> None:
    """Single worker that sends gifts"""

    stats.status = "starting"
    stats.target = quantity

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False, slow_mo=0)
    context = await browser.new_context(
        storage_state=session_path,
        viewport={"width": 1280, "height": 800},
    )
    page = await context.new_page()

    try:
        # Navigate to stream
        stats.status = "connecting"
        await page.goto(f"https://www.tiktok.com/@{username}/live")
        await asyncio.sleep(4)

        # Open gift panel
        stats.status = "opening panel"
        try:
            more_btn = page.locator('text="More"').last
            await more_btn.click()
            await asyncio.sleep(1.5)
        except:
            pass

        # Find gift position
        stats.status = "finding gift"
        gift_pos = await page.evaluate(f"""
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
                                    return {{x: r.x + r.width/2, y: r.y + r.height/2}};
                                }}
                            }}
                            el = el?.parentElement;
                        }}
                    }}
                }}
                return null;
            }}
        """)

        if not gift_pos:
            stats.status = "gift not found"
            return

        # Select gift and find Send button
        await page.mouse.click(gift_pos['x'], gift_pos['y'])
        await asyncio.sleep(0.4)

        send_pos = await page.evaluate("""
            () => {
                const walker = document.createTreeWalker(
                    document.body, NodeFilter.SHOW_TEXT, null, false
                );
                while (walker.nextNode()) {
                    if (walker.currentNode.textContent.trim() === 'Send') {
                        let el = walker.currentNode.parentElement;
                        if (el && el.offsetParent) {
                            const r = el.getBoundingClientRect();
                            return {x: r.x + r.width/2, y: r.y + r.height/2};
                        }
                    }
                }
                return null;
            }
        """)

        if not send_pos:
            stats.status = "send btn not found"
            return

        # Send gifts
        stats.status = "sending"
        delay = 1.0 / cps
        reselect_every = 100

        for i in range(quantity):
            try:
                # Re-select gift periodically
                if i > 0 and i % reselect_every == 0:
                    await page.mouse.click(gift_pos['x'], gift_pos['y'])
                    await asyncio.sleep(0.15)
                    new_send = await page.evaluate("""
                        () => {
                            const walker = document.createTreeWalker(
                                document.body, NodeFilter.SHOW_TEXT, null, false
                            );
                            while (walker.nextNode()) {
                                if (walker.currentNode.textContent.trim() === 'Send') {
                                    let el = walker.currentNode.parentElement;
                                    if (el && el.offsetParent) {
                                        const r = el.getBoundingClientRect();
                                        return {x: r.x + r.width/2, y: r.y + r.height/2};
                                    }
                                }
                            }
                            return null;
                        }
                    """)
                    if new_send:
                        send_pos = new_send

                await page.mouse.click(send_pos['x'], send_pos['y'])
                stats.sent += 1

            except:
                stats.failed += 1

            await asyncio.sleep(delay)

        stats.status = "completed"

    except Exception as e:
        stats.status = f"error: {str(e)[:30]}"

    finally:
        try:
            await context.storage_state(path=session_path)
            await browser.close()
            await playwright.stop()
        except:
            pass


async def display_progress(stats: ParallelStats, num_workers: int):
    """Display live progress"""
    while True:
        # Build display
        lines = []
        lines.append("\033[H\033[J")  # Clear screen
        lines.append("╔══════════════════════════════════════════════════════════════════╗")
        lines.append("║   🚀 PARALLEL GIFT SENDER                                        ║")
        lines.append("╠══════════════════════════════════════════════════════════════════╣")

        for w in stats.workers:
            if w.target > 0:
                pct = w.sent / w.target * 100
                bar_len = 20
                filled = int(pct / 100 * bar_len)
                bar = "█" * filled + "░" * (bar_len - filled)
                line = f"║  Worker {w.worker_id}: [{bar}] {w.sent:>5}/{w.target:<5} | {w.status:<15} ║"
            else:
                line = f"║  Worker {w.worker_id}: {'waiting...':<47} ║"
            lines.append(line)

        lines.append("╠══════════════════════════════════════════════════════════════════╣")

        elapsed = stats.elapsed
        cps = stats.effective_cps
        total_pct = (stats.total_sent / stats.total_target * 100) if stats.total_target > 0 else 0

        lines.append(f"║  TOTAL: {stats.total_sent:,}/{stats.total_target:,} ({total_pct:.1f}%)                              ║")
        lines.append(f"║  Temps: {elapsed:.1f}s | CPS effectif: {cps:.1f} | Échecs: {stats.total_failed}           ║")
        lines.append("╚══════════════════════════════════════════════════════════════════╝")

        print("\n".join(lines), flush=True)

        # Check if done
        if stats.total_sent >= stats.total_target:
            break
        if all(w.status in ["completed", "error", "gift not found", "send btn not found"]
               for w in stats.workers if w.target > 0):
            break

        await asyncio.sleep(0.5)


async def parallel_send(
    username: str,
    gift_name: str,
    total_quantity: int,
    num_workers: int = 5,
    cps_per_worker: float = 12.0,
    session_path: str = "data/tiktok_session/state.json"
):
    """Send gifts using multiple parallel browser instances"""

    username = username.lstrip("@")

    # Calculate quantity per worker
    base_qty = total_quantity // num_workers
    remainder = total_quantity % num_workers

    # Create stats
    stats = ParallelStats(total_target=total_quantity)
    for i in range(num_workers):
        qty = base_qty + (1 if i < remainder else 0)
        stats.workers.append(WorkerStats(worker_id=i+1, target=qty))

    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║   🚀 PARALLEL GIFT SENDER                                        ║
╠══════════════════════════════════════════════════════════════════╣
║   Streamer: @{username:<20}  Gift: {gift_name:<15}         ║
║   Total: {total_quantity:,} cadeaux avec {num_workers} workers à {cps_per_worker} CPS chacun    ║
║   CPS théorique: {num_workers * cps_per_worker:.0f} | Temps estimé: ~{total_quantity/(num_workers*cps_per_worker):.0f}s             ║
╚══════════════════════════════════════════════════════════════════╝

⏳ Lancement des {num_workers} navigateurs...
    """)

    await asyncio.sleep(2)

    stats.start_time = time.time()

    # Create display lock
    display_lock = asyncio.Lock()

    # Start workers
    worker_tasks = []
    for i, worker_stats in enumerate(stats.workers):
        qty = base_qty + (1 if i < remainder else 0)
        task = asyncio.create_task(
            worker_send_gifts(
                worker_id=i+1,
                username=username,
                gift_name=gift_name,
                quantity=qty,
                cps=cps_per_worker,
                session_path=session_path,
                stats=worker_stats,
                display_lock=display_lock
            )
        )
        worker_tasks.append(task)
        await asyncio.sleep(1)  # Stagger browser launches

    # Start display task
    display_task = asyncio.create_task(display_progress(stats, num_workers))

    # Wait for all workers
    await asyncio.gather(*worker_tasks, return_exceptions=True)

    # Final display
    await asyncio.sleep(1)
    display_task.cancel()

    elapsed = stats.elapsed

    print(f"""

{'═' * 66}
📊 RÉSULTAT FINAL
{'═' * 66}
   ✅ Total envoyés: {stats.total_sent:,}
   ❌ Échecs: {stats.total_failed}
   ⏱️  Temps total: {elapsed:.1f} secondes
   ⚡ CPS effectif: {stats.effective_cps:.1f}
   📈 Taux réussite: {stats.total_sent/(stats.total_sent+stats.total_failed)*100:.1f}%
{'═' * 66}
    """)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("""
Usage: python parallel_gift_sender.py <username> <quantity> [workers] [cps]

Exemples:
  python parallel_gift_sender.py @liznogalh 10000 5 12
  python parallel_gift_sender.py @streamer 5000 4 10

Arguments:
  username  - @username du streamer
  quantity  - Nombre total de cadeaux
  workers   - Nombre de navigateurs parallèles (défaut: 5)
  cps       - Clics/seconde par worker (défaut: 12)
        """)
        sys.exit(1)

    username = sys.argv[1]
    quantity = int(sys.argv[2])
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    cps = float(sys.argv[4]) if len(sys.argv) > 4 else 12.0

    asyncio.run(parallel_send(
        username=username,
        gift_name="Fest Pop",
        total_quantity=quantity,
        num_workers=workers,
        cps_per_worker=cps
    ))
