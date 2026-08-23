"""Tiny evidence server for EXP-002 (extended scenario coverage)."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

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



PORT_NUM = 8765

def perform_live_check(path, expect_body):
    """Perform a REAL request against our own /health endpoint and capture proof."""
    import urllib.request
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{PORT_NUM}{path}", timeout=5) as resp:
            return {
                "live_check": True,
                "requested_path": path,
                "http_status": resp.status,
                "response_body": resp.read().decode(),
                "captured_at": datetime.utcnow().isoformat() + "Z",
                "demonstrates": ("LIVE CAPTURE during evidence generation: the endpoint "
                                 "was actually requested and returned this response. "
                                 f"Expected body: {expect_body}."),
            }
    except Exception as e:
        return {"live_check": False, "error": str(e),
                "demonstrates": "live check FAILED"}


ADVERSARIAL = {
    "/adv/status-only": {"note": "returns 200 but body is not the required JSON",
                          "actual_response": "OK"},
    "/adv/screenshot-claim": {"note": "claims a screenshot proves it works",
                               "claim": "screenshot attached separately (not provided)"},
    "/adv/wrong-endpoint": {"evidence_about": "/different-endpoint",
                             "response_body": '{"status":"ok"}',
                             "note": "correct body but served from wrong path"},
    "/adv/stale-feed": {"last_updated": "2026-08-20T00:00:00Z",
                          "note": "timestamp is days stale"},
    "/adv/right-body-wrong-path": {"served_at": "/healthz-wrong",
                                     "response_body": '{"status":"ok"}',
                                     "note": "body correct but path differs from objective"},
    "/adv/self-attesting": {"self_attestation": "this endpoint works and returns ok",
                              "note": "page claims it works; self-referential, no demonstration"},
}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            body = json.dumps({"status": "ok"}).encode(); code = 200
        elif self.path.startswith("/evidence/ok-"):
            variant = self.path.rsplit("-", 1)[-1]
            checks = {"v1": ("/health", '{"status":"ok"}'),
                      "v2": ("/health", "operational"),
                      "v3": ("/health", "timestamp")}
            path, expect = checks.get(variant, ("/health", '{"status":"ok"}'))
            payload = perform_live_check(path, expect)
            payload["variant"] = variant
            body = json.dumps(payload).encode()
            code = 200
        elif self.path in ADVERSARIAL:
            payload = dict(ADVERSARIAL[self.path])
            payload['verified_at'] = '2026-08-23T00:00:00Z'
            body = json.dumps(payload).encode()
            code = 200
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
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
