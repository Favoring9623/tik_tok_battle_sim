#!/usr/bin/env python3
"""
Debug script to find exact battle bar elements in TikTok
"""

import asyncio
import sys
from playwright.async_api import async_playwright


async def debug_battle_bar(username: str):
    """Find the exact battle bar elements."""

    username = username.lstrip("@")

    print(f"Connecting to @{username}...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            storage_state="data/tiktok_session/state.json",
            viewport={"width": 1280, "height": 800}
        )
        page = await context.new_page()

        try:
            await page.goto(
                f"https://www.tiktok.com/@{username}/live",
                wait_until="domcontentloaded",
                timeout=30000
            )
        except Exception as e:
            print(f"Navigation warning: {e}")

        await asyncio.sleep(6)

        print("\n" + "=" * 70)
        print("ANALYZING BATTLE BAR STRUCTURE")
        print("=" * 70)

        # Detailed analysis of the top portion of the page
        analysis = await page.evaluate("""
            () => {
                const results = {
                    topElements: [],
                    scoreElements: [],
                    timerElements: [],
                    battleBar: null
                };

                // Get all elements in the top 150px of the page
                const allElements = document.querySelectorAll('*');

                for (const el of allElements) {
                    const rect = el.getBoundingClientRect();

                    // Focus on elements in the top area (battle bar region)
                    if (rect.y >= 50 && rect.y <= 150 && rect.height > 10 && rect.height < 100) {
                        const text = el.innerText?.trim() || '';
                        const computedStyle = window.getComputedStyle(el);
                        const bgColor = computedStyle.backgroundColor;
                        const color = computedStyle.color;

                        // Check for score-like content (large numbers)
                        if (text.match(/^\\d{4,6}$/)) {
                            results.scoreElements.push({
                                tag: el.tagName,
                                text: text,
                                x: Math.round(rect.x),
                                y: Math.round(rect.y),
                                width: Math.round(rect.width),
                                height: Math.round(rect.height),
                                class: el.className?.toString?.().slice(0, 80) || '',
                                bgColor: bgColor,
                                color: color,
                                parent: el.parentElement?.className?.toString?.().slice(0, 50) || ''
                            });
                        }

                        // Check for timer (MM:SS)
                        if (text.match(/^\\d{1,2}:\\d{2}$/)) {
                            results.timerElements.push({
                                tag: el.tagName,
                                text: text,
                                x: Math.round(rect.x),
                                y: Math.round(rect.y),
                                class: el.className?.toString?.().slice(0, 80) || '',
                                parent: el.parentElement?.className?.toString?.().slice(0, 50) || ''
                            });
                        }
                    }

                    // Look for battle bar container (wide element at top with scores)
                    if (rect.y >= 50 && rect.y <= 120 && rect.width > 300 && rect.height > 20 && rect.height < 60) {
                        const text = el.innerText?.trim() || '';
                        if (text.match(/\\d{4,6}/) && text.length < 50) {
                            results.topElements.push({
                                tag: el.tagName,
                                text: text.replace(/\\n/g, ' | '),
                                x: Math.round(rect.x),
                                y: Math.round(rect.y),
                                width: Math.round(rect.width),
                                height: Math.round(rect.height),
                                class: el.className?.toString?.().slice(0, 100) || ''
                            });
                        }
                    }
                }

                // Try to find the exact battle bar by looking for a container with two scores
                const walker = document.createTreeWalker(
                    document.body, NodeFilter.SHOW_TEXT, null, false
                );

                const scorePositions = [];
                while (walker.nextNode()) {
                    const text = walker.currentNode.textContent.trim();
                    if (text.match(/^\\d{4,6}$/)) {
                        const el = walker.currentNode.parentElement;
                        const rect = el?.getBoundingClientRect();
                        if (rect && rect.y > 50 && rect.y < 150) {
                            scorePositions.push({
                                value: parseInt(text),
                                x: rect.x,
                                y: rect.y,
                                element: {
                                    tag: el.tagName,
                                    class: el.className?.toString?.() || '',
                                    id: el.id || '',
                                    dataTestId: el.getAttribute('data-testid') || ''
                                }
                            });
                        }
                    }
                }

                // Sort by x position to get left and right scores
                scorePositions.sort((a, b) => a.x - b.x);
                results.battleBar = {
                    leftScore: scorePositions[0] || null,
                    rightScore: scorePositions[1] || null
                };

                return results;
            }
        """)

        print("\n--- SCORE ELEMENTS IN BATTLE BAR AREA ---")
        for elem in analysis.get('scoreElements', []):
            print(f"\n  Score: {elem['text']}")
            print(f"    Position: ({elem['x']}, {elem['y']}) size: {elem['width']}x{elem['height']}")
            print(f"    Tag: {elem['tag']}")
            print(f"    Class: {elem['class']}")
            print(f"    Parent: {elem['parent']}")
            print(f"    Color: {elem['color']}")

        print("\n--- TIMER ELEMENTS ---")
        for elem in analysis.get('timerElements', []):
            print(f"\n  Timer: {elem['text']}")
            print(f"    Position: ({elem['x']}, {elem['y']})")
            print(f"    Class: {elem['class']}")
            print(f"    Parent: {elem['parent']}")

        print("\n--- BATTLE BAR DETECTION ---")
        bb = analysis.get('battleBar', {})
        if bb.get('leftScore'):
            left = bb['leftScore']
            print(f"\n  LEFT SCORE: {left['value']}")
            print(f"    Position: ({left['x']}, {left['y']})")
            print(f"    Element: {left['element']}")

        if bb.get('rightScore'):
            right = bb['rightScore']
            print(f"\n  RIGHT SCORE: {right['value']}")
            print(f"    Position: ({right['x']}, {right['y']})")
            print(f"    Element: {right['element']}")

        print("\n--- TOP CONTAINER ELEMENTS ---")
        for elem in analysis.get('topElements', []):
            print(f"\n  Text: {elem['text'][:60]}")
            print(f"    Position: ({elem['x']}, {elem['y']}) size: {elem['width']}x{elem['height']}")
            print(f"    Class: {elem['class'][:60]}")

        # Take focused screenshot of battle bar area
        await page.screenshot(path="debug_battle_bar.png", clip={
            "x": 150, "y": 50, "width": 600, "height": 100
        })
        print("\n\nBattle bar screenshot saved: debug_battle_bar.png")

        # Full screenshot
        await page.screenshot(path="debug_full_page.png")
        print("Full page screenshot saved: debug_full_page.png")

        print("\n>>> Press Enter to close <<<")
        input()

        await context.storage_state(path="data/tiktok_session/state.json")
        await browser.close()


if __name__ == "__main__":
    username = sys.argv[1] if len(sys.argv) > 1 else "liznogalh"
    asyncio.run(debug_battle_bar(username))
