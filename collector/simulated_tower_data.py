"""
Simulated Telecom Tower Sensor Data Collector.
Generates realistic simulated hardware parameters (Temperature, Power, Voltage, Users, Load).
Incorporates dynamic physical relationships and Demo Mode scenario overrides.
"""
import random
import time
import math

class SimulatedTowerCollector:
    def __init__(self):
        # Base realistic state values
        self.current_temp = 34.5
        self.battery_voltage = 12.55
        self.connected_users = 42
        self.base_time = time.time()

    def get_simulated_metrics(self, real_network_metrics, demo_scenario="NORMAL"):
        """
        Generate realistic simulated parameters tied to network activity and demo scenarios.
        """
        throughput_mbps = real_network_metrics.get("throughput_mbps", 1.0)
        bw_utilization = real_network_metrics.get("bandwidth_utilization", 5.0)

        # Apply Demo Mode Scenarios if active
        if demo_scenario == "HIGH_TRAFFIC":
            users = random.randint(150, 210)
            tower_load = round(min(75.0 + (throughput_mbps * 2.0) + random.uniform(-2, 3), 90.0), 2)
            temp = round(44.0 + random.uniform(-0.5, 0.8), 2)
            power = round(175.0 + (tower_load * 0.5) + random.uniform(-2, 3), 2)
            battery = round(12.1 + random.uniform(-0.05, 0.05), 2)
            signal_override = None

        elif demo_scenario == "NETWORK_CONGESTION":
            users = random.randint(280, 420)
            tower_load = round(random.uniform(92.0, 98.5), 2)
            temp = round(48.5 + random.uniform(-0.3, 0.6), 2)
            power = round(210.0 + random.uniform(-3, 4), 2)
            battery = round(11.8 + random.uniform(-0.05, 0.05), 2)
            signal_override = None

        elif demo_scenario == "WEAK_SIGNAL":
            users = random.randint(25, 45)
            tower_load = round(random.uniform(30.0, 45.0), 2)
            temp = round(35.0 + random.uniform(-0.3, 0.3), 2)
            power = round(120.0 + random.uniform(-2, 2), 2)
            battery = round(12.4 + random.uniform(-0.02, 0.02), 2)
            signal_override = round(random.uniform(12.0, 22.0), 1)

        elif demo_scenario == "HIGH_TEMPERATURE":
            users = random.randint(60, 90)
            tower_load = round(random.uniform(65.0, 80.0), 2)
            temp = round(56.8 + random.uniform(-0.4, 0.7), 2)  # CRITICAL Alert > 50°C
            power = round(195.0 + random.uniform(-3, 3), 2)
            battery = round(11.6 + random.uniform(-0.04, 0.04), 2)
            signal_override = None

        elif demo_scenario == "POWER_FAILURE":
            users = random.randint(30, 50)
            tower_load = round(random.uniform(35.0, 50.0), 2)
            temp = round(38.0 + random.uniform(-0.3, 0.3), 2)
            power = round(235.0 + random.uniform(-5, 5), 2)     # High abnormal power drain
            battery = round(10.3 + random.uniform(-0.05, 0.05), 2) # CRITICAL Voltage < 10.8V
            signal_override = None

        else: # NORMAL Operation
            # Realistic continuous random walk & diurnal trend
            elapsed = time.time() - self.base_time
            diurnal_factor = math.sin(elapsed / 300.0) * 5.0 # Smooth oscillation
            
            # Users fluctuate around base + network load
            users = int(max(30 + diurnal_factor + (throughput_mbps * 8.0) + random.randint(-3, 3), 10))
            
            # Tower load scales with connected users and throughput
            calculated_load = 25.0 + (users * 0.4) + (bw_utilization * 0.3)
            tower_load = round(min(max(calculated_load + random.uniform(-2.0, 2.0), 15.0), 85.0), 2)
            
            # Temperature rises gradually with tower load
            target_temp = 32.0 + (tower_load * 0.12) + random.uniform(-0.2, 0.2)
            self.current_temp += (target_temp - self.current_temp) * 0.1 # Exponential smoothing
            temp = round(self.current_temp, 2)
            
            # Power consumption depends directly on tower load (Base 100W + load * 0.75)
            power = round(100.0 + (tower_load * 0.75) + random.uniform(-1.5, 1.5), 2)
            
            # Battery voltage slight float fluctuation around 12.6V
            self.battery_voltage += random.uniform(-0.01, 0.01)
            self.battery_voltage = max(min(self.battery_voltage, 12.75), 12.35)
            battery = round(self.battery_voltage, 2)
            
            signal_override = None

        return {
            "temperature": temp,
            "power_consumption": power,
            "battery_voltage": battery,
            "connected_users": users,
            "tower_load": tower_load,
            "signal_override": signal_override,
            "data_source_label": "Simulated Prototype Data – To Be Replaced by ESP32 Sensors"
        }
