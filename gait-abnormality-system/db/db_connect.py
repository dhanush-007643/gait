# -*- coding: utf-8 -*-
"""
db_connect.py
=============
Database access layer for the Gait Abnormality Classification System.

Supports:
  1. PostgreSQL (default if PGHOST/PGPASSWORD configured and accessible)
  2. SQLite (automatic zero-config fallback; stores data in gait_analysis.db)

Public API:
  - init_db()
  - get_user_by_email(email)
  - create_user(name, email, password_hash, role)
  - get_user_by_id(user_id)
  - create_session(user_id, subject_id, duration_seconds, walking_condition, data_source, file_name)
  - save_features(session_id, features)
  - save_prediction(session_id, predicted_class, confidence_score, probabilities, model_version, model_name)
  - get_session_detail(session_id)
  - get_all_sessions(page=1, per_page=10, gait_class=None, search=None)
  - get_dashboard_summary()
  - get_subjects()
  - delete_session(session_id)
"""

import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Try psycopg2
try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

DATABASE_URL = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

DB_CONFIG = {
    "host":     os.environ.get("PGHOST",     "localhost"),
    "port":     int(os.environ.get("PGPORT", "5432")),
    "dbname":   os.environ.get("PGDATABASE", "gait_db"),
    "user":     os.environ.get("PGUSER",     "postgres"),
    "password": os.environ.get("PGPASSWORD", ""),
}

_DB_DIR = Path(__file__).resolve().parent

def _resolve_sqlite_path() -> Path:
    env_path = os.environ.get("SQLITE_DB_PATH")
    if env_path:
        return Path(env_path)
    candidates = [
        _DB_DIR.parent.parent / "gait_analysis.db",
        _DB_DIR.parent / "gait_analysis.db",
        _DB_DIR / "gait_analysis.db",
        Path.cwd() / "gait_analysis.db",
    ]
    for p in candidates:
        if p.exists():
            return p
    return candidates[0]

_DEFAULT_SQLITE_PATH = _resolve_sqlite_path()


def _is_postgres_available() -> bool:
    if not PSYCOPG2_AVAILABLE:
        return False
    if DATABASE_URL:
        try:
            conn = psycopg2.connect(DATABASE_URL, connect_timeout=3)
            conn.close()
            return True
        except Exception as e:
            logger.warning("PostgreSQL connection via DATABASE_URL failed: %s", e)
            return False
    if DB_CONFIG.get("password"):
        try:
            conn = psycopg2.connect(**DB_CONFIG, connect_timeout=3)
            conn.close()
            return True
        except Exception:
            return False
    return False


USE_POSTGRES = _is_postgres_available()


