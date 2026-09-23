"""
Final End-to-End Verification Script.
Inspects database raw values, performs numeric sanitization, validates dtypes,
calculates target statistics, runs 3-model comparison + naive persistence baseline,
and prints all required diagnostic summaries.
"""
import os
import sys
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import database.database as db
from ml.algorithm_comparison import AlgorithmComparisonEngine, FEATURE_COLUMNS

def verify():
    db.init_db()
    raw_history = db.get_history(limit=200)
    df_raw = pd.DataFrame(raw_history)

    print("========================================================================")
    print("   1. FEATURE DTYPES & SANITIZATION")
    print("========================================================================")
    for col in FEATURE_COLUMNS:
        if col not in df_raw.columns:
            df_raw[col] = 0.0
        df_raw[col] = pd.to_numeric(df_raw[col], errors="coerce")

    if df_raw["system_temperature"].isna().all():
        df_raw["system_temperature"] = 40.0
    else:
        df_raw["system_temperature"] = df_raw["system_temperature"].fillna(40.0)

    df_raw.replace([np.inf, -np.inf], np.nan, inplace=True)
    df_clean = df_raw.dropna(subset=FEATURE_COLUMNS + ["bandwidth_utilization"]).reset_index(drop=True)

    print(df_clean[FEATURE_COLUMNS].dtypes)
    all_numeric = all(pd.api.types.is_numeric_dtype(df_clean[c]) for c in FEATURE_COLUMNS)
    print(f"\nAll feature columns strictly numeric: {all_numeric}")

    print("\n========================================================================")
    print("   2. DATASET SIZE, TRAIN SIZE, TEST SIZE")
    print("========================================================================")
    n_total = len(df_clean)
    split_idx = int(n_total * 0.8)
    train_raw = df_clean.iloc[:split_idx]
    test_raw = df_clean.iloc[split_idx:]
    n_train = len(train_raw) - 1
    n_test = len(test_raw) - 1

    print(f"Total Window Dataset Size: {n_total} records")
    print(f"Training Pair Size (80%): {n_train} records")
    print(f"Testing Pair Size (20%) : {n_test} records")
    print(f"Sampling Horizon       : ~2 seconds interval per record (~{round(n_total*2/60, 1)} minutes total span)")

    print("\n========================================================================")
    print("   3. TARGET STATISTICS (bandwidth_utilization)")
    print("========================================================================")
    t = df_clean["bandwidth_utilization"]
    print(f"Mean : {t.mean():.4f} %")
    print(f"Std  : {t.std():.4f} %")
    print(f"Min  : {t.min():.4f} %")
    print(f"Max  : {t.max():.4f} %")
    print(f"Unique Target Values: {t.nunique()}")

    print("\n========================================================================")
    print("   4. MODEL RESULTS & BEST MODEL")
    print("========================================================================")
    res = AlgorithmComparisonEngine.evaluate_live_data(min_records=100)
    
    if res.get("status") == "success":
        best = res["best_model"]
        print(f"Best Model Selected : {best['algorithm']}")
        print(f"Best Model RMSE     : {best['rmse']}")
        print(f"Best Model MAE      : {best['mae']}")
        print(f"Best Model R^2      : {best['r2']}")
        print(f"Is Weak Fit (R^2<0) : {best['is_weak_fit']}")
        if best.get("performance_warning"):
            print(f"Warning Message     : {best['performance_warning']}")

        print("\nFull Model Metrics:")
        for name, m in res["models"].items():
            print(f"  - {name:20s} | MAE: {m['mae']:<7.4f} | RMSE: {m['rmse']:<7.4f} | R^2: {m['r2']:<7.4f} | Time: {m['train_time_sec']}s")

        print("\n========================================================================")
        print("   5. BASELINE RESULTS (Naive Persistence)")
        print("========================================================================")
        nb = res.get("naive_baseline", {})
        print(f"Name : {nb.get('name')}")
        print(f"MAE  : {nb.get('mae')}")
        print(f"RMSE : {nb.get('rmse')}")
        print(f"R^2  : {nb.get('r2')}")
        print("========================================================================\n")
    else:
        print(f"Comparison Result Status: {res.get('status')} - {res.get('message')}")

if __name__ == "__main__":
    verify()
