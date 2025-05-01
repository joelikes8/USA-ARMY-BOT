"""
Bot configuration and initialization module.
Sets up the Discord bot with necessary configurations.
"""
import os
import logging
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get bot token from environment variables
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
if not TOKEN:
    raise ValueError("No Discord bot token found. Please set the DISCORD_BOT_TOKEN environment variable.")

logger = logging.getLogger("bot")

# Initialize bot with intents
intents = discord.Intents.default()
intents.message_content = True  # Enable message content intent

# Create bot instance with command prefix and intents
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    """Event triggered when the bot is ready and connected to Discord."""
    logger.info(f"Logged in as {bot.user.name} ({bot.user.id})")
    logger.info(f"Discord.py API version: {discord.__version__}")
    
    # Load cogs
    await bot.load_extension("cogs.announce_commands")
    await bot.load_extension("cogs.verify_commands")
    await bot.load_extension("cogs.ticket_commands")
    
    # Register slash commands globally
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} command(s)")
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}")

@bot.event
async def on_command_error(ctx, error):
    """Global error handler for command errors."""
    if isinstance(error, commands.CommandNotFound):
        return
    
    logger.error(f"Command error: {error}")
    await ctx.reply(f"An error occurred: {error}", ephemeral=True)

def run():
    """Run the bot with the token."""
    if not TOKEN:
        logger.critical("No token provided. Please set the DISCORD_BOT_TOKEN environment variable.")
        return
    
    bot.run(TOKEN)
