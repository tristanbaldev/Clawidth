"""
Clawidth - entry point.

Wires the OLED, the button, the persistent state, the optional Claude-usage
client, and the wifi config server together and runs them concurrently with
asyncio. This file auto-runs on boot.
"""

try:
    import asyncio
except ImportError:
    import uasyncio as asyncio

import config
from state import Clawidth
from display import Display
from button import watch_button
from usage import Usage, usage_loop
import server


async def display_loop(disp, state, usage):
    delay = max(1, 1000 // config.REFRESH_HZ)
    while True:
        try:
            disp.render(state, usage)
        except Exception:
            pass
        await asyncio.sleep_ms(delay)


async def main():
    state = Clawidth.load()
    disp = Display()
    usage = Usage()

    def on_short():
        state.toggle()          # tap = clock in / clock out

    def on_long():
        disp.flash_config()     # hold = show wifi card

    asyncio.create_task(display_loop(disp, state, usage))
    asyncio.create_task(watch_button(on_short, on_long))
    asyncio.create_task(usage_loop(usage))   # no-op unless wifi + bridge configured
    await server.serve(state)

    while True:                 # keep the event loop alive
        await asyncio.sleep(3600)


try:
    asyncio.run(main())
except KeyboardInterrupt:
    pass
