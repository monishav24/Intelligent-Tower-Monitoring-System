"""
Internet Connectivity Checker Module.
Performs fast non-blocking socket checks to test public Internet access.
Returns 'ONLINE' or 'OFFLINE'.
Internet connectivity is treated as an optional external dependency; local server continues 100% offline.
"""
import socket

def check_internet_connectivity(host="8.8.8.8", port=53, timeout=1.0):
    """
    Test TCP socket connection to a public DNS IP (8.8.8.8).
    Returns 'ONLINE' or 'OFFLINE'.
    """
    try:
        socket.setdefaulttimeout(timeout)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        s.close()
        return "ONLINE"
    except Exception:
        # Fallback check to Cloudflare DNS 1.1.1.1
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("1.1.1.1", 53))
            s.close()
            return "ONLINE"
        except Exception:
            return "OFFLINE"
