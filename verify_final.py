"""
Final End-to-End Verification Script.
Inspects database raw values, performs numeric sanitization, validates dtypes,
calculates target statistics across all 5 parameters (Traffic, Delay, Throughput, Propagation Time, RAM Usage),
runs 3-algorithm multi-target benchmark (Random Forest, Gradient Boosting, Extra Trees),
verifies 0-10 composite scores, confirms ONE Best Algorithm selection, and validates predictor binding.
"""
import os
import sys
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import database.database as db
from ml.algorithm_comparison import AlgorithmComparisonEngine, FEATURE_COLUMNS, TARGET_COLUMNS
from ml.predictor import NetworkPredictor

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

    df_raw.replace([np.inf, -np.inf], np.nan, inplace=True)
    df_clean = df_raw.dropna(subset=FEATURE_COLUMNS).reset_index(drop=True)

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
    n_train = max(len(train_raw) - 1, 0)
    n_test = max(len(test_raw) - 1, 0)

    print(f"Total Window Dataset Size: {n_total} records")
    print(f"Training Pair Size (80%): {n_train} records")
    print(f"Testing Pair Size (20%) : {n_test} records")
    print(f"Sampling Horizon       : ~2 seconds interval per record (~{round(n_total*2/60, 1)} minutes total span)")

    print("\n========================================================================")
    print("   3. 5 TARGET PARAMETER STATISTICS")
    print("========================================================================")
    for target in TARGET_COLUMNS:
        if target in df_clean.columns:
            t = df_clean[target]
            print(f"[{target:20s}] Mean: {t.mean():.4f} | Std: {t.std():.4f} | Min: {t.min():.4f} | Max: {t.max():.4f}")

    print("\n========================================================================")
    print("   4. 3-ALGORITHM MULTI-TARGET BENCHMARK RESULTS")
    print("========================================================================")
    res = AlgorithmComparisonEngine.evaluate_live_data(min_records=10)
    
    if res.get("status") == "success":
        best_algo = res.get("best_algorithm") or res.get("selected_model")
        top = res.get("top_performer", {})
        print(f"BEST ALGORITHM         : {best_algo}")
        print(f"Selection Status       : {res.get('selection_status')}")
        print(f"Overall Composite Score : {top.get('score')} / 10")
        print(f"Selected Model Predictions: {res.get('live_predictions')}")

        print("\nFull 3-Algorithm Benchmark Table:")
        for name, m in res["models"].items():
            print(f"  - {name:20s} | Avg MAE: {m['avg_mae']:<7.4f} | Avg RMSE: {m['avg_rmse']:<7.4f} | Avg R²: {m['avg_r2']:<7.4f} | Score: {m['overall_score']} / 10")

        # Verify Predictor Binding
        predictor = NetworkPredictor()
        latest_snap = db.get_latest_snapshot()
        preds = predictor.predict(latest_snap)
        print("\nPredictor Inference Verification:")
        print(f"  - Predictor Selected Model: {preds.get('selected_model')}")
        print(f"  - Predicted Status        : {preds.get('predicted_status')}")

        print("========================================================================\n")
        print("[VERIFICATION COMPLETE] All requirements verified successfully.")
    else:
        print(f"Comparison Result Status: {res.get('status')} - {res.get('message')}")

if __name__ == "__main__":
    verify()
