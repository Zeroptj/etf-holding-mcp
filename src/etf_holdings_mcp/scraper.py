"""Scrape top 10 holdings from Morningstar ETF Quote page."""

import time
from typing import Optional

from playwright.sync_api import sync_playwright


DEFAULT_EXCHANGE = "arcx"


def _wait_ready(page, timeout: int = 30_000):
    try:
        page.wait_for_load_state("networkidle", timeout=timeout)
        page.wait_for_load_state("domcontentloaded", timeout=timeout)
        time.sleep(2)
    except Exception:
        pass


def _close_popups(page):
    selectors = [
        'button[aria-label="Close"]',
        'button[aria-label*="close" i]',
        'button.mdc-dialog__close',
        'button:has-text("Accept")',
        'button:has-text("I Accept")',
    ]
    for sel in selectors:
        try:
            if page.locator(sel).count() > 0:
                page.locator(sel).first.click(timeout=2000)
                time.sleep(0.5)
                return
        except Exception:
            continue


def _scrape_top10(page) -> list[dict]:
    rows = page.locator("div.mdc-fund-top-holdings__table__mdc table tbody tr")
    rows.first.wait_for(timeout=15_000)

    results = []
    for i in range(rows.count()):
        row = rows.nth(i)
        try:
            name = row.locator("td:nth-child(1) h3").inner_text().strip()
            weight = row.locator("td:nth-child(2) span").inner_text().strip()
            results.append({"name": name, "weight_pct": float(weight)})
        except Exception:
            continue
    return results


def fetch_holdings(
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
            with sync_playwright() as pw:
                browser = pw.chromium.launch(
                    headless=True,
                    args=["--disable-blink-features=AutomationControlled"],
                )
                context = browser.new_context(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                    viewport={"width": 1920, "height": 1080},
                    locale="en-US",
                )
                page = context.new_page()

                page.goto(url, wait_until="domcontentloaded", timeout=60_000)
                _wait_ready(page)
                _close_popups(page)

                holdings = _scrape_top10(page)
                browser.close()

                if holdings:
                    return holdings

                raise ValueError("empty holdings")

        except Exception as e:
            if attempt < max_retries:
                time.sleep(attempt * 5)
            else:
                print(f"[scraper] {ticker} failed after {max_retries} attempts: {e}")
                return []

    return []
