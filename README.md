# Payband

[![CI](https://github.com/tristanbaldev/Payband/actions/workflows/ci.yml/badge.svg)](https://github.com/tristanbaldev/Payband/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Platform](https://img.shields.io/badge/platform-ESP32--C3-informational)
![Firmware](https://img.shields.io/badge/firmware-MicroPython-2b6cb0)
![PRs welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)

**A discreet little money-ticker for your wrist** — that moonlights as a **Claude
usage HUD**. Set your hourly rate, clock in, and watch your earnings climb in real
time; or flip it to glance at your Claude token burn without opening Settings → Usage.
Worn palm-side, so it's for you, not a billboard for the room.

Smaller than a watch, no cloud, no app to install. Your phone configures it over the
device's own wifi; after that it counts entirely on its own.

> Status: **v1 — bench prototype.** Firmware is complete and runnable; the
> wearable enclosure is in progress. See the [roadmap](#roadmap).
>
> This is a fully open-source hardware project — build it, fork it, remix it.

---

## How it works

- The board runs its **own wifi network** (`Payband`). Join it from your phone,
  open `http://192.168.4.1`, and a one-page panel lets you set your rate, clock
  in/out, and pick the display mode.
- **Earnings mode** counts locally on the chip — `rate × time_worked ÷ 3600`.
- **Claude-usage mode** (optional) polls a tiny [bridge](bridge/) on your computer
  for your token burn. See [Claude usage mode](#claude-usage-mode-optional).
- A single **button**: tap to clock in/out, hold to flash the wifi name + address.

---

## Hardware

| Part | What to get | ~Price |
|------|-------------|--------|
| MCU | **Seeed XIAO ESP32-C3** (onboard LiPo charging) | $5 |
| Display | **0.96" OLED, SSD1306, I2C** (4-pin, not SPI) | $5 |
| Battery | **LiPo 3.7V ~300 mAh** (e.g. 303040) | $7 |
| Input | one **6 mm tactile button** | ~$0 |
| Wiring | thin silicone hookup wire (30 AWG) | $7 |
| Strap | elastic velcro wrist strap | $6 |

**~$35 total.** Why ESP32-C3 and not a Raspberry Pi? A Pi is bigger than a watch,
boots Linux for 30 s, and drains a wrist-sized cell in about an hour. A
microcontroller is instant-on, sips power, and is far smaller — exactly what a
wearable wants.

Full pinout and safety notes: [`docs/WIRING.md`](docs/WIRING.md).

---

## Build it

1. **Wire it up** — four wires for the OLED, two for the button, two for the
   battery. See [`docs/WIRING.md`](docs/WIRING.md).
2. **Flash it** — put MicroPython on the board, copy the `src/` files over. Full
   step-by-step (command line *and* Thonny GUI): [`docs/FLASHING.md`](docs/FLASHING.md).
3. **First light** — the OLED shows `$0.00`; join the `Payband` wifi, set your
   rate, clock in, watch it tick.

---

## Claude usage mode (optional)

Payband can double as a discreet **Claude usage** readout — glance at your wrist
instead of opening Settings → Usage. It's fully opt-in, and **nothing personal is in
the repo**: you point it at *your own* Claude logs and *your own* network.

1. Run **[`bridge/`](bridge/)** on your computer — a tiny, dependency-free service that
   reads your local Claude Code logs and serves your token usage as JSON on your LAN.
   No API key, nothing leaves your machine.
   ```bash
   python bridge/payband_bridge.py        # then open http://localhost:8088/usage
   ```
2. In `src/config.py`, set your wifi + the bridge address (blank by default — your
   values never get committed):
   ```python
   WIFI_SSID     = "your-2.4ghz-network"
   WIFI_PASSWORD = "your-password"
   BRIDGE_URL    = "http://192.168.1.50:8088/usage"
   ```
3. On the phone config page, switch **DISPLAY MODE → CLAUDE**. The watch joins your
   wifi, polls the bridge, and shows tokens this window, time left, and burn rate.

The 5-hour-window **%** is a **local estimate** (Anthropic exposes no API for the
official figure). Full architecture, the disguised "spy watch" roadmap, and the honest
caveats live in [`docs/USAGE_WATCH.md`](docs/USAGE_WATCH.md).

---

## Project layout

```
src/
  main.py       entry point — wires everything together, runs the async loop
  config.py     all tunables: pins, wifi name/password, timings, usage bridge
  state.py      earnings state machine + display mode (pure logic, no hardware)
  display.py    OLED rendering — money ticker, Claude-usage screen, wifi config card
  button.py     async short/long press detection
  server.py     SoftAP + tiny HTTP server + the phone control panel
  usage.py      optional Claude-usage client (joins wifi, polls the bridge)
  ssd1306.py    vendored MicroPython OLED driver (MIT)
bridge/
  payband_bridge.py   PC service: serves your local Claude usage as JSON (stdlib only)
docs/
  WIRING.md       pinout, diagram, charging, LiPo safety
  FLASHING.md     install MicroPython + upload the files
  USAGE_WATCH.md  the Claude-usage feature: architecture, disguise roadmap, caveats
```

The firmware has **no external dependencies** — everything it needs is either in
MicroPython or vendored here, so there's nothing to `pip install` onto the board.

---

## Roadmap

- **v1 — now:** earnings ticker + an optional Claude-usage mode on the current OLED.
- **v1.5:** a **DS3231 real-time clock** (scheduled auto clock-in + a real time face),
  a **Sharp Memory LCD** for an always-on matte dial, and a covert capacitive-touch
  reveal — the start of the disguised "spy watch."
- **v2:** shrink it. A Cartier-Tank-style palm-side enclosure, tuned battery life. The
  actual wearable.
- **someday:** daily/weekly earnings totals, overtime multipliers, dollar cost in usage
  mode, an away-from-home relay.

---

## Contributing

Payband is open source and contributions are very welcome — code, docs, testing
on a board variant I haven't tried, or sharing an enclosure design.

- 🐛 Found a bug or a board quirk? [Open an issue](https://github.com/tristanbaldev/Payband/issues).
- 💡 Got an idea (overtime rules, a different screen, a slicker UI)? Start a
  [discussion](https://github.com/tristanbaldev/Payband/discussions) or open a feature request.
- 🔧 Want to build on it? See [`CONTRIBUTING.md`](CONTRIBUTING.md) for setup and conventions.

Please keep the firmware **dependency-free and MicroPython-compatible**, and put
new tunables in `src/config.py`. CI runs a syntax check on every push. By
participating you agree to the [Code of Conduct](CODE_OF_CONDUCT.md).

---

## License

MIT — see [`LICENSE`](LICENSE). Use it, fork it, build your own, sell your own. ❤️
