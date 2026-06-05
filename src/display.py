"""
Payband - OLED rendering.

Two screens:
  * the money ticker (default)
  * a wifi "config card" (shown for a few seconds after a long-press)

Big digits are drawn by upscaling MicroPython's built-in 8x8 font, so we need
no external font files on the board.
"""

import time
import framebuf
from machine import Pin, I2C

import ssd1306
import config

# one reusable 8x8 glyph buffer for the upscaler
_GLYPH = bytearray(8)


class Display:
    def __init__(self):
        self.i2c = I2C(
            0,
            scl=Pin(config.PIN_SCL),
            sda=Pin(config.PIN_SDA),
            freq=config.I2C_FREQ,
        )
        self.oled = ssd1306.SSD1306_I2C(
            config.OLED_WIDTH, config.OLED_HEIGHT, self.i2c, addr=config.OLED_ADDR
        )
        self._config_until = 0  # ticks_ms deadline for the wifi card

    # ---------- helpers ----------
    def _big(self, s, x, y, scale, c=1):
        """Draw text upscaled by an integer factor using the 8x8 font."""
        gb = framebuf.FrameBuffer(_GLYPH, 8, 8, framebuf.MONO_HLSB)
        for ch in s:
            gb.fill(0)
            gb.text(ch, 0, 0, 1)
            for gy in range(8):
                for gx in range(8):
                    if gb.pixel(gx, gy):
                        self.oled.fill_rect(
                            x + gx * scale, y + gy * scale, scale, scale, c
                        )
            x += 8 * scale

    @staticmethod
    def _hms(total_s):
        total_s = int(total_s)
        h = total_s // 3600
        m = (total_s % 3600) // 60
        s = total_s % 60
        return "%dh %02dm" % (h, m) if h else "%dm %02ds" % (m, s)

    # ---------- public ----------
    def flash_config(self):
        self._config_until = time.ticks_add(time.ticks_ms(), config.CONFIG_CARD_MS)

    def render(self, state):
        if time.ticks_diff(self._config_until, time.ticks_ms()) > 0:
            self._render_config()
        else:
            self._render_main(state)
        self.oled.show()

    # ---------- screens ----------
    def _render_main(self, state):
        o = self.oled
        o.fill(0)

        # top row: status + rate
        o.text("ON" if state.running else "OFF", 0, 0, 1)
        rate_s = "%.2f/hr" % state.rate
        o.text(rate_s, config.OLED_WIDTH - 8 * len(rate_s), 0, 1)

        # big money, centred
        amount = state.earnings()
        if amount > 9999.99:
            amount = 9999.99
        money = "%s%.2f" % (config.CURRENCY, amount)
        scale = 3 if len(money) <= 5 else 2
        w = len(money) * 8 * scale
        x = max(0, (config.OLED_WIDTH - w) // 2)
        self._big(money, x, 24, scale)

        # bottom row: elapsed time worked
        o.text(self._hms(state.worked_s()), 0, config.OLED_HEIGHT - 8, 1)

    def _render_config(self):
        o = self.oled
        o.fill(0)
        o.text("-- CONFIG --", 16, 0, 1)
        o.text("WiFi", 0, 18, 1)
        o.text(config.AP_SSID, 48, 18, 1)
        o.text("Pass", 0, 30, 1)
        o.text(config.AP_PASSWORD, 48, 30, 1)
        o.text("Go to", 0, 48, 1)
        o.text(config.AP_IP, 48, 48, 1)
