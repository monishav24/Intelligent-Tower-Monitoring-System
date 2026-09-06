"""
Wi-Fi Signal Strength Collector.
Collects Wi-Fi signal percentage on Windows using 'netsh wlan show interfaces'.
Handles missing Wi-Fi interface or Ethernet gracefully.
"""
import subprocess
import re
import platform

def get_wifi_signal_strength():
    """
    Extract Wi-Fi signal percentage on Windows host.
    Returns signal_percentage (float, 0-100) and connection_status (str).
    """
    if platform.system() != "Windows":
        return 75.0, "Non-Windows Host (Simulated Signal)"

    try:
        # Run command with hidden window execution
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
            return 80.0, "Interface Unavailable"

        output = result.stdout

        # Search for "Signal : XX%" or "Signal\s*:\s*(\d+)%"
        match = re.search(r"Signal\s*:\s*(\d+)%", output, re.IGNORECASE)
        if match:
            signal_pct = float(match.group(1))
            return signal_pct, "Connected"

        # Check if disconnected
        if "disconnected" in output.lower():
            return 0.0, "Disconnected"

        return 85.0, "Connected (Ethernet/Static)"

    except Exception as e:
        return 75.0, f"Signal Fetch Error ({str(e)})"
