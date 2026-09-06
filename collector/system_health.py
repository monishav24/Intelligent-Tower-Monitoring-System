"""
Laptop System Health Collector.
Measures real host laptop parameters: CPU Usage %, RAM Usage %, Battery %, Charging Status, and System Uptime.
Clearly labeled as 'Prototype Node System Health'.
"""
import time
import os
import sys
import psutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_system_health():
    """Collect real laptop host health indicators."""
    cpu_pct = round(psutil.cpu_percent(interval=None), 1)
    ram_pct = round(psutil.virtual_memory().percent, 1)

    # Battery Telemetry
    battery = psutil.sensors_battery()
    if battery:
        battery_pct = round(battery.percent, 1)
        charging_status = "CHARGING" if battery.power_plugged else "DISCHARGING"
    else:
        battery_pct = None
        charging_status = "AC POWER / NO BATTERY"

    # System Uptime (in hours)
    boot_time = psutil.boot_time()
    uptime_hours = round((time.time() - boot_time) / 3600.0, 1)

    return {
        "cpu_usage": cpu_pct,
        "ram_usage": ram_pct,
        "battery_percentage": battery_pct,
        "battery_status": charging_status,
        "system_uptime_hours": uptime_hours,
        "node_label": "Prototype Node System Health"
    }
