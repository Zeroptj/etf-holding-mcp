"""Scrape top 10 holdings from Morningstar ETF Quote page."""

import asyncio
import time
from typing import Optional

from playwright.async_api import async_playwright


DEFAULT_EXCHANGE = "arcx"


async def _wait_ready(page, timeout: int = 30_000):
    try:
        await page.wait_for_load_state("networkidle", timeout=timeout)
        await page.wait_for_load_state("domcontentloaded", timeout=timeout)
        await asyncio.sleep(2)
    except Exception:
        pass


async def _close_popups(page):
    selectors = [
        'button[aria-label="Close"]',
        'button[aria-label*="close" i]',
        'button.mdc-dialog__close',
        'button:has-text("Accept")',
        'button:has-text("I Accept")',
    ]
    for sel in selectors:
        try:
            if await page.locator(sel).count() > 0:
                await page.locator(sel).first.click(timeout=2000)
                await asyncio.sleep(0.5)
                return
        except Exception:
            continue


async def _scrape_top10(page) -> list[dict]:
    rows = page.locator("div.mdc-fund-top-holdings__table__mdc table tbody tr")
    await rows.first.wait_for(timeout=15_000)

    results = []
    for i in range(await rows.count()):
        row = rows.nth(i)
        try:
            name = (await row.locator("td:nth-child(1) h3").inner_text()).strip()
            weight = (await row.locator("td:nth-child(2) span").inner_text()).strip()
            results.append({"name": name, "weight_pct": float(weight)})
        except Exception:
            continue
    return results


async def fetch_holdings(
    ticker: str,
    exchange: str = DEFAULT_EXCHANGE,
    max_retries: int = 3,
) -> list[dict]:
    """
    Scrape top 10 holdings for an ETF from Morningstar.

    Args:
        ticker: ETF symbol (e.g. "VT", "SPY")
        exchange: Morningstar exchange code (default "arcx")
        max_retries: retry attempts on failure

    Returns:
        List of {"name": str, "weight_pct": float}, empty if all retries fail.
    """
    url = f"https://www.morningstar.com/etfs/{exchange.lower()}/{ticker.lower()}/quote"

    for attempt in range(1, max_retries + 1):
        try:
            async with async_playwright() as pw:
                browser = await pw.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled"],
                )
                context = await browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    viewport={"width": 1920, "height": 1080},
                    locale="en-US",
                )
                page = await context.new_page()

                await page.goto(url, wait_until="domcontentloaded", timeout=60_000)
                await _wait_ready(page)
                await _close_popups(page)

                holdings = await _scrape_top10(page)
                await browser.close()

                if holdings:
                    return holdings

                raise ValueError("empty holdings")

        except Exception as e:
            if attempt < max_retries:
                await asyncio.sleep(attempt * 5)
            else:
                print(f"[scraper] {ticker} failed after {max_retries} attempts: {e}", flush=True)
                return []

    return []
