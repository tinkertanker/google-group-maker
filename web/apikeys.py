"""
Minted API key storage and audit logging (SQLite).

Keys are shown once at mint time; only the SHA-256 hash is stored.
The audit table records what each key did.

DB location: API_KEYS_DB env var, default data/apikeys.db
(a named volume in Docker so keys survive rebuilds).
"""

import hashlib
import os
import secrets
import sqlite3
from datetime import datetime, timezone
from typing import Optional

DB_PATH = os.environ.get("API_KEYS_DB", "data/apikeys.db")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create tables if missing. Called at app startup."""
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key_hash TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                prefix TEXT NOT NULL,
                created_by TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_used_at TEXT,
                revoked INTEGER NOT NULL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS api_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts TEXT NOT NULL,
                key_id INTEGER,
                key_name TEXT,
                key_prefix TEXT,
                action TEXT NOT NULL,
                detail TEXT,
                status INTEGER NOT NULL
            );
            """
        )


def _hash(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def mint_key(name: str, created_by: str) -> str:
    """Mint a key. Returns the plaintext — shown once, never stored."""
    raw = "ggm_" + secrets.token_hex(24)
    with _connect() as conn:
        conn.execute(
            "INSERT INTO api_keys (key_hash, name, prefix, created_by, created_at)"
            " VALUES (?, ?, ?, ?, ?)",
            (_hash(raw), name, raw[:12], created_by, _now()),
        )
    return raw


def lookup_key(raw: str) -> Optional[dict]:
    """Look up a key by its plaintext value. Returns None if unknown/revoked."""
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM api_keys WHERE key_hash = ? AND revoked = 0",
            (_hash(raw),),
        ).fetchone()
        if row is None:
            return None
        conn.execute(
            "UPDATE api_keys SET last_used_at = ? WHERE id = ?",
            (_now(), row["id"]),
        )
        return dict(row)


def list_keys() -> list[dict]:
    """All keys (without hashes), newest first."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, name, prefix, created_by, created_at, last_used_at, revoked"
            " FROM api_keys ORDER BY id DESC"
        ).fetchall()
        return [dict(r) for r in rows]


def revoke_key(key_id: int) -> bool:
    """Revoke a key. Returns True if a key was revoked."""
    with _connect() as conn:
        cur = conn.execute(
            "UPDATE api_keys SET revoked = 1 WHERE id = ? AND revoked = 0",
            (key_id,),
        )
        return cur.rowcount > 0


def log_action(
    key: Optional[dict], action: str, detail: str, status: int
) -> None:
    """Record what a key did. `key` may be None for the env master key."""
    with _connect() as conn:
        conn.execute(
            "INSERT INTO api_audit (ts, key_id, key_name, key_prefix, action, detail, status)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                _now(),
                key.get("id") if key else None,
                key.get("name") if key else None,
                key.get("prefix") if key else None,
                action,
                detail,
                status,
            ),
        )


def list_audit(limit: int = 200) -> list[dict]:
    """Recent audit entries, newest first."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM api_audit ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]
