"""
Simulated Telecom Tower Sensor Collector.
Generates realistic, non-random simulated parameters (Power, Battery Voltage, Users, Tower Load).
Enforces intelligent relationships (Users -> Traffic -> Load -> Power Draw) and Demo Mode scenarios.
All output explicitly tagged as 'SIMULATED PROTOTYPE DATA'.
"""
import random
import time
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class SimulatedTowerCollector:
    def __init__(self):
        self.battery_voltage = 12.60
        self.base_time = time.time()

    def get_metrics(self, net_metrics, demo_scenario="NORMAL"):
        """
        Calculate realistic simulated hardware metrics tied to laptop network throughput and active demo mode.
        """
        throughput = net_metrics.get("throughput_mbps", 1.0)
        bw_util = net_metrics.get("bandwidth_utilization", 5.0)

        scenario = demo_scenario.upper()

        if scenario == "HIGH_TRAFFIC":
            users = random.randint(180, 240)
            tower_load = round(min(78.0 + (throughput * 2.0) + random.uniform(-2, 3), 90.0), 1)
            power = round(175.0 + (tower_load * 0.5) + random.uniform(-2, 3), 1)
            battery = round(12.1 + random.uniform(-0.05, 0.05), 2)

        elif scenario == "NETWORK_CONGESTION":
            users = random.randint(320, 450)
            tower_load = round(random.uniform(93.0, 98.5), 1)
            power = round(215.0 + random.uniform(-3, 4), 1)
            battery = round(11.7 + random.uniform(-0.05, 0.05), 2)

        elif scenario == "WEAK_SIGNAL":
            users = random.randint(20, 40)
            tower_load = round(random.uniform(25.0, 40.0), 1)
            power = round(115.0 + random.uniform(-2, 2), 1)
            battery = round(12.45 + random.uniform(-0.02, 0.02), 2)

        elif scenario == "POWER_ANOMALY":
            users = random.randint(35, 60)
            tower_load = round(random.uniform(35.0, 50.0), 1)
            power = round(245.0 + random.uniform(-5, 6), 1)      # High power surge (>220W Critical)
            battery = round(10.3 + random.uniform(-0.05, 0.05), 2) # Low battery voltage (<10.8V Critical)

        elif scenario == "NETWORK_DISCONNECTED":
            users = 0
            tower_load = 0.0
            power = round(45.0 + random.uniform(-1, 1), 1)
            battery = round(12.5 + random.uniform(-0.02, 0.02), 2)

        else: # NORMAL Operation
            elapsed = time.time() - self.base_time
            diurnal_wave = math.sin(elapsed / 300.0) * 8.0

            # Users scale with throughput
            users = int(max(35 + diurnal_wave + (throughput * 10.0) + random.randint(-2, 2), 10))

            # Tower load scales with users & bandwidth utilization
            raw_load = 20.0 + (users * 0.35) + (bw_util * 0.4)
            tower_load = round(min(max(raw_load + random.uniform(-1.5, 1.5), 10.0), 85.0), 1)

            # Power consumption scales directly with tower load (Base 100W + load * 0.75)
            power = round(100.0 + (tower_load * 0.75) + random.uniform(-1.5, 1.5), 1)

            # Battery voltage subtle float fluctuation
            self.battery_voltage += random.uniform(-0.008, 0.008)
            self.battery_voltage = max(min(self.battery_voltage, 12.75), 12.30)
            battery = round(self.battery_voltage, 2)

        return {
            "connected_users": users,
            "tower_load": tower_load,
            "power_consumption": power,
            "battery_voltage": battery,
            "data_source_label": "SIMULATED PROTOTYPE DATA"
        }
