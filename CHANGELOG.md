# Changelog

All notable changes to Payband are documented here. The format loosely follows
[Keep a Changelog](https://keepachangelog.com).

## [Unreleased]

### Added
- **Claude usage mode** — an optional second display mode that shows your Claude
  token burn (tokens this 5-hour window, time left, burn rate) at a glance.
  - `bridge/payband_bridge.py`: a stdlib-only PC service that reads your local
    Claude Code logs and serves the usage as a tiny JSON feed on your LAN. Nothing
    personal is hardcoded; it auto-discovers whatever logs exist and holds no API key.
  - `src/usage.py`: the watch-side client (joins wifi, polls the bridge).
  - Display mode toggle (Earnings / Claude) on the phone config page, persisted in state.
  - `docs/USAGE_WATCH.md`: architecture, the disguised "spy watch" roadmap, and honest caveats.
  - New (blank-by-default) config in `src/config.py`: `WIFI_SSID`, `WIFI_PASSWORD`, `BRIDGE_URL`.
- **Wall display** (`wall/index.html`) — a fullscreen Claude-usage dashboard for a
  wall-mounted panel (e.g. a 15.6" IPS screen driven by a Raspberry Pi in kiosk mode).
  Reuses the same bridge; `wall/README.md` covers the driver-board + Pi kiosk setup.

### Notes
- The official Claude.ai 5-hour/weekly limit % has no public API; the window % is a
  local estimate from your own logs and is labelled as such.

## [0.1.0] — 2026-06-06

Initial firmware. Bench prototype.

### Added
- MicroPython firmware for Seeed XIAO ESP32-C3 + 0.96" SSD1306 OLED.
- Earnings state machine: tap to clock in, `earnings = rate × worked ÷ 3600`.
- SoftAP `Payband` + single-page phone control panel (set rate, clock in/out, reset).
- OLED money ticker with upscaled digits + wifi config card on long-press.
- Async short/long button handling.
- Wiring and flashing docs.
