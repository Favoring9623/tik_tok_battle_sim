#!/usr/bin/env python3
"""WSGI entry point for production deployment."""
import os
import sys

print("=" * 50)
print("Starting TikTok Battle Simulator...")
print("=" * 50)

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    print("Importing Flask app...")
    from web.backend.app import app, socketio
    print("Flask app imported successfully!")
except Exception as e:
    print(f"ERROR importing app: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Starting server on port {port}...")
    socketio.run(app, host="0.0.0.0", port=port, debug=False)
