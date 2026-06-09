# Payband wall display

A fullscreen **Claude usage HUD** for a wall-mounted panel. It's just a web page
([`index.html`](index.html)) that polls your [`payband-bridge`](../bridge/) for the
usage JSON — so it reuses the exact same data source as the watch. Big glanceable
numbers, a 5-hour-window ring, burn rate, today's totals, in a dark HELMTEK-style
schematic look.

Nothing personal is baked in: you pass your bridge's address in the URL.

---

## See it right now (no hardware needed)

On the computer where you use Claude Code:

```bash
# 1. start the bridge (serves your usage JSON on :8088)
python bridge/payband_bridge.py

# 2. open the dashboard in any browser, pointed at the bridge
#    wall/index.html?bridge=http://localhost:8088/usage
```

Open `index.html` and add `?bridge=http://localhost:8088/usage` to the URL. That's
the whole thing, working, in a browser — before any panel arrives.

---

## The wall build (bare 15.6" panel → Raspberry Pi kiosk)

```
15.6" IPS panel ──ribbon(eDP/LVDS)── driver board ──HDMI── Raspberry Pi
                                       │ USB-C / 12V power      │ Chromium --kiosk
                                       └────────────────        │  fetches the bridge
                                                                 │  over your wifi
                 payband-bridge (your PC) ──/usage JSON──────────┘
```

### 1. The driver board (the part you must match to YOUR panel)

A bare panel can't take HDMI/USB directly — it speaks **eDP** (usually a slim 30-pin
flat connector) or **LVDS** (wider, ~40-pin). You need a controller board built for
*your exact panel*:

1. Read the **LCD model number** off the white barcode sticker on the metal back
   (looks like `B156HAN01.2`, `NT156FHM-N31`, `LP156WF6`, etc.).
2. Note the **resolution** (15.6" IPS "full view" is almost always 1920×1080) and the
   **connector** (count the ribbon pins; modern 1080p IPS is typically eDP 30-pin).
3. Buy a board listed as compatible with that model, with an **HDMI input** (for the
   Pi). Sellers like VSDISPLAY / AliExpress configure the board's firmware + EDID to
   the panel — give them your model number. ~$18–30.
4. **Single-cable bonus:** pick a board with a **USB-C power** input so the whole panel
   runs off one USB-C brick.

> 📷 Tip: tell the maintainer (or paste into an issue) your LCD model + ribbon pin
> count and someone can point you at the exact board.

### 2. The Raspberry Pi (kiosk mode)

Any Pi works; a **Pi Zero 2 W** is plenty for a static dashboard, a **Pi 4** is
smoother. Flash **Raspberry Pi OS (with desktop)**, connect it to wifi, then:

```bash
sudo apt update && sudo apt install -y chromium-browser unclutter
mkdir -p ~/payband && cp index.html ~/payband/    # copy this dashboard onto the Pi
```

Auto-start the kiosk on boot — add to `~/.config/lxsession/LXDE-pi/autostart`
(replace `PC-IP` with the LAN IP of the computer running the bridge):

```
@xset s off
@xset -dpms
@xset s noblank
@unclutter -idle 0
@chromium-browser --kiosk --noerrdialogs --disable-infobars --incognito \
  "file:///home/pi/payband/index.html?bridge=http://PC-IP:8088/usage"
```

Reboot. The Pi boots straight into the fullscreen HUD.

- Screen blanking is disabled so it stays on 24/7.
- If `file://` fetches get blocked, serve the page instead:
  `python3 -m http.server 8090 --directory ~/payband` and point Chromium at
  `http://localhost:8090/index.html?bridge=http://PC-IP:8088/usage`.
- Rotate the display if mounting in portrait: add `display_rotate=1` to
  `/boot/config.txt` (or `video=...` on newer OSes).

### 3. Wiring & power

- **Panel ribbon → driver board** (the board ships with the matching cable).
- **Driver board → Pi**: HDMI.
- **Power**: USB-C / barrel to the driver board; USB to the Pi. (Two small bricks, or
  one if your board does USB-C power-delivery passthrough.)
- Mount: VESA-less panels can sit in a slim 3D-printed/wood frame; tuck the Pi + board
  behind it.

---

## Notes

- The **bridge runs on your PC** (where your Claude logs live), not the Pi — the Pi
  just fetches `http://<PC-IP>:8088/usage` over your network. The bridge already sends
  `Access-Control-Allow-Origin: *`, so the cross-machine fetch works.
- The dashboard is tuned for a **landscape 1080p** panel.
- The 5-hour-window figure is a **local estimate** (see [`../docs/USAGE_WATCH.md`](../docs/USAGE_WATCH.md)).
- This is the wall sibling of the watch's usage mode — same bridge, bigger screen.
