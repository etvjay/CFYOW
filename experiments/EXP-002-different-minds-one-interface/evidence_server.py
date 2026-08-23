"""Tiny evidence server for EXP-002 (extended scenario coverage)."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

EVIDENCE = {
    "/evidence/health-ok": {"case": "health-ok", "endpoint": "/health", "http_status": 200,
        "response_body": '{"status":"ok"}',
        "demonstrates": "live endpoint responded 200 with expected JSON body"},
    "/evidence/wrong-body": {"case": "wrong-body", "endpoint": "/health", "http_status": 200,
        "response_body": '{"state":"fine"}',
        "demonstrates": "endpoint responded but body does not contain required word 'healthy'"},
    "/evidence/uptime-ok": {"case": "uptime-ok", "service": "exp002", "uptime_pct": 99.98,
        "status_page": "operational",
        "demonstrates": "status page shows service operational"},
    "/evidence/no-metrics": {"case": "no-metrics", "endpoint": "/health", "http_status": 200,
        "response_body": '{"status":"ok"}', "note": "no /metrics endpoint exists",
        "demonstrates": "requested /metrics endpoint absent; only /health exists"},
    "/evidence/timestamped": {"case": "timestamped", "endpoint": "/status",
        "response_body": '{"status":"ok","timestamp":"2026-08-23T02:20:00Z"}',
        "demonstrates": "JSON status endpoint includes ISO8601 timestamp field"},
}

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            body = json.dumps({"status": "ok"}).encode(); code = 200
        elif self.path in EVIDENCE:
            payload = dict(EVIDENCE[self.path])
            payload["verified_at"] = datetime.utcnow().isoformat() + "Z"
            body = json.dumps(payload).encode(); code = 200
        else:
            body = json.dumps({"error": "not found"}).encode(); code = 404
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, *a): pass

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()
