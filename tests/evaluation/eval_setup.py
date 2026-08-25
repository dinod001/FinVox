"""
FinVox - Evaluation Setup Helpers
===================================
Shared utilities for evaluation scripts.
Handles test user creation in the users table to prevent
FK constraint violations when saving memory during eval runs.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Stable test user IDs used across all eval scripts
EVAL_USER_RAGAS   = "eval_user_ragas"
EVAL_USER_LATENCY = "eval_user_latency"
EVAL_SESSION_RAGAS   = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
EVAL_SESSION_LATENCY = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

TEST_USERS = [
    {"id": EVAL_USER_RAGAS,   "username": "eval_ragas",   "email": "eval_ragas@finvox.test"},
    {"id": EVAL_USER_LATENCY, "username": "eval_latency", "email": "eval_latency@finvox.test"},
]


def ensure_eval_users():
    """
    Inserts test users into the users table if they don't already exist.
    This prevents FK violations when the orchestrator tries to save
    memory facts for the eval user IDs.
    """
    try:
        from sqlalchemy import text
        from src.infrastructure.db.crm_client import engine

        if not engine:
            print("[WARN] No DB engine - skipping user setup.")
            return

        with engine.begin() as conn:
            for user in TEST_USERS:
                conn.execute(text("""
                    INSERT INTO users (id, username, email, password_hash)
                    VALUES (:id, :username, :email, 'eval-no-password')
                    ON CONFLICT (id) DO NOTHING;
                """), {"id": user["id"], "username": user["username"], "email": user["email"]})

        print("[OK] Eval test users ensured in users table.")
    except Exception as e:
        print(f"[WARN] Could not create eval users (non-fatal): {e}")
