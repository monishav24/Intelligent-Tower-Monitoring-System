"""
Flask REST API Route Blueprint for Live 3-Algorithm ML Comparison, Performance, Predictions, and Retraining.
Exposes:
- GET /api/model-comparison & GET /api/ml/comparison
- GET /api/ml/performance
- GET /api/ml/predictions
- GET /api/ml/active-model
- POST /api/ml/retrain
"""
import os
import sys
from flask import Blueprint, jsonify, request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ml.algorithm_comparison import AlgorithmComparisonEngine

comparison_bp = Blueprint("comparison_api", __name__)
comparison_service_instance = None

def init_comparison_routes(service):
    """Bind global comparison service reference."""
    global comparison_service_instance
    comparison_service_instance = service

@comparison_bp.route("/api/model-comparison", methods=["GET"])
@comparison_bp.route("/api/ml/comparison", methods=["GET"])
def get_model_comparison():
    """Retrieve cached live 3-algorithm comparison metrics, status, and scores."""
    if not comparison_service_instance:
        return jsonify({
            "status": "error",
            "message": "Comparison service reference not bound"
        }), 500

    result = comparison_service_instance.get_latest_comparison()
    return jsonify(result), 200

@comparison_bp.route("/api/ml/performance", methods=["GET"])
def get_model_performance():
    """Retrieve per-target MAE, RMSE, R², and overall score for all 3 models."""
    if not comparison_service_instance:
        return jsonify({"status": "error", "message": "Comparison service reference not bound"}), 500

    res = comparison_service_instance.get_latest_comparison()
    if res.get("status") != "success":
        return jsonify(res), 200

    models_data = res.get("models", {})
    performance_breakdown = {}
    for algo, info in models_data.items():
        score_val = info.get("overall_score", 0)
        performance_breakdown[algo] = {
            "overall_score": score_val,
            "composite_score": score_val,
            "score_scale": 10,
            "avg_mae": info.get("avg_mae", 0),
            "avg_rmse": info.get("avg_rmse", 0),
            "avg_r2": info.get("avg_r2", 0),
            "train_time_sec": info.get("train_time_sec", 0),
            "execution_status": "✓ Executed",
            "targets": info.get("targets", {})
        }

    return jsonify({
        "status": "success",
        "active_model": res.get("active_model"),
        "score_scale": 10,
        "performance": performance_breakdown
    }), 200

@comparison_bp.route("/api/ml/predictions", methods=["GET"])
def get_all_model_predictions():
    """Retrieve predictions for all 5 parameters from all 3 algorithms."""
    if not comparison_service_instance:
        return jsonify({"status": "error", "message": "Comparison service reference not bound"}), 500

    res = comparison_service_instance.get_latest_comparison()
    if res.get("status") != "success":
        return jsonify(res), 200

    models_data = res.get("models", {})
    predictions_by_model = {}
    for algo, info in models_data.items():
        predictions_by_model[algo] = info.get("live_predictions", {})

    return jsonify({
        "status": "success",
        "active_model": res.get("active_model"),
        "active_model_predictions": res.get("live_predictions", {}),
        "all_model_predictions": predictions_by_model
    }), 200

@comparison_bp.route("/api/ml/active-model", methods=["GET"])
def get_active_model_info():
    """Retrieve dynamically selected winning model and its overall score."""
    if not comparison_service_instance:
        return jsonify({"status": "error", "message": "Comparison service reference not bound"}), 500

    res = comparison_service_instance.get_latest_comparison()
    active_model = res.get("active_model", "Random Forest")
    top_info = res.get("top_performer", {})
    score_val = top_info.get("score", 0)

    return jsonify({
        "status": "success",
        "model": active_model,
        "active_model": active_model,
        "score": score_val,
        "composite_score": score_val,
        "score_scale": 10,
        "status_badge": "ACTIVE"
    }), 200

@comparison_bp.route("/api/ml/retrain", methods=["POST", "GET"])
def retrain_models():
    """Trigger manual retraining of ALL 3 algorithms on live SQLite dataset and update winner."""
    try:
        result = AlgorithmComparisonEngine.evaluate_live_data(min_records=10)
        if comparison_service_instance:
            with comparison_service_instance._lock:
                comparison_service_instance.latest_result = result

        return jsonify({
            "status": "success",
            "message": "All 3 algorithms (Random Forest, Gradient Boosting, Extra Trees) retrained and evaluated successfully",
            "data": result
        }), 200
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Retraining failed: {str(e)}"
        }), 500
