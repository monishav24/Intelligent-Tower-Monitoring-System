"""
Laptop Temperature Collector with Fallback & Demo Simulation Modes.
Attempts to query Windows WMI thermal zone information.
If unavailable on specific laptop hardware, gracefully returns 'Temperature Sensor Unavailable'
or allows clearly labeled Demo Temperature Mode (NORMAL, HIGH, CRITICAL).
"""
import subprocess
import os
import sys
import platform

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

class TemperatureCollector:
    def __init__(self):
        self.demo_mode = False
        self.demo_state = "NORMAL" # NORMAL (<60°C), HIGH (60-80°C), CRITICAL (>80°C)

    def get_temperature(self):
        """
        Attempt to collect host CPU/System temperature.
        Returns temperature (°C or None), temperature_source, and is_simulated.
        """
        if self.demo_mode:
            return self._get_demo_temperature()

        # Try WMI thermal zone query on Windows
        if platform.system() == "Windows":
            try:
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

                cmd = ["wmic", "/namespace:\\\\root\\wmi", "PATH", "MSAcpi_ThermalZoneTemperature", "get", "CurrentTemperature"]
                result = subprocess.run(cmd, capture_output=True, text=True, startupinfo=startupinfo, timeout=2)

                if result.returncode == 0 and result.stdout:
                    lines = [line.strip() for line in result.stdout.splitlines() if line.strip().isdigit()]
                    if lines:
                        # WMIC returns temperature in tenths of Kelvin (Kelvin * 10)
                        raw_temp = float(lines[0])
                        celsius = (raw_temp / 10.0) - 273.15
                        if 10.0 <= celsius <= 110.0:
                            return {
                                "temperature": round(celsius, 1),
                                "source": "REAL (Windows ACPI WMI)",
                                "is_simulated": False
                            }
            except Exception:
                pass

        # Fallback if host hardware does not expose ACPI Thermal Zone
        return {
            "temperature": None,
            "source": "Temperature Sensor Unavailable Through OS Interface",
            "is_simulated": False
        }

    def enable_demo_temperature(self, state="NORMAL"):
        """Enable simulated demo temperature mode for presentation."""
        self.demo_mode = True
        self.demo_state = state.upper()

    def disable_demo_temperature(self):
        """Disable demo temperature simulation mode."""
        self.demo_mode = False

    def _get_demo_temperature(self):
        import random
        if self.demo_state == "HIGH":
            temp = round(68.5 + random.uniform(-2.0, 3.0), 1)
        elif self.demo_state == "CRITICAL":
            temp = round(86.2 + random.uniform(-2.0, 4.0), 1)
        else:
            temp = round(45.0 + random.uniform(-1.5, 2.0), 1)

        return {
            "temperature": temp,
            "source": "SIMULATED (Demo Temperature Mode)",
            "is_simulated": True
        }
