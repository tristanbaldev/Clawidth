"""
Payband - earnings state machine.

Deliberately hardware-free: this is pure logic, easy to reason about (and it
even runs on desktop Python for testing).

Model
-----
v1 never needs the wall-clock time of day. It only counts *elapsed* time since
you tapped "clock in", and earnings are just:

    earnings = rate_per_hour * worked_seconds / 3600

  - accumulated_s : time banked from previous (clocked-out) sessions
  - session_start : a monotonic tick marker for the current running session
  - mode          : which screen the watch shows ("earnings" or "usage")

v1 limitation: there is no real-time clock, so if the board fully loses power
mid-shift, the in-flight session time is lost (your rate and banked time still
survive). v1.5 adds a DS3231 RTC to fix this and to enable a scheduled
auto-clock-in.
"""

import json
import time

try:
    from config import STATE_FILE
except ImportError:
    STATE_FILE = "state.json"

MODES = ("earnings", "usage")


def _now_ms():
    return time.ticks_ms()


class Payband:
    def __init__(self, rate=15.0, accumulated_s=0.0, running=False, mode="earnings"):
        self.rate = float(rate)
        self.accumulated_s = float(accumulated_s)
        self.running = bool(running)
        self.mode = mode if mode in MODES else "earnings"
        # session_start is RAM-only; re-based on boot or on clock-in.
        self.session_start = _now_ms() if self.running else None

    # ---------- persistence ----------
    @classmethod
    def load(cls):
        try:
            with open(STATE_FILE) as f:
                d = json.load(f)
            return cls(
                rate=d.get("rate", 15.0),
                accumulated_s=d.get("accumulated_s", 0.0),
                running=d.get("running", False),
                mode=d.get("mode", "earnings"),
            )
        except (OSError, ValueError):
            return cls()

    def save(self):
        try:
            with open(STATE_FILE, "w") as f:
                json.dump(
                    {
                        "rate": self.rate,
                        "accumulated_s": self.accumulated_s,
                        "running": self.running,
                        "mode": self.mode,
                    },
                    f,
                )
        except OSError:
            pass

    # ---------- live time accounting ----------
    def session_s(self):
        if not self.running or self.session_start is None:
            return 0.0
        return time.ticks_diff(_now_ms(), self.session_start) / 1000.0

    def worked_s(self):
        return self.accumulated_s + self.session_s()

    def earnings(self):
        return self.rate * self.worked_s() / 3600.0

    # ---------- actions ----------
    def clock_in(self):
        if not self.running:
            self.running = True
            self.session_start = _now_ms()
            self.save()

    def clock_out(self):
        if self.running:
            self.accumulated_s += self.session_s()
            self.running = False
            self.session_start = None
            self.save()

    def toggle(self):
        self.clock_out() if self.running else self.clock_in()

    def set_rate(self, rate):
        try:
            r = float(rate)
        except (TypeError, ValueError):
            return
        self.rate = r if r >= 0 else 0.0
        self.save()

    def set_mode(self, mode):
        if mode in MODES:
            self.mode = mode
            self.save()

    def reset(self):
        self.accumulated_s = 0.0
        if self.running:
            self.session_start = _now_ms()
        self.save()
