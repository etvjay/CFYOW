"""Tiny evidence server for EXP-002.

Serves real HTTP evidence at /health (and /evidence/<case>) so the GenLayer
contract's leader validator can fetch live web content, exactly as it would
on mainnet. Run: python3 evidence_server.py [port]
"""

from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        if self.path == "/health":
            body = json.dumps({"status": "ok"}).encode()
            code = 200
        elif self.path.startswith("/evidence/"):
            case = self.path.rsplit("/", 1)[-1]
            body = json.dumps({
                "case": case,
                "endpoint": "/health",
                "http_status": 200,
                "response_body": '{"status":"ok"}',
                "verified_at": self.log_date_time_string(),
                "demonstrates": "live endpoint responded 200 with expected JSON body",
            }).encode()
            code = 200
        else:
            body = json.dumps({"error": "not found"}).encode()
            code = 404
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"evidence server on :{port}", flush=True)
    server.serve_forever()