def get_sqlite_conn():
    conn = sqlite3.connect(str(_DEFAULT_SQLITE_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def get_connection():
    if USE_POSTGRES:
        if DATABASE_URL:
            return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
    return get_sqlite_conn()


def init_db():
    """Create all required tables in SQLite / PostgreSQL if they do not exist."""
    if USE_POSTGRES:
        schema_path = _DB_DIR / "schema.sql"
        if schema_path.exists():
            with open(schema_path, "r", encoding="utf-8") as f:
                ddl = f.read()
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(ddl)
                conn.commit()

        # Seed demo user in PostgreSQL if not present
        conn = get_connection()
        try:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM users")
            res = cur.fetchone()
            count = res["count"] if isinstance(res, dict) else (res[0] if res else 0)
            if count == 0:
                from werkzeug.security import generate_password_hash
                cur.execute("""
                INSERT INTO users (name, email, password_hash, role)
                VALUES (%s, %s, %s, %s)
                """, ("Dr. Arjun Sharma", "demo@gaitinsight.dev", generate_password_hash("demo1234"), "researcher"))
                conn.commit()
        finally:
            conn.close()
    else:
        # SQLite initialization
        conn = get_sqlite_conn()
        cur = conn.cursor()
        cur.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'researcher',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS gait_sessions (
            session_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(user_id),
            subject_id TEXT NOT NULL,
            recorded_at TEXT NOT NULL DEFAULT (datetime('now')),
            duration_seconds REAL,
            walking_condition TEXT DEFAULT 'indoor_flat',
            data_source TEXT NOT NULL DEFAULT 'uploaded_csv',
            file_name TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS sensor_data (
            sensor_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER REFERENCES gait_sessions(session_id) ON DELETE CASCADE,
            timestamp REAL,
            acc_x REAL, acc_y REAL, acc_z REAL,
            gyro_x REAL, gyro_y REAL, gyro_z REAL
        );

        CREATE TABLE IF NOT EXISTS gait_features (
            feature_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER UNIQUE REFERENCES gait_sessions(session_id) ON DELETE CASCADE,
            step_count INTEGER,
            cadence REAL,
            walking_speed REAL,
            step_length REAL,
            stride_length REAL,
            step_time REAL,
            stride_time REAL,
            stance_time REAL,
            swing_time REAL,
            gait_symmetry REAL,
            mean_acceleration REAL,
            acceleration_std REAL,
            acceleration_rms REAL,
            mean_gyroscope REAL,
            gyroscope_std REAL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS predictions (
            prediction_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER REFERENCES gait_sessions(session_id) ON DELETE CASCADE,
            predicted_class TEXT NOT NULL,
            confidence_score REAL NOT NULL,
            prob_normal REAL DEFAULT 0,
            prob_parkinsonian REAL DEFAULT 0,
            prob_hemiplegic REAL DEFAULT 0,
            prob_ataxic REAL DEFAULT 0,
            prob_spastic REAL DEFAULT 0,
            prob_antalgic REAL DEFAULT 0,
            model_version TEXT DEFAULT '1.0.0',
            model_name TEXT DEFAULT 'random_forest_baseline',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS model_performance (
            model_id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_name TEXT NOT NULL,
            model_version TEXT NOT NULL,
            evaluated_at TEXT NOT NULL DEFAULT (datetime('now')),
            dataset_name TEXT,
            train_samples INTEGER,
            test_samples INTEGER,
            accuracy REAL,
            precision_macro REAL,
            recall_macro REAL,
            f1_macro REAL,
            f1_normal REAL,
            f1_parkinsonian REAL,
            f1_hemiplegic REAL,
            f1_ataxic REAL,
            f1_spastic REAL,
            f1_antalgic REAL,
            confusion_matrix_json TEXT,
            notes TEXT
        );
        """)
        conn.commit()

        # Seed demo user if none exists
        cur.execute("SELECT COUNT(*) FROM users")
        if cur.fetchone()[0] == 0:
            cur.execute("""
            INSERT INTO users (name, email, password_hash, role)
            VALUES ('Dr. Arjun Sharma', 'demo@gaitinsight.dev', 'demo1234', 'researcher')
            """)
            conn.commit()
        conn.close()


# Initialize on import
init_db()


# ---------------------------------------------------------------------------
# User Helpers
# ---------------------------------------------------------------------------

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        if USE_POSTGRES:
            cur.execute("SELECT * FROM users WHERE email = %s", (email,))
            row = cur.fetchone()
            return dict(row) if row else None
        else:
            cur.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = cur.fetchone()
            return dict(row) if row else None
    finally:
        conn.close()


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        if USE_POSTGRES:
            cur.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
            row = cur.fetchone()
            return dict(row) if row else None
        else:
            cur.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cur.fetchone()
            return dict(row) if row else None
    finally:
        conn.close()


def create_user(name: str, email: str, password_hash: str, role: str = "researcher") -> int:
    conn = get_connection()
    try:
        cur = conn.cursor()
        if USE_POSTGRES:
            cur.execute("""
                INSERT INTO users (name, email, password_hash, role)
                VALUES (%s, %s, %s, %s) RETURNING user_id
            """, (name, email, password_hash, role))
            uid = cur.fetchone()[0]
            conn.commit()
            return uid
        else:
            cur.execute("""
                INSERT INTO users (name, email, password_hash, role)
                VALUES (?, ?, ?, ?)
            """, (name, email, password_hash, role))
            conn.commit()
            return cur.lastrowid
    finally:
        conn.close()


def update_password_hash(user_id: int, password_hash: str) -> None:
    """Replace a user's password hash (also used to migrate legacy demo data)."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        placeholder = "%s" if USE_POSTGRES else "?"
        cur.execute(
            f"UPDATE users SET password_hash = {placeholder} WHERE user_id = {placeholder}",
            (password_hash, user_id),
        )
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Session & Prediction Helpers
# ---------------------------------------------------------------------------

def create_session(user_id: int, subject_id: str, duration_seconds: float = 0.0,
                   walking_condition: str = "indoor_flat", data_source: str = "uploaded_csv",
                   file_name: Optional[str] = None) -> int:
    conn = get_connection()
    try:
        cur = conn.cursor()
        if USE_POSTGRES:
            cur.execute("""
                INSERT INTO gait_sessions
                    (user_id, subject_id, duration_seconds, walking_condition, data_source, file_name)
                VALUES (%s, %s, %s, %s, %s, %s) RETURNING session_id
            """, (user_id, subject_id, duration_seconds, walking_condition, data_source, file_name))
            sid = cur.fetchone()[0]
            conn.commit()
            return sid
        else:
            cur.execute("""
                INSERT INTO gait_sessions
                    (user_id, subject_id, duration_seconds, walking_condition, data_source, file_name)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, subject_id, duration_seconds, walking_condition, data_source, file_name))
            conn.commit()
            return cur.lastrowid
    finally:
        conn.close()


def save_features(session_id: int, features: Dict[str, Any]):
    conn = get_connection()
    try:
        cur = conn.cursor()
        params = (
            session_id,
            features.get("step_count", 0),
            features.get("cadence", 0.0),
            features.get("walking_speed", 0.0),
            features.get("step_length", 0.0),
            features.get("stride_length", 0.0),
            features.get("step_time", 0.0),
            features.get("stride_time", 0.0),
            features.get("stance_time", 0.0),
            features.get("swing_time", 0.0),
            features.get("gait_symmetry", 0.0),
            features.get("mean_acceleration", 0.0),
            features.get("acceleration_std", 0.0),
            features.get("acceleration_rms", 0.0),
            features.get("mean_gyroscope", 0.0),
            features.get("gyroscope_std", 0.0),
        )
        if USE_POSTGRES:
            cur.execute("""
                INSERT INTO gait_features
                    (session_id, step_count, cadence, walking_speed, step_length,
                     stride_length, step_time, stride_time, stance_time, swing_time,
                     gait_symmetry, mean_acceleration, acceleration_std, acceleration_rms,
                     mean_gyroscope, gyroscope_std)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (session_id) DO UPDATE SET
                    step_count = EXCLUDED.step_count,
                    cadence = EXCLUDED.cadence,
                    walking_speed = EXCLUDED.walking_speed,
                    step_length = EXCLUDED.step_length,
                    stride_length = EXCLUDED.stride_length,
                    step_time = EXCLUDED.step_time,
                    stride_time = EXCLUDED.stride_time,
                    stance_time = EXCLUDED.stance_time,
                    swing_time = EXCLUDED.swing_time,
                    gait_symmetry = EXCLUDED.gait_symmetry,
                    mean_acceleration = EXCLUDED.mean_acceleration,
                    acceleration_std = EXCLUDED.acceleration_std,
                    acceleration_rms = EXCLUDED.acceleration_rms,
                    mean_gyroscope = EXCLUDED.mean_gyroscope,
                    gyroscope_std = EXCLUDED.gyroscope_std
            """, params)
        else:
            cur.execute("""
                INSERT OR REPLACE INTO gait_features
                    (session_id, step_count, cadence, walking_speed, step_length,
                     stride_length, step_time, stride_time, stance_time, swing_time,
                     gait_symmetry, mean_acceleration, acceleration_std, acceleration_rms,
                     mean_gyroscope, gyroscope_std)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, params)
        conn.commit()
    finally:
        conn.close()


def save_prediction(session_id: int, predicted_class: str, confidence_score: float,
                    probabilities: Dict[str, float], model_version: str = "1.0.0",
                    model_name: str = "random_forest_baseline") -> int:
    conn = get_connection()
    try:
        cur = conn.cursor()
        params = (
            session_id,
            predicted_class,
            confidence_score,
            probabilities.get("normal", 0.0),
            probabilities.get("parkinsonian", 0.0),
            probabilities.get("hemiplegic", 0.0),
            probabilities.get("ataxic", 0.0),
            probabilities.get("spastic", 0.0),
            probabilities.get("antalgic", 0.0),
            model_version,
            model_name,
        )
        if USE_POSTGRES:
            cur.execute("""
                INSERT INTO predictions
                    (session_id, predicted_class, confidence_score,
                     prob_normal, prob_parkinsonian, prob_hemiplegic,
                     prob_ataxic, prob_spastic, prob_antalgic,
                     model_version, model_name)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING prediction_id
            """, params)
            pid = cur.fetchone()[0]
        else:
            cur.execute("""
                INSERT INTO predictions
                    (session_id, predicted_class, confidence_score,
                     prob_normal, prob_parkinsonian, prob_hemiplegic,
                     prob_ataxic, prob_spastic, prob_antalgic,
                     model_version, model_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, params)
            pid = cur.lastrowid
        conn.commit()
        return pid
    finally:
        conn.close()


def get_session_detail(session_id: int) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        sql = """
            SELECT
                s.session_id, s.user_id, s.subject_id, s.recorded_at, s.duration_seconds,
                s.walking_condition, s.data_source, s.file_name,
                f.step_count, f.cadence, f.walking_speed, f.step_length,
                f.stride_length, f.step_time, f.stride_time, f.stance_time,
                f.swing_time, f.gait_symmetry, f.mean_acceleration,
                f.acceleration_std, f.acceleration_rms, f.mean_gyroscope,
                f.gyroscope_std,
                p.prediction_id, p.predicted_class, p.confidence_score,
                p.prob_normal, p.prob_parkinsonian, p.prob_hemiplegic,
                p.prob_ataxic, p.prob_spastic, p.prob_antalgic,
                p.model_version, p.model_name
            FROM gait_sessions s
            LEFT JOIN gait_features f ON s.session_id = f.session_id
            LEFT JOIN (
                SELECT * FROM predictions
                WHERE session_id = ?
                ORDER BY created_at DESC LIMIT 1
            ) p ON s.session_id = p.session_id
            WHERE s.session_id = ?
        """ if not USE_POSTGRES else """
            SELECT
                s.session_id, s.user_id, s.subject_id, s.recorded_at, s.duration_seconds,
                s.walking_condition, s.data_source, s.file_name,
                f.step_count, f.cadence, f.walking_speed, f.step_length,
                f.stride_length, f.step_time, f.stride_time, f.stance_time,
                f.swing_time, f.gait_symmetry, f.mean_acceleration,
                f.acceleration_std, f.acceleration_rms, f.mean_gyroscope,
                f.gyroscope_std,
                p.prediction_id, p.predicted_class, p.confidence_score,
                p.prob_normal, p.prob_parkinsonian, p.prob_hemiplegic,
                p.prob_ataxic, p.prob_spastic, p.prob_antalgic,
                p.model_version, p.model_name
            FROM gait_sessions s
            LEFT JOIN gait_features f ON s.session_id = f.session_id
            LEFT JOIN (
                SELECT * FROM predictions
                WHERE session_id = %s
                ORDER BY created_at DESC LIMIT 1
            ) p ON s.session_id = p.session_id
            WHERE s.session_id = %s
        """
        cur.execute(sql, (session_id, session_id))
        row = cur.fetchone()
        if not row:
            return None
        d = dict(row)

        session_obj = {
            "session_id": f"GS-{d['session_id']:04d}" if isinstance(d['session_id'], int) else str(d['session_id']),
            "user_id": d.get("user_id", 1),
            "subject_id": str(d["subject_id"]),
            "session_date": str(d.get("recorded_at") or ""),
            "recorded_at": str(d.get("recorded_at") or ""),
            "duration_seconds": float(d.get("duration_seconds") or 0.0),
            "walking_condition": str(d.get("walking_condition") or "indoor_flat"),
            "data_source": str(d.get("data_source") or "uploaded_csv"),
            "file_name": str(d.get("file_name") or ""),
            "status": "completed",
            "created_at": str(d.get("created_at") or ""),
        }

        features_obj = {
            "session_id": session_obj["session_id"],
            "step_count": int(d.get("step_count") or 0),
            "cadence": float(d.get("cadence") or 0.0),
            "walking_speed": float(d.get("walking_speed") or 0.0),
            "step_length": float(d.get("step_length") or 0.0),
            "stride_length": float(d.get("stride_length") or 0.0),
            "step_time": float(d.get("step_time") or 0.0),
            "stride_time": float(d.get("stride_time") or 0.0),
            "stance_time": float(d.get("stance_time") or 0.0),
            "swing_time": float(d.get("swing_time") or 0.0),
            "gait_symmetry": float(d.get("gait_symmetry") or 0.0),
            "mean_acceleration": float(d.get("mean_acceleration") or 0.0),
            "acceleration_std": float(d.get("acceleration_std") or 0.0),
            "acceleration_rms": float(d.get("acceleration_rms") or 0.0),
            "mean_gyroscope": float(d.get("mean_gyroscope") or 0.0),
            "gyroscope_std": float(d.get("gyroscope_std") or 0.0),
        }

        pred_cls = d.get("predicted_class")
        prediction_obj = None if not pred_cls else {
            "prediction_id": d.get("prediction_id", 1),
            "session_id": session_obj["session_id"],
            "predicted_class": pred_cls,
            "confidence_score": float(d.get("confidence_score") or 0.0),
            "model_version": str(d.get("model_version") or "1.0.0"),
            "model_name": str(d.get("model_name") or "Random Forest 6-Class"),
            "prediction_timestamp": str(d.get("recorded_at") or ""),
            "probabilities": {
                "normal": float(d.get("prob_normal") or 0.0),
                "parkinsonian": float(d.get("prob_parkinsonian") or 0.0),
                "hemiplegic": float(d.get("prob_hemiplegic") or 0.0),
                "ataxic": float(d.get("prob_ataxic") or 0.0),
                "spastic": float(d.get("prob_spastic") or 0.0),
                "antalgic": float(d.get("prob_antalgic") or 0.0),
            }
        }

        return {
            "session": session_obj,
            "features": features_obj,
            "prediction": prediction_obj,
            # Top-level fields for backwards compatibility
            "session_id": session_obj["session_id"],
            "subject_id": session_obj["subject_id"],
            "recorded_at": session_obj["recorded_at"],
            "duration_seconds": session_obj["duration_seconds"],
            "walking_condition": session_obj["walking_condition"],
            "data_source": session_obj["data_source"],
            "file_name": session_obj["file_name"],
        }
    finally:
        conn.close()



def get_all_sessions(page: int = 1, per_page: int = 10, gait_class: Optional[str] = None,
                     search: Optional[str] = None, user_id: Optional[int] = None) -> Dict[str, Any]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        query = """
            SELECT
                s.session_id, s.subject_id, s.recorded_at, s.duration_seconds,
                s.walking_condition, s.data_source, s.file_name,
                p.predicted_class, p.confidence_score
            FROM gait_sessions s
            LEFT JOIN (
                SELECT session_id, predicted_class, confidence_score,
                       ROW_NUMBER() OVER (PARTITION BY session_id ORDER BY created_at DESC) as rn
                FROM predictions
            ) p ON s.session_id = p.session_id AND p.rn = 1
            WHERE 1=1
        """
        params = []
        if user_id is not None:
            query += " AND s.user_id = ?" if not USE_POSTGRES else " AND s.user_id = %s"
            params.append(user_id)
        if gait_class and gait_class != "all":
            query += " AND p.predicted_class = ?" if not USE_POSTGRES else " AND p.predicted_class = %s"
            params.append(gait_class)
        if search:
            q = f"%{search}%"
            query += " AND (s.subject_id LIKE ? OR CAST(s.session_id AS TEXT) LIKE ?)" if not USE_POSTGRES else " AND (s.subject_id ILIKE %s OR CAST(s.session_id AS TEXT) ILIKE %s)"
            params.extend([q, q])

        # Count total
        count_sql = f"SELECT COUNT(*) FROM ({query}) AS t"
        cur.execute(count_sql, tuple(params))
        total = cur.fetchone()[0]

        query += " ORDER BY s.session_id DESC LIMIT ? OFFSET ?" if not USE_POSTGRES else " ORDER BY s.session_id DESC LIMIT %s OFFSET %s"
        params.extend([per_page, (page - 1) * per_page])
        cur.execute(query, tuple(params))
        rows = cur.fetchall()

        items = []
        for r in rows:
            d = dict(r)
            items.append({
                "session_id": str(d["session_id"]),
                "user_id": user_id,
                "subject_id": d["subject_id"],
                "session_date": str(d.get("recorded_at") or ""),
                "recorded_at": str(d.get("recorded_at") or ""),
                "duration_seconds": d.get("duration_seconds") or 0.0,
                "walking_condition": d.get("walking_condition") or "indoor_flat",
                "data_source": d.get("data_source") or "uploaded_csv",
                "file_name": d.get("file_name") or "",
                "status": "completed" if d.get("predicted_class") else "pending",
                "created_at": str(d.get("recorded_at") or ""),
                "predicted_class": d.get("predicted_class"),
                "confidence_score": d.get("confidence_score"),
            })

        return {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": max(1, (total + per_page - 1) // per_page),
        }
    finally:
        conn.close()


def get_dashboard_summary(user_id: Optional[int] = None) -> Dict[str, Any]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        placeholder = "%s" if USE_POSTGRES else "?"
        user_where = f" WHERE user_id = {placeholder}" if user_id is not None else ""
        user_params = (user_id,) if user_id is not None else ()
        cur.execute("SELECT COUNT(*) FROM gait_sessions" + user_where, user_params)
        total_sessions = cur.fetchone()[0]

        cur.execute("SELECT COUNT(DISTINCT subject_id) FROM gait_sessions" + user_where, user_params)
        total_subjects = cur.fetchone()[0]

        month_sql = (
            "SELECT COUNT(*) FROM gait_sessions WHERE recorded_at >= date_trunc('month', CURRENT_DATE)"
            if USE_POSTGRES else
            "SELECT COUNT(*) FROM gait_sessions WHERE recorded_at >= datetime('now', 'start of month')"
        )
        month_params = []
        if user_id is not None:
            month_sql += f" AND user_id = {placeholder}"
            month_params.append(user_id)
        cur.execute(month_sql, tuple(month_params))
        sessions_this_month = cur.fetchone()[0]

        class_sql = """
            SELECT predicted_class, COUNT(*) FROM (
                SELECT p.predicted_class,
                       ROW_NUMBER() OVER (PARTITION BY p.session_id ORDER BY p.created_at DESC) as rn
                FROM predictions p
                JOIN gait_sessions s ON s.session_id = p.session_id
                WHERE 1=1
        """
        class_params = []
        if user_id is not None:
            class_sql += f" AND s.user_id = {placeholder}"
            class_params.append(user_id)
        class_sql += """
            ) WHERE rn = 1 GROUP BY predicted_class
        """
        cur.execute(class_sql, tuple(class_params))
        class_counts = {row[0]: row[1] for row in cur.fetchall()}

        normal_count = class_counts.get("normal", 0)
        abnormal_count = sum(v for k, v in class_counts.items() if k != "normal")

        avg_sql = "SELECT AVG(p.confidence_score) FROM predictions p JOIN gait_sessions s ON s.session_id = p.session_id WHERE 1=1"
        avg_params = []
        if user_id is not None:
            avg_sql += f" AND s.user_id = {placeholder}"
            avg_params.append(user_id)
        cur.execute(avg_sql, tuple(avg_params))
        avg_conf_row = cur.fetchone()
        avg_confidence = float(avg_conf_row[0]) if avg_conf_row and avg_conf_row[0] is not None else 0.0

        # Gait distribution with UI colors
        colors = {
            "Normal": "#22c55e",
            "Parkinsonian": "#f97316",
            "Hemiplegic": "#ef4444",
            "Ataxic": "#a855f7",
            "Spastic": "#06b6d4",
            "Antalgic": "#eab308",
        }
        all_classes = ["Normal", "Parkinsonian", "Hemiplegic", "Ataxic", "Spastic", "Antalgic"]
        gait_distribution = [
            {
                "name": cls,
                "value": class_counts.get(cls.lower(), 0),
                "color": colors.get(cls, "#64748b"),
            }
            for cls in all_classes
        ]

        # Recent sessions
        recent_sql = """
            SELECT s.session_id, s.subject_id, s.recorded_at,
                   p.predicted_class as gait_class,
                   p.confidence_score as confidence
            FROM gait_sessions s
            JOIN (
                SELECT session_id, predicted_class, confidence_score,
                       ROW_NUMBER() OVER (PARTITION BY session_id ORDER BY created_at DESC) as rn
                FROM predictions
            ) p ON s.session_id = p.session_id AND p.rn = 1
            WHERE 1=1
        """
        recent_params = []
        if user_id is not None:
            recent_sql += f" AND s.user_id = {placeholder}"
            recent_params.append(user_id)
        recent_sql += """
            ORDER BY s.session_id DESC
            LIMIT 5
        """
        cur.execute(recent_sql, tuple(recent_params))
        recent_rows = cur.fetchall()
        recent_sessions = [
            {
                "session_id": f"GS-{r['session_id']:04d}" if isinstance(r['session_id'], int) else str(r['session_id']),
                "subject_id": str(r['subject_id']),
                "gait_class": str(r['gait_class']),
                "confidence": float(r['confidence']),
                "date": str(r['recorded_at'] or ""),
            }
            for r in recent_rows
        ]

        # Latest features
        latest_sql = """
            SELECT gf.* FROM gait_features gf
            JOIN gait_sessions s ON s.session_id = gf.session_id
            WHERE 1=1
        """
        latest_params = []
        if user_id is not None:
            latest_sql += f" AND s.user_id = {placeholder}"
            latest_params.append(user_id)
        latest_sql += """
            ORDER BY gf.session_id DESC LIMIT 1
        """
        cur.execute(latest_sql, tuple(latest_params))
        latest_feat_row = cur.fetchone()
        latest_features = dict(latest_feat_row) if latest_feat_row else None

        return {
            "total_sessions": total_sessions,
            "total_subjects": total_subjects,
            "normal_gait": normal_count,
            "abnormal_gait": abnormal_count,
            "normal_count": normal_count,
            "abnormal_count": abnormal_count,
            "avg_confidence": avg_confidence,
            "sessions_this_month": sessions_this_month,
            "gait_distribution": gait_distribution,
            "class_distribution": class_counts,
            "recent_sessions": recent_sessions,
            "latest_features": latest_features,
        }
    finally:
        conn.close()



def get_subjects(user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    conn = get_connection()
    try:
        cur = conn.cursor()
        placeholder = "%s" if USE_POSTGRES else "?"
        query = """
            SELECT s.subject_id, COUNT(*) as session_count, MAX(s.recorded_at) as last_session,
                   (SELECT p.predicted_class
                    FROM predictions p
                    JOIN gait_sessions latest_s ON latest_s.session_id = p.session_id
                    WHERE latest_s.subject_id = s.subject_id AND latest_s.user_id = s.user_id
                    ORDER BY p.created_at DESC LIMIT 1) as latest_gait_class
            FROM gait_sessions s
            WHERE 1=1
        """
        params = []
        if user_id is not None:
            query += f" AND s.user_id = {placeholder}"
            params.append(user_id)
        query += """
            GROUP BY s.subject_id, s.user_id
            ORDER BY s.subject_id
        """
        cur.execute(query, tuple(params))
        rows = cur.fetchall()
        return [
            {
                "subject_id": r["subject_id"],
                "age_group": "Not recorded",
                "sex": None,
                "session_count": r["session_count"],
                "last_session": str(r["last_session"] or ""),
                "latest_gait_class": r["latest_gait_class"],
            }
            for r in rows
        ]
    finally:
        conn.close()


def delete_session(session_id: int, user_id: Optional[int] = None) -> bool:
    conn = get_connection()
    try:
        cur = conn.cursor()
        if USE_POSTGRES:
            sql = "DELETE FROM gait_sessions WHERE session_id = %s"
            params = [session_id]
            if user_id is not None:
                sql += " AND user_id = %s"
                params.append(user_id)
        else:
            sql = "DELETE FROM gait_sessions WHERE session_id = ?"
            params = [session_id]
            if user_id is not None:
                sql += " AND user_id = ?"
                params.append(user_id)
        cur.execute(sql, tuple(params))
        deleted = cur.rowcount > 0
        conn.commit()
        return deleted
    finally:
        conn.close()
