"""Ranking database management for Super Tilt Bro."""

from __future__ import annotations

import copy
import json
import logging
import os.path

import requests

#
# Working structures
#

_db_file = None
_login_server = None

ranking_db = {
    "users": {},
}

#
# Utilities
#


def _elo(player_mmr, opponent_mmr, score):
    """Compute player's updated mmr after an event.

    >>> _elo(1000, 1000, 1)
    1016
    >>> _elo(1000, 1000, 0)
    984
    >>> _elo(1000, 1200, 0)
    992
    >>> _elo(1000, 1200, 1)
    1024
    >>> _elo(1200, 1000, 1)
    1208
    >>> _elo(1200, 1000, 0)
    1176
    """
    K = 32  # Maximum change in score
    SPREAD = 400  # A difference of SPREAD/2 MMR points, means the highest ranked player should have ~75% winrate
    expected_score = 1 / (1 + 10 ** ((opponent_mmr - player_mmr) / SPREAD))
    new_mmr = player_mmr + K * (score - expected_score)
    return max(0, round(new_mmr))


#
# Internal utilities
#


def _sync_db():
    global _db_file, ranking_db
    if _db_file is not None:
        tmp_db_path = f"{_db_file}.tmp"
        with open(tmp_db_path, "w") as tmp_db:
            json.dump(ranking_db, tmp_db)
        os.replace(tmp_db_path, _db_file)


def _get_user_id(timepoint, connection_id):
    # TODO should ask the login server for the association timepoint+connection_id to user_id
    #     For now user_id == connection_id, let's assume it
    #     just convert it to hex string type (to be a valid json property name)
    return f"{int(connection_id):08x}"


def _get_user_name(user_id):
    user_id_int = int(user_id, 16)
    resp = requests.get(
        "http://{}:{}/api/login/user_name/{}".format(
            _login_server["addr"], _login_server["port"], user_id_int
        )
    )
    if resp.status_code != 200:
        logging.error("bad status code for resoultion of user %s: %d", user_id, resp.status_code)
        return None
    user_name = json.loads(resp.text)

    if user_name is None:
        return None
    if not isinstance(user_name, str):
        raise Exception(f"bad response type: {user_name}")
    if len(user_name) < 3 or len(user_name) > 16:
        raise Exception(f'unvalid name: "{user_name}"')
    return user_name


#
# Public API
#


def load(db_file, login_server):
    global _db_file, _login_server, ranking_db

    _db_file = db_file
    if db_file is not None and os.path.isfile(db_file):
        with open(db_file) as f:
            ranking_db = json.load(f)

    _login_server = copy.deepcopy(login_server)


def push_games(games_info):
    global ranking_db

    # Update rankings
    for game_info in games_info:
        # Check game consistency
        mandatory_fields = [
            "begin",
            "end",
            "client_a",
            "client_b",
            "player_a_ranked",
            "player_b_ranked",
            "winner",
        ]
        for field in mandatory_fields:
            if field not in game_info:
                raise Exception(
                    f'invalid game info format, missing "{field}" field'
                )

        # Retrieve users IDs
        user_a = _get_user_id(game_info["begin"], game_info["client_a"])
        user_b = _get_user_id(game_info["begin"], game_info["client_b"])

        # Create missing users
        for user_id in [user_a, user_b]:
            if user_id not in ranking_db["users"]:
                ranking_db["users"][user_id] = {
                    "ranked_mmr": 1000,
                    "unranked_mmr": 1000,
                    "name": None,
                }

        # Apply MMR change
        if game_info["winner"] == 0:
            winner = user_a
            loser = user_b
            winner_mmr_key = (
                "ranked_mmr" if game_info["player_a_ranked"] == 1 else "unranked_mmr"
            )
            loser_mmr_key = (
                "ranked_mmr" if game_info["player_b_ranked"] == 1 else "unranked_mmr"
            )
        else:
            winner = user_b
            loser = user_a
            winner_mmr_key = (
                "ranked_mmr" if game_info["player_b_ranked"] == 1 else "unranked_mmr"
            )
            loser_mmr_key = (
                "ranked_mmr" if game_info["player_a_ranked"] == 1 else "unranked_mmr"
            )

        winner = ranking_db["users"][winner]
        loser = ranking_db["users"][loser]
        winner_mmr = winner[winner_mmr_key]
        loser_mmr = loser[loser_mmr_key]

        winner[winner_mmr_key] = _elo(winner_mmr, loser_mmr, 1)
        loser[loser_mmr_key] = _elo(loser_mmr, winner_mmr, 0)

    # Update DB file
    _sync_db()


def get_ladder():
    global ranking_db
    users = ranking_db["users"]

    # Update names of ranked players
    db_updated = False
    try:
        for user_id in users:
            user_info = users[user_id]
            if user_info["name"] is None:
                user_info["name"] = _get_user_name(user_id)
                db_updated = True
    except Exception as e:
        logging.error("Failed to retrieve new ranked players names: %s", e)

    if db_updated:
        _sync_db()

    # Generate sorted array of player
    return sorted(
        [
            {"mmr": users[u]["ranked_mmr"], "user_name": users[u]["name"]}
            for u in users
            if users[u]["name"] is not None
        ],
        key=lambda x: (x["mmr"], x["user_name"]),
        reverse=True,
    )
