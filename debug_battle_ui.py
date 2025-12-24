#!/usr/bin/env python3
"""
Debug script to analyze TikTok battle UI structure
"""

import asyncio
import sys
from playwright.async_api import async_playwright


async def debug_battle_ui(username: str):
    """Analyze the battle UI elements on a TikTok live page."""

    username = username.lstrip("@")

    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║   DEBUG: TikTok Battle UI Analysis                               ║
╠══════════════════════════════════════════════════════════════════╣
║   Target: @{username:<20}                                        ║
╚══════════════════════════════════════════════════════════════════╝
    """)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(
            storage_state="data/tiktok_session/state.json",
            viewport={"width": 1280, "height": 800}
        )
        page = await context.new_page()

        print(f"Connecting to @{username}...")
        try:
            await page.goto(
                f"https://www.tiktok.com/@{username}/live",
                wait_until="domcontentloaded",
                timeout=30000
            )
        except Exception as e:
            print(f"Navigation warning: {e}")

        await asyncio.sleep(5)
        print("Page loaded. Analyzing battle UI...\n")

        # Analyze the page structure
        analysis = await page.evaluate("""
            () => {
                const results = {
                    // Look for battle-related elements
                    battleKeywords: [],
                    vsElements: [],
                    scorePatterns: [],
                    timerPatterns: [],
                    panelElements: [],
                    allNumbers: [],
                    possibleScores: []
                };

                // Get all text content
                const bodyText = document.body.innerText;

                // Find VS indicators
                const vsMatches = bodyText.match(/.{0,30}(VS|vs|v\\.s\\.|V\\.S\\.).{0,30}/g);
                if (vsMatches) {
                    results.vsElements = vsMatches.slice(0, 5);
                }

                // Find numbers that look like scores (comma-separated or large)
                const scoreMatches = bodyText.match(/\\d{1,3}(?:,\\d{3})*(?:\\s|$|\\n)/g);
                if (scoreMatches) {
                    results.scorePatterns = [...new Set(scoreMatches)].slice(0, 10);
                }

                // Find timer patterns (MM:SS)
                const timerMatches = bodyText.match(/\\d{1,2}:\\d{2}/g);
                if (timerMatches) {
                    results.timerPatterns = [...new Set(timerMatches)];
                }

                // Find elements with battle-related classes
                const allElements = document.querySelectorAll('*');
                allElements.forEach(el => {
                    const className = el.className?.toString?.() || '';
                    const id = el.id || '';

                    if (className.toLowerCase().includes('battle') ||
                        className.toLowerCase().includes('pk') ||
                        className.toLowerCase().includes('versus') ||
                        className.toLowerCase().includes('score') ||
                        id.toLowerCase().includes('battle') ||
                        id.toLowerCase().includes('pk')) {

                        const text = el.innerText?.slice(0, 100) || '';
                        if (text) {
                            results.battleKeywords.push({
                                tag: el.tagName,
                                class: className.slice(0, 80),
                                text: text.replace(/\\n/g, ' ').slice(0, 60)
                            });
                        }
                    }
                });

                // Look for panel/overlay elements
                const panels = document.querySelectorAll('[class*="panel"], [class*="Panel"], [class*="overlay"], [class*="Overlay"]');
                panels.forEach(panel => {
                    const text = panel.innerText?.slice(0, 200) || '';
                    if (text && (text.includes('VS') || text.match(/\\d{1,3},\\d{3}/))) {
                        results.panelElements.push({
                            class: panel.className?.toString?.().slice(0, 80),
                            text: text.replace(/\\n/g, ' ').slice(0, 100)
                        });
                    }
                });

                // Find all visible numbers on page
                const walker = document.createTreeWalker(
                    document.body, NodeFilter.SHOW_TEXT, null, false
                );
                while (walker.nextNode()) {
                    const text = walker.currentNode.textContent.trim();
                    // Look for number patterns
                    if (text.match(/^\\d{1,3}(,\\d{3})*$/)) {
                        const parent = walker.currentNode.parentElement;
                        const rect = parent?.getBoundingClientRect();
                        if (rect && rect.width > 0 && rect.height > 0) {
                            results.allNumbers.push({
                                value: text,
                                tag: parent?.tagName,
                                x: Math.round(rect.x),
                                y: Math.round(rect.y),
                                class: parent?.className?.toString?.().slice(0, 50)
                            });
                        }
                    }
                }

                // Deduplicate
                results.battleKeywords = results.battleKeywords.slice(0, 10);
                results.panelElements = results.panelElements.slice(0, 5);
                results.allNumbers = results.allNumbers.slice(0, 20);

                return results;
            }
        """)

        print("=" * 60)
        print("VS ELEMENTS FOUND:")
        print("=" * 60)
        for vs in analysis.get('vsElements', []):
            print(f"  {vs}")

        print("\n" + "=" * 60)
        print("TIMER PATTERNS:")
        print("=" * 60)
        for timer in analysis.get('timerPatterns', []):
            print(f"  {timer}")

        print("\n" + "=" * 60)
        print("SCORE-LIKE NUMBERS:")
        print("=" * 60)
        for score in analysis.get('scorePatterns', []):
            print(f"  {score.strip()}")

        print("\n" + "=" * 60)
        print("BATTLE-RELATED ELEMENTS:")
        print("=" * 60)
        for elem in analysis.get('battleKeywords', []):
            print(f"  [{elem['tag']}] {elem['class'][:40]}")
            print(f"      Text: {elem['text']}")

        print("\n" + "=" * 60)
        print("PANEL ELEMENTS WITH SCORES:")
        print("=" * 60)
        for panel in analysis.get('panelElements', []):
            print(f"  Class: {panel['class'][:50]}")
            print(f"  Text: {panel['text']}")
            print()

        print("\n" + "=" * 60)
        print("ALL VISIBLE NUMBERS:")
        print("=" * 60)
        for num in analysis.get('allNumbers', []):
            print(f"  {num['value']:>12} at ({num['x']}, {num['y']}) [{num['tag']}] {num.get('class', '')[:30]}")

        # Take a screenshot
        screenshot_path = "debug_battle_screenshot.png"
        await page.screenshot(path=screenshot_path)
        print(f"\nScreenshot saved: {screenshot_path}")

        # Keep browser open for manual inspection
        print("\n>>> Browser open for inspection. Press Enter to close <<<")
        input()

        await context.storage_state(path="data/tiktok_session/state.json")
        await browser.close()


if __name__ == "__main__":
    username = sys.argv[1] if len(sys.argv) > 1 else "liznogalh"
    asyncio.run(debug_battle_ui(username))
