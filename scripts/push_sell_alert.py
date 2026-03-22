#!/usr/bin/env python3
"""
Post a sell / exit alert to Discord.

Usage:
    python scripts/push_sell_alert.py \
        --ticker TSLA \
        --reason "20% Week Decline" \
        --price-from 245.80 \
        --price-to 196.20 \
        --change-pct -20.2
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import requests
from dotenv import load_dotenv

from lib.embeds import format_sell_alert

load_dotenv()


def post_webhook(webhook_url: str, payload: dict) -> None:
    resp = requests.post(webhook_url, json=payload, timeout=10)
    resp.raise_for_status()


def main() -> None:
    parser = argparse.ArgumentParser(description="Push Sell Alert to Discord")
    parser.add_argument("--ticker", required=True, help="Ticker symbol")
    parser.add_argument("--reason", required=True, help="Sell reason")
    parser.add_argument("--price-from", type=float, required=True, help="Entry / prior price")
    parser.add_argument("--price-to", type=float, required=True, help="Current / exit price")
    parser.add_argument("--change-pct", type=float, required=True, help="Percent change (e.g. -20.2)")
    args = parser.parse_args()

    webhook_url = os.environ.get("DISCORD_WEBHOOK_SELL_ALERTS")
    if not webhook_url:
        print("ERROR: DISCORD_WEBHOOK_SELL_ALERTS not set", file=sys.stderr)
        sys.exit(1)

    payload = format_sell_alert(
        ticker=args.ticker,
        reason=args.reason,
        price_from=args.price_from,
        price_to=args.price_to,
        change_pct=args.change_pct,
    )
    print(f"Posting sell alert for {args.ticker}...")
    post_webhook(webhook_url, payload)
    print("Done.")


if __name__ == "__main__":
    main()
