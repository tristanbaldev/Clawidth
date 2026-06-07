#!/usr/bin/env python3
"""
payband-bridge - serve your Claude Code usage as a tiny JSON feed for the Payband watch.

It reads the LOCAL Claude Code logs on whatever machine you run it on and exposes a
small JSON document on your LAN that the watch (or anything else) can poll.

  - No API key. Nothing personal is hardcoded - it auto-discovers whatever Claude
    logs exist for the current user.
  - Nothing leaves your machine except the aggregate numbers you serve on your own LAN.
  - Stdlib only. Works on Windows / macOS / Linux.

The headline token count is input + output + cache-creation tokens (the real work).
Cheap cache-READ tokens are reported separately as `cache_read_today` and are excluded
from the headline by default (use --include-cache-read to fold them in).

Usage:
    python payband_bridge.py              # serve on http://0.0.0.0:8088/usage
    python payband_bridge.py --once       # print the JSON once and exit (great for testing)
    python payband_bridge.py --token-limit 20000000   # enable window_pct vs your own budget

See bridge/README.md for the full picture.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

WINDOW_HOURS_DEFAULT = 5.0


def candidate_project_dirs():
    """Every directory that might hold Claude Code project transcripts, for any OS."""
    found = []

    def add(path):
        try:
            p = Path(path).expanduser()
        except Exception:
            return
        if p not in found:
            found.append(p)

    # Honour an explicit override first (ccusage uses the same env var).
    env = os.environ.get("CLAUDE_CONFIG_DIR")
    if env:
        for chunk in env.replace(",", os.pathsep).split(os.pathsep):
            chunk = chunk.strip()
            if chunk:
                add(Path(chunk) / "projects")

    home = Path.home()
    add(home / ".claude" / "projects")             # classic location
    add(home / ".config" / "claude" / "projects")  # XDG location

    return [p for p in found if p.is_dir()]


def _parse_ts(obj):
    ts = obj.get("timestamp")
    if not isinstance(ts, str):
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def _components(usage):
    """(input, output, cache_creation, cache_read) tokens for one message."""
    def g(key):
        try:
            return int(usage.get(key, 0) or 0)
        except (TypeError, ValueError):
            return 0
    return (
        g("input_tokens"),
        g("output_tokens"),
        g("cache_creation_input_tokens"),
        g("cache_read_input_tokens"),
    )


def collect(window_hours=WINDOW_HOURS_DEFAULT, lookback_days=2, include_cache_read=False):
    """Walk recent transcripts and aggregate token usage. Returns plain numbers."""
    now = datetime.now(timezone.utc)
    now_epoch = now.timestamp()
    today_local = now.astimezone().date()
    window_start = now_epoch - window_hours * 3600.0
    file_cutoff = now_epoch - lookback_days * 86400.0

    # [input, output, cache_creation, cache_read]
    today = [0, 0, 0, 0]
    window = [0, 0, 0, 0]
    earliest_window = None
    latest_epoch = None
    latest_model = None
    saw_logs = False

    for proj in candidate_project_dirs():
        for path in proj.rglob("*.jsonl"):
            try:
                if path.stat().st_mtime < file_cutoff:
                    continue
            except OSError:
                continue
            saw_logs = True
            try:
                with path.open("r", encoding="utf-8", errors="ignore") as fh:
                    for line in fh:
                        if '"usage"' not in line:
                            continue
                        try:
                            obj = json.loads(line)
                        except ValueError:
                            continue
                        msg = obj.get("message")
                        if not isinstance(msg, dict):
                            continue
                        usage = msg.get("usage")
                        if not isinstance(usage, dict):
                            continue
                        dt = _parse_ts(obj)
                        if dt is None:
                            continue
                        epoch = dt.timestamp()
                        comp = _components(usage)
                        if dt.astimezone().date() == today_local:
                            for i in range(4):
                                today[i] += comp[i]
                        if epoch >= window_start:
                            for i in range(4):
                                window[i] += comp[i]
                            if earliest_window is None or epoch < earliest_window:
                                earliest_window = epoch
                        if latest_epoch is None or epoch > latest_epoch:
                            latest_epoch = epoch
                            latest_model = msg.get("model") or latest_model
            except OSError:
                continue

    def headline(parts):
        base = parts[0] + parts[1] + parts[2]   # input + output + cache_creation
        return base + (parts[3] if include_cache_read else 0)

    tokens_today = headline(today)
    tokens_window = headline(window)

    window_min_left = None
    burn_tpm = None
    if earliest_window is not None:
        elapsed_min = max(1.0, (now_epoch - earliest_window) / 60.0)
        burn_tpm = int(tokens_window / elapsed_min)
        # 5h block measured from the first activity in the window: a LOCAL estimate,
        # not the authoritative server-side figure.
        window_min_left = max(
            0, int((earliest_window + window_hours * 3600.0 - now_epoch) / 60.0)
        )

    return {
        "tokens_today": tokens_today,
        "tokens_window": tokens_window,
        "out_tokens_today": today[1],
        "cache_read_today": today[3],
        "window_min_left": window_min_left,
        "burn_tpm": burn_tpm,
        "model": latest_model,
        "saw_logs": saw_logs,
    }


def build_payload(args):
    d = collect(window_hours=args.window_hours, include_cache_read=args.include_cache_read)
    window_pct = None
    if args.token_limit and args.token_limit > 0:
        window_pct = min(999, int(100 * d["tokens_window"] / args.token_limit))
    return {
        "status": "OK" if d["saw_logs"] else "NO-LOGS",
        "updated": int(time.time()),
        "tokens_today": d["tokens_today"],
        "tokens_window": d["tokens_window"],
        "out_tokens_today": d["out_tokens_today"],
        "cache_read_today": d["cache_read_today"],
        "window_min_left": d["window_min_left"],
        "window_pct": window_pct,           # null unless you set --token-limit (a local estimate)
        "window_limit": args.token_limit or None,
        "burn_tpm": d["burn_tpm"],
        "model": d["model"],
        "cost_today_cents": None,           # tokens only for now; see README for cost options
    }


class _Cache:
    def __init__(self, ttl):
        self.ttl = ttl
        self.at = 0.0
        self.value = None

    def get(self, fn):
        now = time.time()
        if self.value is None or (now - self.at) > self.ttl:
            self.value = fn()
            self.at = now
        return self.value


INDEX_HTML = """<!doctype html><meta charset=utf-8><title>payband-bridge</title>
<style>body{font:14px ui-monospace,monospace;background:#0a0c10;color:#e8eaed;padding:24px}
pre{background:#13161c;padding:16px;border-radius:10px;border:1px solid #262b34}</style>
<h3>payband-bridge</h3><p>Live feed at <a style="color:#8ab4ff" href="/usage">/usage</a></p>
<pre id=o>loading...</pre>
<script>async function t(){try{o.textContent=JSON.stringify(await(await fetch('/usage')).json(),null,2)}catch(e){o.textContent=e}}t();setInterval(t,2000)</script>
"""


def make_handler(args, cache):
    class Handler(BaseHTTPRequestHandler):
        def _send(self, code, body, ctype="application/json"):
            data = body.encode() if isinstance(body, str) else body
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            try:
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def do_GET(self):
            path = self.path.split("?", 1)[0].rstrip("/")
            if path == "":
                return self._send(200, INDEX_HTML, "text/html")
            if path == "/usage":
                try:
                    payload = cache.get(lambda: build_payload(args))
                    self._send(200, json.dumps(payload))
                except Exception as exc:  # never crash the watch's poll
                    self._send(500, json.dumps({"status": "ERROR", "error": str(exc)}))
            else:
                self._send(404, json.dumps({"status": "NOT_FOUND"}))

        def log_message(self, *a):
            if args.verbose:
                super().log_message(*a)

    return Handler


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Serve Claude Code usage as JSON for the Payband watch."
    )
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8088)
    ap.add_argument("--window-hours", type=float, default=WINDOW_HOURS_DEFAULT)
    ap.add_argument("--token-limit", type=int,
                    default=int(os.environ.get("PAYBAND_TOKEN_LIMIT", "0") or 0),
                    help="Your own approx window token budget; enables window_pct (a local estimate).")
    ap.add_argument("--include-cache-read", action="store_true",
                    help="Fold cheap cache-read tokens into the headline count.")
    ap.add_argument("--cache-seconds", type=float, default=15.0)
    ap.add_argument("--once", action="store_true", help="Print the JSON once and exit.")
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args(argv)

    if args.once:
        print(json.dumps(build_payload(args), indent=2))
        return

    if not candidate_project_dirs():
        print("warning: no Claude log dirs found (looked in ~/.claude/projects, "
              "~/.config/claude/projects, $CLAUDE_CONFIG_DIR). Serving zeros until logs appear.",
              file=sys.stderr)

    cache = _Cache(args.cache_seconds)
    httpd = ThreadingHTTPServer((args.host, args.port), make_handler(args, cache))
    print("payband-bridge serving on http://%s:%d/usage  (Ctrl-C to stop)" % (args.host, args.port))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped.")


if __name__ == "__main__":
    main()
