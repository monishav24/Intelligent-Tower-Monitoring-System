"""
Wi-Fi Signal and State Collector.
Parses Windows native 'netsh wlan show interfaces' command output.
Detects Wi-Fi state, signal percentage (0-100%), SSID, and qualitative signal quality.
Handles disconnection gracefully without application crashes.
"""
import subprocess
import re
import platform
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def get_wifi_info():
    """
    Extract Wi-Fi signal percentage, state, SSID, and quality status on Windows.
    Returns dictionary with wifi_status, signal_strength, ssid, and connection_quality.
    """
    if platform.system() != "Windows":
        return {
            "wifi_status": "CONNECTED",
            "signal_strength": 75.0,
            "ssid": "Simulated_WiFi",
            "connection_quality": "GOOD"
        }

    try:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        
        result = subprocess.run(
            ["netsh", "wlan", "show", "interfaces"],
            capture_output=True,
            text=True,
            startupinfo=startupinfo,
            timeout=3
        )

        if result.returncode != 0 or not result.stdout:
            return {
                "wifi_status": "DISCONNECTED",
                "signal_strength": 0.0,
                "ssid": "N/A",
                "connection_quality": "DISCONNECTED"
            }

        output = result.stdout

        # Check for State
        state_match = re.search(r"State\s*:\s*(\w+)", output, re.IGNORECASE)
        state = state_match.group(1).lower() if state_match else "unknown"

        if "disconnected" in state or "disconnected" in output.lower():
            return {
                "wifi_status": "DISCONNECTED",
                "signal_strength": 0.0,
                "ssid": "N/A",
                "connection_quality": "DISCONNECTED"
            }

        # SSID extraction
        ssid_match = re.search(r"SSID\s*:\s*(.+)", output, re.IGNORECASE)
        ssid = ssid_match.group(1).strip() if ssid_match else "Connected Interface"

        # Signal percentage extraction
        signal_match = re.search(r"Signal\s*:\s*(\d+)%", output, re.IGNORECASE)
        if signal_match:
            signal_pct = float(signal_match.group(1))
        else:
            signal_pct = 85.0 # Ethernet or unlisted signal fallback

        # Determine signal quality classification
        th = config.THRESHOLDS["signal_strength"]
        if signal_pct >= th["excellent"]:
            quality = "EXCELLENT"
        elif signal_pct >= th["good"]:
            quality = "GOOD"
        elif signal_pct >= th["fair"]:
            quality = "FAIR"
        elif signal_pct >= th["weak"]:
            quality = "WEAK"
        elif signal_pct > 0:
            quality = "CRITICAL"
        else:
            quality = "DISCONNECTED"

        return {
            "wifi_status": "CONNECTED",
            "signal_strength": signal_pct,
            "ssid": ssid,
            "connection_quality": quality
        }

    except Exception as e:
        return {
            "wifi_status": "DISCONNECTED",
            "signal_strength": 0.0,
            "ssid": "Error",
            "connection_quality": "DISCONNECTED"
        }
