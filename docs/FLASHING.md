# Flashing & uploading

Two parts: (1) put **MicroPython** on the board once, (2) copy the Payband files
onto it. Pick the command-line route or the beginner-friendly Thonny GUI.

---

## 0. Find the COM port

Plug the XIAO in via USB-C. On Windows, open **Device Manager → Ports (COM & LPT)**
and note the `COMx`. Or:

```bash
mpremote connect list
```

---

## Option A — command line (mpremote + esptool)

```bash
pip install esptool mpremote
```

**1. Get the firmware:** download the latest `ESP32_GENERIC_C3` `.bin` from
<https://micropython.org/download/ESP32_GENERIC_C3/>

**2. Erase + flash MicroPython** (replace `COM5` and the filename):

```bash
esptool --chip esp32c3 --port COM5 erase_flash
esptool --chip esp32c3 --port COM5 --baud 460800 write_flash -z 0x0 ESP32_GENERIC_C3-20xxxxxx-vx.xx.bin
```

> If flashing fails, hold the **BOOT** button while plugging in to force
> bootloader mode, then run the command.

**3. Upload Payband** (run from the repo root):

```bash
mpremote connect COM5 fs cp src/ssd1306.py src/config.py src/state.py src/display.py src/button.py src/server.py src/main.py :
```

**4. Reboot and watch it run:**

```bash
mpremote connect COM5 reset
mpremote connect COM5 repl     # Ctrl-] to exit; shows any errors
```

---

## Option B — Thonny (GUI, easiest)

1. Install Thonny: <https://thonny.org>
2. **Tools → Options → Interpreter** → choose *MicroPython (ESP32)* and your COM port.
3. Click **"Install or update MicroPython"**, pick the `ESP32-C3` variant, install.
4. Open each file in `src/`, then **File → Save as → MicroPython device**, keeping
   the **same filename** (e.g. `main.py`). Do this for all seven files.
5. Press the board's reset, or **Stop/Restart** in Thonny. `main.py` runs on boot.

---

## First light ✨

When it boots you should see `$0.00` on the OLED. Then:

1. On your phone, join wifi **`Payband`** (password `payday123`).
2. Open **http://192.168.4.1** in a browser.
3. Set your hourly rate → **SAVE RATE**.
4. **CLOCK IN** (or tap the button on the device) and watch the cents climb.

Hold the device button (~1.2 s) any time to flash the wifi name/IP on screen.

---

## Tweaking

All pins, wifi name/password, and timings live in `src/config.py`. Edit, re-copy
that one file, reset. With Thonny you can also just edit on the device and hit run.
