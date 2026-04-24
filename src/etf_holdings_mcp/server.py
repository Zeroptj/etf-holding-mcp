"""MCP server: exposes `get_etf_holdings` tool."""

from mcp.server.fastmcp import FastMCP

from etf_holdings_mcp.scraper import fetch_holdings


mcp = FastMCP("etf-holdings")


@mcp.tool()
async def get_etf_holdings(ticker: str, exchange: str = "arcx") -> dict:
    """
    Return top 10 holdings of an ETF with weight percentages.

    Source: Morningstar ETF Quote page (live scrape, not cached).

    Args:
        ticker: ETF symbol, e.g. "VT", "SPY", "SMH".
        exchange: Morningstar exchange code. Defaults to "arcx" (NYSE Arca).
                  Other common values: "xnas" (Nasdaq), "xnys" (NYSE).

    Returns:
        {
            "ticker": "VT",
            "holdings": [
                {"name": "Apple Inc", "weight_pct": 2.53},
                {"name": "Microsoft Corp", "weight_pct": 2.12},
                ...
            ],
            "count": 10
        }

        If scraping fails, holdings will be an empty list.
    """
    holdings = await fetch_holdings(ticker.upper(), exchange=exchange)
    return {
        "ticker": ticker.upper(),
        "holdings": holdings,
        "count": len(holdings),
    }


def main():
    mcp.run()


if __name__ == "__main__":
    main()
