"""
Helper functions for creating and formatting Discord embeds.
"""
import re
import discord
from datetime import datetime
from urllib.parse import urlparse

# Color mapping for embed colors
COLOR_MAP = {
    "red": discord.Color.red(),
    "blue": discord.Color.blue(),
    "green": discord.Color.green(),
    "purple": discord.Color.purple(),
    "black": discord.Color.dark_theme()
}

def is_valid_url(url):
    """
    Check if a string is a valid URL.
    
    Args:
        url (str): The URL to validate
        
    Returns:
        bool: True if the URL is valid, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def is_valid_google_drive_link(url):
    """
    Check if a URL is a valid Google Drive link.
    
    Args:
        url (str): The URL to check
        
    Returns:
        bool: True if it's a Google Drive link, False otherwise
    """
    # Check for common Google Drive URL patterns
    drive_patterns = [
        r'drive\.google\.com/file/d/',
        r'drive\.google\.com/open\?id=',
        r'docs\.google\.com/document',
        r'docs\.google\.com/spreadsheets',
        r'docs\.google\.com/presentation'
    ]
    
    if not is_valid_url(url):
        return False
    
    for pattern in drive_patterns:
        if re.search(pattern, url):
            return True
    
    return False

def format_message(message):
    """
    Format a message with Discord markdown.
    
    Args:
        message (str): The message to format
        
    Returns:
        str: The formatted message
    """
    # Discord already supports markdown, so we just need to ensure it's clean
    # Process special markdown features for enhanced rendering
    
    # Convert custom multi-line code blocks with language specification
    message = re.sub(r'```(\w+)\n([\s\S]+?)```', r'```\1\n\2```', message)
    
    # Format headers with # symbols
    message = re.sub(r'^(#{1,3})\s+(.+)$', r'**\2**', message, flags=re.MULTILINE)
    
    # Format bold and italic text
    message = re.sub(r'\*\*(.+?)\*\*', r'**\1**', message)  # Bold
    message = re.sub(r'\*(.+?)\*', r'*\1*', message)  # Italic
    
    # Format lists
    message = re.sub(r'^-\s+(.+)$', r'• \1', message, flags=re.MULTILINE)  # Bullet points
    message = re.sub(r'^(\d+)\.\s+(.+)$', r'\1. \2', message, flags=re.MULTILINE)  # Numbered lists
    
    # Format links (if not already in markdown format)
    message = re.sub(r'(?<!\()https?:\/\/[^\s\)]+(?!\))', r'[link](\g<0>)', message)
    
    return message

def create_announcement_embed(author, message, color="blue", media_url=None, media_type=None):
    """
    Create an announcement embed with the specified parameters.
    
    Args:
        author (discord.User): The user who created the announcement
        message (str): The message content
        color (str): The color for the embed
        media_url (str, optional): URL to an image or Google Drive link
        media_type (str, optional): Type of media ("image", "drive", or "url")
        
    Returns:
        discord.Embed: The created embed
    """
    # Get the color from the color map, default to blue
    embed_color = COLOR_MAP.get(color.lower(), discord.Color.blue())
    
    # Create the base embed
    embed = discord.Embed(
        description=message,
        color=embed_color,
        timestamp=datetime.now()
    )
    
    # Set the author
    embed.set_author(
        name=f"Announcement from {author.display_name}",
        icon_url=author.display_avatar.url
    )
    
    # Add media if provided
    if media_url:
        if media_type == "image":
            # Set image directly in the embed
            embed.set_image(url=media_url)
        elif media_type == "drive":
            # Try to extract image from Google Drive if possible
            if "id=" in media_url or "/d/" in media_url:
                # Extract the file ID
                file_id = None
                if "id=" in media_url:
                    file_id = media_url.split("id=")[1].split("&")[0]
                elif "/d/" in media_url:
                    file_id = media_url.split("/d/")[1].split("/")[0]
                
                if file_id:
                    # Create direct image URL if it's an image
                    # This works for public Google Drive images
                    direct_image_url = f"https://drive.google.com/uc?export=view&id={file_id}"
                    embed.set_image(url=direct_image_url)
                    
                    # Also add a link to the original document
                    embed.add_field(
                        name="Google Drive Link", 
                        value=f"[Click here to view original]({media_url})",
                        inline=False
                    )
                else:
                    # If we couldn't extract ID, fall back to link
                    embed.add_field(
                        name="Shared Document", 
                        value=f"[Click here to view]({media_url})",
                        inline=False
                    )
            else:
                # Handle other Google Drive URLs
                embed.add_field(
                    name="Shared Document", 
                    value=f"[Click here to view]({media_url})",
                    inline=False
                )
        elif media_type == "url":
            # Check if URL might be an image even if it doesn't have standard extension
            if "i.imgur.com" in media_url or "cdn.discordapp.com" in media_url:
                embed.set_image(url=media_url)
            else:
                embed.add_field(
                    name="Attached Link", 
                    value=f"[Click here]({media_url})",
                    inline=False
                )
    
    # Add footer with timestamp
    try:
        # Try using the new Discord format (without discriminator)
        embed.set_footer(text=f"Sent by {author.name}")
    except AttributeError:
        # Fallback to old format with discriminator if needed
        embed.set_footer(text=f"Sent by {author.name}#{author.discriminator}")
    
    return embed
