from flask import Flask, render_template, request, flash, redirect, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
import os
import logging
from datetime import datetime

# For template context
from datetime import date

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

if __name__ == '__main__':
    # Create all database tables
    with app.app_context():
        db.create_all()
        logger.info("Database tables created.")
    
    # Run the application
    app.run(host='0.0.0.0', port=5000, debug=True)
