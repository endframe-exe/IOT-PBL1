# Segment 05: Wokwi Embedded Firmware & Hardware Parity Devlog

### [2026-11-24 02:39] Update #6: Wokwi Arduino Uno Circuit & Embedded Firmware
- **Syllabus / System Scope:** Module 5 (Arduino Programming, Sensor/Actuator Interfacing & IoT Telemetry)
- **Files Changed:** `firmware/wokwi/sketch.ino`, `firmware/wokwi/diagram.json`, `test_agrisense.py`
- **What Changed:**
  - Authored standalone embedded C++ firmware `firmware/wokwi/sketch.ino` running on an Arduino Uno (ATmega328P) with complete mathematical parity to `digital_core.py`.
  - Implemented exact Boolean logic equations ($P = W \land \overline{R} \land (O \lor M)$ and $A = \overline{W}$), Schmitt-trigger hysteresis ($<30\%$ dry trip, $\ge 45\%$ wet clear), 2-bit sequential FSM (`IDLE` `00`, `ZONE_1_ACTIVE` `01`, `ZONE_2_ACTIVE` `10`, `FAULT_LOCK` `11`), MOD-16 counter (Count 4 fertigation, Count 15 watchdog timeout), and 4-bit PIPO register.
  - Interfaced optocoupler relay module on pin D8 (guaranteeing physical motor isolation), status LEDs on D9–D12 with 220-ohm resistors, debounced clock pulse (D4) and reset (D5) pushbuttons, analog potentiometers (A0–A2), and LiquidCrystal_I2C 16x2 LCD on A4/A5.
  - Transmits live JSON telemetry over 9600-baud serial on every clock step.
  - Authored Wokwi schematic `firmware/wokwi/diagram.json` connecting all components ready for one-click simulation on wokwi.com.
  - Added automated test `test_wokwi_firmware_and_diagram_parity` in `test_agrisense.py` auditing JSON validity, threshold constant parity, and zero pin conflicts.
- **Why (Engineering Reasoning):** Replaces fragile cloud MQTT brokers with a self-contained embedded hardware simulation package, achieving 100% cyber-physical parity between the Python simulation core and physical microcontroller firmware for the DEC0101 syllabus.
- **Verification Status:** Diagram JSON validated, threshold parity verified, and `.\.venv\Scripts\pytest -v` executed with 45/45 tests passing in 2.65s (PASS).
