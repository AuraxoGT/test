import discord
import aiohttp
import asyncio
import json
import os
from discord.ext import commands, tasks
from dotenv import load_dotenv
import sys
# Load environment variables from .env file
load_dotenv()

TOKEN = "MTMzMjM3MTIxMTU2MDQyMzU1Nw.GSABFD.jPeIP0w_9xXEWJ3_LsnrtnL3nuRB_T7nqqspgo"
API_URL = "https://apii-8avg.onrender.com/free-games"
CHANNEL_ID = 1335923156132696186
SENT_GAMES_FILE = "sent_games.json"

# Bot setup
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

async def fetch_free_games():
    """Fetch free games from the FastAPI server."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(API_URL) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("epic", [])
                else:
                    print(f"⚠️ Failed to fetch data. Status code: {response.status}")
                    return []
    except Exception as e:
        print(f"⚠️ Error fetching free games: {e}")
        return []

def load_sent_games():
    """Load previously sent game IDs from a JSON file."""
    try:
        with open(SENT_GAMES_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_sent_games(sent_games):
    """Save sent game IDs to a JSON file."""
    with open(SENT_GAMES_FILE, "w") as f:
        json.dump(sent_games, f)

async def send_new_games(channel, games):
    """Send only new free games to the specified Discord channel."""
    sent_games = load_sent_games()
    new_games = [game for game in games if game.get("title") not in sent_games]

    if not new_games:
        return

    for game in new_games:
        embed = discord.Embed(
            title=game.get("title", "Unknown"),
            url=game.get("url", ""),
            description="🎉 **Nemokamas žaidimas!**\n" + game.get("title", "Unknown"),
            color=0x00FF00
        )
        embed.set_image(url=game.get("cover", ""))
        embed.add_field(
            name="Pasiūlymas Baigiasi",
            value=f"<t:{game.get('offer_end_date_timestamp')}:F>",
            inline=False
        )
        embed.set_footer(text="Nemokami Žaidimai (Epic Games)")

        await channel.send(embed=embed)

        # Add to sent games list
        sent_games.append(game.get("title"))

    # Save updated sent games list
    save_sent_games(sent_games)

@tasks.loop(minutes=60)  # Check for new games every hour
async def check_for_new_games():
    """Automatically fetch games and send only new ones."""
    await bot.wait_until_ready()
    channel = bot.get_channel(CHANNEL_ID)
    
    if not channel:
        print("⚠️ Invalid channel ID! Please check your .env file.")
        return

    games = await fetch_free_games()
    await send_new_games(channel, games)

@bot.event
async def on_ready():
    """Runs when the bot starts up."""
    print(f"✅ Logged in as {bot.user}")
    check_for_new_games.start()  # Start the automatic loop

@bot.command(name="freegames")
async def freegames(ctx):
    """Manually fetch and send the latest free games."""
    await ctx.send("🔍 Tikrinama, ar yra naujų nemokamų žaidimų...")
    games = await fetch_free_games()
    await send_new_games(ctx.channel, games)

# Run the bot
if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Error: DISCORD_BOT_TOKEN is missing! Check your .env file.")
