# Changelog

All notable changes to Payband are documented here. The format loosely follows
[Keep a Changelog](https://keepachangelog.com).

## [Unreleased]

- v1.5 groundwork: DS3231 RTC for scheduled auto clock-in; gate the wifi AP
  behind the long-press to save battery.

## [0.1.0] — 2026-06-06

Initial firmware. Bench prototype.

### Added
- MicroPython firmware for Seeed XIAO ESP32-C3 + 0.96" SSD1306 OLED.
- Earnings state machine: tap to clock in, `earnings = rate × worked ÷ 3600`.
- SoftAP `Payband` + single-page phone control panel (set rate, clock in/out, reset).
- OLED money ticker with upscaled digits + wifi config card on long-press.
- Async short/long button handling.
- Wiring and flashing docs.
