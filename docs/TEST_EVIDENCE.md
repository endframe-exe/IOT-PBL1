# AgriSense Formal Test Verification & Evidence Dossier

**Document Release:** v1.1 Academic Evidence Dossier  
**Course Context:** DEC0101 / DEC0151 - Digital Electronics & IoT Systems  
**Author Team:** Group 11  
**Generation Timestamp:** `2026-11-23 21:12:50 UTC`  
**Verification Scope:** Modules 1 through 5, PRD TC-01 to TC-12, and Specification Lock v1.1  

---

## 1. Executive Test Summary

- **Core Scenario Tests (TC-01 to TC-12):** 12/12 PASSED
- **Boolean Combinational Min-terms:** 16/16 VERIFIED
- **Empty Database Fault Tolerance:** VERIFIED (zero crashes, exact schema preserved)
- **PDF Binary Integrity:** VERIFIED (Valid `%PDF` binary header, styled tables, disclaimer present)
- **CSV Export Integrity:** VERIFIED (UTF-8 bytes, disclaimer preamble prepended)

---

## 2. Acceptance Test Results Matrix (TC-01 through TC-12)

| Test ID | Scenario Name | Test Stimulus | Expected Behavior | Actual Behavior | Result |
| :---: | :--- | :--- | :--- | :--- | :---: |
| `TC-01` | **Normal Irrigation Zone 1** | Z1=20%, Z2=65%, Tank=90%, Rain=OFF | Pump ON (1), Zone 1 selected, Z1 +5%, Tank -2%, State=ZONE_1_ACTIVE | Pump=1, Zone=ZONE_1, Z1=25.0%, Tank=88.0%, State=ZONE_1_ACTIVE | **PASS** |
| `TC-02` | **Rain Safety Interlock** | Z1=20%, Tank=90%, Rain=ON | Pump OFF (0), IDLE, No active zone, Alarm=0 | Pump=0, Zone=NONE, State=IDLE, Alarm=0 | **PASS** |
| `TC-03` | **Low Tank Safety Lock** | Tank=10% (<20% safe threshold) | Pump OFF (0), Alarm=1, State=FAULT_LOCK | Pump=0, Alarm=1, State=FAULT_LOCK | **PASS** |
| `TC-04` | **Zone 2 Selection** | Z1=65% (adequate), Z2=20% (dry), Tank=90%, Rain=OFF | Pump ON (1), Zone 2 selected, Z2 +5%, State=ZONE_2_ACTIVE | Pump=1, Zone=ZONE_2, Z2=25.0%, State=ZONE_2_ACTIVE | **PASS** |
| `TC-05` | **Zone 1 Priority Encoder** | Both Z1=20% and Z2=20% dry, Tank=90%, Rain=OFF | Pump ON (1), Zone 1 selected (strict priority), State=ZONE_1_ACTIVE | Pump=1, Zone=ZONE_1, State=ZONE_1_ACTIVE | **PASS** |
| `TC-06` | **Both Zones Adequate (IDLE)** | Z1=55%, Z2=60%, Tank=90%, Rain=OFF, Manual=OFF | Pump OFF (0), IDLE state, No active zone | Pump=0, Zone=NONE, State=IDLE | **PASS** |
| `TC-07` | **Manual Override Safe Routing** | Both zones wet, Tank=90%, Rain=OFF, Manual=ON | Pump ON (1), Routes to default manual target (Zone 1) | Pump=1, Zone=ZONE_1, State=ZONE_1_ACTIVE | **PASS** |
| `TC-08` | **Manual Blocked by Rain** | Manual=ON, Rain=ON, Tank=90% | Pump OFF (0), Rain interlock suppresses manual override | Pump=0, State=IDLE | **PASS** |
| `TC-09` | **Manual Blocked by Low Tank** | Manual=ON, Tank=12% (<20%) | Pump OFF (0), Alarm=1, State=FAULT_LOCK | Pump=0, Alarm=1, State=FAULT_LOCK | **PASS** |
| `TC-10` | **MOD-16 Fertigation Event** | Active irrigation advances counter to Count 4 | Counter=4 (0100), Fertigation active=True, PIPO Q1=1 | Counter=4 (0100), Fertigation=True, Q1=1 | **PASS** |
| `TC-11` | **MOD-16 Watchdog Emergency Lock** | Active irrigation advances counter to Count 15 with pipe_burst_fault=True | Counter=15 (1111), Watchdog tripped=True, State=FAULT_LOCK, Pump=0, Alarm=1 | Counter=15 (1111), Watchdog=True, State=FAULT_LOCK, Pump=0, Q0=1 | **PASS** |
| `TC-12` | **Empty DB & Export Integrity** | Query empty SQLite database; generate PDF/CSV from empty & populated datasets | No crash; empty DataFrame preserved; valid %PDF headers; SIMULATED DATA disclaimers | Empty DF cols=13, PDF empty=2706B, PDF pop=4225B, CSV header present=True | **PASS** |

