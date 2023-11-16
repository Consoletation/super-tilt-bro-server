"""UDP service for STNP login extension."""

from __future__ import annotations

import asyncio
import logging
import string

from . import logindb

MESSAGE_LEN = 72

#
# STNP, login extension
#

STNP_LOGIN_MSG_TYPE = 255

STNP_LOGIN_FROM_SERVER_LOGGED_IN = 0
STNP_LOGIN_FROM_SERVER_LOGIN_FAILED = 1

STNP_LOGIN_ANONYMOUS = 0
STNP_LOGIN_PASSWORD = 1
STNP_LOGIN_CREATE_ACCOUNT = 2

STNP_LOGIN_CHARSET = [
    " ",
    *string.ascii_lowercase,
    *string.digits,
    None,
]


#
# Implementation
#


def logged_in_msg(client_id: int, login_type: int) -> bytes:
    """Return a logged in message."""
    res = bytearray(7)
    res[0] = STNP_LOGIN_MSG_TYPE
    res[1] = STNP_LOGIN_FROM_SERVER_LOGGED_IN
    res[2] = login_type
    res[3] = client_id & 0x000000FF
    res[4] = (client_id & 0x0000FF00) >> 8
    res[5] = (client_id & 0x00FF0000) >> 16
    res[6] = (client_id & 0xFF000000) >> 24
    return bytes(res)


def login_failed_msg(message: str) -> bytes:
    """Return a login failed message."""
    assert len(message) == MESSAGE_LEN

    res = bytearray(MESSAGE_LEN + 2)
    res[0] = STNP_LOGIN_MSG_TYPE
    res[1] = STNP_LOGIN_FROM_SERVER_LOGIN_FAILED

    for i in range(MESSAGE_LEN):
        res[i + 2] = STNP_LOGIN_CHARSET.index(message[i])

    return res


def parse_login_request(message: bytes) -> dict[str, str] | None:
    """Parse a login request."""

    def parse_stnp_str(offset):
        """Parse a STNP string."""
        value = ""
        for i in range(offset, offset + 16):
            c = message[i]
            if c >= len(STNP_LOGIN_CHARSET):
                logging.warning(
                    "ill formated login request: invalid character at byte %s", i
                )
                return None
            if c == 0:
                break
            value += STNP_LOGIN_CHARSET[c]
        return value

    if (
        len(message) != 34
        or message[0] != STNP_LOGIN_MSG_TYPE
        or message[1] not in [STNP_LOGIN_PASSWORD, STNP_LOGIN_CREATE_ACCOUNT]
    ):
        logging.warning("ill formated login request")
        return None

    user = parse_stnp_str(2)
    password = message[18 : 18 + 16].hex()
    if user is None or password is None:
        return None

    return {"user": user, "password": password}


def check_login_request(message: bytes) -> tuple[bool, dict[str, str] | str]:
    """Check a login request."""
    # Parse message
    client_credential = parse_login_request(message)

    # Check invalid cases
    if client_credential is None:
        return (
            False,
            "missformed user   "
            "name or password  "
            "                  "
            "                  ",
        )
    if len(client_credential["user"]) < 3:
        return (
            False,
            "user name shall   "
            "have at least     "
            "three characters  "
            "                  ",
        )

    # Return parsed result
    return (True, client_credential)


def handle_msg_login_anonymous(
    message: bytes,
    client_addr: tuple[str, int],
    sock: asyncio.DatagramTransport,
):
    """Handle a login anonymous message."""
    # Log the user with a fresh anonymous ID
    client_id = logindb.get_anonymous_id()
    sock.sendto(logged_in_msg(client_id, STNP_LOGIN_ANONYMOUS), client_addr)


