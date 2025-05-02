"""
Utility script to check environment variables required for the application.
This helps with debugging configuration issues.
"""
import os
import sys

def check_env_vars():
    """Check required environment variables and print status."""
    required_vars = {
        "DISCORD_BOT_TOKEN": "Required for Discord bot connection",
        "DATABASE_URL": "Required for database connection",
        "ROBLOX_COOKIE": "Required for Roblox verification",
        "SESSION_SECRET": "Used for Flask session security",
        "PORT": "Port for web application (provided by Render)",
        "RUN_BOT": "Set to 'true' to run bot in combined mode",
        "APP_URL": "URL for self-ping mechanism"
    }
    
    # Print header
    print("\n===== ENVIRONMENT VARIABLES CHECK =====")
    
    # Check each required var
    all_ok = True
    for var, desc in required_vars.items():
        value = os.environ.get(var)
        status = "✓ SET" if value else "✗ MISSING"
        if not value:
            all_ok = False
        
        # For tokens, only show length not actual value
        if var.endswith("TOKEN") or var.endswith("SECRET") or var.endswith("COOKIE"):
            display = f"length={len(value)}" if value else "NONE"
        else:
            display = value if value else "NONE"
            
        print(f"{var}: {status} ({display}) - {desc}")
    
    # Print summary
    print("\nSUMMARY: " + ("All required variables are set." if all_ok else "Some required variables are missing!"))
    print("========================================\n")
    
    return all_ok

if __name__ == "__main__":
    success = check_env_vars()
    sys.exit(0 if success else 1)