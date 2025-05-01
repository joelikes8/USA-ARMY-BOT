from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from database import Base

class Announcement(Base):
    """Model to store announcements sent through the bot."""
    __tablename__ = 'announcements'
    
    id = Column(Integer, primary_key=True)
    author_id = Column(String(20), nullable=False)  # Discord user ID
    author_name = Column(String(100), nullable=False)  # Discord username
    channel_id = Column(String(20), nullable=False)  # Discord channel ID
    channel_name = Column(String(100), nullable=False)  # Channel name
    message = Column(Text, nullable=False)  # Announcement content
    color = Column(String(20), nullable=True)  # Embed color
    media_url = Column(Text, nullable=True)  # Media URL if provided (using Text for longer URLs)
    media_type = Column(String(20), nullable=True)  # Type of media (image, drive, url)
    created_at = Column(DateTime, default=datetime.utcnow)  # Timestamp
    
    def __repr__(self):
        return f"<Announcement id={self.id} author_name={self.author_name}>"


class RobloxVerification(Base):
    """Model to store Roblox verification data."""
    __tablename__ = 'roblox_verifications'
    
    id = Column(Integer, primary_key=True)
    discord_id = Column(String(20), nullable=False, unique=True)  # Discord user ID
    discord_name = Column(String(100), nullable=False)  # Discord username
    roblox_username = Column(String(100), nullable=False)  # Roblox username
    roblox_id = Column(String(20), nullable=True)  # Roblox ID
    verification_code = Column(String(20), nullable=False)  # Verification code
    is_verified = Column(Boolean, default=False)  # Whether verification is complete
    created_at = Column(DateTime, default=datetime.utcnow)  # When verification started
    verified_at = Column(DateTime, nullable=True)  # When verification completed
    
    def __repr__(self):
        status = "Verified" if self.is_verified else "Pending"
        return f"<RobloxVerification discord_name={self.discord_name} roblox_username={self.roblox_username} status={status}>"


class Ticket(Base):
    """Model to store support tickets."""
    __tablename__ = 'tickets'
    
    id = Column(Integer, primary_key=True)
    ticket_number = Column(Integer, nullable=False)  # Incremental ticket number (0-10000)
    creator_id = Column(String(20), nullable=False)  # Discord user ID of creator
    creator_name = Column(String(100), nullable=False)  # Discord username of creator
    channel_id = Column(String(20), nullable=False)  # Discord channel ID for the ticket
    guild_id = Column(String(20), nullable=False)  # Discord guild (server) ID
    status = Column(String(20), default="open")  # Status: open, closed
    created_at = Column(DateTime, default=datetime.utcnow)  # When ticket was created
    closed_at = Column(DateTime, nullable=True)  # When ticket was closed (if applicable)
    closed_by = Column(String(20), nullable=True)  # Discord user ID who closed the ticket (if applicable)
    
    def __repr__(self):
        return f"<Ticket number={self.ticket_number} creator={self.creator_name} status={self.status}>"
