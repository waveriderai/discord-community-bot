"""Unit tests for lib.embeds formatters."""

import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib.embeds import (
    REGIME_COLORS,
    UPSELL_URL,
    APP_URL,
    classify_regime,
    format_market_pulse,
    format_strategy_alert_public,
    format_strategy_alert_full,
    format_sell_alert,
    format_content_notification,
)


class TestClassifyRegime(unittest.TestCase):
    def test_bullish(self):
        self.assertEqual(classify_regime(65), "BULLISH")
        self.assertEqual(classify_regime(80), "BULLISH")
        self.assertEqual(classify_regime(100), "BULLISH")

    def test_cautious(self):
        self.assertEqual(classify_regime(40), "CAUTIOUS")
        self.assertEqual(classify_regime(50), "CAUTIOUS")
        self.assertEqual(classify_regime(64.9), "CAUTIOUS")

    def test_cautious_bearish(self):
        self.assertEqual(classify_regime(30), "CAUTIOUS_BEARISH")
        self.assertEqual(classify_regime(35), "CAUTIOUS_BEARISH")
        self.assertEqual(classify_regime(39.9), "CAUTIOUS_BEARISH")

    def test_bearish(self):
        self.assertEqual(classify_regime(20), "BEARISH")
        self.assertEqual(classify_regime(25), "BEARISH")
        self.assertEqual(classify_regime(29.9), "BEARISH")

    def test_correction(self):
        self.assertEqual(classify_regime(19.9), "CORRECTION")
        self.assertEqual(classify_regime(10), "CORRECTION")
        self.assertEqual(classify_regime(0), "CORRECTION")


class TestEmbedStructure(unittest.TestCase):
    """Verify all formatters return valid Discord webhook shape."""

    def _assert_embed_shape(self, result: dict):
        self.assertIn("embeds", result)
        self.assertIsInstance(result["embeds"], list)
        self.assertEqual(len(result["embeds"]), 1)
        embed = result["embeds"][0]
        self.assertIn("title", embed)
        self.assertIn("description", embed)
        self.assertIn("color", embed)
        self.assertIn("footer", embed)
        self.assertIn("timestamp", embed)
        self.assertIsInstance(embed["color"], int)
        self.assertIn("text", embed["footer"])

    def test_market_pulse_structure(self):
        data = {"pct_above_sma40": 55.3}
        result = format_market_pulse(data)
        self._assert_embed_shape(result)

    def test_strategy_alert_public_structure(self):
        result = format_strategy_alert_public(
            "Test Strategy", ["AAPL", "MSFT", "GOOGL", "TSLA"], 4, "2026-03-22"
        )
        self._assert_embed_shape(result)

    def test_strategy_alert_full_structure(self):
        result = format_strategy_alert_full(
            "Test Strategy", ["AAPL", "MSFT"], "2026-03-22"
        )
        self._assert_embed_shape(result)

    def test_sell_alert_structure(self):
        result = format_sell_alert("TSLA", "Stop hit", 245.80, 196.20, -20.2)
        self._assert_embed_shape(result)

    def test_content_notification_structure(self):
        result = format_content_notification(
            "analysis", "Market Outlook", "https://waverider.ai/post/1"
        )
        self._assert_embed_shape(result)


class TestMarketPulse(unittest.TestCase):
    def test_regime_color_matches(self):
        data = {"pct_above_sma40": 70}
        result = format_market_pulse(data)
        self.assertEqual(result["embeds"][0]["color"], REGIME_COLORS["BULLISH"])

    def test_bearish_color(self):
        data = {"pct_above_sma40": 25}
        result = format_market_pulse(data)
        self.assertEqual(result["embeds"][0]["color"], REGIME_COLORS["BEARISH"])

    def test_time_label_in_title(self):
        data = {"pct_above_sma40": 50}
        result = format_market_pulse(data, time_label="2:30 PM ET")
        self.assertIn("2:30 PM ET", result["embeds"][0]["title"])

    def test_no_time_label(self):
        data = {"pct_above_sma40": 50}
        result = format_market_pulse(data)
        self.assertEqual(result["embeds"][0]["title"], "Market Pulse")

    def test_optional_fields_included(self):
        data = {
            "pct_above_sma40": 60,
            "pct_above_sma20": 55,
            "pct_above_sma50": 58,
            "pct_above_sma200": 72,
            "advance_decline_ratio": 1.45,
            "new_highs": 120,
            "new_lows": 30,
        }
        result = format_market_pulse(data)
        desc = result["embeds"][0]["description"]
        self.assertIn("SMA-20", desc)
        self.assertIn("SMA-50", desc)
        self.assertIn("SMA-200", desc)
        self.assertIn("A/D Ratio", desc)
        self.assertIn("120", desc)
        self.assertIn("30", desc)

    def test_app_url_in_description(self):
        data = {"pct_above_sma40": 50}
        result = format_market_pulse(data)
        self.assertIn(APP_URL, result["embeds"][0]["description"])


