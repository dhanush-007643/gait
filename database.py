# -*- coding: utf-8 -*-
"""
database.py
==========
Unified database module for the Gait Analysis system.
Redirects to the canonical db_connect module in gait-abnormality-system/db/db_connect.py.
"""

import sys
from pathlib import Path

_DB_DIR = Path(__file__).resolve().parent / "gait-abnormality-system" / "db"
if str(_DB_DIR) not in sys.path:
    sys.path.insert(0, str(_DB_DIR))

import db_connect as _db

init_db = _db.init_db
get_connection = _db.get_connection
create_user = _db.create_user
update_password_hash = _db.update_password_hash
get_user_by_email = _db.get_user_by_email
get_user_by_id = _db.get_user_by_id
create_session = _db.create_session
save_features = _db.save_features
save_prediction = _db.save_prediction
get_session_detail = _db.get_session_detail
get_all_sessions = _db.get_all_sessions
get_dashboard_summary = _db.get_dashboard_summary
get_subjects = _db.get_subjects
delete_session = _db.delete_session
USE_POSTGRES = _db.USE_POSTGRES

if __name__ == "__main__":
    init_db()
    print("[database.py] Database initialized successfully. Backend:", "PostgreSQL" if USE_POSTGRES else "SQLite (gait_analysis.db)")
