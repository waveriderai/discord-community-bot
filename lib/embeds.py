"""
Discord webhook embed formatters for WaveRider.

All functions return dicts compatible with Discord webhook POST body:
    {"embeds": [{"title": ..., "description": ..., "color": ..., ...}]}
"""

from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Regime colour map
# ---------------------------------------------------------------------------
REGIME_COLORS = {
    "BULLISH": 0x00FF00,
    "CAUTIOUS": 0xFFA500,
    "CAUTIOUS_BEARISH": 0xFF8C00,
    "BEARISH": 0xFF0000,
    "CORRECTION": 0x8B0000,
}

REGIME_EMOJIS = {
    "BULLISH": "\U0001f7e2",        # green circle
    "CAUTIOUS": "\U0001f7e1",       # yellow circle
    "CAUTIOUS_BEARISH": "\U0001f7e0",  # orange circle
    "BEARISH": "\U0001f534",        # red circle
    "CORRECTION": "\u26d4",         # no entry
}

# ---------------------------------------------------------------------------
# URLs
# ---------------------------------------------------------------------------
UPSELL_URL = (
    "https://waverider.ai/pricing"
    "?utm_source=discord&utm_medium=signal&utm_campaign=upsell"
)
APP_URL = "https://app.waverider.ai"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    """Return current UTC time in ISO-8601 format for embed timestamps."""
    return datetime.now(timezone.utc).isoformat()


def _footer(extra: str = "") -> dict:
    text = "WaveRider.ai"
    if extra:
        text = f"{extra} | {text}"
    return {"text": text}


def classify_regime(pct_above_sma40: float) -> str:
    """Classify market regime from pct_above_sma40 (0-100 scale)."""
    if pct_above_sma40 >= 65:
        return "BULLISH"
    elif pct_above_sma40 >= 40:
        return "CAUTIOUS"
    elif pct_above_sma40 >= 30:
        return "CAUTIOUS_BEARISH"
    elif pct_above_sma40 >= 20:
        return "BEARISH"
    else:
        return "CORRECTION"


# ---------------------------------------------------------------------------
# Embed formatters
# ---------------------------------------------------------------------------

def format_market_pulse(data: dict, time_label: str = "") -> dict:
    """
    Format a market breadth / pulse embed.

    Parameters
    ----------
    data : dict
        Must contain at least ``pct_above_sma40``.  Optional keys:
        ``pct_above_sma20``, ``pct_above_sma50``, ``pct_above_sma200``,
        ``advance_decline_ratio``, ``new_highs``, ``new_lows``.
    time_label : str
        e.g. "2:30 PM ET".  Shown in the embed title.
    """
    pct40 = data.get("pct_above_sma40", 0)
    regime = classify_regime(pct40)
    emoji = REGIME_EMOJIS.get(regime, "")
    color = REGIME_COLORS.get(regime, 0x808080)

    title = "Market Pulse"
    if time_label:
        title += f" — {time_label}"

    lines = [
        f"**Regime**: {emoji} {regime.replace('_', ' ').title()}",
        "",
        "**Breadth Indicators**",
        f"> SMA-40: **{pct40:.1f}%**",
    ]
    if "pct_above_sma20" in data:
        lines.append(f"> SMA-20: **{data['pct_above_sma20']:.1f}%**")
    if "pct_above_sma50" in data:
        lines.append(f"> SMA-50: **{data['pct_above_sma50']:.1f}%**")
    if "pct_above_sma200" in data:
        lines.append(f"> SMA-200: **{data['pct_above_sma200']:.1f}%**")
    if "advance_decline_ratio" in data:
        lines.append(f"> A/D Ratio: **{data['advance_decline_ratio']:.2f}**")
    if "new_highs" in data or "new_lows" in data:
        nh = data.get("new_highs", "—")
        nl = data.get("new_lows", "—")
        lines.append(f"> New Highs / Lows: **{nh}** / **{nl}**")

    lines.append("")
    lines.append(f"[Open WaveFinder]({APP_URL})")

    return {
        "embeds": [
            {
                "title": title,
                "description": "\n".join(lines),
                "color": color,
                "footer": _footer("Market Breadth"),
                "timestamp": _now_iso(),
            }
        ]
    }