class TestStrategyAlertPublic(unittest.TestCase):
    def test_preview_count_default(self):
        tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"]
        result = format_strategy_alert_public("Test", tickers, 5, "2026-03-22")
        desc = result["embeds"][0]["description"]
        self.assertIn("AAPL", desc)
        self.assertIn("MSFT", desc)
        self.assertIn("GOOGL", desc)
        self.assertNotIn("TSLA", desc)  # beyond preview_count=3

    def test_upsell_shown_when_remaining(self):
        tickers = ["AAPL", "MSFT", "GOOGL", "TSLA"]
        result = format_strategy_alert_public("Test", tickers, 4, "2026-03-22")
        desc = result["embeds"][0]["description"]
        self.assertIn(UPSELL_URL, desc)
        self.assertIn("+1 more", desc)

    def test_no_upsell_when_all_shown(self):
        tickers = ["AAPL", "MSFT"]
        result = format_strategy_alert_public("Test", tickers, 2, "2026-03-22")
        desc = result["embeds"][0]["description"]
        self.assertNotIn(UPSELL_URL, desc)

    def test_custom_preview_count(self):
        tickers = ["A", "B", "C", "D", "E"]
        result = format_strategy_alert_public("Test", tickers, 5, "2026-03-22", preview_count=2)
        desc = result["embeds"][0]["description"]
        self.assertIn("`A`", desc)
        self.assertIn("`B`", desc)
        self.assertNotIn("`C`", desc)
        self.assertIn("+3 more", desc)

    def test_total_count_in_description(self):
        result = format_strategy_alert_public("Test", ["AAPL"], 1, "2026-03-22")
        desc = result["embeds"][0]["description"]
        self.assertIn("**1** ticker", desc)
        # singular — should not say "tickers"
        self.assertNotIn("**1** tickers", desc)


class TestStrategyAlertFull(unittest.TestCase):
    def test_all_tickers_shown(self):
        tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA", "AMD"]
        result = format_strategy_alert_full("Full Test", tickers, "2026-03-22")
        desc = result["embeds"][0]["description"]
        for t in tickers:
            self.assertIn(t, desc)

    def test_gold_color(self):
        result = format_strategy_alert_full("Test", ["AAPL"], "2026-03-22")
        self.assertEqual(result["embeds"][0]["color"], 0xFFD700)

    def test_app_url(self):
        result = format_strategy_alert_full("Test", ["AAPL"], "2026-03-22")
        self.assertIn(APP_URL, result["embeds"][0]["description"])

    def test_rider_plus_in_footer(self):
        result = format_strategy_alert_full("Test", ["AAPL"], "2026-03-22")
        self.assertIn("Rider+", result["embeds"][0]["footer"]["text"])


class TestSellAlert(unittest.TestCase):
    def test_negative_change_red(self):
        result = format_sell_alert("TSLA", "Stop hit", 245.80, 196.20, -20.2)
        self.assertEqual(result["embeds"][0]["color"], 0xFF0000)

    def test_positive_change_green(self):
        result = format_sell_alert("AAPL", "Target hit", 150.00, 180.00, 20.0)
        self.assertEqual(result["embeds"][0]["color"], 0x00FF00)

    def test_ticker_in_title(self):
        result = format_sell_alert("NVDA", "Breakdown", 300.00, 280.00, -6.7)
        self.assertIn("NVDA", result["embeds"][0]["title"])

    def test_prices_formatted(self):
        result = format_sell_alert("AAPL", "Test", 1234.56, 1100.00, -10.9)
        desc = result["embeds"][0]["description"]
        self.assertIn("$1,234.56", desc)
        self.assertIn("$1,100.00", desc)

    def test_change_pct_in_description(self):
        result = format_sell_alert("TSLA", "Test", 200, 180, -10.0)
        desc = result["embeds"][0]["description"]
        self.assertIn("-10.0%", desc)


class TestContentNotification(unittest.TestCase):
    def test_analysis_type(self):
        result = format_content_notification(
            "analysis", "Weekly Outlook", "https://waverider.ai/post/1"
        )
        embed = result["embeds"][0]
        self.assertIn("Analysis", embed["title"])
        self.assertEqual(embed["color"], 0x3498DB)

    def test_podcast_type(self):
        result = format_content_notification(
            "podcast", "Episode 10", "https://podcast.waverider.ai/ep/10"
        )
        embed = result["embeds"][0]
        self.assertIn("Podcast", embed["title"])
        self.assertEqual(embed["color"], 0x9B59B6)

    def test_url_in_description(self):
        url = "https://example.com/post/42"
        result = format_content_notification("analysis", "Test", url)
        self.assertIn(url, result["embeds"][0]["description"])

    def test_title_in_description(self):
        result = format_content_notification("analysis", "My Great Post", "https://x.com")
        self.assertIn("My Great Post", result["embeds"][0]["description"])


if __name__ == "__main__":
    unittest.main()
