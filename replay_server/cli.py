#!/usr/bin/env python3

"""Replay server launcher for Super Tilt Bro."""

from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path

import click

from . import replaydb, restservice

# Parameters' default
LISTEN_PORT_REST = 8125
DB_FILE = Path("/var/lib/stb/replay_server/db.json")
REPLAY_DIR = Path("/var/lib/stb/replay_server")
BMOV_TO_FM2 = "bmov_to_fm2"
LOG_FILE = Path("/var/log/stb/replay_server.log")
LOG_LEVEL = "info"
CLIENTS_WHITE_LIST = "127.0.0.1"


@click.command()
@click.option(
    "--rest-port",
    type=int,
    default=LISTEN_PORT_REST,
    help="port listening for REST requests",
)
@click.option(
    "--db-file",
    type=Path,
    default=DB_FILE,
    help="file storing persistant info, empty for no file",
)
@click.option(
    "--replay-dir",
    type=Path,
    default=REPLAY_DIR,
    help="directory to store replay files",
)
@click.option(
    "--bmov-to-fm2",
    type=Path,
    default=BMOV_TO_FM2,
    help="replay conversion utility, absolute or in PATH",
)
@click.option(
    "--white-list",
    type=str,
    default=CLIENTS_WHITE_LIST,
    help="comma-separated list of IP addresses of authorised clients",
)
@click.option(
    "--log-file",
    type=Path,
    default=LOG_FILE,
    help="logs destination, empty for stderr",
)
@click.option(
    "--log-level",
    type=click.Choice(["debug", "info", "warning", "error", "critical"]),
    default=LOG_LEVEL,
    help="minimal severity of logs [debug, info, warning, error, critical]",
)
def main(
    rest_port: int,
    db_file: Path,
    replay_dir: Path,
    bmov_to_fm2: Path,
    white_list: str,
    log_file: Path,
    log_level: str,
):
    """Launch the replay server."""
    clients_white_list = white_list.split(",")

    if not bmov_to_fm2.is_file():
        res = subprocess.run(["which", bmov_to_fm2], encoding="utf-8")
        if res.returncode != 0:
            logging.error('unable to find replay converter "%s"', bmov_to_fm2)
            sys.exit(1)
        bmov_to_fm2 = res.stdout.rstrip("\r\n")

    if not replay_dir.is_dir():
        logging.error('invalid replay directory: "%s"', replay_dir)
        sys.exit(1)

    # Configure logging
    if log_file.is_dir():
        log_file = log_file / "replay_server.log"
    logging.basicConfig(
        format="[%(asctime)s] %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S %Z",
        filename=log_file,
        level=getattr(logging, log_level.upper()),
    )

    # Initialize database
    replaydb.load(db_file, replay_dir, bmov_to_fm2)

    # Start serving REST requests
    restservice.serve(rest_port, whitelist=clients_white_list)


if __name__ == "__main__":
    main()
