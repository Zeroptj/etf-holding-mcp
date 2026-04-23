# etf-holdings-mcp

MCP server exposing top 10 holdings of ETFs scraped from Morningstar.

One tool: `get_etf_holdings(ticker, exchange)` → name + weight %.

## Install

```bash
pip install -e .
playwright install chromium
```

## Test manually

```bash
python -c "from etf_holdings_mcp.scraper import fetch_holdings; print(fetch_holdings('SPY'))"
```

Expected output:
```
[{'name': 'Apple Inc', 'weight_pct': 7.12}, {'name': 'Microsoft Corp', 'weight_pct': 6.45}, ...]
```

## Wire into Claude Code

Add to `.mcp.json` in your vault:

```json
{
  "mcpServers": {
    "sec-edgar": {
      "command": "sec-mcp-server"
    },
    "etf-holdings": {
      "command": "etf-holdings-mcp"
    }
  }
}
```

Restart Claude Code. Verify: `/mcp` should show both servers.

## Exchange codes

Morningstar uses these exchange codes in their URL:
- `arcx` — NYSE Arca (most ETFs: SPY, VT, QQQ)
- `xnas` — Nasdaq
- `xnys` — NYSE

Default is `arcx`, which covers ~90% of US-listed ETFs.

## Notes

- Live scrape, no caching. Each call takes 5-10 seconds.
- Playwright runs headless Chromium. Requires ~200MB disk on first `playwright install`.
- Morningstar may rate-limit. If scraping fails, empty list is returned.

## Scope (intentionally minimal)

Only top 10 holdings. No sector/region/financial metrics. If you need those, either:
- Add tools to this MCP
- Query the Morningstar DB directly from your main `ai-stock-analysis` project
