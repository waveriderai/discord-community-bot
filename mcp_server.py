"""
WaveRider Discord MCP Server
讓 Claude CLI 可以直接操作 Discord
"""

import os
import asyncio
import json
from datetime import datetime
from typing import Any

import discord
from discord.ext import commands
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

# Load environment variables
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Initialize MCP server
mcp = FastMCP("discord-waverider")

# Discord client setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

client = discord.Client(intents=intents)

# Store for the connected client
discord_ready = asyncio.Event()


@client.event
async def on_ready():
    """Called when Discord client is ready."""
    print(f"Discord MCP: Connected as {client.user}")
    discord_ready.set()


# =============================================================================
# MCP Tools
# =============================================================================


@mcp.tool()
async def list_guilds() -> str:
    """列出 Bot 所在的所有 Discord 伺服器"""
    await discord_ready.wait()

    guilds = []
    for guild in client.guilds:
        guilds.append({
            "id": str(guild.id),
            "name": guild.name,
            "member_count": guild.member_count,
            "owner": str(guild.owner) if guild.owner else None,
        })

    return json.dumps(guilds, ensure_ascii=False, indent=2)


@mcp.tool()
async def list_channels(guild_id: str) -> str:
    """列出指定伺服器的所有頻道

    Args:
        guild_id: Discord 伺服器 ID
    """
    await discord_ready.wait()

    guild = client.get_guild(int(guild_id))
    if not guild:
        return json.dumps({"error": f"找不到伺服器 ID: {guild_id}"})

    channels = []
    for channel in guild.channels:
        channel_info = {
            "id": str(channel.id),
            "name": channel.name,
            "type": str(channel.type),
        }

        if isinstance(channel, discord.CategoryChannel):
            channel_info["type"] = "category"
        elif isinstance(channel, discord.TextChannel):
            channel_info["type"] = "text"
            channel_info["topic"] = channel.topic
            channel_info["category"] = channel.category.name if channel.category else None
        elif isinstance(channel, discord.VoiceChannel):
            channel_info["type"] = "voice"
            channel_info["category"] = channel.category.name if channel.category else None
        elif isinstance(channel, discord.ForumChannel):
            channel_info["type"] = "forum"
            channel_info["category"] = channel.category.name if channel.category else None

        channels.append(channel_info)

    # Sort by category and type
    channels.sort(key=lambda x: (x.get("category") or "", x["type"], x["name"]))

    return json.dumps(channels, ensure_ascii=False, indent=2)


@mcp.tool()
async def get_channel_messages(channel_id: str, limit: int = 20) -> str:
    """讀取指定頻道的訊息歷史

    Args:
        channel_id: Discord 頻道 ID
        limit: 要讀取的訊息數量 (預設 20，最大 100)
    """
    await discord_ready.wait()

    channel = client.get_channel(int(channel_id))
    if not channel:
        return json.dumps({"error": f"找不到頻道 ID: {channel_id}"})

    if not isinstance(channel, discord.TextChannel):
        return json.dumps({"error": "此頻道不是文字頻道"})

    limit = min(limit, 100)
    messages = []

    async for message in channel.history(limit=limit):
        messages.append({
            "id": str(message.id),
            "author": str(message.author),
            "content": message.content,
            "timestamp": message.created_at.isoformat(),
            "attachments": [a.url for a in message.attachments],
        })

    return json.dumps(messages, ensure_ascii=False, indent=2)


