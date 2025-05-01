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

# Start the Discord bot in a background thread if RUN_BOT is enabled
def start_bot():
    try:
        logging.info("Starting Discord bot in background thread...")
        from bot import run
        run()
    except Exception as e:
        logging.error(f"Error starting Discord bot: {e}")

# Start the bot if RUN_BOT is set
if os.environ.get("RUN_BOT") == "true":
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    logging.info("Discord bot thread started")

# For running directly (not through gunicorn)
if __name__ == "__main__":
    # Run the app directly
    app.run(host='0.0.0.0', port=port, debug=True)
