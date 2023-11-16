#!/usr/bin/env python3

"""Login server launcher for Super Tilt Bro."""

from __future__ import annotations

import logging
from pathlib import Path

import click

from . import logindb, restservice

# Parameters' default
LISTEN_PORT_UDP = 0x1234
LISTEN_PORT_REST = 8124
LOGIN_DB_FILE = Path("/var/lib/stb/login_server_db.json")
LOG_FILE = Path("/var/log/stb/login_server.log")
LOG_LEVEL = "info"


@click.command()
@click.option(
    "--udp-port",
    type=int,
    default=LISTEN_PORT_UDP,
    help="port listening for UDP requests",
)
@click.option(
    "--rest-port",
    type=int,
    default=LISTEN_PORT_REST,
    help="port listening for REST requests",
)
@click.option(
    "--db-file",
    type=Path,
    default=LOGIN_DB_FILE,
    help="file storing persistant login info, empty for no file",
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
    udp_port: int,
    rest_port: int,
    db_file: str,
    log_file: Path,
    log_level: str,
):
    """Launch the login server."""
    # Configure logging
    if log_file.is_dir():
        log_file = log_file / "login_server.log"
    logging.basicConfig(
        format="[%(asctime)s] %(levelname)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S %Z",
        filename=log_file,
        level=getattr(logging, log_level.upper()),
    )

    # Initialize login database
    logindb.load(db_file if db_file != "" else None)

    # Start serving UDP and REST requests
    restservice.serve(
        rest_port,
        udp_port,
    )


if __name__ == "__main__":
    main()
