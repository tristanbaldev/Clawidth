"""
Clawidth - async button watcher.

Active-low button on config.PIN_BUTTON (other leg to GND, internal pull-up).

  short press -> on_short()   (clock in / out)
  long  press -> on_long()    (show the wifi config card)

The long-press fires once, the moment the hold crosses LONG_PRESS_MS, so it
feels instant rather than waiting for you to let go.
"""

try:
    import asyncio
except ImportError:
    import uasyncio as asyncio

import time
from machine import Pin

import config


async def watch_button(on_short, on_long):
    btn = Pin(config.PIN_BUTTON, Pin.IN, Pin.PULL_UP)
    pressed_at = None
    long_fired = False

    while True:
        down = btn.value() == 0  # active low
        now = time.ticks_ms()

        if down:
            if pressed_at is None:
                pressed_at = now
                long_fired = False
            elif not long_fired and time.ticks_diff(now, pressed_at) >= config.LONG_PRESS_MS:
                long_fired = True
                on_long()
        else:
            if pressed_at is not None:
                held = time.ticks_diff(now, pressed_at)
                if not long_fired and held >= config.DEBOUNCE_MS:
                    on_short()
                pressed_at = None

        await asyncio.sleep_ms(20)
