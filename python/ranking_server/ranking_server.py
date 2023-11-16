#!/usr/bin/env python3

"""Ranking server launcher for Super Tilt Bro."""

from __future__ import annotations

import argparse
import logging
import sys

from . import rankingdb, restservice

# Parameters' default
LISTEN_PORT_REST = 8123
RANKING_DB_FILE = "/var/lib/stb/ranking_server_db.json"
LOG_FILE = "/var/log/stb/ranking_server.log"
LOG_LEVEL = "info"
CLIENTS_WHITE_LIST = "127.0.0.1"
LOGIN_SERVER_ADDR = "127.0.0.1"
LOGIN_SERVER_PORT = 8124

# Parse command line
parser = argparse.ArgumentParser(description="Ranking server for Super Tilt Bro.")
parser.add_argument(
    "--rest-port",
    type=int,
    default=LISTEN_PORT_REST,
    help=f"port listening for REST requests (default: {LISTEN_PORT_REST})",
)
parser.add_argument(
    "--db-file",
    type=str,
    default=RANKING_DB_FILE,
    help=f"file storing persistant ranking info, empty for no file (default: {RANKING_DB_FILE})",
)
parser.add_argument(
    "--white-list",
    type=str,
    default=CLIENTS_WHITE_LIST,
    help=f"comma-separated list of IP addresses of authorised clients (default: {CLIENTS_WHITE_LIST})",
)
parser.add_argument(
    "--login-srv-addr",
    type=str,
    default=LOGIN_SERVER_ADDR,
    help=f"address of the login server (default: {LOGIN_SERVER_ADDR})",
)
parser.add_argument(
    "--login-srv-port",
    type=int,
    default=LOGIN_SERVER_PORT,
    help=f"port of the login server's REST API  (default: {LOGIN_SERVER_PORT})",
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

login_server = {
    "addr": args.login_srv_addr,
    "port": args.login_srv_port,
}
db_file = args.db_file if args.db_file != "" else None
clients_white_list = args.white_list.split(",")

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

# Initialize ranking database
rankingdb.load(db_file, login_server)

# Start serving REST requests
restservice.serve(args.rest_port, whitelist=clients_white_list)
