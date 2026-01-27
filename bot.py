"""
WaveRider Discord Community Bot - Phase 1 MVP
智慧問答系統，整合 Claude AI
"""

import os
import asyncio
import logging
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv
import anthropic

# Load environment variables
load_dotenv()

# Configuration
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
BOT_PREFIX = os.getenv("BOT_PREFIX", "!")
CHANNEL_BOT_QA = os.getenv("CHANNEL_BOT_QA")

# Logging setup
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("waverider-bot")

# Bot setup with intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)

# Claude client
claude_client = None
if ANTHROPIC_API_KEY:
    claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


# System prompt for Claude
SYSTEM_PROMPT = """你是 WaveRider 社群的 AI 助理，專門協助用戶解答關於動能股波段交易的問題。

你的專長包括：
- 動能交易策略（StockBee、CANSLIM、SEPA、VCP 等）
- 技術分析基礎
- WaveRider 平台功能說明
- 交易心理與風險管理

回答規則：
1. 使用繁體中文，語氣友善專業
2. 回答簡潔，重點清晰
3. 涉及具體買賣建議時，務必加上免責聲明
4. 如果不確定，誠實說明並建議用戶查閱官方資源

免責聲明模板：
「⚠️ 以上僅供參考，不構成投資建議。投資有風險，請自行評估。」
"""


def ask_claude(question: str, context: str = "") -> str:
    """Send a question to Claude and get a response."""
    if not claude_client:
        return "Claude API 尚未設定，請聯繫管理員。"

    try:
        message = claude_client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[
                {
                    "role": "user",
                    "content": f"{context}\n\n問題：{question}" if context else question,
                }
            ],
        )
        return message.content[0].text
    except anthropic.APIError as e:
        logger.error(f"Claude API error: {e}")
        return "抱歉，AI 服務暫時無法使用，請稍後再試。"
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return "發生錯誤，請稍後再試。"


# =============================================================================
# Events
# =============================================================================


@bot.event
async def on_ready():
    """Called when the bot is ready."""
    logger.info(f"Bot is ready! Logged in as {bot.user}")
    logger.info(f"Connected to {len(bot.guilds)} guild(s)")

    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} slash command(s)")
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}")

    # Set bot status
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching, name="動能股市場 | /help"
        )
    )


@bot.event
async def on_member_join(member: discord.Member):
    """Welcome new members."""
    logger.info(f"New member joined: {member.name}")

    # Find a welcome channel or use system channel
    welcome_channel = member.guild.system_channel

    if welcome_channel:
        embed = discord.Embed(
            title=f"歡迎 {member.display_name} 加入 WaveRider 社群！",
            description=(
                "很高興你加入我們的交易討論社群！\n\n"
                "**快速開始：**\n"
                "• 📖 閱讀社群規則\n"
                "• 👋 到自我介紹區打個招呼\n"
                "• 🤖 有問題可以用 `/ask` 問我\n\n"
                "祝交易順利！📈"
            ),
            color=discord.Color.green(),
            timestamp=datetime.now(),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await welcome_channel.send(embed=embed)


# =============================================================================
# Slash Commands
# =============================================================================


@bot.tree.command(name="ping", description="檢查機器人是否在線")
async def ping(interaction: discord.Interaction):
    """Check bot latency."""
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"🏓 Pong! 延遲: {latency}ms")


@bot.tree.command(name="help", description="顯示可用指令列表")
async def help_command(interaction: discord.Interaction):
    """Show available commands."""
    embed = discord.Embed(
        title="WaveRider Bot 指令列表",
        description="以下是可用的指令：",
        color=discord.Color.blue(),
    )

    embed.add_field(
        name="🤖 AI 問答",
        value="`/ask <問題>` - 詢問交易相關問題",
        inline=False,
    )
    embed.add_field(
        name="📊 資訊",
        value=(
            "`/ping` - 檢查機器人狀態\n"
            "`/help` - 顯示此說明\n"
            "`/about` - 關於本機器人"
        ),
        inline=False,
    )
    embed.add_field(
        name="📈 交易（開發中）",
        value=(
            "`/signals` - 查看最新訊號\n"
            "`/watchlist` - 查看觀察清單"
        ),
        inline=False,
    )

    embed.set_footer(text="WaveRider Discord Bot v1.0")
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="about", description="關於 WaveRider Bot")
async def about(interaction: discord.Interaction):
    """Show bot information."""
    embed = discord.Embed(
        title="關於 WaveRider Bot",
        description=(
            "WaveRider Discord Bot 是一個智慧化的社群管理機器人，"
            "整合 Claude AI 提供交易策略問答服務。"
        ),
        color=discord.Color.gold(),
    )

    embed.add_field(name="版本", value="1.0.0 (Phase 1 MVP)", inline=True)
    embed.add_field(name="AI 引擎", value="Claude by Anthropic", inline=True)
    embed.add_field(
        name="功能",
        value=(
            "• 智慧問答系統\n"
            "• 新成員歡迎\n"
            "• 交易訊號推播（開發中）"
        ),
        inline=False,
    )

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="ask", description="詢問交易相關問題")
@app_commands.describe(question="你想問的問題")
async def ask(interaction: discord.Interaction, question: str):
    """Ask Claude a trading-related question."""
    # Defer response since Claude might take a moment
    await interaction.response.defer(thinking=True)

    logger.info(f"Question from {interaction.user.name}: {question}")

    # Get response from Claude
    response = await asyncio.to_thread(ask_claude, question)

    # Create embed for response
    embed = discord.Embed(
        title="💡 AI 回答",
        description=response,
        color=discord.Color.purple(),
        timestamp=datetime.now(),
    )
    embed.set_footer(text=f"Asked by {interaction.user.display_name}")

    await interaction.followup.send(embed=embed)


# =============================================================================
# Prefix Commands (Legacy support)
# =============================================================================


@bot.command(name="ask")
async def ask_prefix(ctx: commands.Context, *, question: str):
    """Ask Claude a question (prefix command version)."""
    async with ctx.typing():
        response = await asyncio.to_thread(ask_claude, question)

    embed = discord.Embed(
        title="💡 AI 回答",
        description=response,
        color=discord.Color.purple(),
        timestamp=datetime.now(),
    )
    embed.set_footer(text=f"Asked by {ctx.author.display_name}")

    await ctx.reply(embed=embed)


# =============================================================================
# Main
# =============================================================================


def main():
    """Main entry point."""
    if not DISCORD_TOKEN:
        logger.error("DISCORD_TOKEN is not set!")
        return

    logger.info("Starting WaveRider Discord Bot...")
    bot.run(DISCORD_TOKEN)


if __name__ == "__main__":
    main()
