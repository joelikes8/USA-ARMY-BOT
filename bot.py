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

# Set reconnect parameters
_max_reconnect_attempts = 10  # Maximum number of consecutive reconnection attempts
_reconnect_delay = 5  # Delay in seconds between reconnection attempts
_reconnect_delay_max = 300  # Maximum delay between reconnection attempts (5 minutes)

# Create bot instance with command prefix and intents
bot = commands.Bot(command_prefix="!", intents=intents, reconnect=True, auto_reconnect=True)

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

@bot.event
async def on_disconnect():
    """Event triggered when the bot disconnects from Discord."""
    logger.warning("Bot has disconnected from Discord. Attempting to reconnect...")
    print("ALERT: Bot disconnected from Discord. Auto-reconnect initiated...", flush=True)

@bot.event
async def on_resumed():
    """Event triggered when the bot reconnects after a disconnect."""
    logger.info("Bot has successfully reconnected to Discord")
    print("STATUS: Bot successfully reconnected to Discord", flush=True)
    
@bot.event
async def on_connect():
    """Event triggered when the bot connects to Discord (before ready)."""
    logger.info("Bot connected to Discord gateway")
    print("STATUS: Bot connected to Discord gateway", flush=True)

def run():
    """Run the bot with the token and auto-reconnect on failures."""
    # Check for token in environment again (might have been updated)
    token = os.getenv("DISCORD_BOT_TOKEN") or TOKEN
    if not token:
        logger.critical("No token provided. Please set the DISCORD_BOT_TOKEN environment variable.")
        print("CRITICAL ERROR: No Discord token found in environment", flush=True)
        return
    
    logger.info(f"Starting Discord bot with token length: {len(token)}")
    print(f"STARTING BOT: Token length is {len(token)} with automatic reconnection", flush=True)
    
    # Set up resilient connection with auto-reconnect
    reconnect_attempts = 0
    reconnect_delay = _reconnect_delay
    
    while True:
        try:
            # Start the bot with reconnect=True to enable Discord's built-in reconnection
            bot.run(token, reconnect=True)
            # If run() completes normally, we've exited the bot loop deliberately
            logger.info("Bot has shut down normally")
            # Exit the loop as this was a normal shutdown
            break
        except (discord.ConnectionClosed, discord.GatewayNotFound, 
                discord.HTTPException, discord.LoginFailure) as e:
            # Handle known Discord exceptions
            if isinstance(e, discord.LoginFailure):
                # If the token is invalid, no point retrying
                logger.critical(f"Invalid token provided. Please check your Discord token: {e}")
                print(f"CRITICAL ERROR: Invalid Discord token: {e}", flush=True)
                break
                
            # Increment reconnection attempts
            reconnect_attempts += 1
            
            # If we've exceeded the maximum attempts, stop trying
            if reconnect_attempts > _max_reconnect_attempts:
                logger.critical(f"Failed to reconnect after {_max_reconnect_attempts} attempts. Giving up.")
                print(f"CRITICAL ERROR: Failed to reconnect after {_max_reconnect_attempts} attempts.", flush=True)
                break
                
            # Log the error and wait before reconnecting with exponential backoff
            logger.error(f"Discord connection error (attempt {reconnect_attempts}/{_max_reconnect_attempts}): {e}")
            print(f"CONNECTION ERROR: {e} - Reconnecting in {reconnect_delay} seconds...", flush=True)
            
            # Wait before retrying with exponential backoff
            import time
            time.sleep(reconnect_delay)
            
            # Increase the delay for the next attempt (exponential backoff)
            reconnect_delay = min(reconnect_delay * 2, _reconnect_delay_max)
            
        except Exception as e:
            # Log unexpected errors
            logger.critical(f"Unexpected error: {e}")
            print(f"CRITICAL ERROR: Bot failed with unexpected error: {e}", flush=True)
            import traceback
            traceback.print_exc()
            break