@mcp.tool()
async def send_message(channel_id: str, content: str) -> str:
    """發送訊息到指定頻道

    Args:
        channel_id: Discord 頻道 ID
        content: 訊息內容
    """
    await discord_ready.wait()

    channel = client.get_channel(int(channel_id))
    if not channel:
        return json.dumps({"error": f"找不到頻道 ID: {channel_id}"})

    if not isinstance(channel, discord.TextChannel):
        return json.dumps({"error": "此頻道不是文字頻道"})

    try:
        message = await channel.send(content)
        return json.dumps({
            "success": True,
            "message_id": str(message.id),
            "channel": channel.name,
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def send_embed(
    channel_id: str,
    title: str,
    description: str,
    color: str = "blue",
    fields: str = "[]"
) -> str:
    """發送 Embed 格式訊息到指定頻道

    Args:
        channel_id: Discord 頻道 ID
        title: Embed 標題
        description: Embed 內容
        color: 顏色 (blue, green, red, gold, purple)
        fields: JSON 格式的欄位列表，例如 [{"name": "欄位名", "value": "內容", "inline": true}]
    """
    await discord_ready.wait()

    channel = client.get_channel(int(channel_id))
    if not channel:
        return json.dumps({"error": f"找不到頻道 ID: {channel_id}"})

    if not isinstance(channel, discord.TextChannel):
        return json.dumps({"error": "此頻道不是文字頻道"})

    # Parse color
    colors = {
        "blue": discord.Color.blue(),
        "green": discord.Color.green(),
        "red": discord.Color.red(),
        "gold": discord.Color.gold(),
        "purple": discord.Color.purple(),
    }
    embed_color = colors.get(color.lower(), discord.Color.blue())

    # Create embed
    embed = discord.Embed(
        title=title,
        description=description,
        color=embed_color,
        timestamp=datetime.now(),
    )

    # Add fields
    try:
        field_list = json.loads(fields)
        for field in field_list:
            embed.add_field(
                name=field.get("name", ""),
                value=field.get("value", ""),
                inline=field.get("inline", False),
            )
    except json.JSONDecodeError:
        pass

    try:
        message = await channel.send(embed=embed)
        return json.dumps({
            "success": True,
            "message_id": str(message.id),
            "channel": channel.name,
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def create_channel(
    guild_id: str,
    name: str,
    channel_type: str = "text",
    category_id: str = None,
    topic: str = None
) -> str:
    """建立新頻道

    Args:
        guild_id: Discord 伺服器 ID
        name: 頻道名稱
        channel_type: 頻道類型 (text, voice, category)
        category_id: 分類 ID（可選）
        topic: 頻道主題（僅文字頻道）
    """
    await discord_ready.wait()

    guild = client.get_guild(int(guild_id))
    if not guild:
        return json.dumps({"error": f"找不到伺服器 ID: {guild_id}"})

    category = None
    if category_id:
        category = guild.get_channel(int(category_id))

    try:
        if channel_type == "category":
            channel = await guild.create_category(name)
        elif channel_type == "voice":
            channel = await guild.create_voice_channel(name, category=category)
        else:
            channel = await guild.create_text_channel(name, category=category, topic=topic)

        return json.dumps({
            "success": True,
            "channel_id": str(channel.id),
            "name": channel.name,
            "type": channel_type,
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def delete_channel(channel_id: str, reason: str = None) -> str:
    """刪除頻道

    Args:
        channel_id: Discord 頻道 ID
        reason: 刪除原因（可選）
    """
    await discord_ready.wait()

    channel = client.get_channel(int(channel_id))
    if not channel:
        return json.dumps({"error": f"找不到頻道 ID: {channel_id}"})

    try:
        name = channel.name
        await channel.delete(reason=reason)
        return json.dumps({
            "success": True,
            "deleted_channel": name,
        }, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool()
async def list_members(guild_id: str, limit: int = 100) -> str:
    """列出伺服器成員

    Args:
        guild_id: Discord 伺服器 ID
        limit: 要列出的成員數量（預設 100）
    """
    await discord_ready.wait()

    guild = client.get_guild(int(guild_id))
    if not guild:
        return json.dumps({"error": f"找不到伺服器 ID: {guild_id}"})

    members = []
    for member in list(guild.members)[:limit]:
        members.append({
            "id": str(member.id),
            "name": member.name,
            "display_name": member.display_name,
            "bot": member.bot,
            "roles": [role.name for role in member.roles if role.name != "@everyone"],
            "joined_at": member.joined_at.isoformat() if member.joined_at else None,
        })

    return json.dumps(members, ensure_ascii=False, indent=2)


@mcp.tool()
async def get_guild_info(guild_id: str) -> str:
    """取得伺服器詳細資訊

    Args:
        guild_id: Discord 伺服器 ID
    """
    await discord_ready.wait()

    guild = client.get_guild(int(guild_id))
    if not guild:
        return json.dumps({"error": f"找不到伺服器 ID: {guild_id}"})

    info = {
        "id": str(guild.id),
        "name": guild.name,
        "description": guild.description,
        "member_count": guild.member_count,
        "owner": str(guild.owner) if guild.owner else None,
        "created_at": guild.created_at.isoformat(),
        "categories": [],
        "channels_summary": {
            "text": 0,
            "voice": 0,
            "category": 0,
            "forum": 0,
        },
        "roles": [{"name": r.name, "color": str(r.color)} for r in guild.roles if r.name != "@everyone"],
    }

    for channel in guild.channels:
        if isinstance(channel, discord.CategoryChannel):
            info["channels_summary"]["category"] += 1
            info["categories"].append({
                "id": str(channel.id),
                "name": channel.name,
                "channels": [{"id": str(c.id), "name": c.name, "type": str(c.type)} for c in channel.channels]
            })
        elif isinstance(channel, discord.TextChannel):
            info["channels_summary"]["text"] += 1
        elif isinstance(channel, discord.VoiceChannel):
            info["channels_summary"]["voice"] += 1
        elif isinstance(channel, discord.ForumChannel):
            info["channels_summary"]["forum"] += 1

    return json.dumps(info, ensure_ascii=False, indent=2)


# =============================================================================
# Main
# =============================================================================


async def start_discord():
    """Start Discord client in background."""
    await client.start(DISCORD_TOKEN)


def main():
    """Main entry point."""
    if not DISCORD_TOKEN:
        print("Error: DISCORD_TOKEN is not set!")
        return

    # Start Discord client in background
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Run Discord client in background task
    loop.create_task(start_discord())

    # Run MCP server
    print("Starting Discord MCP Server...")
    mcp.run()


if __name__ == "__main__":
    main()
