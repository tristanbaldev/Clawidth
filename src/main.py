"""
Payband - entry point.

Wires the OLED, the button, the persistent state, and the wifi config server
together and runs them concurrently with asyncio. This file auto-runs on boot.
"""

try:
    import asyncio
except ImportError:
    import uasyncio as asyncio

import config
from state import Payband
from display import Display
from button import watch_button
import server


async def display_loop(disp, state):
    delay = max(1, 1000 // config.REFRESH_HZ)
    while True:
        try:
            disp.render(state)
        except Exception:
            pass
        await asyncio.sleep_ms(delay)


async def main():
    state = Payband.load()
    disp = Display()

    def on_short():
        state.toggle()          # tap = clock in / clock out

    def on_long():
        disp.flash_config()     # hold = show wifi card

    asyncio.create_task(display_loop(disp, state))
    asyncio.create_task(watch_button(on_short, on_long))
    await server.serve(state)

    while True:                 # keep the event loop alive
        await asyncio.sleep(3600)


try:
    asyncio.run(main())
except KeyboardInterrupt:
    pass
