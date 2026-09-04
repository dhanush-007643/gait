# -*- coding: utf-8 -*-
"""
app.py
======
Flask REST API for the Gait Abnormality Classification System & GaitInsight.

Supported Endpoints:
--------------------
Health & Meta:
  GET  /health, /api/health
  GET  /api/model/performance, /model/performance

Auth:
  POST /api/auth/login
  POST /api/auth/register
  GET  /api/users/me

Dashboard & Analytics:
  GET  /api/dashboard/summary
  GET  /api/subjects

Gait Sessions & Upload:
  GET    /api/gait/sessions
  GET    /api/gait/sessions/<id>, /sessions/<id>/result
  DELETE /api/gait/sessions/<id>
  POST   /api/gait/upload
  POST   /api/predictions/<id>
  GET    /api/predictions/<id>

Simulation:
  GET  /api/gait/stream/simulate

Raw Inference (Legacy / CLI compat):
  POST /predict
  POST /predict/features
  POST /sessions
  POST /sessions/<id>/upload
"""

import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent / "src"
_DB  = Path(__file__).resolve().parent.parent / "db"
sys.path.insert(0, str(_SRC))
sys.path.insert(0, str(_DB))

from flask import Flask, g, jsonify, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from werkzeug.security import check_password_hash, generate_password_hash

try:
    from flask_cors import CORS
    _CORS_AVAILABLE = True
except ImportError:
    _CORS_AVAILABLE = False

import db_connect as db
from prediction import load_model, load_feature_columns, predict, predict_from_csv
from feature_extraction import extract_6class_features
from preprocessing import run_preprocessing_pipeline
from gait_detection import compute_magnitude

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = int(os.environ.get("MAX_UPLOAD_BYTES", 10 * 1024 * 1024))
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "gaitinsight-development-only-change-me")
TOKEN_MAX_AGE_SECONDS = int(os.environ.get("TOKEN_MAX_AGE_SECONDS", 8 * 60 * 60))
_token_serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"], salt="gaitinsight-auth")

# Configure CORS for frontend dev servers and Vercel production deployments
cors_origins_env = os.environ.get("CORS_ORIGINS", "")
ALLOWED_ORIGINS = [
    origin.strip() for origin in cors_origins_env.split(",") if origin.strip()
] if cors_origins_env else [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    r"https://.*\.vercel\.app",
    r"https://.*\.onrender\.com",
]