def handle_msg_login_password(
    message: bytes,
    client_addr: tuple[str, int],
    sock: asyncio.DatagramTransport,
):
    """Handle a login password message."""
    # Parse message
    parsed_message = check_login_request(message)
    if not parsed_message[0]:
        assert isinstance(parsed_message[1], str)
        sock.sendto(login_failed_msg(parsed_message[1]), client_addr)
        return
    client_credential = parsed_message[1]

    # Get client info from DB (register the user if needed)
    assert isinstance(client_credential, dict)
    client_info = logindb.get_user_info(client_credential["user"])
    if client_info is None:
        logging.info('new user: "%s"', client_credential["user"])
        logindb.register_user(client_credential["user"], client_credential["password"])
        client_info = logindb.get_user_info(client_credential["user"])

    # Send response
    if (
        client_info is not None
        and client_info["password"] == client_credential["password"]
    ):
        # Password match, send the ID
        sock.sendto(
            logged_in_msg(client_info["user_id"], STNP_LOGIN_PASSWORD), client_addr
        )
    else:
        # Password mismatch, send access denied
        sock.sendto(
            login_failed_msg(
                "invalid user name "
                "or password       "
                "                  "
                "                  "
            ),
            client_addr,
        )


def handle_msg_create_account(
    message: bytes,
    client_addr: tuple[str, int],
    sock: asyncio.DatagramTransport,
):
    """Handle a create account message."""
    # Parse message
    parsed_message = check_login_request(message)
    if not parsed_message[0]:
        assert isinstance(parsed_message[1], str)
        sock.sendto(login_failed_msg(parsed_message[1]), client_addr)
        return
    client_credential = parsed_message[1]

    # Check that client does not already exists
    assert isinstance(client_credential, dict)
    client_info = logindb.get_user_info(client_credential["user"])
    if client_info is not None:
        sock.sendto(
            login_failed_msg(
                "this user name    "
                "already exists    "
                "                  "
                "                  "
            ),
            client_addr,
        )
        return

    # Register the user
    logging.info('new user: "%s"', client_credential["user"])
    logindb.register_user(client_credential["user"], client_credential["password"])
    client_info = logindb.get_user_info(client_credential["user"])

    # Sanity check
    if client_info is None or client_info["password"] != client_credential["password"]:
        logging.error(
            "failed to create '%s' '%s'",
            client_credential["user"],
            client_credential["password"],
        )
        sock.sendto(
            login_failed_msg(
                "internal error    "
                "when creating your"
                "account           "
                "                  "
            ),
            client_addr,
        )
    else:
        sock.sendto(
            logged_in_msg(client_info["user_id"], STNP_LOGIN_CREATE_ACCOUNT),
            client_addr,
        )


class LoginServiceProtocol(asyncio.DatagramProtocol):
    """Login service protocol."""

    def connection_made(self, transport: asyncio.BaseTransport) -> None:
        """Handle a new connection."""
        assert isinstance(transport, asyncio.DatagramTransport)
        self.transport = transport

    def datagram_received(self, message: bytes, client_addr: tuple[str, int]) -> None:
        """Handle a datagram."""
        logging.debug(
            "got message from %s:%d: %s",
            client_addr[0],
            client_addr[1],
            message,
        )
        message_handlers = {
            STNP_LOGIN_ANONYMOUS: handle_msg_login_anonymous,
            STNP_LOGIN_PASSWORD: handle_msg_login_password,
            STNP_LOGIN_CREATE_ACCOUNT: handle_msg_create_account,
        }
        if len(message) >= 2 and message[0] == STNP_LOGIN_MSG_TYPE:
            logging.debug("login message")
            if message[1] in message_handlers:
                try:
                    message_handlers[message[1]](message, client_addr, self.transport)
                except Exception:
                    logging.exception("error when handling message")
            else:
                logging.debug("unknown login method")
                self.transport.sendto(
                    login_failed_msg(
                        "invalid login     "
                        "message           "
                        "                  "
                        "                  "
                    ),
                    client_addr,
                )


async def serve(listen_port: int) -> asyncio.DatagramTransport:
    """Serve login requests."""
    logging.info("starting login service on port %s", listen_port)
    loop = asyncio.get_running_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        LoginServiceProtocol, local_addr=("0.0.0.0", listen_port)
    )
    assert isinstance(transport, asyncio.DatagramTransport)
    return transport
