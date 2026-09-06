"""
Alert Service Module.
Handles alert dispatching, persistence, and active alerts logging.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database.database as db

class AlertService:
    def __init__(self):
        pass

    def log_alerts(self, alerts):
        """Persist list of alert objects into SQLite."""
        for alert in alerts:
            db.insert_alert(alert)

    def get_alerts(self, limit=20):
        """Retrieve recent active alerts."""
        return db.get_active_alerts(limit=limit)
