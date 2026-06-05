# Payband

**A discreet little money-ticker for your wrist.** Set your hourly rate, clock
in, and watch your earnings climb in real time — worn palm-side so it's for you,
not a billboard for the room.

Built for people paid by the hour who want to *feel* the money accruing. Smaller
than a watch, no cloud, no app to install. Your phone configures it over the
device's own wifi; after that it counts entirely on its own.

> Status: **v1 — bench prototype.** Firmware is complete and runnable; the
> wearable enclosure is in progress. See the [roadmap](#roadmap).

---

## How it works

- The board runs its **own wifi network** (`Payband`). Join it from your phone,
  open `http://192.168.4.1`, and a one-page panel lets you set your rate and
  clock in/out.
- It counts **locally on the chip** — once set, the screen just shows the number
  climbing. Earnings are simply `rate × time_worked ÷ 3600`.
- A single **button** on the device: tap to clock in/out, hold to flash the wifi
  name + address on screen.

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

## Project layout

```
src/
  main.py       entry point — wires everything together, runs the async loop
  config.py     all tunables: pins, wifi name/password, timings
  state.py      earnings state machine (pure logic, no hardware)
  display.py    OLED rendering — the money ticker + wifi config card
  button.py     async short/long press detection
  server.py     SoftAP + tiny HTTP server + the phone control panel
  ssd1306.py    vendored MicroPython OLED driver (MIT)
docs/
  WIRING.md     pinout, diagram, charging, LiPo safety
  FLASHING.md   install MicroPython + upload the files
```

The firmware has **no external dependencies** — everything it needs is either in
MicroPython or vendored here, so there's nothing to `pip install` onto the board.

---

## Roadmap

- **v1 — now:** tap to clock in, set rate from your phone, watch earnings climb.
- **v1.5:** add a **DS3231 real-time clock** → scheduled auto clock-in ("set the
  time you start work"), and survives a battery swap mid-shift. Gate the wifi AP
  behind the long-press so it only sips power when you're actually configuring.
- **v2:** shrink it. Proper palm-side enclosure, smaller OLED, tuned battery
  life. The actual wearable.
- **someday:** daily/weekly totals, overtime multipliers, a tap-to-see-today view.

---

## License

MIT — see [`LICENSE`](LICENSE).
