#!/usr/bin/env python3

"""Login server launcher for Super Tilt Bro."""

from __future__ import annotations

import argparse
import logging
import signal
import sys
import threading

from . import logindb, restservice, udpservice

# Parameters' default
LISTEN_PORT_UDP = 0x1234
LISTEN_PORT_REST = 8124
LOGIN_DB_FILE = "/var/lib/stb/login_server_db.json"
LOG_FILE = "/var/log/stb/login_server.log"
LOG_LEVEL = "info"

# Parse command line
parser = argparse.ArgumentParser(
    description="Authentication server for Super Tilt Bro.",
)
parser.add_argument(
    "--udp-port",
    type=int,
    default=LISTEN_PORT_UDP,
    help=f"port listening for UDP requests (default: {LISTEN_PORT_UDP})",
)
parser.add_argument(
    "--rest-port",
    type=int,
    default=LISTEN_PORT_REST,
    help=f"port listening for REST requests (default: {LISTEN_PORT_REST})",
)
parser.add_argument(
    "--db-file",
    type=str,
    default=LOGIN_DB_FILE,
    help=f"file storing persistant login info, empty for no file (default: {LOGIN_DB_FILE})",
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

if args.log_level not in ["debug", "info", "warning", "error", "critical"]:
    sys.stderr.write("invalid debug level\n")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S %Z",
    filename=args.log_file if args.log_file != "" else None,
    level=getattr(logging, args.log_level.upper()),
)

# Initialize login database
logindb.load(args.db_file if args.db_file != "" else None)

# Start serving UDP requests
thread_udp = threading.Thread(
    target=udpservice.serve, name="udp_service", daemon=True, args=(args.udp_port,)
)
thread_rest = threading.Thread(
    target=restservice.serve, name="rest_service", daemon=True, args=(args.rest_port,)
)
thread_udp.start()
thread_rest.start()

# Wait for known signal
try:
    # Dumb implementation, wait any signal,
    # KeyboardInterrupt will break the loop on SIGINT
    while True:
        signal.pause()
except KeyboardInterrupt:
    pass
