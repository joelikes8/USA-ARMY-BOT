import os
import logging
import sys
import threading
from webapp import app
from database import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Initialize the database
init_db()

# Get the port from Render's environment
port = int(os.environ.get("PORT", 10000))

# Log port binding for Render to detect
print(f"RENDER PORT DETECTION: Web server binding to PORT={port}", file=sys.stderr)
logging.info(f"USA Army Dashboard starting on port {port}")

# Import Discord bot dependencies early to ensure they're loaded
import bot

# Start the Discord bot in a separate thread if RUN_BOT is enabled
def start_bot():
    try:
        print("===> STARTING DISCORD BOT IN BACKGROUND THREAD", file=sys.stderr)
        logging.info("Starting Discord bot in background thread...")
        # Get token from environment
        token = os.environ.get("DISCORD_BOT_TOKEN")
        if not token:
            logging.error("DISCORD_BOT_TOKEN not found in environment variables!")
            print("ERROR: DISCORD_BOT_TOKEN NOT FOUND", file=sys.stderr)
            return
        
        # Log token length for verification (don't log the actual token)
        logging.info(f"Discord token found (length: {len(token)}). Starting bot...")
        print(f"===> DISCORD TOKEN FOUND (LENGTH: {len(token)})", file=sys.stderr)
        
        # Start the bot
        from bot import run
        run()
    except Exception as e:
        logging.error(f"Error starting Discord bot: {str(e)}")
        print(f"ERROR STARTING BOT: {str(e)}", file=sys.stderr)

# Start the bot if RUN_BOT is set
if os.environ.get("RUN_BOT") == "true":
    print("===> RUN_BOT=true DETECTED, STARTING BOT THREAD", file=sys.stderr)
    bot_thread = threading.Thread(target=start_bot)
    bot_thread.daemon = True  # Make thread a daemon so it doesn't block process exit
    bot_thread.start()
    logging.info("Discord bot thread started with ID: " + str(bot_thread.ident))
else:
    print("===> RUN_BOT NOT SET TO 'true', BOT WILL NOT START", file=sys.stderr)

# For running directly (not through gunicorn)
if __name__ == "__main__":
    # Run the app directly
    app.run(host='0.0.0.0', port=port, debug=True)
