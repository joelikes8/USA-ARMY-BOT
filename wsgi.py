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

# Simplify the approach for Render
port = int(os.environ.get("PORT", 10000))
logging.info(f"USA Army Dashboard ready on port {port}")

# Make this file available for Gunicorn
if __name__ == "__main__":
    # Run the app directly when executed
    app.run(host='0.0.0.0', port=port, debug=True)
