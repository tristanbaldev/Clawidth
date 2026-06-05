# Wiring

Everything runs off the **Seeed XIAO ESP32-C3**. Four wires for the screen, two
for the button, two for the battery. That's the whole build.

## Connections

| From (component)      | To (XIAO ESP32-C3) | Notes                          |
|-----------------------|--------------------|--------------------------------|
| OLED `VCC`            | `3V3`              | not 5V                         |
| OLED `GND`            | `GND`              |                                |
| OLED `SDA`            | `D4` (GPIO6)       | I2C data                       |
| OLED `SCL`            | `D5` (GPIO7)       | I2C clock                      |
| Button leg A          | `D1` (GPIO3)       | uses the internal pull-up      |
| Button leg B          | `GND`              |                                |
| LiPo `+`              | `B+` pad (back)    | onboard charger — no TP4056    |
| LiPo `-`              | `B-` pad (back)    |                                |

The button needs **no resistor** — the firmware enables the ESP32's internal
pull-up, so the pin idles HIGH and reads LOW when you press.

## Diagram

```
            XIAO ESP32-C3
          +---------------+
   3V3 ---| 3V3       5V  |
   GND ---| GND       D10 |
          | D0/A0     D9  |
          | D1/A1 *---|   |---* button --- GND
          | D2/A2     D7  |
          | D3        D6  |
   SDA ---| D4        D5  |--- SCL
          +---------------+
            (B+)   (B-)         <- LiPo solders to the pads on the back
              |     |
            LiPo + / -

   OLED:  VCC->3V3  GND->GND  SDA->D4  SCL->D5
```

## Charging

The XIAO ESP32-C3 has a LiPo charger built in. Plug a USB-C cable into the
**XIAO's own port** to charge the battery — no separate charging board needed.
Default charge current is gentle (~100 mA), which is fine for a small cell.

## ⚠️ LiPo safety

- Never let `B+` and `B-` touch each other (dead short = fire risk).
- Tape over the cell so you can't puncture it while building.
- Don't leave the **first** charge unattended.
- A puffy/swollen cell is done — recycle it, don't use it.

## Address gotcha

Most 0.96" OLEDs are at I2C address `0x3C`. If the screen stays black, scan the
bus and try `0x3D` in `src/config.py`:

```python
from machine import Pin, I2C
print(I2C(0, scl=Pin(7), sda=Pin(6)).scan())   # prints e.g. [60] -> 0x3C
```
