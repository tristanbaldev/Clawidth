# Claude usage mode — the "spy watch"

Payband can double as a discreet **Claude usage** readout: glance at your wrist to
see your token burn instead of breaking flow to open **Settings → Usage**. This is
fully opt-in, and there's nothing personal in the repo — you point it at *your own*
Claude logs and *your own* network.

This doc covers what's actually possible, the architecture, and the longer-term
"looks like a Cartier, secretly a HUD" vision.

---

## What's real (the honest version)

There are three ways to know your Claude usage, and they are not equal:

| Source | What you get | Works for you? |
|--------|--------------|----------------|
| **Claude Code local logs** | Exact tokens (in/out/cache) per message + model, computed cost via tools like [ccusage](https://github.com/ryoppippi/ccusage) | ✅ **Yes — this is the path.** It's your own data on your own disk. |
| **Anthropic Admin API** (`/v1/organizations/usage_report`, `/cost_report`) | Metered **API** tokens + USD, org-wide | ⚠️ Org-only (needs an `sk-ant-admin` key); irrelevant if you just use Claude Code on a Pro/Max plan |
| **Claude.ai Pro/Max subscription %** (the official 5-hour / weekly bars) | The *authoritative* limit % | ❌ **No public API.** It exists only in-app. |

**So:** tokens and burn rate come straight from your local logs and are precise. The
5-hour-window **%** shown on the watch is a **local estimate** derived the same way
[ccusage](https://github.com/ryoppippi/ccusage)'s `blocks` view is — it will drift
from the official figure. We label it as an estimate and never pretend it's the real
server-side number.

---

## Architecture

The watch never holds an API key and never calls Anthropic. A tiny bridge on your
computer does the reading; the watch just polls it.

```
Claude Code logs ──► payband-bridge (your PC)              ──LAN, plain HTTP──► ⌚ watch
  ~/.claude/...       reads logs, aggregates tokens,                              polls /usage,
                      serves a tiny flat JSON                                     renders glance
                            │
                            └─(future)─► Vercel relay ──HTTPS──► ⌚ when away from home
```

Why a bridge instead of the watch calling Anthropic directly:

- **Secrets stay off the wrist.** A wearable is physically extractable; it must never
  hold a key. Only the bridge (on your machine) ever touches your logs.
- **The ESP32-C3's TLS is fragile.** MicroPython HTTPS on the C3 hits RAM/handshake
  limits. Talking to a plain-HTTP LAN endpoint is reliable and cheap.
- **Tiny payload.** The bridge reduces megabytes of JSONL to ~150 bytes of flat ints.

### The JSON the watch fetches

```json
{
  "status": "OK",
  "updated": 1749200000,
  "tokens_today": 44829390,
  "tokens_window": 22678392,
  "out_tokens_today": 4117591,
  "cache_read_today": 298560770,
  "window_min_left": 154,
  "window_pct": null,
  "window_limit": null,
  "burn_tpm": 156172,
  "model": "claude-opus-4-8",
  "cost_today_cents": null
}
```

- `tokens_*` = input + output + cache-creation (the real work). Cheap cache-**reads**
  are reported separately as `cache_read_today`, not folded into the headline.
- `window_pct` is `null` unless you set a token budget (`--token-limit`) on the bridge —
  and even then it's a **local estimate**.
- `status` (`OK` / `STALE` / `NO-LINK`) lets the watch show last-good numbers rather
  than a blank face when the link drops.

---

## Setup

1. **Run the bridge** on your computer (see [`../bridge/README.md`](../bridge/README.md)):
   ```bash
   python bridge/payband_bridge.py
   # open http://localhost:8088/usage to see it working
   ```
2. **Point the watch at it** in [`../src/config.py`](../src/config.py) (blank by default —
   your values never get committed):
   ```python
   WIFI_SSID     = "your-2.4ghz-network"
   WIFI_PASSWORD = "your-password"
   BRIDGE_URL    = "http://192.168.1.50:8088/usage"   # your PC's LAN IP
   ```
3. **Switch modes** on the phone config page: **DISPLAY MODE → CLAUDE**. The watch
   joins your wifi, polls the bridge, and shows tokens this window, time left, and
   burn rate.

> ESP32-C3 is **2.4 GHz only** — make sure the network you give it is 2.4 GHz.

---

## The disguise roadmap (where this is going)

The endgame is a watch that *looks* like an elegant dress watch and only reveals usage
to you, on a secret gesture.

- **Display → Sharp Memory LCD** (1.28", 128×128, reflective monochrome, ~10 µA
  always-on). A matte, non-emissive panel reads like a printed enamel dial in daylight —
  a glowing OLED/IPS instantly looks like electronics. Square at this size, which suits a
  **Cartier Tank** case (the easiest luxury form to fake convincingly).
- **The cover face** = a static Roman-numeral Tank dial with live hands off a DS3231 RTC.
  Just a watch.
- **The reveal** = the ESP32-C3 has no real capacitive touch, so a **TTP223** pad bonded
  behind the crystal senses a finger *through the glass*. A covert double-tap "develops"
  the usage layer for a few seconds, then it fades back to the dial — reusing the same
  self-reverting overlay pattern the wifi config card already uses (`Display.flash_config`).
- **Worn palm-side**, the reveal faces only you.

That makes Payband a three-mode discreet display: **Time / Earnings / Claude-usage**, on
one hardware family.

This rides the existing roadmap: the usage mode here is **v1** (software-only, on the
current OLED); the Sharp panel + RTC + covert touch is **v1.5**; the Cartier-Tank luxe
enclosure is **v2**.

---

## Honest caveats

- **The official subscription % has no API.** The watch shows a local estimate; it will
  diverge from the in-app Settings → Usage figure. Don't treat it as the real number.
- **The Admin API is org-only** and only covers metered API spend — not Pro/Max Claude
  Code usage. The core experience deliberately doesn't depend on it.
- **Freshness:** a glance can be up to ~1 minute stale (bridge poll + watch poll). The
  `STALE` / `NO-LINK` states exist so it never shows confidently-wrong numbers.
- **Cost is tokens-first.** `cost_today_cents` is `null` for now; pricing changes per
  model and is best left to a tool like ccusage. Tokens and burn are the reliable headline.
- **Keys stay on the bridge.** Never put an API key (or a long-lived relay secret) on the
  watch.
