"""CropFlow Application Entry Point.

Run this script to launch the local web server:
    python run.py
"""

import os
from app import create_app

# Attempt to load .env if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = create_app(os.getenv("FLASK_ENV", "development"))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "yes")
    print("=" * 65)
    print("  CropFlow - Optimal Irrigation Scheduling with Limited Water")
    print(f"  Server running at: http://127.0.0.1:{port}/")
    print(f"  Dashboard available at: http://127.0.0.1:{port}/dashboard")
    print(f"  Health Check: http://127.0.0.1:{port}/health")
    print("=" * 65)
    app.run(host="0.0.0.0", port=port, debug=debug)
