#!/usr/bin/env python3

"""Ranking server launcher for Super Tilt Bro."""

from __future__ import annotations

import logging
from pathlib import Path

import click

from . import rankingdb, restservice

# Parameters' default
LISTEN_PORT_REST = 8123
RANKING_DB_FILE = Path("/var/lib/stb/ranking_server_db.json")
LOG_FILE = Path("/var/log/stb/ranking_server.log")
LOG_LEVEL = "info"
CLIENTS_WHITE_LIST = "127.0.0.1"
LOGIN_SERVER_ADDR = "127.0.0.1"
LOGIN_SERVER_PORT = 8124


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
    default=RANKING_DB_FILE,
    help="file storing persistant ranking info, empty for no file",
)
@click.option(
    "--white-list",
    type=str,
    default=CLIENTS_WHITE_LIST,
    help="comma-separated list of IP addresses of authorised clients",
)
@click.option(
    "--login-srv-addr",
    type=str,
    default=LOGIN_SERVER_ADDR,
    help="address of the login server",
)
@click.option(
    "--login-srv-port",
    type=int,
    default=LOGIN_SERVER_PORT,
    help="port of the login server's REST API",
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
    white_list: str,
    login_srv_addr: str,
    login_srv_port: int,
    log_file: Path,
    log_level: str,
):
    """Launch the ranking server."""
    # Configure logging
    if log_file.is_dir():
        log_file = log_file / "ranking_server.log"
    logging.basicConfig(
        format="[%(asctime)s] %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S %Z",
        filename=log_file,
        level=getattr(logging, log_level.upper()),
    )

    login_server = {
        "addr": login_srv_addr,
        "port": login_srv_port,
    }
    db_file = db_file if db_file != "" else None
    clients_white_list = white_list.split(",")

    # Initialize ranking database
    rankingdb.load(db_file, login_server)

    # Start serving REST requests
    restservice.serve(rest_port, whitelist=clients_white_list)


if __name__ == "__main__":
    main()
