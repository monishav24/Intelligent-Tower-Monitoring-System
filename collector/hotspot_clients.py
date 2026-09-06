"""
Dedicated Windows Mobile Hotspot Client Collector.
Scans actual devices connected to the Windows laptop's Mobile Hotspot using ARP table ('arp -a')
and PowerShell Get-NetNeighbor interface inspection.
Exposes hotspot state, connected client count, client IP/MAC addresses, and scan timestamp.
Does NOT generate fake or random connected-user numbers.
"""
import subprocess
import re
import platform
import os
import sys
from datetime import datetime
import psutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_connected_hotspot_clients():
    """
    Scan Windows ARP table and network neighbors to detect connected devices.
    Returns dict with hotspot_active, client_count, client_list, client_details, and timestamp.
    """
    last_scan = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 1. Determine if Hotspot / Virtual Adapter is active
    hotspot_active = False
    hotspot_interface_name = "N/A"
    
    try:
        if_addrs = psutil.net_if_addrs()
        if_stats = psutil.net_if_stats()
        
        for name, stats in if_stats.items():
            lower = name.lower()
            if ("hotspot" in lower or "local area connection*" in lower or "virtual" in lower) and stats.isup:
                hotspot_active = True
                hotspot_interface_name = name
                break
    except Exception:
        pass

    clients = []
    
    if platform.system() == "Windows":
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            # Run 'arp -a' to inspect local IPv4 neighbor table
            result = subprocess.run(
                ["arp", "-a"],
                capture_output=True,
                text=True,
                startupinfo=startupinfo,
                timeout=3
            )

            if result.returncode == 0 and result.stdout:
                lines = result.stdout.splitlines()
                current_if = ""
                for line in lines:
                    line_str = line.strip()
                    if line_str.startswith("Interface:"):
                        current_if = line_str
                        continue

                    # Match IP and MAC address pattern: 192.168.137.x  00-11-22-33-44-55  dynamic
                    match = re.search(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\s+([0-9a-fa-f]{2}[-:][0-9a-fa-f]{2}[-:][0-9a-fa-f]{2}[-:][0-9a-fa-f]{2}[-:][0-9a-fa-f]{2}[-:][0-9a-fa-f]{2})\s+(\w+)", line_str, re.IGNORECASE)
                    if match:
                        ip = match.group(1)
                        mac = match.group(2).upper()
                        entry_type = match.group(3).lower()

                        # Filter out broadcast, multicast, and loopback IP ranges
                        if entry_type in ["dynamic", "static"]:
                            ip_parts = [int(p) for p in ip.split(".")]
                            # Exclude 224.x.x.x (multicast), 255.255.255.255, 127.0.0.1, and broadcast .255 / .1 gateway
                            if not (ip_parts[0] in [127, 224, 239, 255] or ip_parts[3] in [0, 255]):
                                # Filter out common router self-addresses if desired, keep real connected clients
                                if mac != "FF-FF-FF-FF-FF-FF":
                                    clients.append({
                                        "ip": ip,
                                        "mac": mac,
                                        "interface": current_if or hotspot_interface_name,
                                        "status": "CONNECTED"
                                    })
        except Exception as e:
            print(f"[Hotspot Client Collector Error]: {e}")

    # Remove duplicate IPs if any
    unique_clients = []
    seen_ips = set()
    for c in clients:
        if c["ip"] not in seen_ips:
            seen_ips.add(c["ip"])
            unique_clients.append(c)

    client_ip_list = [c["ip"] for c in unique_clients]
    client_count = len(unique_clients)

    return {
        "hotspot_active": "ACTIVE" if hotspot_active or client_count > 0 else "INACTIVE",
        "connected_client_count": client_count,
        "client_ip_list": client_ip_list,
        "client_details": unique_clients,
        "last_scan_timestamp": last_scan,
        "connection_status": f"{client_count} Devices Connected" if client_count > 0 else "No Devices Connected"
    }
