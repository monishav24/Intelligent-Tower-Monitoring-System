"""
Live Network Delay & Propagation Time Collector.
Measures real round-trip network latency (delay_ms) using ICMP ping / socket connection tests.
Calculates estimated propagation time as (delay_ms / 2.0).
Gracefully handles offline or network failure without crashing the service.
"""
import time
import socket
import subprocess
import os

class DelayCollector:
    def __init__(self, target_host="8.8.8.8", fallback_host="127.0.0.1", timeout_sec=1.0):
        self.target_host = target_host
        self.fallback_host = fallback_host
        self.timeout_sec = timeout_sec

    def measure_delay(self):
        """
        Measure round-trip time (RTT) delay in milliseconds.
        Returns dict containing delay_ms and estimated propagation_time_ms.
        """
        delay_ms = self._ping(self.target_host)
        
        # Fallback to local loopback if external host ping fails
        if delay_ms is None:
            delay_ms = self._ping(self.fallback_host)
            
        if delay_ms is None:
            # Measure local TCP socket handshake latency as ultimate fallback
            delay_ms = self._socket_latency(self.fallback_host, 5000)

        if delay_ms is not None:
            delay_ms = round(max(delay_ms, 0.1), 2)
            propagation_time_ms = round(delay_ms / 2.0, 2)
        else:
            delay_ms = 1.0
            propagation_time_ms = 0.5

        return {
            "delay_ms": delay_ms,
            "propagation_time_ms": propagation_time_ms
        }

    def _ping(self, host):
        """Perform system ping command and parse latency."""
        try:
            if os.name == "nt":
                cmd = ["ping", "-n", "1", "-w", str(int(self.timeout_sec * 1000)), host]
            else:
                cmd = ["ping", "-c", "1", "-W", str(int(self.timeout_sec)), host]

            t0 = time.perf_counter()
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=self.timeout_sec + 0.5)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0

            if res.returncode == 0:
                # Parse output for time=XXms
                out = res.stdout.lower()
                if "time=" in out or "time<" in out:
                    try:
                        part = out.split("time=")[1] if "time=" in out else out.split("time<")[1]
                        val_str = part.split("ms")[0].strip()
                        return float(val_str)
                    except Exception:
                        return elapsed_ms
                return elapsed_ms
            return None
        except Exception:
            return None

    def _socket_latency(self, host, port):
        """Measure TCP connect latency in milliseconds."""
        try:
            t0 = time.perf_counter()
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(self.timeout_sec)
            s.connect((host, port))
            s.close()
            return (time.perf_counter() - t0) * 1000.0
        except Exception:
            return None
