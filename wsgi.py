import os
import logging
import sys
from webapp import app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Get the port from Render's environment
port = int(os.environ.get("PORT", 10000))

# Log the port binding explicitly for Render to detect
print(f"RENDER PORT DETECTION: Web server will bind to PORT={port}", file=sys.stderr)
logging.info(f"USA Army Dashboard starting on port {port}")

# For running directly (not through gunicorn)
if __name__ == "__main__":
    # Run the app directly
    app.run(host='0.0.0.0', port=port, debug=True)
