# AgriSense: Smart Irrigation Monitoring System

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests Passing](https://img.shields.io/badge/tests-45%20passed-brightgreen.svg)]()
[![DEC0101 Syllabus](https://img.shields.io/badge/syllabus-DEC0101%20DEC0151-forestgreen.svg)]()
[![Wokwi Parity](https://img.shields.io/badge/hardware-Wokwi%20Uno-orange.svg)](https://wokwi.com/projects/new/arduino-uno)
[![GitHub Repository](https://img.shields.io/badge/GitHub-endframe--exe%2FIOT--PBL1-black.svg)](https://github.com/endframe-exe/IOT-PBL1)

> **Academic Project Notice:**  
> First-Year B.Tech Project-Based Learning (PBL) in **Digital Electronics & IoT Systems (DEC0101 / DEC0151)**  
> **Team:** Group 11  
> **Repository:** [https://github.com/endframe-exe/IOT-PBL1](https://github.com/endframe-exe/IOT-PBL1)  
> **Simulation Disclaimer:** All sensor measurements, soil hydrology values, and actuator signals in this software and firmware prototype represent deterministic simulation models for academic coursework and viva defense. No physical sensor accuracy or commercial crop yield savings are claimed.

---

## 1. System Overview & Digital Twin

**AgriSense** is an educational, production-grade cyber-physical smart irrigation controller that unifies **combinational Boolean logic, sequential finite-state machines, synchronous counters, parallel registers, 2.5D Blender-shaded virtual farm digital twin, and embedded microcontroller hardware simulation** into a single cohesive agricultural technology system.

### Key Capabilities
- **2.5D Isometric Digital Twin:** Shaded canvas simulator (`assets/virtual_farm_twin.html`) with interactive 1-click switches for Rain, Zone 1 & 2 Irrigation, Manual Pump, NPK Fertigation, Empty Tank Fault, and Pipe Burst Watchdog.
- **Pure Python Core:** Decoupled digital electronics engine (`digital_core.py`) with zero external runtime dependencies.
- **Hardware-Software Parity:** Standalone Arduino Uno embedded firmware and schematic (`firmware/wokwi/`) running the exact same logic equations and state machine on physical embedded silicon.
- **1-Click Windows Launcher:** Launch the entire application with one double-click using `START_AGRISENSE.bat`.

---

## 2. Live System Architecture

```text
+-----------------------------------------------------------------------------------+
|                            VIRTUAL FARM ENVIRONMENT                               |
|        Zone 1 Moisture (%)  |  Zone 2 Moisture (%)  |  Reservoir Capacity (%)      |
|             Rainfall Switch (R)     |     Manual Override Switch (O)              |
+-----------------------------------------+-----------------------------------------+
                                          |
                        +-----------------+-----------------+
                        |                                   |
                [Streamlit Controls]                [Wokwi Arduino Uno]
                 app.py (Web Browser)             sketch.ino (Physical C++)
                        |                                   |
                        +-----------------+-----------------+
                                          |
                      +-------------------v-------------------+
                      |      DIGITAL ELECTRONICS CORE         |
                      |          (digital_core.py)            |
                      |                                       |
                      |  1. Quantization & 74LS85 Comparator  |
                      |  2. Boolean Safety Interlocks (P, A)  |
                      |  3. Schmitt Hysteresis (<30%, >=45%)  |
                      |  4. 2-Bit Sequential FSM (00..11)     |
                      |  5. MOD-16 Counter & Watchdog Limit   |
                      |  6. 4-Bit PIPO Status Register        |
                      +-------------------+-------------------+
                                          |
                        +-----------------+-----------------+
                        |                                   |
               [SQLite Data Store]                 [Export Services]
                  (database.py)                       (reports.py)
            - Thread-safe events log            - ReportLab PDF reports
            - Summary metrics                   - UTF-8 CSV datasets
```

---

## 3. Syllabus Module Mapping & Group 11 Team Ownership

To ensure complete clarity during academic viva defenses and faculty reviews, every repository file is explicitly mapped to the DEC0101/DEC0151 5-module syllabus and assigned to a primary team lead:

| Syllabus Module | Subject Coverage | Implementation Files | Primary Viva Owner | Key Theoretical Concepts |
| :---: | :--- | :--- | :--- | :--- |
| **Module 1** | Number Systems & Codes | [digital_core.py](file:///c:/Users/akhil/Downloads/PBL%20PROJECTS/IOT%20PBL/gemini%20project/digital_core.py) | **Member 1** (Systems Lead) | 4-bit A/D quantization ($0000_2 \to 1111_2$), binary representation, 74LS85 magnitude comparator ($S < T$) |
| **Module 2** | Boolean Algebra & Gate Logic | [digital_core.py](file:///c:/Users/akhil/Downloads/PBL%20PROJECTS/IOT%20PBL/gemini%20project/digital_core.py), [test_agrisense.py](file:///c:/Users/akhil/Downloads/PBL%20PROJECTS/IOT%20PBL/gemini%20project/test_agrisense.py) | **Member 2** (Logic Engineer) | Equations $P = W \cdot \overline{R} \cdot (O + M)$, $A = \overline{W}$, 16-row Truth Table, K-Map reduction, safety interlocks |
| **Module 3** | Combinational Logic & Hysteresis | [digital_core.py](file:///c:/Users/akhil/Downloads/PBL%20PROJECTS/IOT%20PBL/gemini%20project/digital_core.py) | **Member 3** (Sequential Lead) | Schmitt-trigger moisture hysteresis ($<30\%$ ON, $\ge 45\%$ OFF), strict zone priority encoder, manual routing |
| **Module 4** | Sequential Logic, Counters & Registers | [digital_core.py](file:///c:/Users/akhil/Downloads/PBL%20PROJECTS/IOT%20PBL/gemini%20project/digital_core.py), [database.py](file:///c:/Users/akhil/Downloads/PBL%20PROJECTS/IOT%20PBL/gemini%20project/database.py) | **Member 4** (Data & FSM Eng.) | 2-bit D flip-flop FSM (`00`, `01`, `10`, `11`), MOD-16 counter, Fertigation pulse (Count 4), Watchdog trip (Count 15), 4-bit PIPO register |
| **Module 5** | Embedded Microcontroller & Hardware Parity | [sketch.ino](file:///c:/Users/akhil/Downloads/PBL%20PROJECTS/IOT%20PBL/gemini%20project/firmware/wokwi/sketch.ino), [diagram.json](file:///c:/Users/akhil/Downloads/PBL%20PROJECTS/IOT%20PBL/gemini%20project/firmware/wokwi/diagram.json) | **Member 5** (Embedded Lead) | Arduino Uno C++, ADC pot conditioning, optocoupled relay isolation, I2C LCD, debounced clocking, serial telemetry |
| **Full Stack** | UI, 3D Digital Twin & Reporting | [app.py](file:///c:/Users/akhil/Downloads/PBL%20PROJECTS/IOT%20PBL/gemini%20project/app.py), [virtual_farm_twin.html](file:///c:/Users/akhil/Downloads/PBL%20PROJECTS/IOT%20PBL/gemini%20project/assets/virtual_farm_twin.html), [reports.py](file:///c:/Users/akhil/Downloads/PBL%20PROJECTS/IOT%20PBL/gemini%20project/reports.py) | **Entire Team** | Streamlit web presentation, 2.5D canvas shader, ReportLab PDF generation, SQLite persistence |

---

## 4. Formal Design Change Log (Safety Interlock Upgrade)

In preliminary **Progress Report I**, the initial draft pump equation permitted manual override to bypass rainfall:

$$\text{Draft Equation (Progress Report I): } \quad P = W \cdot (O + M \cdot \overline{R})$$

*Engineering Hazard Identified:* Under this early formulation, if rainfall was active ($R = 1$) but manual override was accidentally toggled ($O = 1$), the pump energized, creating severe electrical hazard, soil waterlogging, and water wastage.

**Final Release Upgrade (Locked in SPEC_LOCK.md):**

$$P = W \cdot \overline{R} \cdot (O + M)$$
$$A = \overline{W}$$

*Guarantees Established:*
1. **Unconditional Rain Interlock:** Rainfall ($\overline{R}$) is a master multiplicative series interlock. Rain shuts the pump OFF unconditionally ($P = 0$), even if manual override is engaged.
2. **Unconditional Tank Interlock:** Low reservoir level ($W = 0$) shuts the pump OFF unconditionally ($P = 0$) and asserts the Low-Level Alarm ($A = 1$).
3. **Explicit Alarm Nomenclature:** Output $A$ is explicitly defined as the *Reservoir Low-Level Interlock Alarm*, eliminating confusion when the system asserts $A = 1$ from `IDLE`.

---

## 5. Quickstart & Installation Guide

### Option A: 1-Click Windows Launcher (Recommended for Demos)
Simply double-click:
```text
START_AGRISENSE.bat
```
*What this script does:*
1. Detects Python 3.10+ in system PATH.
2. Creates `.venv` and installs `requirements.txt` automatically if missing.
3. Opens `http://localhost:8501` in your default browser.
4. Starts the Streamlit application server.

---

### Option B: Manual Setup (Windows PowerShell)
```powershell
# 1. Clone repository & enter workspace
git clone https://github.com/endframe-exe/IOT-PBL1.git
cd IOT-PBL1

# 2. Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install pinned dependencies
pip install -r requirements.txt

# 4. Run automated test suite (45 tests)
pytest -v

# 5. Launch Streamlit Dashboard
streamlit run app.py
```

---

### Option C: Manual Setup (Linux / macOS)
```bash
# 1. Clone repository & enter workspace
git clone https://github.com/endframe-exe/IOT-PBL1.git
cd IOT-PBL1

# 2. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install pinned dependencies
pip install -r requirements.txt

# 4. Run automated test suite (45 tests)
pytest -v

# 5. Launch Streamlit Dashboard
streamlit run app.py
```

---

## 6. Wokwi Hardware Simulation Setup

Run our standalone embedded microcontroller simulation directly in your browser:
1. Open the [Wokwi Arduino Uno Simulator](https://wokwi.com/projects/new/arduino-uno).
2. Paste the contents of [firmware/wokwi/sketch.ino](file:///c:/Users/akhil/Downloads/PBL%20PROJECTS/IOT%20PBL/gemini%20project/firmware/wokwi/sketch.ino) into the sketch editor.
3. Paste the contents of [firmware/wokwi/diagram.json](file:///c:/Users/akhil/Downloads/PBL%20PROJECTS/IOT%20PBL/gemini%20project/firmware/wokwi/diagram.json) into the diagram tab.
4. Click **Start Simulation (Play)**.
5. **Interactive Hardware Controls:**
   - Potentiometers: `A0` (Zone 1 Soil), `A1` (Zone 2 Soil), `A2` (Tank Level).
   - Slide Switches: `D2` (Rain Sensor), `D3` (Manual Override).
   - Pushbuttons: `D4` (Debounced Clock Pulse), `D5` (Fault Reset).
   - Actuator Indicators: `D8` (Relay), `D9` (Zone 1 LED), `D10` (Zone 2 LED), `D11` (Fertigation LED), `D12` (Alarm LED).
   - Live I2C LCD Display on `A4`/`A5` (0x27).

---

## 7. Verification & Automated Evidence Generation

To run the automated verification suite and compile the academic evidence report:
```powershell
pytest -v
python scripts/generate_evidence.py
```
This validates all 12 acceptance test scenarios (`TC-01` to `TC-12`), audits all 16 truth table minterms, verifies PDF and CSV export byte integrity, and compiles [docs/TEST_EVIDENCE.md](file:///c:/Users/akhil/Downloads/PBL%20PROJECTS/IOT%20PBL/gemini%20project/docs/TEST_EVIDENCE.md).

---

## 8. Repository File Directory

```text
IOT-PBL1/
├── START_AGRISENSE.bat      # 1-Click automated Windows demo launcher
├── digital_core.py          # Modules 1–4: Pure Python digital electronics engine
├── database.py              # Persistence: SQLite thread-safe event logger
├── reports.py               # Document generation: ReportLab PDF & CSV exports
├── app.py                   # Presentation: 5-tab Streamlit dashboard with 3D twin
├── test_agrisense.py        # Automated test suite (45 unit & integration tests)
├── requirements.txt         # Pinned production dependencies
├── SPEC_LOCK.md             # Locked architectural specifications v1.1
├── README.md                # Complete developer & examiner documentation
├── assets/
│   └── virtual_farm_twin.html # 2.5D Blender-shaded canvas digital twin
├── scripts/
│   └── generate_evidence.py # Acceptance scenario runner & dossier generator
├── firmware/
│   └── wokwi/
│       ├── diagram.json     # Wokwi Arduino Uno circuit schematic
│       └── sketch.ino       # Standalone C++ embedded firmware
└── docs/
    ├── TEST_EVIDENCE.md     # Formal acceptance test evidence dossier
    └── devlog/              # Automated engineering audit log
```

---

*AgriSense • DEC0101 / DEC0151 Digital Electronics & IoT Systems PBL • Group 11 • [GitHub Repository](https://github.com/endframe-exe/IOT-PBL1)*
