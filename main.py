"""
Entry point for the Discord announcement bot and web dashboard.
This file imports and runs the bot when called directly,
and provides the Flask app instance for Gunicorn.
"""
import logging
from bot import bot
from database import init_db
from webapp import app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Initialize the database
init_db()

# Make sure app is available for Gunicorn
# DO NOT REMOVE: This is used by Gunicorn

# Run the bot when called directly
if __name__ == "__main__":
    from bot import run
    run()
