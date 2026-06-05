"""
Payband - central configuration.

Every tunable lives here so no other file hardcodes a pin, a wifi name, or a
timing constant. Change things here, re-upload, done.
"""

# --- Display (SSD1306 OLED over I2C) ---
OLED_WIDTH = 128
OLED_HEIGHT = 64
OLED_ADDR = 0x3C            # most 0.96" modules are 0x3C; a few are 0x3D

# --- Pins (Seeed XIAO ESP32-C3; silk-screen labels in comments) ---
PIN_SDA = 6                 # D4
PIN_SCL = 7                 # D5
PIN_BUTTON = 3              # D1  (wire the button's other leg to GND)
I2C_FREQ = 400_000

# --- Button timing (milliseconds) ---
DEBOUNCE_MS = 30
LONG_PRESS_MS = 1200        # hold this long -> show the wifi "config card"

# --- Wi-Fi access point (this is the network your PHONE joins) ---
AP_SSID = "Payband"
AP_PASSWORD = "payday123"   # must be >= 8 chars. CHANGE THIS.
AP_IP = "192.168.4.1"       # default SoftAP address, shown on the config card

# --- Display behaviour ---
REFRESH_HZ = 10             # how often the money ticker redraws (cents ticking)
CONFIG_CARD_MS = 6000       # how long the wifi card stays up after a long-press
CURRENCY = "$"

# --- Persistence ---
STATE_FILE = "state.json"
