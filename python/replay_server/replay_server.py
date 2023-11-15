#!/usr/bin/env python3

"""Replay server launcher for Super Tilt Bro."""

from __future__ import annotations

import argparse
import logging
import os.path
import subprocess
import sys

from . import replaydb, restservice

# Parameters' default
LISTEN_PORT_REST = 8125
DB_FILE = "/var/lib/stb/replay_server/db.json"
REPLAY_DIR = "/var/lib/stb/replay_server"
BMOV_TO_FM2 = "bmov_to_fm2"
LOG_FILE = "/var/log/stb/replay_server.log"
LOG_LEVEL = "info"
CLIENTS_WHITE_LIST = "127.0.0.1"

# Parse command line
parser = argparse.ArgumentParser(description="Replay server for Super Tilt Bro.")
parser.add_argument(
    "--rest-port",
    type=int,
    default=LISTEN_PORT_REST,
    help=f"port listening for REST requests (default: {LISTEN_PORT_REST})",
)
parser.add_argument(
    "--db-file",
    type=str,
    default=DB_FILE,
    help=f"file storing persistant info, empty for no file (default: {DB_FILE})",
)
parser.add_argument(
    "--replay-dir",
    type=str,
    default=REPLAY_DIR,
    help=f"directory to store replay files (default: {REPLAY_DIR})",
)
parser.add_argument(
    "--bmov-to-fm2",
    type=str,
    default=BMOV_TO_FM2,
    help=f"replay conversion utility, absolute or in PATH (default: {BMOV_TO_FM2})",
)
parser.add_argument(
    "--white-list",
    type=str,
    default=CLIENTS_WHITE_LIST,
    help=f"comma-separated list of IP addresses of authorised clients (default: {CLIENTS_WHITE_LIST})",
)
parser.add_argument(
    "--log-file",
    type=str,
    default=LOG_FILE,
    help=f"logs destination, empty for stderr (default: {LOG_FILE})",
)
parser.add_argument(
    "--log-level",
    type=str,
    default=LOG_LEVEL,
    help=f"minimal severity of logs [debug, info, warning, error, critical] (default: {LOG_LEVEL})",
)
args = parser.parse_args()

db_file = args.db_file if args.db_file != "" else None
replay_dir = args.replay_dir
bmov_to_fm2 = args.bmov_to_fm2
clients_white_list = args.white_list.split(",")

if args.log_level not in ["debug", "info", "warning", "error", "critical"]:
    sys.stderr.write("invalid debug level\n")
    sys.exit(1)

if not os.path.isfile(bmov_to_fm2):
    res = subprocess.run(["which", bmov_to_fm2], encoding="utf-8")
    if res.returncode != 0:
        logging.error('unable to find replay converter "%s"', bmov_to_fm2)
        sys.exit(1)
    bmov_to_fm2 = res.stdout.rstrip("\r\n")

if not os.path.isdir(replay_dir):
    logging.error('invalid replay directory: "%s"', replay_dir)
    sys.exit(1)

# Configure logging
logging.basicConfig(
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S %Z",
    filename=args.log_file if args.log_file != "" else None,
    level=getattr(logging, args.log_level.upper()),
)

# Initialize database
replaydb.load(db_file, replay_dir, bmov_to_fm2)

# Start serving REST requests
restservice.serve(args.rest_port, whitelist=clients_white_list)
