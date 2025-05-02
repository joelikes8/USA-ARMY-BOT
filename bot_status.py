"""
Shared module for tracking Discord bot status.
This avoids circular imports between bot.py and webapp.py.
It uses a simple file-based mechanism to share status between processes.
"""
import time
import logging
import threading
import json
import os
import tempfile
from typing import Optional, Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

# Path to status file (in /tmp to ensure it's writable)
STATUS_FILE = os.path.join(tempfile.gettempdir(), 'usa_army_bot_status.json')

# Default bot status dictionary
DEFAULT_STATUS: Dict[str, Any] = {
    'is_connected': False,
    'last_heartbeat': None,
    'discord_username': None,
    'uptime_start': time.time(),
    'reconnect_count': 0
}

# Initialize the status file if it doesn't exist
if not os.path.exists(STATUS_FILE):
    try:
        with open(STATUS_FILE, 'w') as f:
            json.dump(DEFAULT_STATUS, f)
        logger.info(f"Created bot status file at {STATUS_FILE}")
    except Exception as e:
        logger.error(f"Failed to create status file: {e}")

# Lock for thread-safe updates
_status_lock = threading.Lock()

def _read_status() -> Dict[str, Any]:
    """
    Read the current status from the status file.
    
    Returns:
        The current status dict, or the default status if the file cannot be read
    """
    try:
        with open(STATUS_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to read status file: {e}")
        return dict(DEFAULT_STATUS)

def _write_status(status: Dict[str, Any]) -> None:
    """
    Write the status to the status file.
    
    Args:
        status: The status dict to write
    """
    try:
        with open(STATUS_FILE, 'w') as f:
            json.dump(status, f)
    except Exception as e:
        logger.error(f"Failed to write status file: {e}")

def update_status(connected: Optional[bool] = None, 
                 discord_username: Optional[str] = None, 
                 reconnect_count: Optional[int] = None) -> None:
    """
    Update the bot status with the provided values.
    
    Args:
        connected: Whether the bot is currently connected to Discord
        discord_username: The Discord username of the bot
        reconnect_count: The number of reconnection attempts
    """
    with _status_lock:
        # Read current status
        status = _read_status()
        
        # Always update the heartbeat time when this function is called
        status['last_heartbeat'] = time.time()
        
        # Update other fields only if provided
        if connected is not None:
            status['is_connected'] = connected
            logger.info(f"Bot connection status updated: {connected}")
            
        if discord_username is not None:
            status['discord_username'] = discord_username
            logger.info(f"Bot username updated: {discord_username}")
            
        if reconnect_count is not None:
            status['reconnect_count'] = reconnect_count
            logger.info(f"Bot reconnect count updated: {reconnect_count}")
        
        # Write updated status
        _write_status(status)
            
        # Log full status for debugging
        logger.info(f"Bot status updated: connected={status['is_connected']}, username={status['discord_username']}, heartbeat={status['last_heartbeat']}")

def get_status() -> Dict[str, Any]:
    """
    Get a copy of the current bot status.
    
    Returns:
        A dictionary containing the current bot status
    """
    with _status_lock:
        # Read and return current status
        return _read_status()

def is_bot_alive() -> bool:
    """
    Check if the bot is currently alive based on heartbeat.
    
    Returns:
        True if the bot has sent a heartbeat recently, False otherwise
    """
    with _status_lock:
        # Read current status
        status = _read_status()
        
        # Check if last_heartbeat exists and is recent (within 2 minutes)
        if status['last_heartbeat'] is None:
            return False
            
        heartbeat_age = time.time() - status['last_heartbeat']
        return heartbeat_age < 120  # 2 minutes

def reset_status() -> None:
    """
    Reset the bot status to default values.
    """
    with _status_lock:
        # Write default status
        _write_status(DEFAULT_STATUS)

# Start a heartbeat thread for the bot status
def start_heartbeat_thread() -> threading.Thread:
    """
    Start a background thread that sends regular heartbeats.
    This thread periodically updates the heartbeat timestamp in the status file,
    which helps other processes know that the bot is still alive.
    
    Returns:
        The started thread object
    """
    def heartbeat_worker():
        logger.info("Bot status heartbeat worker thread started")
        
        while True:
            try:
                # Just update the heartbeat timestamp if the bot is connected
                with _status_lock:
                    # Read current status
                    current_status = _read_status()
                    
                    if current_status['is_connected']:
                        # Update heartbeat time
                        current_status['last_heartbeat'] = time.time()
                        _write_status(current_status)
                        logger.debug("Bot status heartbeat sent")
                    else:
                        logger.debug("Bot is not connected, heartbeat not sent")
            except Exception as e:
                logger.error(f"Error in heartbeat worker: {e}")
            
            # Sleep for 30 seconds
            time.sleep(30)
    
    # Create and start the thread
    thread = threading.Thread(target=heartbeat_worker, daemon=True)
    thread.name = "Bot-Status-Heartbeat"
    thread.start()
    logger.info("Bot status heartbeat thread started")
    return thread