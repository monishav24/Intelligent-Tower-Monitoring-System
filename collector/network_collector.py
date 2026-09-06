"""
Real-Time Network Telemetry Collector.
Measures bytes sent/received via psutil, upload/download speeds, throughput, and bandwidth utilization.
Formats data dynamically into human-readable units (B, KB, MB, GB, Mbps).
"""
import time
import os
import sys
import psutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

class NetworkCollector:
    def __init__(self, max_bandwidth_mbps=None):
        self.last_bytes_sent = None
        self.last_bytes_recv = None
        self.last_timestamp = None
        self.max_bandwidth_mbps = max_bandwidth_mbps or config.DEFAULT_MAX_BANDWIDTH_MBPS

    def get_metrics(self):
        """
        Calculate upload speed, download speed, total traffic, and bandwidth utilization.
        """
        net_io = psutil.net_io_counters()
        current_time = time.time()

        bytes_sent = net_io.bytes_sent
        bytes_recv = net_io.bytes_recv

        if self.last_bytes_sent is None or self.last_bytes_recv is None or self.last_timestamp is None:
            upload_speed_kbps = 0.0
            download_speed_kbps = 0.0
            time_delta = 1.0
        else:
            time_delta = max(current_time - self.last_timestamp, 0.1)
            upload_speed_kbps = (bytes_sent - self.last_bytes_sent) / (1024.0 * time_delta)
            download_speed_kbps = (bytes_recv - self.last_bytes_recv) / (1024.0 * time_delta)

        self.last_bytes_sent = bytes_sent
        self.last_bytes_recv = bytes_recv
        self.last_timestamp = current_time

        # Convert throughput to Mbps
        total_speed_kbps = upload_speed_kbps + download_speed_kbps
        throughput_mbps = (total_speed_kbps * 8.0) / 1024.0

        # Bandwidth Utilization (%) = (Throughput / Max Bandwidth) * 100
        bandwidth_utilization = (throughput_mbps / self.max_bandwidth_mbps) * 100.0
        bandwidth_utilization = round(max(bandwidth_utilization, 0.0), 2)

        # Total traffic in Megabytes
        total_traffic_mb = round((bytes_sent + bytes_recv) / (1024.0 * 1024.0), 2)

        return {
            "bytes_sent": bytes_sent,
            "bytes_recv": bytes_recv,
            "upload_speed": round(upload_speed_kbps, 2), # KB/s
            "download_speed": round(download_speed_kbps, 2), # KB/s
            "throughput_mbps": round(throughput_mbps, 3),
            "total_network_traffic": total_traffic_mb,
            "bandwidth_utilization": bandwidth_utilization,
            "max_bandwidth_mbps": self.max_bandwidth_mbps,
            "formatted_total_traffic": self._format_bytes(bytes_sent + bytes_recv)
        }

    @staticmethod
    def _format_bytes(size_bytes):
        """Format raw byte counts into B, KB, MB, or GB."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{round(size_bytes / 1024.0, 2)} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{round(size_bytes / (1024.0 * 1024.0), 2)} MB"
        else:
            return f"{round(size_bytes / (1024.0 * 1024 * 1024.0), 2)} GB"

    def set_max_bandwidth(self, mbps):
        """Dynamically reconfigure maximum bandwidth threshold."""
        if mbps > 0:
            self.max_bandwidth_mbps = float(mbps)
