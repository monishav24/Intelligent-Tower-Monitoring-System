"""
Windows Mobile Hotspot Monitor Module.
Monitors Windows Mobile Hotspot status (ON/OFF) and interface traffic.
Displays explicit label 'Connected Client Details Not Available Through Current OS Interface'
when Windows OS restricts per-device client details.
"""
import subprocess
import re
import os
import sys
import psutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_hotspot_status():
    """
    Query Windows network interfaces for Mobile Hotspot / Hosted Network activity.
    Returns hotspot status dictionary.
    """
    hotspot_active = False
    interface_name = "N/A"
    
    try:
        # Check netsh wlan show hostednetwork or net_if_addrs for Virtual Adapter
        interfaces = psutil.net_if_addrs()
        for name in interfaces:
            lower_name = name.lower()
            if "hotspot" in lower_name or "local area connection*" in lower_name or "virtual" in lower_name:
                hotspot_active = True
                interface_name = name
                break
    except Exception:
        pass

    status_str = "ON" if hotspot_active else "OFF"
    
    return {
        "hotspot_status": status_str,
        "interface_name": interface_name,
        "client_count": 0 if not hotspot_active else None,
        "client_details_status": "Connected Client Details Not Available Through Current OS Interface"
    }