def format_strategy_alert_public(
    strategy_name: str,
    tickers: list[str],
    total_count: int,
    date: str,
    preview_count: int = 3,
) -> dict:
    """
    Public channel alert — shows top N tickers + upsell CTA.

    Parameters
    ----------
    strategy_name : str
        Human-readable strategy name, e.g. "Continuation Breakout".
    tickers : list[str]
        Full list of tickers (only first ``preview_count`` shown).
    total_count : int
        Total number of tickers that matched.
    date : str
        Scan date, e.g. "2026-03-22".
    preview_count : int
        How many tickers to show (default 3).
    """
    preview = tickers[:preview_count]
    remaining = total_count - len(preview)

    lines = [
        f"**{strategy_name}** — {date}",
        f"Found **{total_count}** ticker{'s' if total_count != 1 else ''}",
        "",
        "**Top picks:**",
    ]
    for t in preview:
        lines.append(f"> \U0001f4c8 `{t}`")

    if remaining > 0:
        lines.append("")
        lines.append(
            f"\U0001f512 **+{remaining} more** — "
            f"[Upgrade to Rider+]({UPSELL_URL}) for the full list"
        )

    return {
        "embeds": [
            {
                "title": f"\U0001f4e1 {strategy_name} Alert",
                "description": "\n".join(lines),
                "color": 0x5865F2,  # Discord blurple
                "footer": _footer(date),
                "timestamp": _now_iso(),
            }
        ]
    }


def format_strategy_alert_full(
    strategy_name: str,
    tickers: list[str],
    date: str,
) -> dict:
    """
    Rider+ full alert — shows complete ticker list.
    """
    # Split into rows of 5 for readability
    rows: list[str] = []
    for i in range(0, len(tickers), 5):
        chunk = tickers[i : i + 5]
        rows.append("  ".join(f"`{t}`" for t in chunk))

    lines = [
        f"**{strategy_name}** — {date}",
        f"**{len(tickers)}** ticker{'s' if len(tickers) != 1 else ''} found",
        "",
    ]
    lines.extend(rows)
    lines.append("")
    lines.append(f"[View in WaveFinder]({APP_URL})")

    return {
        "embeds": [
            {
                "title": f"\U0001f451 {strategy_name} — Full List",
                "description": "\n".join(lines),
                "color": 0xFFD700,  # gold
                "footer": _footer(f"Rider+ | {date}"),
                "timestamp": _now_iso(),
            }
        ]
    }


def format_sell_alert(
    ticker: str,
    reason: str,
    price_from: float,
    price_to: float,
    change_pct: float,
) -> dict:
    """
    Sell / exit alert embed.
    """
    emoji = "\U0001f53b" if change_pct < 0 else "\U0001f53a"
    color = 0xFF0000 if change_pct < 0 else 0x00FF00

    lines = [
        f"**{ticker}** {emoji} {change_pct:+.1f}%",
        "",
        f"> **Reason**: {reason}",
        f"> **From**: ${price_from:,.2f}",
        f"> **To**: ${price_to:,.2f}",
    ]

    return {
        "embeds": [
            {
                "title": f"\u26a0\ufe0f Sell Alert — {ticker}",
                "description": "\n".join(lines),
                "color": color,
                "footer": _footer("Exit Signal"),
                "timestamp": _now_iso(),
            }
        ]
    }


def format_content_notification(
    content_type: str,
    title: str,
    url: str,
) -> dict:
    """
    New analysis / podcast notification embed.

    Parameters
    ----------
    content_type : str
        "analysis" or "podcast".
    title : str
        Content title.
    url : str
        Link to the content.
    """
    if content_type.lower() == "podcast":
        emoji = "\U0001f3a7"
        color = 0x9B59B6  # purple
        label = "New Podcast Episode"
    else:
        emoji = "\U0001f4dd"
        color = 0x3498DB  # blue
        label = "New Analysis"

    lines = [
        f"**{title}**",
        "",
        f"[Read / Listen \u2192]({url})",
    ]

    return {
        "embeds": [
            {
                "title": f"{emoji} {label}",
                "description": "\n".join(lines),
                "color": color,
                "footer": _footer(content_type.title()),
                "timestamp": _now_iso(),
            }
        ]
    }