---

## 3. Combinational Boolean Truth Table Audit (Module 2)

The complete 16-row truth table was audited for strict compliance with the safety policy equations:

$$P = W \cdot \overline{R} \cdot (O + M), \quad A = \overline{W}$$

| Min-term | M | W | R | O | P (Pump) | A (Alarm) | Operational Verification Summary | Status |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :---: |
| `m0` | 0 | 0 | 0 | 0 | **0** | **1** | Tank empty; pump cut off; low water alarm active | **PASS** |
| `m1` | 0 | 0 | 0 | 1 | **0** | **1** | Tank empty; manual override blocked by low-water interlock | **PASS** |
| `m2` | 0 | 0 | 1 | 0 | **0** | **1** | Tank empty and rain detected; dual safety interlock active | **PASS** |
| `m3` | 0 | 0 | 1 | 1 | **0** | **1** | Tank empty and rain; manual override safely suppressed | **PASS** |
| `m4` | 0 | 1 | 0 | 0 | **0** | **0** | Soil moist, tank safe, no rain; system idle (P=0) | **PASS** |
| `m5` | 0 | 1 | 0 | 1 | **1** | **0** | Manual override active with safe tank and no rain (P=1) | **PASS** |
| `m6` | 0 | 1 | 1 | 0 | **0** | **0** | Rain detected; automatic irrigation suppressed | **PASS** |
| `m7` | 0 | 1 | 1 | 1 | **0** | **0** | Rain detected; manual override blocked by rain interlock | **PASS** |
| `m8` | 1 | 0 | 0 | 0 | **0** | **1** | Soil dry but tank empty; pump blocked by tank interlock | **PASS** |
| `m9` | 1 | 0 | 0 | 1 | **0** | **1** | Soil dry and manual ON, but tank empty; low water alarm active | **PASS** |
| `m10` | 1 | 0 | 1 | 0 | **0** | **1** | Soil dry, tank empty, and rain; dual safety interlock active | **PASS** |
| `m11` | 1 | 0 | 1 | 1 | **0** | **1** | Soil dry, empty tank, rain, manual ON; all safety interlocks active | **PASS** |
| `m12` | 1 | 1 | 0 | 0 | **1** | **0** | Normal automated irrigation: soil dry, tank safe, no rain (P=1) | **PASS** |
| `m13` | 1 | 1 | 0 | 1 | **1** | **0** | Automated + manual demand active under safe conditions (P=1) | **PASS** |
| `m14` | 1 | 1 | 1 | 0 | **0** | **0** | Soil dry but natural rain detected; pump safely suppressed | **PASS** |
| `m15` | 1 | 1 | 1 | 1 | **0** | **0** | Soil dry, manual ON, but rain detected; rain interlock active | **PASS** |

---

## 4. Reporting & Persistence Audit

### 4.1 Empty Database Handling (`TC-12`)
- **Query Execution:** `DatabaseManager.fetch_events()` executed against clean SQLite database with 0 rows.
- **DataFrame Schema:** Preserved all 13 columns (`id, timestamp, zone1, zone2, tank, rain, manual, pump, active_zone, fsm_state, counter, alarm, message`).
- **Summary Metrics:** Returned zero counts without `NoneType` or `ZeroDivisionError`.

### 4.2 PDF Generation (`reports.py`)
- **Populated Report Size:** 4225 bytes.
- **Empty-State Report Size:** 2706 bytes.
- **Format Verification:** Begins with standard `%PDF-1.4` magic bytes.
- **Mandatory Compliance Disclaimer:** Formatted in amber callout block:  
  > *"SIMULATED DATA — Educational Prototype (AgriSense, Group 11). All sensor readings, soil hydrology, and actuator signals are generated by software models for DEC0101/DEC0151 coursework. No physical sensor accuracy or field agronomic performance is claimed."*

### 4.3 CSV Export (`reports.py`)
- **UTF-8 Output:** 3534 bytes with metadata header.
- **Header Preamble:** `# SIMULATED DATA — Educational Prototype (AgriSense, Group 11)`

---

## 5. Certification Sign-off

This dossier confirms that the AgriSense software core satisfies all functional, architectural, and educational requirements specified in the DEC0101 syllabus.

**Chief Systems Engineering Verdict: APPROVED FOR ACADEMIC CITATION**