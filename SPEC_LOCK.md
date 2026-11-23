# AgriSense Specification Lock v1.1: Engineering Overrides & Architecture Baseline

**Document Type:** Formal System Architecture Override Specification  
**System Codename:** AgriSense (Smart Irrigation Monitoring System)  
**Academic Alignment:** Digital Electronics & IoT Systems (DEC0101 / DEC0151 - Modules 1 through 5)  
**Baseline Document:** [AgriSense_Smart_Irrigation_PRD.md](file:///c:/Users/akhil/Downloads/PBL%20PROJECTS/IOT%20PBL/gemini%20project/AgriSense_Smart_Irrigation_PRD.md)  
**Status:** FROZEN & LOCKED  

---

## 1. Executive Summary & Rationale

This document establishes the binding architectural overrides to the AgriSense baseline PRD. In educational IoT engineering, prototypes often suffer from architectural fragmentation (over-modularization into dozens of micro-files before logic stabilization) and edge-case contradictions between combinational Boolean outputs and sequential FSM states. 

The v1.1 Specification Lock formalizes a cohesive, mathematically rigorous foundation ensuring:
1. **Zero Contradiction** between combinational outputs (`P`, `A`) and sequential state (`FSM_STATE`, `PIPO`).
2. **Deterministic Edge Transitions** during interactive faculty review and test runs.
3. **Hardware Parity** without fragile cloud networking dependencies.

---

## 2. Core Architectural Overrides

### 2.1 Compact 5-File Python Architecture
Rather than maintaining a fragmented 16-file micro-package hierarchy that introduces unnecessary import overhead and circular dependencies, the entire software core is consolidated into 5 high-cohesion, decoupled files:

```text
gemini project/
├── digital_core.py          # Module 1–4: Boolean logic, FSM, Counter, PIPO, & Plant Physics Engine
├── database.py              # Persistence layer: SQLite schema, connection management, telemetry logs
├── reports.py               # Document generation: ReportLab PDF builder & CSV data exports
├── app.py                   # Presentation layer: Multi-tab Streamlit interactive dashboard
├── test_agrisense.py        # Complete verification suite across all 5 syllabus modules
├── scripts/
│   └── generate_evidence.py # Automated end-to-end evidence generator for academic review
├── firmware/
│   └── wokwi/
│       ├── diagram.json     # Wokwi Arduino Uno circuit definition (sensors, LCD, relays, LEDs)
│       └── sketch.ino       # Standalone C++ firmware implementing DEC0101/0151 logic on hardware
├── docs/
│   └── devlog/              # Automated audit log and change-tracking registry
└── SPEC_LOCK.md             # This document
```

---

### 2.2 Boolean Safety Policy & Interlock Nomenclature (Modules 1 & 2)

#### Formal Equations
$$\mathbf{P} = \mathbf{W} \land \overline{\mathbf{R}} \land (\mathbf{O} \lor \mathbf{M})$$
$$\mathbf{A} = \overline{\mathbf{W}}$$

Where:
- $\mathbf{W}$ (Water Reservoir Safe): $1$ if Tank Level $\ge 20\%$, $0$ if Tank Level $< 20\%$.
- $\mathbf{R}$ (Rainfall Interlock): $1$ if Rain detected, $0$ if Dry.
- $\mathbf{O}$ (Manual Override): $1$ if Operator Manual Override is ON, $0$ if OFF.
- $\mathbf{M}$ (Soil Moisture Demand): $\mathbf{M}_1 \lor \mathbf{M}_2$ ($1$ if either zone asserts dry demand).
- $\mathbf{P}$ (Main Pump Relay Drive): $1$ indicates energized pump; $0$ indicates cut-off.
- $\mathbf{A}$ (Reservoir Low-Level Interlock Alarm): Renamed explicitly from generic "Alarm" to **Reservoir Low-Level Interlock Alarm**.

#### Operational Semantic Guarantee
- When the water tank is depleted ($\mathbf{W} = 0$), $\mathbf{A}$ asserts $1$ and $\mathbf{P}$ asserts $0$ unconditionally, irrespective of $\mathbf{O}$ or $\mathbf{M}$.
- Even when the system is in an un-clocked or idle state, a depleted tank triggers the Low-Level Interlock Alarm $\mathbf{A} = 1$ and forces the controller into `FAULT_LOCK` upon clock evaluation. This behavior is mathematically provable and intentional.

#### Complete 16-Row Truth Table (M, W, R, O)
| Row | M (Moisture Demand) | W (Water Safe >=20%) | R (Rainfall) | O (Manual Override) | P (Pump Output) | A (Low Tank Alarm) | System Operational Meaning |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **0** | 0 | 0 | 0 | 0 | **0** | **1** | Tank empty; system locked |
| **1** | 0 | 0 | 0 | 1 | **0** | **1** | Tank empty; manual override blocked by safety |
| **2** | 0 | 0 | 1 | 0 | **0** | **1** | Tank empty & rain; dual safety interlock |
| **3** | 0 | 0 | 1 | 1 | **0** | **1** | Tank empty & rain; manual override blocked |
| **4** | 0 | 1 | 0 | 0 | **0** | **0** | All conditions normal, soil moist; IDLE |
| **5** | 0 | 1 | 0 | 1 | **1** | **0** | Manual override active with safe tank & no rain |
| **6** | 0 | 1 | 1 | 0 | **0** | **0** | Rain detected; automatic irrigation suppressed |
| **7** | 0 | 1 | 1 | 1 | **0** | **0** | Rain detected; manual override blocked by rain |
| **8** | 1 | 0 | 0 | 0 | **0** | **1** | Soil dry but tank empty; pump blocked by tank interlock |
| **9** | 1 | 0 | 0 | 1 | **0** | **1** | Soil dry & manual ON, but tank empty; pump blocked |
| **10** | 1 | 0 | 1 | 0 | **0** | **1** | Dry soil, empty tank, rain; pump blocked |
| **11** | 1 | 0 | 1 | 1 | **0** | **1** | Dry soil, empty tank, rain, manual; pump blocked |
| **12** | 1 | 1 | 0 | 0 | **1** | **0** | Normal automated irrigation active |
| **13** | 1 | 1 | 0 | 1 | **1** | **0** | Automated + manual demand active; safe irrigation |
| **14** | 1 | 1 | 1 | 0 | **0** | **0** | Dry soil but rain active; natural rainfall prioritized |
| **15** | 1 | 1 | 1 | 1 | **0** | **0** | Dry soil + manual ON, but rain active; rain interlock active |

---

### 2.3 Schmitt-Trigger Soil Hysteresis (Module 3)

To prevent electromechanical relay chatter and erratic switching around boundary thresholds, Zone dry demand ($\mathbf{M}_z$) implements Schmitt-trigger hysteresis:

$$\mathbf{M}_z[t] = \begin{cases} 1 & \text{if } \text{Moisture}_z < 30\% \quad (\text{Dry Trip Threshold}) \\ 0 & \text{if } \text{Moisture}_z \ge 45\% \quad (\text{Wet Clear Threshold}) \\ \mathbf{M}_z[t-1] & \text{if } 30\% \le \text{Moisture}_z < 45\% \quad (\text{Deadband / Memory Zone}) \end{cases}$$

- **Zone Priority:** If both $\mathbf{M}_1 = 1$ and $\mathbf{M}_2 = 1$, Zone 1 has strict priority. Once Zone 1 satisfies hysteresis ($\ge 45\%$), Zone 2 automatically gains activation on the subsequent clock step.

---

### 2.4 Manual Override Routing Resolution

In the baseline PRD, asserting $\mathbf{O} = 1$ when both zones are wet ($\mathbf{M}_1=0, \mathbf{M}_2=0$) causes the combinational logic to demand $\mathbf{P} = 1$, yet standard priority logic would resolve to `IDLE` (no active zone valve), resulting in an illegal state: pump running against closed valves.

**Specification Resolution:**
- The system introduces an explicit configuration parameter: `manual_target_zone` (defaulting to `ZONE_1`, selectable to `ZONE_2`).
- When $\mathbf{O} = 1$, $\mathbf{W} = 1$, $\mathbf{R} = 0$, and $\mathbf{M} = 0$:
  - The controller transitions to the state corresponding to `manual_target_zone` (`ZONE_1_ACTIVE` or `ZONE_2_ACTIVE`).
  - The corresponding zone valve opens ($\mathbf{Q}_3 = 1$ or $\mathbf{Q}_2 = 1$).
  - Pump energizes ($\mathbf{P} = 1$).
  - `P = 1` never contradicts the FSM state.

---

### 2.5 MOD-16 Counter, Fertigation & Watchdog Semantics (Module 4)

- **Counter Width:** 4-bit synchronous binary counter ($0000_2$ to $1111_2$, $0$ to $15_{10}$).
- **Clock Increment Policy:** The counter increments by exactly $+1$ for every active irrigation simulation clock pulse (when $\mathbf{P} = 1$).
- **Clean Reset Policy:** When all demands are satisfied and the system transitions back to `IDLE`, the counter synchronously clears to $0$ ($0000_2$).
- **Fertigation Output Signal:** At Count **4** ($0100_2$), the simulated fertigation solenoid pulse asserts high (`fertigation_active = True`, reflected on PIPO bit $\mathbf{Q}_1$).
- **Watchdog Emergency Lock:** At Count **15** ($1111_2$), the counter trips the maximum continuous-run watchdog limit. The system latches into `FAULT_LOCK`, trips pump relay $\mathbf{P} = 0$, asserts the alarm, and requires an explicit operator reset.
- **Pipe-Burst Simulation Toggle (`pipe_burst_fault`):**
  - Under normal simulation, an active irrigation step increases zone soil moisture by $+5\%$ per step.
  - When `pipe_burst_fault = True`, soil moisture delta is clamped to $0.0\%$, simulating water escaping through a ruptured pipe without reaching the sensor.
  - This allows examiners and automated test suites to deterministically advance the simulation through all 16 counts ($0 \to 15$) to demonstrate the watchdog lockout without artificial hacks.

---

### 2.6 PIPO Output Register Representation

The Parallel-In Parallel-Out (PIPO) status register latches and displays the 4-bit operational vector:

$$\mathbf{PIPO} = [\mathbf{Q}_3, \mathbf{Q}_2, \mathbf{Q}_1, \mathbf{Q}_0]$$

| Register Bit | Signal Name | Description |
| :---: | :--- | :--- |
| **Q3** | Valve 1 Status | `1` when Zone 1 valve is energized, `0` when closed |
| **Q2** | Valve 2 Status | `1` when Zone 2 valve is energized, `0` when closed |
| **Q1** | Fertigation Pulse | `1` when Counter == 4 ($0100_2$), `0` otherwise |
| **Q0** | Alarm Output | `1` when Low Tank Interlock or Watchdog Fault is asserted |

---

### 2.7 Module 5 Hardware Parity: Wokwi Arduino Uno Implementation

Rather than relying on fragile cloud MQTT brokers or unstable external networking that fail during offline demonstrations, Module 5 is implemented as a standalone, zero-dependency Wokwi Arduino Uno simulation:
- **Board:** Arduino Uno R3.
- **Circuit (`firmware/wokwi/diagram.json`):**
  - Potentiometer 1 $\to$ Analog A0 (Zone 1 Soil Moisture).
  - Potentiometer 2 $\to$ Analog A1 (Zone 2 Soil Moisture).
  - Potentiometer 3 $\to$ Analog A2 (Reservoir Water Level).
  - Slide Switch 1 $\to$ Digital Pin 2 (Rain Sensor Switch).
  - Slide Switch 2 $\to$ Digital Pin 3 (Manual Override Switch).
  - Relay Module / LED $\to$ Digital Pin 8 (Pump Relay Drive).
  - LED Red $\to$ Digital Pin 9 (Alarm Indicator).
  - LED Yellow $\to$ Digital Pin 10 (Zone 1 Valve Indicator).
  - LED Green $\to$ Digital Pin 11 (Zone 2 Valve Indicator).
  - I2C LCD 1602 $\to$ Pins A4 (SDA) & A5 (SCL) displaying live FSM state, count, and pump telemetry.
- **Firmware (`firmware/wokwi/sketch.ino`):**
  - Implements the exact same Boolean logic equation and FSM transition matrix running on an 8-bit AVR microcontroller.
  - Demonstrates full cyber-physical parity between Python simulation and embedded C++ logic.

---

## 3. Syllabus Compliance Matrix (DEC0101 / DEC0151)

| Module | Syllabus Subject | AgriSense Implementation | Verification Vehicle |
| :---: | :--- | :--- | :--- |
| **Module 1** | Number Systems & Codes | BCD/Binary representation of MOD-16 counter, PIPO 4-bit hex/binary readout | Unit tests & Streamlit display |
| **Module 2** | Boolean Algebra & Gate Logic | Equations for $P$ and $A$, 16-row Truth Table, K-Map simplification proof | Unit tests & Truth Table viewer |
| **Module 3** | Combinational Logic & Hysteresis | Dual-zone priority encoder, Schmitt-trigger moisture hysteresis | Priority tests & hysteresis tests |
| **Module 4** | Sequential Logic & State Machines | 4-State Mealy/Moore FSM, D flip-flop clocking, MOD-16 counter, PIPO register | FSM transition test suite |
| **Module 5** | Embedded Microcontroller & IoT Parity | Standalone Arduino Uno Wokwi firmware, I2C LCD telemetry, actuator relays | C++ sketch & Wokwi simulation |

---

## 4. Engineering Verification Standard

All subsequent application code must pass `pytest -v` within `.venv` with 100% test coverage over:
1. All 16 truth table input permutations.
2. Hysteresis band holding ($30\% \to 44\%$ preserving state).
3. Priority selection between Zone 1 and Zone 2.
4. Watchdog trip at Count 15 with pipe-burst simulation.
5. SQLite event persistence and recovery.
6. PDF report binary integrity.
