"""
Main Application Entry Point for Intelligent Telecom Tower Monitoring System.
Initializes SQLite database, starts background telemetry daemon thread,
registers REST API routes, and serves the offline-first web dashboard.
"""
import os
import sys
from flask import Flask, render_template

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config
import database.database as db
from services.monitoring_service import MonitoringService
from routes.api import api_bp, init_api_service

app = Flask(__name__)
app.register_blueprint(api_bp)

# Instantiate background monitoring service
monitoring_service = MonitoringService()
init_api_service(monitoring_service)

@app.route("/")
def index():
    """Serve offline-first dashboard template."""
    return render_template("index.html", metadata=config.SYSTEM_METADATA)

if __name__ == "__main__":
    # Initialize database tables
    db.init_db()

    # Start telemetry daemon thread
    monitoring_service.start()

    print("\n========================================================================")
    print("   INTELLIGENT TELECOM TOWER MONITORING AND ALERT SYSTEM               ")
    print("========================================================================")
    print("   Status: Local Server Running on http://127.0.0.1:5000               ")
    print("   Offline Mode: Fully Supported (Zero Internet / CDN Dependencies)      ")
    print("========================================================================\n")

    app.run(host="0.0.0.0", port=5000, debug=False)
