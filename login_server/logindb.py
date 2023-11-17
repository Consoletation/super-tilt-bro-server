"""Login database management for Super Tilt Bro."""

from __future__ import annotations

import json
import threading
from pathlib import Path

#
# Working structures
#

_db_file: Path | None = None
_db_mutex = threading.Lock()

user_db = {
    "registered_logins": {},
    "next_anonymous_id": 0,
    "next_registered_id": 0x80000000,
}

#
# Internal utilities
#


def _new_registered_user_id() -> int:
    """Get a new registered user ID."""
    global user_db
    new_id = user_db["next_registered_id"]
    assert new_id < 0x100000000
    user_db["next_registered_id"] += 1
    return new_id


def _sync_db() -> None:
    """Synchronize the database with the file."""
    global _db_file, user_db
    if _db_file is not None:
        tmp_db_path = Path(f"{_db_file}.tmp")
        with tmp_db_path.open("w") as tmp_db:
            json.dump(user_db, tmp_db)
        tmp_db_path.replace(_db_file)


#
# Public API
#


def load(db_file: str | Path | None) -> None:
    """Load the database from the given file."""
    global _db_file, _db_mutex, user_db
    if isinstance(db_file, str):
        db_file = Path(db_file)
    with _db_mutex:
        _db_file = db_file

        if db_file is not None and db_file.is_file():
            with db_file.open() as f:
                user_db = json.load(f)


def get_anonymous_id() -> int:
    """Get a new anonymous user ID."""
    global _db_mutex, user_db
    with _db_mutex:
        new_id = user_db["next_anonymous_id"]
        user_db["next_anonymous_id"] = (user_db["next_anonymous_id"] + 1) % 0x80000000
        _sync_db()
        return new_id


def get_user_info(username: str) -> dict | None:
    """Get the user info for the given user name."""
    global _db_mutex, user_db
    with _db_mutex:
        _sync_db()
        return user_db["registered_logins"].get(username)


def get_user_name(user_id: int) -> str | None:
    """Get the user name for the given user ID."""
    global _db_mutex, user_db
    with _db_mutex:
        for user_name, user_info in user_db["registered_logins"].items():
            if user_info["user_id"] == user_id:
                return user_name
        return None


def register_user(username: str, password: str) -> None:
    """Register a new user."""
    global _db_mutex, user_db
    with _db_mutex:
        assert username not in user_db["registered_logins"]
        user_db["registered_logins"][username] = {
            "password": password,
            "user_id": _new_registered_user_id(),
        }
        _sync_db()
