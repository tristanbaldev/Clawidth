## What this does

Brief description of the change.

## Hardware tested on

- Board / OLED / MicroPython version — or "logic-only change, not flashed".

## Checklist

- [ ] Firmware stays dependency-free and MicroPython-compatible
- [ ] New tunables (if any) live in `src/config.py`
- [ ] Syntax check passes — `python -c "import ast,glob;[ast.parse(open(f,encoding='utf-8').read(),filename=f) for f in glob.glob('src/*.py')]"`
- [ ] Docs updated if behavior changed
