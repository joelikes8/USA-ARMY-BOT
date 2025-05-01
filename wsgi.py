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

# Make sure app is available for Gunicorn
port = int(os.environ.get("PORT", 10000))
logging.info(f"Application configured to run on port {port}")
print(f"RENDER PORT CONFIGURATION: {port}", file=sys.stderr)

# Make this file available for rendering
if __name__ == "__main__":
    # Run the application
    app.run(host='0.0.0.0', port=port, debug=True)
