"""
Clawidth - central configuration.

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
AP_SSID = "Clawidth"
AP_PASSWORD = "payday123"   # must be >= 8 chars. CHANGE THIS.
AP_IP = "192.168.4.1"       # default SoftAP address, shown on the config card

# --- Display behaviour ---
REFRESH_HZ = 10             # how often the money ticker redraws (cents ticking)
CONFIG_CARD_MS = 6000       # how long the wifi card stays up after a long-press
CURRENCY = "$"

# --- Persistence ---
STATE_FILE = "state.json"

# --- Claude usage mode (OPTIONAL) ---
# Leave WIFI_SSID empty to disable usage mode entirely. To turn it on, each
# builder fills in THEIR OWN 2.4GHz network and the address of THEIR OWN
# clawidth-bridge (see the /bridge folder). Nothing here ships with a real value,
# and the watch never holds an API key - only your bridge does.
WIFI_SSID = ""              # your 2.4 GHz network name (ESP32-C3 is 2.4 GHz only)
WIFI_PASSWORD = ""          # your network password
BRIDGE_URL = ""             # e.g. "http://192.168.1.50:8088/usage"  (plain http, LAN)
USAGE_POLL_S = 30           # how often the watch refreshes usage
USAGE_STALE_S = 180         # a reading older than this is shown as STALE
