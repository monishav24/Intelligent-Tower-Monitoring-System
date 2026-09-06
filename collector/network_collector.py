"""
Network Data Collector.
Monitors real-time laptop network traffic using psutil.
Calculates upload speed, download speed, throughput, and bandwidth utilization.
"""
import time
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import psutil
import config

class NetworkCollector:
    def __init__(self, max_bandwidth_mbps=None):
        self.last_bytes_sent = None
        self.last_bytes_recv = None
        self.last_timestamp = None
        self.max_bandwidth_mbps = max_bandwidth_mbps or config.DEFAULT_MAX_BANDWIDTH_MBPS

    def get_network_metrics(self):
        """
        Calculate upload speed, download speed, total traffic, and bandwidth utilization.
        """
        net_io = psutil.net_io_counters()
        current_time = time.time()

        bytes_sent = net_io.bytes_sent
        bytes_recv = net_io.bytes_recv

        if self.last_bytes_sent is None or self.last_bytes_recv is None or self.last_timestamp is None:
            # First initialization measurement
            upload_speed_kbps = 0.0
            download_speed_kbps = 0.0
            time_delta = 1.0
        else:
            time_delta = max(current_time - self.last_timestamp, 0.1)
            # KB/s
            upload_speed_kbps = (bytes_sent - self.last_bytes_sent) / (1024.0 * time_delta)
            download_speed_kbps = (bytes_recv - self.last_bytes_recv) / (1024.0 * time_delta)

        # Update last states
        self.last_bytes_sent = bytes_sent
        self.last_bytes_recv = bytes_recv
        self.last_timestamp = current_time

        # Total throughput in Mbps: (KB/s * 8) / 1024
        total_speed_kbps = upload_speed_kbps + download_speed_kbps
        throughput_mbps = (total_speed_kbps * 8.0) / 1024.0

        # Bandwidth Utilization (%) = (Current Throughput / Maximum Bandwidth) * 100
        # If max_bandwidth_mbps is 100 Mbps, cap utilization nicely or allow full %
        bandwidth_utilization = (throughput_mbps / self.max_bandwidth_mbps) * 100.0
        # Ensure non-negative and reasonable float precision
        bandwidth_utilization = round(max(bandwidth_utilization, 0.0), 2)

        # Total traffic in Megabytes
        total_traffic_mb = round((bytes_sent + bytes_recv) / (1024.0 * 1024.0), 2)

        return {
            "bytes_sent": bytes_sent,
            "bytes_recv": bytes_recv,
            "upload_speed_kbps": round(upload_speed_kbps, 2),
            "download_speed_kbps": round(download_speed_kbps, 2),
            "upload_speed_mbps": round((upload_speed_kbps * 8.0) / 1024.0, 3),
            "download_speed_mbps": round((download_speed_kbps * 8.0) / 1024.0, 3),
            "throughput_mbps": round(throughput_mbps, 3),
            "total_traffic_mb": total_traffic_mb,
            "bandwidth_utilization": bandwidth_utilization,
            "max_bandwidth_mbps": self.max_bandwidth_mbps
        }

    def set_max_bandwidth(self, mbps):
        """Allow user to dynamically configure maximum network bandwidth."""
        if mbps > 0:
            self.max_bandwidth_mbps = float(mbps)
