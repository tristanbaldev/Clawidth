"""
Payband - Claude usage client (OPTIONAL).

If config.WIFI_SSID + config.BRIDGE_URL are set, the watch joins your wifi (STA)
and polls your payband-bridge (see the /bridge folder) for a tiny usage JSON, so
the screen can show your Claude token burn at a glance.

Nothing here is personal: the network and bridge address come from config.py,
which every builder fills in themselves. The watch holds no API key - only the
bridge (on your own computer) ever reads your Claude logs.

Plain HTTP only, on purpose: the ESP32-C3's MicroPython TLS stack is fragile, so
the watch talks to a simple LAN bridge instead of anything over HTTPS.
"""

try:
    import asyncio
except ImportError:
    import uasyncio as asyncio

import time
import json

try:
    import network
except ImportError:        # allows importing on desktop Python for tests
    network = None

import config


class Usage:
    """Latest usage snapshot + link status. Held in RAM, updated by usage_loop."""

    def __init__(self):
        self.status = "OFF"        # OFF / NO-LINK / STALE / OK
        self.tokens_today = 0
        self.tokens_window = 0
        self.window_min_left = None
        self.window_pct = None
        self.burn_tpm = None
        self.model = ""
        self.updated_ms = 0

    def enabled(self):
        return bool(config.WIFI_SSID) and bool(config.BRIDGE_URL)

    def fresh(self):
        if self.updated_ms == 0:
            return False
        age_s = time.ticks_diff(time.ticks_ms(), self.updated_ms) / 1000.0
        return age_s <= config.USAGE_STALE_S


def _split_url(url):
    """http://host[:port]/path -> (host, port, path)."""
    rest = url.split("://", 1)[-1]
    if "/" in rest:
        hostport, path = rest.split("/", 1)
        path = "/" + path
    else:
        hostport, path = rest, "/"
    if ":" in hostport:
        host, port = hostport.split(":", 1)
        port = int(port)
    else:
        host, port = hostport, 80
    return host, port, path


async def _http_get_json(url):
    host, port, path = _split_url(url)
    reader, writer = await asyncio.open_connection(host, port)
    try:
        req = "GET %s HTTP/1.0\r\nHost: %s\r\nConnection: close\r\n\r\n" % (path, host)
        writer.write(req.encode())
        await writer.drain()
        buf = b""
        while True:
            chunk = await reader.read(512)
            if not chunk:
                break
            buf += chunk
            if len(buf) > 2048:     # the payload is tiny; cap to protect RAM
                break
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass
    i = buf.find(b"\r\n\r\n")
    if i < 0:
        return None
    return json.loads(buf[i + 4:])


async def _ensure_wifi():
    if network is None or not config.WIFI_SSID:
        return False
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    if not sta.isconnected():
        sta.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
        for _ in range(40):             # ~10 s to associate
            if sta.isconnected():
                break
            await asyncio.sleep_ms(250)
    return sta.isconnected()


async def usage_loop(usage):
    if not usage.enabled():
        usage.status = "OFF"
        return
    while True:
        ok = False
        try:
            if await _ensure_wifi():
                data = await _http_get_json(config.BRIDGE_URL)
                if data:
                    usage.tokens_today = int(data.get("tokens_today", 0) or 0)
                    usage.tokens_window = int(data.get("tokens_window", 0) or 0)
                    usage.window_min_left = data.get("window_min_left")
                    usage.window_pct = data.get("window_pct")
                    usage.burn_tpm = data.get("burn_tpm")
                    usage.model = data.get("model") or ""
                    usage.updated_ms = time.ticks_ms()
                    usage.status = "OK"
                    ok = True
        except Exception:
            pass
        if not ok:
            usage.status = "STALE" if usage.fresh() else "NO-LINK"
        await asyncio.sleep(config.USAGE_POLL_S)
