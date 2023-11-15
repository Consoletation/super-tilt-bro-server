"""REST API for ranking service."""

from __future__ import annotations

import http.server
import json
import logging

from . import rankingdb


class AuthError(Exception):
    """Raised when the client is not authorized to perform the request."""


class RequestHandler(http.server.BaseHTTPRequestHandler):
    """Request handler for the ranking service."""

    def _check_addr(self):
        """Check that the client address is authorized."""
        if self.client_address[0] not in self.server._addr_white_list:
            raise AuthError

    @staticmethod
    def log_request(code="-", size="-"):
        """Suppress logging of requests."""

    def do_POST(self):
        """Handle a POST request."""
        try:
            self._check_addr()
            if self.path == "/api/rankings" and "Content-Length" in self.headers:
                data = self.rfile.read(int(self.headers["Content-Length"]))
                msg = json.loads(data)
                rankingdb.push_games(msg)

                self.send_response(200)
                self.end_headers()
                self.wfile.write(b'{"status": "ok"}')
        except AuthError:
            pass
        except Exception:
            logging.exception('failed handling request on "%s"', self.path)

    def do_GET(self):
        """Handle a GET request."""
        try:
            self._check_addr()
            if self.path == "/api/rankings":
                self.send_response(200)
                self.end_headers()
                self.wfile.write(bytes(json.dumps(rankingdb.get_ladder()), "utf-8"))
        except AuthError:
            pass


def serve(port, whitelist):
    """Serve the ranking service on the given port."""
    server_address = ("", port)
    httpd = http.server.ThreadingHTTPServer(server_address, RequestHandler)
    httpd._addr_white_list = whitelist
    httpd.serve_forever()
