# USA Army Discord Bot

A feature-rich Discord bot with announcement management, Roblox verification, and ticket support systems.

## Features

### Announcement System
- Send formatted embeds with customizable colors
- Support for images and Google Drive links
- History tracking with database storage
- Admin/Mod permission restrictions

### Roblox Verification
- Link Discord accounts to Roblox profiles
- Secure verification with profile description checks
- Verification code generation and validation
- Automatic role assignment (with proper permissions)

### Ticket System
- Create support tickets with a button click
- Private channels with permission management
- Automatic ticket numbering and tracking
- Admin/Mod accessible ticket commands

### Web Dashboard
- View announcements and verification data
- Track bot activity
- Clean, responsive interface

## Setup

### Prerequisites
- Python 3.11 or higher
- PostgreSQL database
- Discord Bot Token with proper intents
- Roblox security cookie (for verification)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/joelikes8/USA-ARMY-BOT.git
   cd USA-ARMY-BOT
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   ```
   cp .env.example .env
   ```
   Edit the `.env` file with your bot token, database URL, and other required settings.

4. Run the application:
   ```
   python main.py
   ```

### Running the Web Dashboard

The web dashboard runs on Flask and can be launched in a production environment using Gunicorn:

```
gunicorn --bind 0.0.0.0:5000 main:app
```

## Using with Render

This project is ready for deployment on Render. Use the following settings:

- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn --bind 0.0.0.0:$PORT main:app`

Make sure to set all the required environment variables in the Render dashboard.

## Commands

### Announcement Commands
- `/announce <channel> <message> [media] [color]` - Create and send an announcement (Admin/Mod only)
- `/announcements [limit]` - List recent announcements

### Verification Commands
- `/verify <roblox_username>` - Link your Discord account to your Roblox account
- `/reverify <roblox_username>` - Change your verified Roblox account
- `/check` - Complete verification after adding the code to your profile
- `/whois [user]` - Check a user's verified Roblox account

### Ticket Commands
- `/sendticket <channel>` - Send a ticket creation button to a channel (Admin/Mod only)
- `/closeticket <ticket_number>` - Close a ticket (Admin/Mod only)

## License

This project is licensed under the MIT License - see the LICENSE file for details.
