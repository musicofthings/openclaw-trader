#!/usr/bin/env python3
"""OpenPlot agent bridge for TradingView webhook alerts.

- Accepts TradingView webhook payloads over HTTP POST.
- Validates a shared secret token.
- Forwards normalized events to an OpenPlot endpoint.
"""

from __future__ import annotations

import argparse
import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib import request


def _load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _post_json(url: str, token: str, payload: dict[str, Any], timeout: float) -> tuple[int, str]:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "openplot-agent/1.0",
        },
    )
    with request.urlopen(req, timeout=timeout) as resp:
        return int(resp.status), resp.read().decode("utf-8", errors="replace")


class WebhookHandler(BaseHTTPRequestHandler):
    config: dict[str, Any] = {}

    def _send(self, status: HTTPStatus, body: dict[str, Any]) -> None:
        raw = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self) -> None:  # noqa: N802
        if self.path != self.config["webhook_path"]:
            self._send(HTTPStatus.NOT_FOUND, {"error": "not_found"})
            return

        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        try:
            payload = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            self._send(HTTPStatus.BAD_REQUEST, {"error": "invalid_json"})
            return

        token = payload.get("token")
        if token != self.config["shared_secret"]:
            self._send(HTTPStatus.UNAUTHORIZED, {"error": "invalid_token"})
            return

        normalized = {
            "source": "tradingview",
            "symbol": payload.get("ticker") or payload.get("symbol"),
            "signal": payload.get("signal"),
            "price": payload.get("price") or payload.get("close"),
            "time": payload.get("time"),
            "raw": payload,
        }

        try:
            status, response = _post_json(
                self.config["openplot_ingest_url"],
                self.config["openplot_api_token"],
                normalized,
                timeout=float(self.config.get("forward_timeout_seconds", 8)),
            )
        except Exception as exc:  # pragma: no cover
            self._send(HTTPStatus.BAD_GATEWAY, {"error": "forward_failed", "detail": str(exc)})
            return

        self._send(HTTPStatus.OK, {"ok": True, "upstream_status": status, "upstream_response": response})

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/healthz":
            self._send(HTTPStatus.OK, {"ok": True, "service": "openplot-agent"})
            return
        self._send(HTTPStatus.NOT_FOUND, {"error": "not_found"})


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run OpenPlot TradingView webhook bridge")
    parser.add_argument(
        "--config",
        default=os.environ.get("OPENCLAW_AGENT_CONFIG", "openplot_agent/config.json"),
        help="Path to JSON config file",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config_path = Path(args.config).expanduser().resolve()
    config = _load_config(config_path)

    WebhookHandler.config = config
    server = ThreadingHTTPServer((config.get("host", "127.0.0.1"), int(config.get("port", 8787))), WebhookHandler)

    print(f"[openplot-agent] listening on http://{config.get('host', '127.0.0.1')}:{int(config.get('port', 8787))}{config['webhook_path']}")
    print(f"[openplot-agent] forwarding to {config['openplot_ingest_url']}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[openplot-agent] stopped")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
