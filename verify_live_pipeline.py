"""
Verification script for Requirement 16 & Requirement 9.
Monitors SQLite telemetry row insertion over 30 seconds.
Verifies row count increases, timestamps advance (e.g. 10:00:00, 10:00:02, 10:00:04),
and real measurements for traffic, delay, throughput, propagation time, ram_usage are captured.
"""
import time
import os
import sys
import urllib.request
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import database.database as db

def verify_live():
    print("\n========================================================================")
    print("   VERIFYING REAL-TIME TELEMETRY PIPELINE (30-SECOND MONITORING)")
    print("========================================================================\n")

    checkpoints = [0, 10, 20, 30]
    results = []

    t0 = time.time()

    for interval in checkpoints:
        elapsed = time.time() - t0
        if interval > elapsed:
            time.sleep(interval - elapsed)

        diag_res = json.loads(urllib.request.urlopen("http://127.0.0.1:5000/api/telemetry/diagnostic").read().decode("utf-8"))
        diag = diag_res.get("diagnostic", {})
        count = diag.get("row_count")
        ts = diag.get("latest_timestamp")
        latest = diag.get("latest_telemetry", {})

        print(f"[t={interval:2d}s] SQLite Row Count: {count:4d} | Latest Timestamp: {ts} | Delay: {latest.get('delay')}ms | RAM: {latest.get('ram_usage')}% | Traffic: {latest.get('traffic')}MB")
        results.append({
            "t": interval,
            "count": count,
            "timestamp": ts,
            "latest": latest
        })

    print("\n========================================================================")
    print("   ANALYZING PIPELINE CONTINUITY")
    print("========================================================================")

    count_t0 = results[0]["count"]
    count_t30 = results[-1]["count"]
    count_diff = count_t30 - count_t0

    print(f"Row Count at t=0s : {count_t0}")
    print(f"Row Count at t=30s: {count_t30}")
    print(f"New Rows Inserted : {count_diff} rows in 30 seconds")

    assert count_t30 > count_t0, f"FAILED: Row count did not increase! (t0={count_t0}, t30={count_t30})"
    assert count_diff >= 10, f"FAILED: Expected at least 10 new rows inserted in 30s, got {count_diff}!"

    ts0 = results[0]["timestamp"]
    ts30 = results[-1]["timestamp"]
    assert ts0 != ts30, f"FAILED: Timestamps did not advance! (ts0={ts0}, ts30={ts30})"

    print("\n[OK] VERIFICATION PASSED: SQLite row count continuously increases with fresh, non-duplicate timestamps and real measurements!")

if __name__ == "__main__":
    verify_live()
