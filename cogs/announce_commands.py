"""
Cog containing the announcement commands for the Discord bot.
Implements the /announce slash command with various parameters.
"""
import logging
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional, Literal
from utils.embed_helpers import create_announcement_embed, is_valid_url, is_valid_google_drive_link, format_message
from database import get_session
from models import Announcement

logger = logging.getLogger("announce_commands")

class AnnouncementCommands(commands.Cog):
    """Cog for announcement-related commands."""
    
    def __init__(self, bot):
        self.bot = bot
        
    @app_commands.command(
        name="announcements",
        description="List recent announcements made by the bot"
    )
    @app_commands.describe(
        limit="Number of recent announcements to show (default: 5)"
    )
    async def list_announcements(self, interaction: discord.Interaction, limit: int = 5):
        """List recent announcements made by the bot."""
        await interaction.response.defer(ephemeral=True)
        
        try:
            session = get_session()
            # Get recent announcements, ordered by creation date (newest first)
            from sqlalchemy import desc
            announcements = session.query(Announcement).order_by(desc(Announcement.created_at)).limit(limit).all()
            session.close()
            
            if not announcements:
                await interaction.followup.send("No announcements have been made yet.", ephemeral=True)
                return
            
            # Create an embed to display the announcements
            embed = discord.Embed(
                title="Recent Announcements",
                description=f"Showing the {len(announcements)} most recent announcements",
                color=discord.Color.blue()
            )
            
            for i, announcement in enumerate(announcements):
                # Create a short preview of the message
                preview = announcement.message[:100] + "..." if len(announcement.message) > 100 else announcement.message
                
                # Add a field for each announcement
                embed.add_field(
                    name=f"{i+1}. By {announcement.author_name} in #{announcement.channel_name}",
                    value=f"**Message:** {preview}\n**Color:** {announcement.color or 'blue'}\n**Date:** <t:{int(announcement.created_at.timestamp())}:R>",
                    inline=False
                )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error listing announcements: {e}")
            await interaction.followup.send(f"An error occurred while retrieving announcements: {e}", ephemeral=True)
    
    @app_commands.command(
        name="announce",
        description="Create and send an announcement to a specified channel"
    )
    @app_commands.describe(
        channel="The channel to send the announcement to",
        message="The message content of the announcement",
        media="URL to an image or Google Drive link (optional)",
        color="The color of the announcement embed (default: blue)"
    )
    @app_commands.checks.has_permissions(administrator=True, manage_messages=True)
    async def announce(
        self, 
        interaction: discord.Interaction, 
        channel: discord.TextChannel, 
        message: str,
        media: Optional[str] = None,
        color: Literal["red", "blue", "green", "purple", "black"] = "blue"
    ):
        """
        Create and send an announcement to a specified channel.
        
        Parameters:
            interaction: The interaction object
            channel: The channel to send the announcement to
            message: The message content of the announcement
            media: URL to an image or Google Drive link (optional)
            color: The color of the announcement embed
        """
        # Defer the response to give us time to process
        await interaction.response.defer(ephemeral=True)
        
        # Check permissions
        if not channel.permissions_for(interaction.guild.me).send_messages:
            await interaction.followup.send(f"I don't have permission to send messages in {channel.mention}.", ephemeral=True)
            return
        
        # Check if the user has permission to send to the channel
        if not channel.permissions_for(interaction.user).send_messages:
            await interaction.followup.send(f"You don't have permission to send announcements to {channel.mention}.", ephemeral=True)
            return
        
        # Validate media URL if provided
        media_type = None
        if media:
            if is_valid_url(media):
                # Check for standard image extensions
                if media.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                    media_type = "image"
                # Check for Google Drive links
                elif is_valid_google_drive_link(media):
                    media_type = "drive"
                # Check for common image hosting services without extensions
                elif any(host in media.lower() for host in ['i.imgur.com', 'cdn.discordapp.com', 'media.discordapp.net']):
                    media_type = "image"
                else:
                    media_type = "url"
            else:
                await interaction.followup.send("Invalid media URL provided. Please provide a valid image URL or Google Drive link.", ephemeral=True)
                return
        
        try:
            # Format the message with markdown support
            formatted_message = format_message(message)
            
            # Create the embed
            embed = create_announcement_embed(
                author=interaction.user,
                message=formatted_message,
                media_url=media,
                media_type=media_type,
                color=color
            )
            
            # Send the announcement to the specified channel
            sent_message = await channel.send(embed=embed)
            
            # Save the announcement to the database
            try:
                session = get_session()
                announcement = Announcement(
                    author_id=str(interaction.user.id),
                    author_name=interaction.user.name,
                    channel_id=str(channel.id),
                    channel_name=channel.name,
                    message=message,  # Original message (not formatted)
                    color=color,
                    media_url=media,
                    media_type=media_type
                )
                session.add(announcement)
                session.commit()
                logger.info(f"Saved announcement to database with ID {announcement.id}")
                session.close()
            except Exception as db_error:
                logger.error(f"Error saving to database: {db_error}")
                # Continue even if database save fails
            
            # Send confirmation to the user
            await interaction.followup.send(
                f"Announcement sent to {channel.mention} successfully! [Jump to message]({sent_message.jump_url})",
                ephemeral=True
            )
            
            logger.info(f"User {interaction.user.name} ({interaction.user.id}) sent an announcement to channel {channel.name} ({channel.id})")

            
        except Exception as e:
            logger.error(f"Error sending announcement: {e}")
            await interaction.followup.send(f"An error occurred while sending the announcement: {e}", ephemeral=True)

    @announce.error
    async def announce_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Handle errors for the announce command."""
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(
                "You need Administrator or Manage Messages permission to use this command.",
                ephemeral=True
            )
        else:
            logger.error(f"Unhandled error in announce command: {error}")
            await interaction.response.send_message(
                f"An error occurred: {error}",
                ephemeral=True
            )

async def setup(bot):
    """Add the cog to the bot."""
    await bot.add_cog(AnnouncementCommands(bot))
