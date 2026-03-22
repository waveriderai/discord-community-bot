#!/usr/bin/env python3
"""
Fetch scan results from WaveFinder API for each strategy, then post:
  - Top 3 + upsell to public channel webhook
  - Full list to Rider+ channel webhook

Usage:
    python scripts/push_strategy_alerts.py [--date 2026-03-22] [--strategy continuation-breakout]
"""

import argparse
import os
import sys
from datetime import date as date_cls

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import requests
from dotenv import load_dotenv

from lib.embeds import format_strategy_alert_full, format_strategy_alert_public

load_dotenv()

WAVEFINDER_BASE = "http://173.230.145.71:8000"

# Strategy slug → (display name, scan endpoint path, public webhook env, rider webhook env)
STRATEGIES = {
    "continuation-breakout": {
        "display": "Continuation Breakout",
        "scan_body": {"strategy": "continuation_breakout"},
        "public_env": "DISCORD_WEBHOOK_CONTINUATION",
        "rider_env": "DISCORD_WEBHOOK_RIDER_CONTINUATION",
    },
    "reversal-bullish": {
        "display": "Reversal Bullish",
        "scan_body": {"strategy": "reversal_bullish"},
        "public_env": "DISCORD_WEBHOOK_REVERSAL",
        "rider_env": "DISCORD_WEBHOOK_RIDER_REVERSAL",
    },
    "9m-catalyst": {
        "display": "9M Catalyst",
        "scan_body": {"strategy": "9m_catalyst"},
        "public_env": "DISCORD_WEBHOOK_9M_CATALYST",
        "rider_env": "DISCORD_WEBHOOK_RIDER_9M_CATALYST",
    },
    "stocks-in-play": {
        "display": "Stocks In Play",
        "scan_body": {"strategy": "stocks_in_play"},
        "public_env": "DISCORD_WEBHOOK_STOCKS_IN_PLAY",
        "rider_env": "DISCORD_WEBHOOK_RIDER_SIP",
    },
    "earnings": {
        "display": "Earnings",
        "scan_body": {"strategy": "earnings"},
        "public_env": "DISCORD_WEBHOOK_EARNINGS",
        "rider_env": "DISCORD_WEBHOOK_RIDER_EARNINGS",
    },
}


def fetch_scan(scan_body: dict) -> list[str]:
    """POST to WaveFinder /scan and return ticker list."""
    resp = requests.post(
        f"{WAVEFINDER_BASE}/api/v1/scan",
        json=scan_body,
        timeout=30,
    )
    resp.raise_for_status()
    result = resp.json()
    # Expect {"tickers": [...]} or a list directly
    if isinstance(result, list):
        return result
    return result.get("tickers", [])


def post_webhook(webhook_url: str, payload: dict) -> None:
    resp = requests.post(webhook_url, json=payload, timeout=10)
    resp.raise_for_status()


def process_strategy(slug: str, cfg: dict, scan_date: str) -> None:
    """Fetch scan, post public + rider embeds for one strategy."""
    print(f"  [{slug}] Fetching scan...")
    try:
        tickers = fetch_scan(cfg["scan_body"])
    except Exception as e:
        print(f"  [{slug}] Scan failed: {e}", file=sys.stderr)
        return

    if not tickers:
        print(f"  [{slug}] No tickers found, skipping.")
        return

    total = len(tickers)
    print(f"  [{slug}] {total} tickers found.")

    # Public channel — top 3
    public_url = os.environ.get(cfg["public_env"])
    if public_url:
        payload = format_strategy_alert_public(
            strategy_name=cfg["display"],
            tickers=tickers,
            total_count=total,
            date=scan_date,
        )
        try:
            post_webhook(public_url, payload)
            print(f"  [{slug}] Public posted.")
        except Exception as e:
            print(f"  [{slug}] Public post failed: {e}", file=sys.stderr)
    else:
        print(f"  [{slug}] {cfg['public_env']} not set, skipping public.")

    # Rider+ channel — full list
    rider_url = os.environ.get(cfg["rider_env"])
    if rider_url:
        payload = format_strategy_alert_full(
            strategy_name=cfg["display"],
            tickers=tickers,
            date=scan_date,
        )
        try:
            post_webhook(rider_url, payload)
            print(f"  [{slug}] Rider+ posted.")
        except Exception as e:
            print(f"  [{slug}] Rider+ post failed: {e}", file=sys.stderr)
    else:
        print(f"  [{slug}] {cfg['rider_env']} not set, skipping Rider+.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Push Strategy Alerts to Discord")
    parser.add_argument(
        "--date",
        default=date_cls.today().isoformat(),
        help="Scan date (default: today)",
    )
    parser.add_argument(
        "--strategy",
        default=None,
        choices=list(STRATEGIES.keys()),
        help="Run only one strategy (default: all)",
    )
    args = parser.parse_args()

    strategies = (
        {args.strategy: STRATEGIES[args.strategy]}
        if args.strategy
        else STRATEGIES
    )

    print(f"Strategy alerts for {args.date}")
    for slug, cfg in strategies.items():
        process_strategy(slug, cfg, args.date)

    print("All done.")


if __name__ == "__main__":
    main()
