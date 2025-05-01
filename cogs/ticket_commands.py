"""
Cog containing the ticket system commands for the Discord bot.
Implements the /sendticket, /closeticket and related commands.
"""
import logging
import discord
from discord import app_commands, ButtonStyle, Interaction
from discord.ext import commands
from discord.ui import View, Button
from typing import Optional, List
from datetime import datetime
import asyncio

from database import get_session
from models import Ticket

logger = logging.getLogger("ticket_commands")

class TicketButton(Button):
    """Custom button for creating tickets."""
    def __init__(self, ticket_cog):
        self.ticket_cog = ticket_cog
        super().__init__(
            style=ButtonStyle.success,
            label="Create Ticket",
            emoji="🎫"
        )
    
    async def callback(self, interaction: Interaction):
        """Called when the button is clicked."""
        await self.ticket_cog.create_ticket(interaction)

class TicketView(View):
    """View containing the ticket button."""
    def __init__(self, ticket_cog):
        super().__init__(timeout=None)  # No timeout for persistent buttons
        self.add_item(TicketButton(ticket_cog))

class TicketCommands(commands.Cog):
    """Cog for ticket-related commands."""
    
    def __init__(self, bot):
        self.bot = bot
        self.active_tickets = {}  # Store active ticket channels
    
    @app_commands.command(
        name="sendticket",
        description="Send a ticket creation button to a channel"
    )
    @app_commands.describe(
        channel="The channel to send the ticket button to"
    )
    @app_commands.checks.has_permissions(administrator=True, manage_channels=True)
    async def sendticket(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Send a ticket creation button to a specified channel."""
        await interaction.response.defer(ephemeral=True)
        
        # Check if bot has permissions to send messages in the channel
        if not channel.permissions_for(interaction.guild.me).send_messages:
            await interaction.followup.send(
                f"I don't have permission to send messages in {channel.mention}.",
                ephemeral=True
            )
            return
        
        # Create embed for ticket system
        embed = discord.Embed(
            title="Support Ticket System",
            description="Click the button below to create a support ticket.",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="How it works",
            value="A private channel will be created for your ticket where you can discuss your issue with the staff.",
            inline=False
        )
        
        embed.set_footer(text=f"Requested by {interaction.user.name}")
        
        # Send the embed with the button
        await channel.send(embed=embed, view=TicketView(self))
        
        # Confirm to the requesting user
        await interaction.followup.send(
            f"Ticket creation button sent to {channel.mention} successfully!",
            ephemeral=True
        )
        
        logger.info(f"User {interaction.user.name} ({interaction.user.id}) set up ticket system in {channel.name}")
    
    @sendticket.error
    async def sendticket_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        """Handle errors for the sendticket command."""
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(
                "You need Administrator or Manage Channels permission to use this command.",
                ephemeral=True
            )
        else:
            logger.error(f"Unhandled error in sendticket command: {error}")
            await interaction.response.send_message(
                f"An error occurred: {error}",
                ephemeral=True
            )
    
    async def create_ticket(self, interaction: discord.Interaction):
        """Create a new ticket channel when the button is clicked."""
        await interaction.response.defer(ephemeral=True)
        
        # Get the next ticket number
        session = get_session()
        try:
            # Find the highest ticket number in the database
            highest_ticket = session.query(Ticket).order_by(Ticket.ticket_number.desc()).first()
            next_ticket_num = 1 if not highest_ticket else (highest_ticket.ticket_number + 1) % 10001
            
            # Create a new ticket channel
            guild = interaction.guild
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True)
            }
            
            # Also give access to users with admin or manage channels permissions
            for role in guild.roles:
                permissions = role.permissions
                if permissions.administrator or permissions.manage_channels:
                    overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
            
            # Create the channel
            ticket_channel = await guild.create_text_channel(
                name=f"ticket-{next_ticket_num}",
                overwrites=overwrites,
                reason=f"Support ticket for {interaction.user.name}"
            )
            
            # Send initial message in the ticket channel
            embed = discord.Embed(
                title=f"Ticket #{next_ticket_num}",
                description=f"Thank you for creating a ticket, {interaction.user.mention}!\n\nPlease describe your issue and a staff member will be with you shortly.",
                color=discord.Color.blue()
            )
            
            embed.set_footer(text=f"Created at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
            
            # Add a close ticket button
            close_button = Button(style=ButtonStyle.danger, label="Close Ticket", emoji="🔒")
            
            async def close_button_callback(close_interaction: Interaction):
                # Only allow staff to close tickets
                member = close_interaction.guild.get_member(close_interaction.user.id)
                if not member:
                    return
                
                permissions = close_interaction.channel.permissions_for(member)
                if permissions.administrator or permissions.manage_channels:
                    await self.close_ticket(close_interaction, ticket_number=next_ticket_num)
                else:
                    await close_interaction.response.send_message(
                        "Only staff members can close tickets.",
                        ephemeral=True
                    )
            
            close_button.callback = close_button_callback
            
            view = View(timeout=None)
            view.add_item(close_button)
            
            message = await ticket_channel.send(embed=embed, view=view)
            await message.pin()
            
            # Save ticket to database
            new_ticket = Ticket(
                ticket_number=next_ticket_num,
                creator_id=str(interaction.user.id),
                creator_name=interaction.user.name,
                channel_id=str(ticket_channel.id),
                guild_id=str(guild.id),
                status="open"
            )
            session.add(new_ticket)
            session.commit()
            
            # Store in memory for quick access
            self.active_tickets[ticket_channel.id] = {
                "ticket_number": next_ticket_num,
                "creator_id": interaction.user.id
            }
            
            # Send confirmation to the user
            await interaction.followup.send(
                f"Ticket created! Please check {ticket_channel.mention}.",
                ephemeral=True
            )
            
            logger.info(f"User {interaction.user.name} ({interaction.user.id}) created ticket #{next_ticket_num}")
        
        except Exception as e:
            logger.error(f"Error creating ticket: {e}")
            await interaction.followup.send(
                f"An error occurred while creating your ticket: {e}",
                ephemeral=True
            )
        finally:
            session.close()
    
    @app_commands.command(
        name="closeticket",
        description="Close a ticket channel"
    )
    @app_commands.describe(
        ticket_number="The ticket number to close"
    )
    async def closeticket_command(self, interaction: discord.Interaction, ticket_number: int):
        """Command to close a ticket by number."""
        await self.close_ticket(interaction, ticket_number)
    
    async def close_ticket(self, interaction: discord.Interaction, ticket_number: int):
        """Close a ticket channel."""
        await interaction.response.defer(ephemeral=True)
        
        # Check if user has permission to close tickets
        member = interaction.guild.get_member(interaction.user.id)
        if not member:
            await interaction.followup.send("Could not verify your permissions.", ephemeral=True)
            return
            
        permissions = interaction.channel.permissions_for(member)
        if not (permissions.administrator or permissions.manage_channels):
            await interaction.followup.send("You don't have permission to close tickets.", ephemeral=True)
            return
        
        session = get_session()
        try:
            # Find the ticket in the database
            ticket = session.query(Ticket).filter_by(
                ticket_number=ticket_number,
                guild_id=str(interaction.guild.id),
                status="open"
            ).first()
            
            if not ticket:
                await interaction.followup.send(f"Could not find an open ticket with number {ticket_number}.", ephemeral=True)
                session.close()
                return
            
            # Mark ticket as closed in database
            ticket.status = "closed"
            ticket.closed_at = datetime.utcnow()
            ticket.closed_by = str(interaction.user.id)
            session.commit()
            
            # Get the ticket channel
            ticket_channel = interaction.guild.get_channel(int(ticket.channel_id))
            
            if ticket_channel:
                await interaction.followup.send(f"Closing ticket #{ticket_number}. The channel will be deleted in 5 seconds.", ephemeral=True)
                
                # Send closing message in the ticket channel
                await ticket_channel.send(
                    embed=discord.Embed(
                        title="Ticket Closed",
                        description=f"This ticket has been closed by {interaction.user.mention}. This channel will be deleted in 5 seconds.",
                        color=discord.Color.red()
                    )
                )
                
                # Wait a bit before deleting the channel
                await asyncio.sleep(5)
                await ticket_channel.delete(reason=f"Ticket #{ticket_number} closed by {interaction.user.name}")
                
                # Remove from active tickets
                if int(ticket.channel_id) in self.active_tickets:
                    del self.active_tickets[int(ticket.channel_id)]
                
                logger.info(f"User {interaction.user.name} ({interaction.user.id}) closed ticket #{ticket_number}")
            else:
                await interaction.followup.send("The ticket channel could not be found. It may have been deleted manually.", ephemeral=True)
        
        except Exception as e:
            logger.error(f"Error closing ticket: {e}")
            await interaction.followup.send(f"An error occurred while closing the ticket: {e}", ephemeral=True)
        
        finally:
            session.close()

async def setup(bot):
    """Add the cog to the bot."""
    await bot.add_cog(TicketCommands(bot))
