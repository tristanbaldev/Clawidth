# Contributing to Payband

Thanks for being here! Payband is a small, friendly open-source hardware project,
and contributions of every size are welcome — code, docs, a fix for a board
variant I haven't tested, or just a good bug report.

## Ways to help

- **Report a bug or a board quirk** — open an [issue](https://github.com/tristanbaldev/Payband/issues)
  and include your hardware (board, OLED, MicroPython version).
- **Test on hardware** — different XIAO / ESP32-C3 batches, OLED addresses
  (`0x3C` vs `0x3D`), or battery setups. Real-world reports are gold.
- **Improve the firmware** — see the roadmap in the [README](README.md).
- **Share an enclosure** — STLs / strap designs for the wearable build are very welcome.
- **Polish the docs** — if `WIRING.md` or `FLASHING.md` tripped you up, fix it for the next person.

## Dev setup

You don't need the hardware to work on the logic.

1. Install tooling: `pip install mpremote esptool` (and [Thonny](https://thonny.org) if you like a GUI).
2. Flash MicroPython and upload `src/` — full steps in [`docs/FLASHING.md`](docs/FLASHING.md).
3. `src/state.py` is pure logic (no hardware imports), so you can poke at the
   earnings math on desktop Python.

## Conventions

- **Keep it dependency-free.** The board should need nothing `pip`-installed —
  everything is either built into MicroPython or vendored (see `src/ssd1306.py`).
- **MicroPython-compatible only** — no CPython-only stdlib.
- **All tunables go in `src/config.py`** — don't hardcode pins, wifi names, or timings elsewhere.
- Match the existing module style: small, single-purpose files with short docstrings.

## Before you open a PR

Run the same check CI runs (validates every module parses):

```bash
python -c "import ast,glob; [ast.parse(open(f,encoding='utf-8').read(),filename=f) for f in glob.glob('src/*.py')]; print('ok')"
```

Then:

1. Branch off `main`.
2. Keep PRs small and focused; describe **what hardware you tested on**.
3. Update the docs if behavior changed.

That's it. Be kind, have fun, build something cool. 🛠️
