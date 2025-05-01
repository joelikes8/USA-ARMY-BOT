import os
import logging
from webapp import app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Make sure app is available for Gunicorn
port = int(os.environ.get("PORT", 8080))
logging.info(f"Application will run on port {port}")

# Make this file available for rendering
if __name__ == "__main__":
    # Run the application
    app.run(host='0.0.0.0', port=port, debug=True)
