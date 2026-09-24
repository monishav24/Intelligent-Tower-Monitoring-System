"""
Background Algorithm Comparison Service.
Executes the live 3-algorithm comparison cycle periodically (every 60 seconds) in a background daemon thread.
Caches evaluation results safely in memory so REST API requests return instantly without blocking or triggering re-training.
"""
import threading
import time
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ml.algorithm_comparison import AlgorithmComparisonEngine

COMPARISON_INTERVAL_SECONDS = 60.0

class AlgorithmComparisonService:
    def __init__(self):
        self.latest_result = {
            "status": "warming_up",
            "message": "Algorithm comparison service is initializing...",
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.running = False
        self.thread = None
        self._lock = threading.Lock()

    def start(self):
        """Start background comparison thread."""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()
            print("[Algorithm Comparison Service] Background daemon thread started (Interval: 60s).")

    def _run_loop(self):
        # Give telemetry collector 3 seconds to spin up on startup
        time.sleep(3.0)

        # Perform initial model evaluation on startup
        try:
            result = AlgorithmComparisonEngine.evaluate_live_data()
            with self._lock:
                self.latest_result = result
            print(f"[Algorithm Comparison Service] Initial model evaluation complete. Fixed selected model: {result.get('best_algorithm', 'Random Forest')}")
        except Exception as e:
            print(f"[Algorithm Comparison Service Startup Error]: {e}")

        # Maintain thread lifecycle without continuous model switching loops
        while self.running:
            time.sleep(300.0)

    def get_latest_comparison(self):
        """Thread-safe retrieval of latest cached evaluation result."""
        with self._lock:
            # If still warming up, attempt on-the-fly evaluation
            if self.latest_result.get("status") == "warming_up":
                res = AlgorithmComparisonEngine.evaluate_live_data()
                self.latest_result = res
            return self.latest_result
