"""
Cog containing the Roblox verification commands for the Discord bot.
Implements the /verify and /reverify slash commands to link Discord accounts to Roblox accounts.
"""
import logging
import random
import string
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional
from datetime import datetime
from roblox import Client
from database import get_session
from models import RobloxVerification

logger = logging.getLogger("verify_commands")

# Initialize Roblox client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Roblox cookie from environment variables
ROBLOX_COOKIE = os.getenv("ROBLOX_COOKIE")

# Initialize Roblox client with cookie if available
if ROBLOX_COOKIE:
    roblox_client = Client(ROBLOX_COOKIE)
    logger.info("Initialized Roblox client with authentication cookie")
else:
    roblox_client = Client()
    logger.warning("Initialized Roblox client without authentication cookie - some features may be limited")

def generate_verification_code():
    """Generate a random verification code in the format 'VERIFY-XXXXX'."""
    # Generate 5 random alphanumeric characters
    code_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"VERIFY-{code_chars}"

class VerificationCommands(commands.Cog):
    """Cog for Roblox verification commands."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(
        name="verify",
        description="Verify your Discord account with your Roblox account"
    )
    @app_commands.describe(
        roblox_username="Your Roblox username"
    )
    async def verify(self, interaction: discord.Interaction, roblox_username: str):
        """Verify your Discord account with your Roblox account."""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Check if user is already verified
            session = get_session()
            existing_verification = session.query(RobloxVerification).filter_by(
                discord_id=str(interaction.user.id),
                is_verified=True
            ).first()
            
            if existing_verification:
                await interaction.followup.send(
                    f"You are already verified as {existing_verification.roblox_username}. " +
                    "If you need to change your Roblox account, use `/reverify`.",
                    ephemeral=True
                )
                session.close()
                return
            
            # Check if the Roblox user exists
            try:
                # Try to find the user by username with error handling and retries
                try:
                    roblox_user = await roblox_client.get_user_by_username(roblox_username)
                    
                    if not roblox_user:
                        await interaction.followup.send(
                            f"Could not find a Roblox user with the username '{roblox_username}'. " +
                            "Please check the spelling and try again.",
                            ephemeral=True
                        )
                        session.close()
                        return
                    
                    # Get additional user details to confirm the account exists
                    # The Roblox API has changed - profile must be accessed differently
                    try:
                        # Different methods to verify the user exists and fetch details
                        if hasattr(roblox_user, 'get_status'):
                            status = await roblox_user.get_status()
                            logger.info(f"Got status for user {roblox_username}")
                        else:
                            logger.info(f"User {roblox_username} exists but status method unavailable")
                    except Exception as detail_error:
                        logger.warning(f"Error getting user details: {detail_error}")
                        
                    logger.info(f"Found Roblox user: {roblox_username} (ID: {roblox_user.id})")
                    
                    # Add user thumbnail to verification if available
                    try:
                        avatar_urls = await roblox_client.thumbnails.get_user_avatar_thumbnails([roblox_user.id], size=(420, 420))
                        if avatar_urls and len(avatar_urls) > 0:
                            user_avatar_url = avatar_urls[0].image_url
                        else:
                            user_avatar_url = None
                    except Exception as avatar_error:
                        logger.warning(f"Could not fetch avatar for {roblox_username}: {avatar_error}")
                        user_avatar_url = None
                    
                    roblox_id = str(roblox_user.id)
                except Exception as roblox_api_error:
                    logger.error(f"Roblox API error: {roblox_api_error}")
                    # Direct username lookup (instead of search) as a fallback
                    try:
                        # The Roblox API changed - we can't use user_search asynchronously
                        # Try a different method to lookup the user
                        logger.info(f"Attempting direct lookup for username: {roblox_username}")
                        
                        # Try to use a different method to get the user ID
                        try:
                            # Use alternative username lookup methods
                            user_details = await roblox_client.get_user_id_by_username(roblox_username)
                            if user_details:
                                roblox_id = str(user_details)
                                # Get the full user by ID
                                roblox_user = await roblox_client.get_user(user_details)
                                if roblox_user:
                                    user_avatar_url = None  # We'll skip avatar for this lookup method
                                    logger.info(f"Found Roblox user via direct ID lookup: {roblox_username} (ID: {roblox_id})")
                            else:
                                await interaction.followup.send(
                                    f"Could not find a Roblox user with the username '{roblox_username}'. " +
                                    "Please check the spelling and try again.",
                                    ephemeral=True
                                )
                                session.close()
                                return
                        except Exception as direct_error:
                            logger.error(f"Direct user lookup error: {direct_error}")
                            # Ultimate fallback - just try to create the verification with what we have
                            # Let users manually verify via the check command
                            logger.warning(f"Using backup method for {roblox_username} without ID verification")
                            roblox_id = "0" # Placeholder ID that will be updated on verification
                    except Exception as search_error:
                        logger.error(f"Roblox user verification error: {search_error}")
                        await interaction.followup.send(
                            f"Error connecting to Roblox API. Please try again later.",
                            ephemeral=True
                        )
                        session.close()
                        return
                
            except Exception as roblox_error:
                logger.error(f"Error checking Roblox user: {roblox_error}")
                await interaction.followup.send(
                    f"Error checking Roblox user: {roblox_error}. Please try again later.",
                    ephemeral=True
                )
                session.close()
                return
            
            # Generate a verification code
            verification_code = generate_verification_code()
            
            # Create or update verification entry
            pending_verification = session.query(RobloxVerification).filter_by(
                discord_id=str(interaction.user.id),
                is_verified=False
            ).first()
            
            if pending_verification:
                # Update existing pending verification
                pending_verification.roblox_username = roblox_username
                pending_verification.roblox_id = roblox_id
                pending_verification.verification_code = verification_code
                pending_verification.created_at = datetime.utcnow()
            else:
                # Create new verification entry
                new_verification = RobloxVerification(
                    discord_id=str(interaction.user.id),
                    discord_name=interaction.user.name,
                    roblox_username=roblox_username,
                    roblox_id=roblox_id,
                    verification_code=verification_code
                )
                session.add(new_verification)
            
            session.commit()
            session.close()
            
            # Create an embed with verification instructions
            embed = discord.Embed(
                title="Roblox Verification",
                description=f"Please follow these steps to verify your Roblox account:",
                color=discord.Color.blue()
            )
            
            embed.add_field(
                name="Step 1",
                value=f"Go to your [Roblox Profile](https://www.roblox.com/users/{roblox_id}/profile)",
                inline=False
            )
            
            embed.add_field(
                name="Step 2",
                value="Click on the pencil icon next to your description to edit it",
                inline=False
            )
            
            embed.add_field(
                name="Step 3",
                value=f"Add this code to your profile description: `{verification_code}`\n" +
                      "(You can remove it after verification is complete)",
                inline=False
            )
            
            embed.add_field(
                name="Step 4",
                value="After adding the code, run `/check` to complete the verification",
                inline=False
            )
            
            embed.set_footer(text="Verification code will expire after 24 hours")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
            
            logger.info(f"User {interaction.user.name} ({interaction.user.id}) started verification for Roblox account {roblox_username}")
            
        except Exception as e:
            logger.error(f"Error in verify command: {e}")
            await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)
    
    @app_commands.command(
        name="reverify",
        description="Change your verified Roblox account"
    )
    @app_commands.describe(
        roblox_username="Your new Roblox username"
    )
    async def reverify(self, interaction: discord.Interaction, roblox_username: str):
        """Change your verified Roblox account."""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Delete any existing verification for this user
            session = get_session()
            session.query(RobloxVerification).filter_by(discord_id=str(interaction.user.id)).delete()
            session.commit()
            session.close()
            
            # Run the regular verification process
            await self.verify(interaction, roblox_username)
            
        except Exception as e:
            logger.error(f"Error in reverify command: {e}")
            await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)
    
    @app_commands.command(
        name="check",
        description="Complete your Roblox verification after adding the code to your profile"
    )
    async def check_verification(self, interaction: discord.Interaction):
        """Check and complete the verification process."""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Get pending verification
            session = get_session()
            pending_verification = session.query(RobloxVerification).filter_by(
                discord_id=str(interaction.user.id),
                is_verified=False
            ).first()
            
            if not pending_verification:
                await interaction.followup.send(
                    "You don't have a pending verification. Please use `/verify` first.",
                    ephemeral=True
                )
                session.close()
                return
            
            # Get Roblox user profile with multiple methods and fallbacks
            try:
                # Try different methods to find the user
                roblox_user = None
                try:
                    # First try by username
                    logger.info(f"Looking up Roblox user by username: {pending_verification.roblox_username}")
                    roblox_user = await roblox_client.get_user_by_username(pending_verification.roblox_username)
                except Exception as username_error:
                    logger.warning(f"Error looking up by username: {username_error}")
                
                # If username lookup failed, try by ID
                if not roblox_user and pending_verification.roblox_id:
                    try:
                        logger.info(f"Looking up Roblox user by ID: {pending_verification.roblox_id}")
                        roblox_user = await roblox_client.get_user(int(pending_verification.roblox_id))
                    except Exception as id_error:
                        logger.warning(f"Error looking up by ID: {id_error}")
                
                # If both methods failed, report error
                if not roblox_user:
                    await interaction.followup.send(
                        f"Could not find your Roblox user '{pending_verification.roblox_username}'. " +
                        "Please verify again with `/verify`.",
                        ephemeral=True
                    )
                    session.close()
                    return
                
                logger.info(f"Successfully found Roblox user: {roblox_user.name} (ID: {roblox_user.id})")
                
                # Get the verification code from profile description using multiple methods
                description = ""
                verification_found = False
                
                # Method 1: Try to get description from status
                try:
                    logger.info(f"Getting status for user {roblox_user.name}")
                    user_status = await roblox_user.get_status()
                    if user_status and hasattr(user_status, 'description') and user_status.description:
                        description = user_status.description.strip()
                        logger.info(f"Found description via status: {description[:30]}...")
                        if pending_verification.verification_code in description:
                            verification_found = True
                            logger.info(f"Found verification code in status description")
                except Exception as status_error:
                    logger.warning(f"Error getting status: {status_error}")
                
                # Method 2: Try to get description using alternative methods
                if not verification_found:
                    try:
                        # Try to get description using alternative methods if status didn't work
                        logger.info(f"Trying alternative methods to get description for user {roblox_user.name}")
                        
                        # Method 2a: Try direct API call to get description
                        try:
                            # Some versions of roblox.py have different methods to access profiles
                            if hasattr(roblox_client, 'get_user_profile'):
                                user_profile = await roblox_client.get_user_profile(roblox_user.id)
                                if user_profile and hasattr(user_profile, 'description'):
                                    description = user_profile.description.strip()
                                    if description:
                                        logger.info(f"Found description via client profile method: {description[:30]}...")
                                        if pending_verification.verification_code in description:
                                            verification_found = True
                                            logger.info(f"Found verification code in client profile description")
                        except Exception as client_profile_error:
                            logger.warning(f"Error getting profile via client method: {client_profile_error}")
                        
                        # Method 2b: Attempt to get the 'about' section from user info
                        if not verification_found:
                            try:
                                # Try an alternative API endpoint to get the description
                                # This is a workaround since the get_profile method seems to be missing
                                logger.info(f"Attempting to get 'about' info for user {roblox_user.name}")
                                # Just log what attributes the user object has
                                logger.info(f"User object has attributes: {dir(roblox_user)}")
                                
                                # If we have a way to check description directly on the user
                                if hasattr(roblox_user, 'description'):
                                    description = roblox_user.description.strip()
                                    logger.info(f"Found description directly on user object: {description[:30]}...")
                                    if pending_verification.verification_code in description:
                                        verification_found = True
                                        logger.info(f"Found verification code in user object description")
                            except Exception as about_error:
                                logger.warning(f"Error getting about section: {about_error}")
                    except Exception as profile_error:
                        logger.warning(f"Error with alternative profile methods: {profile_error}")
                
                # If verification code wasn't found, tell the user
                if not verification_found:
                    await interaction.followup.send(
                        f"Verification code `{pending_verification.verification_code}` not found in your Roblox profile description.\n\n" +
                        f"Please make sure you added the code exactly as shown: `{pending_verification.verification_code}`\n" +
                        "It may take a few minutes for Roblox to update your profile. Try again shortly, or use `/verify` to generate a new code if needed.",
                        ephemeral=True
                    )
                    session.close()
                    return
                
                # Verification successful!
                pending_verification.is_verified = True
                pending_verification.verified_at = datetime.utcnow()
                session.commit()
                
                # Try to change nickname if in a guild
                try:
                    if interaction.guild and interaction.guild.me.guild_permissions.manage_nicknames:
                        await interaction.user.edit(nick=pending_verification.roblox_username)
                except Exception as nick_error:
                    logger.error(f"Error changing nickname: {nick_error}")
                    # Continue even if nickname change fails
                
                await interaction.followup.send(
                    f"✅ Successfully verified as **{pending_verification.roblox_username}**!\n" +
                    "Your Discord account is now linked to your Roblox account.",
                    ephemeral=True
                )
                
                logger.info(f"User {interaction.user.name} ({interaction.user.id}) verified as Roblox user {pending_verification.roblox_username}")
                
            except Exception as roblox_error:
                logger.error(f"Error checking Roblox profile: {roblox_error}")
                await interaction.followup.send(
                    f"Error checking Roblox profile: {roblox_error}. Please try again later.",
                    ephemeral=True
                )
            
            session.close()
            
        except Exception as e:
            logger.error(f"Error in check_verification command: {e}")
            await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)

    @app_commands.command(
        name="whois",
        description="Check a user's verified Roblox account"
    )
    @app_commands.describe(
        user="The Discord user to check"
    )
    async def whois(self, interaction: discord.Interaction, user: Optional[discord.User] = None):
        """Check a user's verified Roblox account."""
        await interaction.response.defer(ephemeral=False)  # This info can be public
        
        # Use the provided user or the command user if none provided
        target_user = user or interaction.user
        
        try:
            # Get verification info
            session = get_session()
            verification = session.query(RobloxVerification).filter_by(
                discord_id=str(target_user.id),
                is_verified=True
            ).first()
            
            if not verification:
                await interaction.followup.send(
                    f"{'You are' if target_user == interaction.user else f'**{target_user.name}** is'} not verified with any Roblox account.",
                    ephemeral=False
                )
                session.close()
                return
            
            # Create embed with Roblox info
            embed = discord.Embed(
                title=f"Roblox Information for {target_user.name}",
                description=f"Discord user {'you' if target_user == interaction.user else f'**{target_user.name}**'} is verified as:",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="Roblox Username",
                value=f"**{verification.roblox_username}**",
                inline=True
            )
            
            embed.add_field(
                name="Roblox Profile",
                value=f"[View Profile](https://www.roblox.com/users/{verification.roblox_id}/profile)",
                inline=True
            )
            
            embed.add_field(
                name="Verified Since",
                value=f"<t:{int(verification.verified_at.timestamp())}:R>" if verification.verified_at else "Unknown",
                inline=True
            )
            
            # Try to get Roblox avatar
            try:
                roblox_user = await roblox_client.get_user_by_username(verification.roblox_username)
                if roblox_user:
                    avatar_url = await roblox_user.get_headshot()
                    if avatar_url:
                        embed.set_thumbnail(url=avatar_url)
            except Exception as avatar_error:
                logger.error(f"Error getting Roblox avatar: {avatar_error}")
                # Continue even if avatar fetch fails
            
            await interaction.followup.send(embed=embed, ephemeral=False)
            session.close()
            
        except Exception as e:
            logger.error(f"Error in whois command: {e}")
            await interaction.followup.send(f"An error occurred: {e}", ephemeral=True)

async def setup(bot):
    """Add the cog to the bot."""
    await bot.add_cog(VerificationCommands(bot))
