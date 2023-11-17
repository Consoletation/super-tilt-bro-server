"""Replay database management for Super Tilt Bro."""

from __future__ import annotations

import base64
import json
import subprocess
from pathlib import Path

#
# Working structures
#

_replay_dir: Path = Path.cwd()
_db_file: Path | None = None
_bmov_to_fm2: Path | None = None

replay_db = {
    "replays": {},
}

#
# Internal utilities
#


def _sync_db() -> None:
    """Synchronize the database with the file."""
    global _db_file, replay_db
    if _db_file is not None:
        tmp_db_path = Path(f"{_db_file}.tmp")
        with tmp_db_path.open("w") as tmp_db:
            json.dump(replay_db, tmp_db)
        tmp_db_path.replace(_db_file)


def get_fm2_path(game: str) -> Path:
    """Return the path to the fm2 file for the given game."""
    global _replay_dir
    return _replay_dir / f"{game}.fm2"


#
# Public API
#


def load(
    db_file: str | Path | None,
    replay_dir: str | Path,
    bmov_to_fm2: str | Path | None,
) -> None:
    """Load the database from the given file."""
    global _db_file, _replay_dir, _bmov_to_fm2, replay_db
    if isinstance(db_file, str):
        db_file = Path(db_file)
    if isinstance(replay_dir, str):
        replay_dir = Path(replay_dir)
    if isinstance(bmov_to_fm2, str):
        bmov_to_fm2 = Path(bmov_to_fm2)
    _replay_dir = replay_dir
    if replay_dir and not replay_dir.is_dir():
        replay_dir.mkdir(mode=0o666, parents=True, exist_ok=True)

    _bmov_to_fm2 = bmov_to_fm2
    if bmov_to_fm2 and not bmov_to_fm2.is_file():
        raise Exception(f'unable to find bmov_to_fm2 at "{bmov_to_fm2}"')

    _db_file = db_file
    if db_file and db_file.is_file():
        with db_file.open() as f:
            replay_db = json.load(f)


def push_games(games_info: list[dict]) -> None:
    """Push the given games info to the database."""
    global replay_db, _replay_dir, _bmov_to_fm2

    # Record games
    for game_info in games_info:
        # Check game consistency
        mandatory_fields = [
            "bmov",
            "game_server",
            "game",
            "begin",
            "character_a",
            "character_b",
            "character_a_palette",
            "character_b_palette",
        ]
        for field in mandatory_fields:
            if field not in game_info:
                raise Exception(f'invalid game info format, missing "{field}" field')

        if game_info["game"] in replay_db["replays"]:
            raise Exception(
                'pushed already present game "{}"'.format(game_info["game"])
            )

        # Save bmov file
        bmov_path = _replay_dir / f"{game_info['game']}.bmov"
        bmov_data = base64.b64decode(game_info["bmov"])
        with bmov_path.open("wb") as bmov_file:
            bmov_file.write(bmov_data)

        # Convert bmov to fm2
        fm2_path = get_fm2_path(game_info["game"])
        cmd = [
            str(_bmov_to_fm2),
            "--palette-a",
            str(game_info["character_a_palette"]),
            "--palette-b",
            str(game_info["character_b_palette"]),
            str(bmov_path),
        ]
        fm2_data = subprocess.run(
            cmd, check=True, encoding="utf-8", stdout=subprocess.PIPE
        ).stdout
        with fm2_path.open("w") as fm2_file:
            fm2_file.write(fm2_data)

        # Delete bmov file
        bmov_path.unlink()

        # Add replay entry in DB
        replay_db["replays"][game_info["game"]] = {
            "game": game_info["game"],
            "begin": game_info["begin"],
            "character_a": game_info["character_a"],
            "character_b": game_info["character_b"],
            "character_a_palette": game_info["character_a_palette"],
            "character_b_palette": game_info["character_b_palette"],
            "stage": game_info["stage"],
            "game_server": game_info["game_server"],
        }

    # Update DB file
    _sync_db()


def get_games_list() -> list[dict]:
    """Return the list of the last 50 games."""
    global replay_db
    return sorted(
        [replay_db["replays"][game] for game in replay_db["replays"]],
        key=lambda x: x["begin"],
    )[-50:]


def get_fm2(game: str) -> str:
    """Return the fm2 file for the given game."""
    with get_fm2_path(game).open() as fm2_file:
        return fm2_file.read()
