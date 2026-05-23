#!/usr/bin/env python3
import json
import os
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

DASHBOARD_DIR = Path.home() / "news-dashboard"
GH_BIN = "/opt/homebrew/bin/gh"
PORT = 8765


class Handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self._send_cors(200)
        self.end_headers()

    def do_GET(self):
        if self.path == "/update":
            self._handle_update()
        elif self.path == "/status":
            self._send_json(200, {"status": "ok"})
        else:
            self._send_json(404, {"status": "not_found"})

    def _handle_update(self):
        try:
            print("fetch_news.py 実行中...", flush=True)
            r = subprocess.run(
                [sys.executable, str(DASHBOARD_DIR / "fetch_news.py")],
                capture_output=True, text=True, timeout=120,
                cwd=str(DASHBOARD_DIR),
            )
            if r.returncode != 0:
                self._send_json(500, {"status": "error", "message": r.stderr or r.stdout})
                return

            env = {
                **os.environ,
                "PATH": f"/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:{os.environ.get('PATH', '')}",
                "HOME": str(Path.home()),
            }
            subprocess.run(
                ["git", "-C", str(DASHBOARD_DIR), "add", "index.html"],
                timeout=10, env=env,
            )
            cp = subprocess.run(
                ["git", "-C", str(DASHBOARD_DIR), "commit", "-m",
                 "Auto-update: fetch latest RSS articles"],
                capture_output=True, text=True, timeout=10, env=env,
            )
            if cp.returncode == 0:
                print("git push 中...", flush=True)
                subprocess.run(
                    ["git", "-C", str(DASHBOARD_DIR),
                     "-c", f"credential.helper=!{GH_BIN} auth git-credential",
                     "push", "origin", "main"],
                    timeout=60, env=env,
                )

            print("更新完了", flush=True)
            self._send_json(200, {"status": "ok", "output": r.stdout.strip()})

        except subprocess.TimeoutExpired:
            self._send_json(500, {"status": "error", "message": "タイムアウトしました"})
        except Exception as e:
            self._send_json(500, {"status": "error", "message": str(e)})

    def _send_cors(self, code):
        self.send_response(code)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")

    def _send_json(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass  # suppress per-request logs


if __name__ == "__main__":
    server = HTTPServer(("localhost", PORT), Handler)
    print(f"News server listening on http://localhost:{PORT}", flush=True)
    server.serve_forever()
