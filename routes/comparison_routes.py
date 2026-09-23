"""
Flask REST API Route Blueprint for Live Algorithm Comparison.
Exposes GET /api/model-comparison returning cached evaluation benchmark results.
"""
import os
import sys
from flask import Blueprint, jsonify

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

comparison_bp = Blueprint("comparison_api", __name__)
comparison_service_instance = None

def init_comparison_routes(service):
    """Bind global comparison service reference."""
    global comparison_service_instance
    comparison_service_instance = service

@comparison_bp.route("/api/model-comparison", methods=["GET"])
def get_model_comparison():
    """Retrieve cached live 3-algorithm comparison metrics."""
    if not comparison_service_instance:
        return jsonify({
            "status": "error",
            "message": "Comparison service reference not bound"
        }), 500

    result = comparison_service_instance.get_latest_comparison()
    return jsonify(result), 200