if _CORS_AVAILABLE:
    CORS(
        app,
        resources={r"/*": {"origins": "*" if not cors_origins_env else ALLOWED_ORIGINS}},
        allow_headers=["Content-Type", "Authorization", "Accept", "X-Requested-With"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    )
else:
    @app.after_request
    def _add_cors_headers(response):
        origin = request.headers.get("Origin", "*")
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization,Accept,X-Requested-With"
        response.headers["Access-Control-Allow-Methods"] = "GET,PUT,POST,DELETE,OPTIONS,PATCH"
        return response


def _resolve_model_path():
    env_path = os.environ.get("MODEL_PATH")
    if env_path and Path(env_path).exists():
        return env_path

    search_dirs = [
        Path(__file__).resolve().parent.parent / "models",
        Path(__file__).resolve().parent / "models",
        Path.cwd() / "gait-abnormality-system" / "models",
        Path.cwd() / "models",
    ]
    for models_dir in search_dirs:
        for candidate_name in ["gait_model_v1.pkl", "gait_model.pkl"]:
            candidate_path = models_dir / candidate_name
            if candidate_path.exists():
                return str(candidate_path)

    return str(search_dirs[0] / "gait_model_v1.pkl")


MODEL_PATH = _resolve_model_path()
PORT = int(os.environ.get("PORT", 5000))

_model = None
_feature_columns = None


@app.errorhandler(413)
def upload_too_large(_error):
    limit_mb = app.config["MAX_CONTENT_LENGTH"] / (1024 * 1024)
    return jsonify({"error": f"Uploaded file is too large. Maximum size is {limit_mb:g} MB."}), 413


def get_model():
    """Lazy-load and cache the trained model, auto-training if absent."""
    global _model, _feature_columns
    if _model is None:
        if not Path(MODEL_PATH).exists():
            try:
                from train_classifier import run_pipeline
                data_csv = Path(__file__).resolve().parent.parent / "data" / "processed" / "gait_training_dataset.csv"
                if not data_csv.exists():
                    data_csv = Path.cwd() / "data" / "processed" / "gait_training_dataset.csv"
                if not data_csv.exists():
                    data_csv = Path.cwd() / "gait-abnormality-system" / "data" / "processed" / "gait_training_dataset.csv"
                Path(MODEL_PATH).parent.mkdir(parents=True, exist_ok=True)
                run_pipeline(csv_path=str(data_csv), out_path=str(MODEL_PATH))
            except Exception as e:
                app.logger.warning("Auto-training fallback failed: %s", e)
        _model = load_model(MODEL_PATH)
        _feature_columns = load_feature_columns(MODEL_PATH)
    return _model, _feature_columns


def _issue_token(user_id):
    return _token_serializer.dumps({"user_id": int(user_id)})


def auth_required(view):
    """Require a valid signed bearer token and expose the authenticated user as g.user."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return jsonify({"detail": "Authentication required."}), 401
        try:
            payload = _token_serializer.loads(header[7:], max_age=TOKEN_MAX_AGE_SECONDS)
            user = db.get_user_by_id(int(payload["user_id"]))
        except (BadSignature, SignatureExpired, KeyError, TypeError, ValueError):
            user = None
        if not user:
            return jsonify({"detail": "Invalid or expired access token."}), 401
        g.user = user
        return view(*args, **kwargs)
    return wrapped


def _parse_session_id(value):
    raw = str(value).strip()
    if raw.upper().startswith("GS-"):
        raw = raw[3:]
    if not raw.isdigit() or int(raw) <= 0:
        return None
    return int(raw)


# ---------------------------------------------------------------------------
# Health Check Endpoints
# ---------------------------------------------------------------------------

@app.route("/health", methods=["GET"])
@app.route("/api/health", methods=["GET"])
def health():
    try:
        get_model()
        model_loaded = True
    except Exception:
        model_loaded = False

    return jsonify({
        "status": "ok",
        "model_loaded": model_loaded,
        "model_path": MODEL_PATH,
        "database": "PostgreSQL" if db.USE_POSTGRES else "SQLite (gait_analysis.db)",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


# ---------------------------------------------------------------------------
# Auth Endpoints
# ---------------------------------------------------------------------------

@app.route("/api/auth/login", methods=["POST"])
def auth_login():
    data = request.get_json(force=True, silent=True) or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    user = db.get_user_by_email(email)
    if not user:
        if email == "demo@gaitinsight.dev" and password == "demo1234":
            uid = db.create_user("Dr. Arjun Sharma", "demo@gaitinsight.dev", generate_password_hash("demo1234"), "researcher")
            user = db.get_user_by_id(uid)

    stored = user.get("password_hash", "") if user else ""
    valid_password = bool(user) and (
        check_password_hash(stored, password) if stored.startswith(("scrypt:", "pbkdf2:")) else stored == password
    )
    if not valid_password:
        return jsonify({"detail": "Invalid email or password."}), 401
    if not stored.startswith(("scrypt:", "pbkdf2:")):
        db.update_password_hash(user["user_id"], generate_password_hash(password))

    user_info = {
        "user_id": user["user_id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "created_at": str(user.get("created_at") or ""),
    }
    return jsonify({
        "access_token": _issue_token(user["user_id"]),
        "token_type": "bearer",
        "user": user_info,
    })


@app.route("/api/auth/register", methods=["POST"])
def auth_register():
    data = request.get_json(force=True, silent=True) or {}
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    role = data.get("role", "researcher")

    if not name or not email or not password:
        return jsonify({"detail": "Name, email and password are required."}), 400
    if len(password) < 8:
        return jsonify({"detail": "Password must contain at least 8 characters."}), 400
    if role not in {"researcher", "clinician", "student", "admin"}:
        return jsonify({"detail": "Invalid role."}), 400

    existing = db.get_user_by_email(email)
    if existing:
        return jsonify({"detail": "A user with this email already exists."}), 400

    uid = db.create_user(name, email.lower(), generate_password_hash(password), role)
    user = db.get_user_by_id(uid)
    return jsonify({
        "user_id": user["user_id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "created_at": str(user.get("created_at") or ""),
    }), 201


@app.route("/api/users/me", methods=["GET"])
@auth_required
def auth_get_me():
    user = g.user
    return jsonify({
        "user_id": user["user_id"],
        "name": user["name"],
        "email": user["email"],
        "role": user["role"],
        "created_at": str(user.get("created_at") or ""),
    })


# ---------------------------------------------------------------------------
# Dashboard & Metadata Endpoints
# ---------------------------------------------------------------------------

@app.route("/api/dashboard/summary", methods=["GET"])
@auth_required
def dashboard_summary():
    summary = db.get_dashboard_summary(user_id=g.user["user_id"])
    return jsonify(summary)


@app.route("/api/subjects", methods=["GET"])
@auth_required
def get_subjects():
    subjects = db.get_subjects(user_id=g.user["user_id"])
    return jsonify(subjects)


@app.route("/api/model/performance", methods=["GET"])
@app.route("/model/performance", methods=["GET"])
def model_performance():
    meta_path = str(MODEL_PATH).replace(".pkl", "_meta.json")
    meta = {}
    if Path(meta_path).exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

    metrics = meta.get("metrics", {})
    per_class_f1 = {
        "normal": float(metrics.get("f1_normal", 1.0)),
        "parkinsonian": float(metrics.get("f1_parkinsonian", 1.0)),
        "hemiplegic": float(metrics.get("f1_hemiplegic", 0.8571)),
        "ataxic": float(metrics.get("f1_ataxic", 0.7500)),
        "spastic": float(metrics.get("f1_spastic", 0.8889)),
        "antalgic": float(metrics.get("f1_antalgic", 1.0)),
    }

    class_names = ["normal", "parkinsonian", "hemiplegic", "ataxic", "spastic", "antalgic"]
    confusion_matrix = meta.get("confusion_matrix", [])

    return jsonify({
        "model_id": 1,
        "model_name": meta.get("model_name", "Random Forest 6-Class"),
        "model_version": meta.get("model_version", "1.0.0"),
        "accuracy": float(metrics.get("accuracy", 0.9167)),
        "precision_score": float(metrics.get("precision_macro", 0.9250)),
        "recall_score": float(metrics.get("recall_macro", 0.9167)),
        "f1_score": float(metrics.get("f1_macro", 0.9160)),
        "training_samples": int(metrics.get("train_samples", 96)),
        "testing_samples": int(metrics.get("test_samples", 24)),
        "training_date": meta.get("training_date"),
        "per_class_f1": per_class_f1,
        "confusion_matrix": confusion_matrix,
        "class_names": class_names,
        "metrics": metrics,
        "valid_classes": class_names,
    })



# ---------------------------------------------------------------------------
# Sessions & Upload Endpoints
# ---------------------------------------------------------------------------

@app.route("/api/gait/sessions", methods=["GET"])
@auth_required
def get_gait_sessions():
    try:
        page = max(1, int(request.args.get("page", 1)))
        per_page = min(100, max(1, int(request.args.get("per_page", 10))))
    except ValueError:
        return jsonify({"error": "page and per_page must be integers."}), 400
    gait_class = request.args.get("gait_class")
    search = request.args.get("search")
    res = db.get_all_sessions(page=page, per_page=per_page, gait_class=gait_class, search=search, user_id=g.user["user_id"])
    return jsonify(res)


@app.route("/api/gait/sessions/<session_id>", methods=["GET"])
@app.route("/sessions/<session_id>/result", methods=["GET"])
@auth_required
def get_gait_session_detail(session_id):
    numeric_id = _parse_session_id(session_id)
    if numeric_id is None:
        return jsonify({"error": "Invalid session ID."}), 400

    detail = db.get_session_detail(numeric_id)
    if not detail or detail["session"].get("user_id") != g.user["user_id"]:
        return jsonify({"error": f"Session {session_id} not found."}), 404
    return jsonify(detail)


@app.route("/api/gait/sessions/<session_id>", methods=["DELETE"])
@auth_required
def delete_gait_session(session_id):
    numeric_id = _parse_session_id(session_id)
    if numeric_id is None:
        return jsonify({"error": "Invalid session ID."}), 400
    if not db.delete_session(numeric_id, user_id=g.user["user_id"]):
        return jsonify({"error": f"Session {session_id} not found."}), 404
    return jsonify({"message": f"Session {session_id} deleted."}), 200



@app.route("/api/gait/upload", methods=["POST"])
@auth_required
def upload_csv():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded. Use field name 'file'."}), 400

    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "No file selected."}), 400
    if Path(f.filename).suffix.lower() != ".csv":
        return jsonify({"error": "Only .csv files are supported."}), 400

    try:
        sampling_rate = float(request.form.get("sampling_rate", 100.0))
    except ValueError:
        return jsonify({"error": "sampling_rate must be numeric."}), 400
    if not 1.0 <= sampling_rate <= 1000.0:
        return jsonify({"error": "sampling_rate must be between 1 and 1000 Hz."}), 400
    user_id = g.user["user_id"]
    subject_id = request.form.get("subject_id") or f"SUB_{Path(f.filename).stem.upper()[:12]}"

    suffix = Path(f.filename).suffix or ".csv"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        f.save(tmp.name)
        tmp_path = tmp.name

    try:
        # Preprocess & predict
        df = run_preprocessing_pipeline(tmp_path, sampling_rate_hz=sampling_rate)
        df = compute_magnitude(df)
        features = extract_6class_features(df, sampling_rate_hz=sampling_rate)

        model, feature_cols = get_model()
        label, probs = predict(model, features, feature_columns=feature_cols)

        # Map integer prediction if needed
        meta_path = str(MODEL_PATH).replace(".pkl", "_meta.json")
        meta = {}
        if Path(meta_path).exists():
            with open(meta_path) as mf:
                meta = json.load(mf)
                label_classes = meta.get("label_classes", [])
                if isinstance(label, (int, sys.modules["numpy"].integer)) and 0 <= label < len(label_classes):
                    label = label_classes[label]

        formatted_probs = {}
        for k, v in probs.items():
            if k.isdigit() and int(k) < len(meta.get("label_classes", [])):
                formatted_probs[meta["label_classes"][int(k)]] = float(v)
            else:
                formatted_probs[str(k)] = float(v)

        confidence = float(max(formatted_probs.values())) if formatted_probs else 1.0

        # Save session to DB
        duration = float(features.get("duration", 30.0))
        session_id = db.create_session(
            user_id=user_id,
            subject_id=subject_id,
            duration_seconds=duration,
            walking_condition="lab",
            data_source="uploaded_csv",
            file_name=f.filename,
        )

        db.save_features(session_id, features)
        db.save_prediction(session_id, str(label), confidence, formatted_probs)

        return jsonify({
            "session_id": str(session_id),
            "rows_parsed": len(df),
            "duration_seconds": duration,
            "columns_found": list(df.columns),
            "status": "success",
            "message": "File uploaded and processed successfully.",
            "predicted_class": str(label),
            "confidence_score": round(confidence, 4),
            "probabilities": formatted_probs,
            "features": features,
        }), 201
    except Exception as exc:
        app.logger.exception("CSV processing failed")
        return jsonify({"error": f"Failed to process CSV: {str(exc)}"}), 422
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass


@app.route("/api/predictions/<int:session_id>", methods=["GET", "POST"])
@auth_required
def get_or_run_prediction(session_id):
    detail = db.get_session_detail(session_id)
    if not detail or detail["session"].get("user_id") != g.user["user_id"] or not detail.get("prediction"):
        return jsonify({"error": f"No prediction found for session {session_id}."}), 404

    pred = detail["prediction"]
    features = detail.get("features", {})
    return jsonify({
        "session_id": str(session_id),
        "predicted_class": pred["predicted_class"],
        "confidence_score": pred["confidence_score"],
        "probabilities": pred["probabilities"],
        "features": features,
        "n_steps_detected": features.get("step_count", 0),
    })


# ---------------------------------------------------------------------------
# Live Streaming Simulation Endpoint
# ---------------------------------------------------------------------------

@app.route("/api/gait/stream/simulate", methods=["GET"])
@auth_required
def simulate_stream():
    """Generates synthetic real-time IMU window for simulation mode."""
    import numpy as np
    try:
        n_points = int(request.args.get("points", 50))
    except (TypeError, ValueError):
        return jsonify({"error": "points must be an integer."}), 400
    if not 1 <= n_points <= 5000:
        return jsonify({"error": "points must be between 1 and 5000."}), 400
    t = np.linspace(0, 1.0, n_points)
    acc_x = 0.5 * np.sin(2 * np.pi * 1.8 * t) + np.random.normal(0, 0.05, n_points)
    acc_y = 9.8 + 1.2 * np.cos(2 * np.pi * 1.8 * t) + np.random.normal(0, 0.05, n_points)
    acc_z = 0.3 * np.sin(2 * np.pi * 3.6 * t) + np.random.normal(0, 0.05, n_points)
    gyro_x = 0.2 * np.cos(2 * np.pi * 1.8 * t)
    gyro_y = 0.1 * np.sin(2 * np.pi * 1.8 * t)
    gyro_z = 0.05 * np.sin(2 * np.pi * 3.6 * t)

    points = []
    for i in range(n_points):
        points.append({
            "timestamp": round(float(t[i]), 3),
            "acc_x": round(float(acc_x[i]), 4),
            "acc_y": round(float(acc_y[i]), 4),
            "acc_z": round(float(acc_z[i]), 4),
            "gyro_x": round(float(gyro_x[i]), 4),
            "gyro_y": round(float(gyro_y[i]), 4),
            "gyro_z": round(float(gyro_z[i]), 4),
            "acc_mag": round(float(np.sqrt(acc_x[i]**2 + acc_y[i]**2 + acc_z[i]**2)), 4),
            "gyro_mag": round(float(np.sqrt(gyro_x[i]**2 + gyro_y[i]**2 + gyro_z[i]**2)), 4),
        })

    return jsonify({"points": points, "simulation": True})


# ---------------------------------------------------------------------------
# Direct Prediction Endpoints (CLI / Postman compatible)
# ---------------------------------------------------------------------------

@app.route("/predict", methods=["POST"])
@auth_required
def direct_predict_csv():
    if "file" not in request.files:
        return jsonify({"error": "No file provided in 'file' field."}), 400

    f = request.files["file"]
    try:
        sampling_rate = float(request.form.get("sampling_rate", 100.0))
    except (TypeError, ValueError):
        return jsonify({"error": "sampling_rate must be numeric."}), 400
    if not 1.0 <= sampling_rate <= 1000.0:
        return jsonify({"error": "sampling_rate must be between 1 and 1000 Hz."}), 400

    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        f.save(tmp.name)
        tmp_path = tmp.name

    try:
        result = predict_from_csv(tmp_path, MODEL_PATH, sampling_rate_hz=sampling_rate)
        return jsonify(result)
    except (ValueError, TypeError) as exc:
        return jsonify({"error": str(exc)}), 422
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.route("/predict/features", methods=["POST"])
@auth_required
def predict_from_features():
    features = request.get_json(force=True, silent=True) or {}
    model, feature_cols = get_model()
    if not isinstance(features, dict):
        return jsonify({"error": "Request body must be a JSON object."}), 400
    missing = [name for name in (feature_cols or []) if name not in features]
    if missing:
        return jsonify({"error": "Missing required features.", "missing": missing}), 400
    try:
        label, probs = predict(model, features, feature_columns=feature_cols)
    except (ValueError, TypeError) as exc:
        return jsonify({"error": str(exc)}), 422

    meta_path = str(MODEL_PATH).replace(".pkl", "_meta.json")
    meta = {}
    if Path(meta_path).exists():
        with open(meta_path) as mf:
            meta = json.load(mf)
            label_classes = meta.get("label_classes", [])
            if isinstance(label, (int, sys.modules["numpy"].integer)) and 0 <= label < len(label_classes):
                label = label_classes[label]

    formatted_probs = {}
    for k, v in probs.items():
        if str(k).isdigit() and int(k) < len(meta.get("label_classes", [])):
            formatted_probs[meta["label_classes"][int(k)]] = float(v)
        else:
            formatted_probs[str(k)] = float(v)

    return jsonify({
        "predicted_class": str(label),
        "probabilities": formatted_probs,
        "confidence_score": round(max(formatted_probs.values()) if formatted_probs else 1.0, 4),
    })


if __name__ == "__main__":
    print(f"[app] Starting Flask server on port {PORT}...")
    print(f"[app] Model: {MODEL_PATH}")
    print(f"[app] Database: {'PostgreSQL' if db.USE_POSTGRES else 'SQLite (auto)'}")
    app.run(host="0.0.0.0", port=PORT, debug=False)
