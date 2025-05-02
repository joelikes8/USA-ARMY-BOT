from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
import os
import logging
import threading
import time
import sys
from datetime import datetime

# For template context
from datetime import date

# Import the shared bot status module
import bot_status

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database setup
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key")

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)

# Import models to ensure they're registered with SQLAlchemy
from models import Announcement, RobloxVerification

# Context processor for templates
@app.context_processor
def inject_context():
    return {
        'current_year': date.today().year
    }

@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html')

@app.route('/announcements')
def announcements():
    """List all announcements."""
    announcements = db.session.query(Announcement).order_by(Announcement.created_at.desc()).all()
    return render_template('announcements.html', announcements=announcements)

@app.route('/verifications')
def verifications():
    """List all verified users."""
    verifications = db.session.query(RobloxVerification).filter_by(is_verified=True).all()
    return render_template('verifications.html', verifications=verifications)

@app.route('/api/announcements')
def api_announcements():
    """API endpoint for announcements."""
    announcements = db.session.query(Announcement).order_by(Announcement.created_at.desc()).all()
    result = []
    for announcement in announcements:
        result.append({
            'id': announcement.id,
            'author_name': announcement.author_name,
            'channel_name': announcement.channel_name,
            'message': announcement.message,
            'color': announcement.color,
            'media_url': announcement.media_url,
            'created_at': announcement.created_at.isoformat()
        })
    return jsonify(result)

@app.route('/api/verifications')
def api_verifications():
    """API endpoint for verifications."""
    verifications = db.session.query(RobloxVerification).filter_by(is_verified=True).all()
    result = []
    for verification in verifications:
        result.append({
            'id': verification.id,
            'discord_name': verification.discord_name,
            'roblox_username': verification.roblox_username,
            'roblox_id': verification.roblox_id,
            'verified_at': verification.verified_at.isoformat() if verification.verified_at else None
        })
    return jsonify(result)

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring services like UptimeRobot.
    This endpoint is what keeps your service alive.
    
    It returns:
    - HTTP 200: When the bot is connected to Discord
    - HTTP 503: When the bot is not connected
    
    It also provides detailed status information.
    """
    # Get current bot status
    current_status = bot_status.get_status()
    
    # Calculate uptime
    uptime_seconds = time.time() - current_status['uptime_start']
    days, remainder = divmod(uptime_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_str = f"{int(days)}d {int(hours)}h {int(minutes)}m {int(seconds)}s"
    
    # Check if bot is alive
    is_alive = bot_status.is_bot_alive()
    
    # Calculate heartbeat age
    heartbeat_age = None
    if current_status['last_heartbeat']:
        heartbeat_age = time.time() - current_status['last_heartbeat']
    
    # Create status response
    status_data = {
        'service': 'USA Army Bot',
        'bot_connected': current_status['is_connected'],
        'bot_username': current_status['discord_username'],
        'bot_alive': is_alive,
        'uptime': uptime_str,
        'last_heartbeat': f"{int(heartbeat_age)} seconds ago" if heartbeat_age else "Never",
        'reconnect_count': current_status['reconnect_count'],
        'timestamp': datetime.utcnow().isoformat(),
        'web_service': 'online'
    }
    
    # Set status code based on bot connection status
    status_code = 200 if current_status['is_connected'] else 503
    
    # This will log each health check to help with debugging
    logger.info(f"Health check: Bot connected={current_status['is_connected']}, Status code={status_code}")
    
    return jsonify(status_data), status_code

# Self-ping mechanism to keep the app running even when external services are down
def self_ping_task():
    """Background task that pings the app's health endpoint to keep it running."""
    base_url = os.environ.get("APP_URL") or "http://localhost:5000"
    health_url = f"{base_url}/health"
    ping_interval = 120  # Ping every 2 minutes
    
    logger.info(f"Starting self-ping task, will ping {health_url} every {ping_interval} seconds")
    
    while True:
        try:
            # We'll use a simple urllib request to avoid adding more dependencies
            import urllib.request
            response = urllib.request.urlopen(health_url)
            status_code = response.status
            logger.info(f"Self-ping: status_code={status_code}")
            
            # The health check already reads the bot status directly
            # We don't need to update it here
            
        except Exception as e:
            logger.error(f"Self-ping failed: {e}")
        
        # Sleep for the ping interval
        time.sleep(ping_interval)

# Function to start the self-ping task
def start_self_ping():
    ping_thread = threading.Thread(target=self_ping_task, daemon=True)
    ping_thread.start()
    logger.info("Self-ping mechanism started")
    return ping_thread

if __name__ == '__main__':
    # Create all database tables
    with app.app_context():
        db.create_all()
        logger.info("Database tables created.")
    
    # Start the self-ping task
    start_self_ping()
    
    # Run the application
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
