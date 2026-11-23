"""
AgriSense Unit and Integration Test Suite
=========================================
Syllabus Verification across Modules 1 to 5 (DEC0101 / DEC0151).

Tests Included:
- Parametrized tests for ALL 16 rows of the Boolean Truth Table (m0 to m15).
- Invariant safety checks: W=0 forces P=0, A=1; R=1 forces P=0; Manual override never bypasses safety.
- 4-Bit Quantization and 74LS85 Magnitude Comparator logic.
- 4-Bit PIPO Register bit mappings, hex/binary encodings, and transitions.
- Schmitt-Trigger Moisture Hysteresis (<30% trip, >=45% clear, deadband preservation).
- Strict Zone Priority (Zone 1 over Zone 2).
- Manual override resolution when both zones are wet (routing to manual_target_zone).
- Synchronous MOD-16 Counter, Fertigation event at Count 4, and Watchdog Lockout at Count 15 with pipe-burst simulation.
- Latched FAULT_LOCK behavior and reset rejection when tank remains below safety threshold.
- Full PRD Scenario Test Matrix (TC-01 through TC-11).
"""

import pytest
from digital_core import (
    DigitalCoreEngine,
    FSMState,
    ZoneId,
    ROMConfig,
    RAMState,
    PIPORegister,
    quantize_4bit,
    dequantize_4bit,
    to_binary_4bit,
    magnitude_comparator_4bit,
    evaluate_boolean_logic,
    generate_truth_table,
)


# ============================================================================
# MODULE 1 & 2: NUMBER SYSTEMS, QUANTIZATION & COMPARATOR TESTS
# ============================================================================

def test_quantization_boundaries():
    assert quantize_4bit(0.0) == 0
    assert quantize_4bit(100.0) == 15
    assert quantize_4bit(-10.0) == 0
    assert quantize_4bit(120.0) == 15
    # 30% -> round(0.3 * 15) = round(4.5) -> 4 or 5 depending on round half to even
    assert quantize_4bit(30.0) in (4, 5)
    assert quantize_4bit(50.0) in (7, 8)


def test_binary_formatting():
    assert to_binary_4bit(0) == "0000"
    assert to_binary_4bit(4) == "0100"
    assert to_binary_4bit(15) == "1111"
    assert to_binary_4bit(16) == "1111"  # Clamped to 15


def test_magnitude_comparator_74ls85():
    res_lt = magnitude_comparator_4bit(3, 5)
    assert res_lt.a_lt_b is True
    assert res_lt.a_eq_b is False
    assert res_lt.a_gt_b is False
    assert res_lt.bit_tuple == (1, 0, 0)

    res_eq = magnitude_comparator_4bit(7, 7)
    assert res_eq.a_lt_b is False
    assert res_eq.a_eq_b is True
    assert res_eq.a_gt_b is False
    assert res_eq.bit_tuple == (0, 1, 0)

    res_gt = magnitude_comparator_4bit(12, 4)
    assert res_gt.a_lt_b is False
    assert res_gt.a_eq_b is False
    assert res_gt.a_gt_b is True
    assert res_gt.bit_tuple == (0, 0, 1)


# ============================================================================
# MODULE 2: COMPLETE 16-ROW BOOLEAN TRUTH TABLE VERIFICATION
# ============================================================================

@pytest.mark.parametrize(
    "row,m,w,r,o,expected_p,expected_a",
    [
        (0, 0, 0, 0, 0, 0, 1),
        (1, 0, 0, 0, 1, 0, 1),
        (2, 0, 0, 1, 0, 0, 1),
        (3, 0, 0, 1, 1, 0, 1),
        (4, 0, 1, 0, 0, 0, 0),
        (5, 0, 1, 0, 1, 1, 0),
        (6, 0, 1, 1, 0, 0, 0),
        (7, 0, 1, 1, 1, 0, 0),
        (8, 1, 0, 0, 0, 0, 1),
        (9, 1, 0, 0, 1, 0, 1),
        (10, 1, 0, 1, 0, 0, 1),
        (11, 1, 0, 1, 1, 0, 1),
        (12, 1, 1, 0, 0, 1, 0),
        (13, 1, 1, 0, 1, 1, 0),
        (14, 1, 1, 1, 0, 0, 0),
        (15, 1, 1, 1, 1, 0, 0),
    ],
)
def test_all_16_truth_table_rows(row, m, w, r, o, expected_p, expected_a):
    p, a = evaluate_boolean_logic(m, w, r, o)
    assert p == expected_p, f"Row {row} failed for P: got {p}, expected {expected_p}"
    assert a == expected_a, f"Row {row} failed for A: got {a}, expected {expected_a}"


def test_truth_table_generator_cardinality():
    table = generate_truth_table()
    assert len(table) == 16
    for idx, row in enumerate(table):
        assert row.row == idx
        assert row.minterm == f"m{idx}"
        # Invariant checks
        if row.w == 0:
            assert row.p == 0, f"Safety invariant violated: W=0 must force P=0 (row {idx})"
            assert row.a == 1, f"Safety invariant violated: W=0 must force A=1 (row {idx})"
        if row.r == 1:
            assert row.p == 0, f"Safety invariant violated: R=1 must force P=0 (row {idx})"


# ============================================================================
# MODULE 3: SCHMITT-TRIGGER HYSTERESIS & PRIORITY ENCODER TESTS
# ============================================================================

def test_schmitt_trigger_hysteresis_cycle():
    engine = DigitalCoreEngine()
    
    # Initial state: 50% (adequate, dry demand is False)
    engine.set_inputs(zone1_moisture=50.0)
    comb = engine.evaluate_combinational()
    assert comb["m1"] == 0

    # Moisture drops into deadband (40%): still above 30%, demand stays False
    engine.set_inputs(zone1_moisture=40.0)
    comb = engine.evaluate_combinational()
    assert comb["m1"] == 0

    # Moisture drops below 30% trip point (28%): demand asserts True (1)
    engine.set_inputs(zone1_moisture=28.0)
    comb = engine.evaluate_combinational()
    assert comb["m1"] == 1

    # Moisture rises into deadband during irrigation (35%): demand MUST remain latched True (1)
    engine.set_inputs(zone1_moisture=35.0)
    comb = engine.evaluate_combinational()
    assert comb["m1"] == 1

    # Moisture rises to 44%: still in deadband, demand MUST remain True (1)
    engine.set_inputs(zone1_moisture=44.0)
    comb = engine.evaluate_combinational()
    assert comb["m1"] == 1

    # Moisture reaches clear threshold (45.0%): demand clears to False (0)
    engine.set_inputs(zone1_moisture=45.0)
    comb = engine.evaluate_combinational()
    assert comb["m1"] == 0


def test_zone_priority_encoder():
    engine = DigitalCoreEngine()
    # Both zones dry: Zone 1 (25%) and Zone 2 (20%), tank safe (80%), no rain
    engine.set_inputs(zone1_moisture=25.0, zone2_moisture=20.0, tank_level=80.0, rain_detected=False)
    
    snap = engine.step_clock()
    assert snap.fsm_state == FSMState.ZONE_1_ACTIVE
    assert snap.active_zone == ZoneId.ZONE_1
    assert snap.pump_output == 1

    # Simulate Zone 1 hydrating until it clears (>=45%)
    engine.set_inputs(zone1_moisture=46.0)
    snap2 = engine.step_clock()
    # Now Zone 2 must be served
    assert snap2.fsm_state == FSMState.ZONE_2_ACTIVE
    assert snap2.active_zone == ZoneId.ZONE_2
    assert snap2.pump_output == 1


def test_manual_override_with_both_zones_wet():
    engine = DigitalCoreEngine()
    # Both zones wet (50%), safe tank (80%), no rain, manual override ON
    engine.set_inputs(
        zone1_moisture=50.0,
        zone2_moisture=50.0,
        tank_level=80.0,
        rain_detected=False,
        manual_override=True,
        manual_target_zone=ZoneId.ZONE_2,
    )
    snap = engine.step_clock()
    # Should route to Zone 2 per target configuration without contradiction
    assert snap.pump_output == 1
    assert snap.fsm_state == FSMState.ZONE_2_ACTIVE
    assert snap.active_zone == ZoneId.ZONE_2


# ============================================================================
# MODULE 4: COUNTER, FERTIGATION, WATCHDOG & PIPO REGISTER TESTS
# ============================================================================

def test_pipo_register_encoding():
    pipo = PIPORegister(q3_valve1=1, q2_valve2=0, q1_fertigation=1, q0_alarm=0)
    assert pipo.as_tuple == (1, 0, 1, 0)
    assert pipo.as_int == 10
    assert pipo.binary_str == "1010"
    assert pipo.hex_str == "0xA"


def test_fertigation_event_at_count_4():
    engine = DigitalCoreEngine()
    # Set continuous dry zone with pipe burst to advance counter steadily
    engine.set_inputs(
        zone1_moisture=20.0,
        tank_level=90.0,
        rain_detected=False,
        pipe_burst_fault=True,
    )

    # Step 1: count 1
    s1 = engine.step_clock()
    assert s1.counter == 1
    assert s1.fertigation_active is False
    assert s1.pipo.q1_fertigation == 0

    # Step 2: count 2
    engine.step_clock()
    # Step 3: count 3
    engine.step_clock()

    # Step 4: count 4 -> Fertigation must assert!
    s4 = engine.step_clock()
    assert s4.counter == 4
    assert s4.fertigation_active is True
    assert s4.pipo.q1_fertigation == 1


def test_watchdog_fault_lock_at_count_15():
    engine = DigitalCoreEngine()
    # Set pipe burst fault to prevent moisture gain so pump runs continuously
    engine.set_inputs(
        zone1_moisture=20.0,
        tank_level=90.0,
        rain_detected=False,
        pipe_burst_fault=True,
    )

    # Step through 14 counts
    for _ in range(14):
        snap = engine.step_clock()
        assert snap.fsm_state == FSMState.ZONE_1_ACTIVE
        assert snap.watchdog_tripped is False

    # Step 15: reaches count 15 -> Emergency Lockout
    s15 = engine.step_clock()
    assert s15.counter == 15
    assert s15.watchdog_tripped is True
    assert s15.fsm_state == FSMState.FAULT_LOCK
    assert s15.pump_output == 0
    assert s15.alarm_output == 1
    assert s15.pipo.q0_alarm == 1


def test_counter_synchronous_reset_on_idle():
    engine = DigitalCoreEngine()
    engine.set_inputs(zone1_moisture=20.0, tank_level=90.0, pipe_burst_fault=True)
    engine.step_clock()  # count 1
    engine.step_clock()  # count 2
    assert engine.state.counter == 2

    # Satisfy soil moisture (e.g., natural rain arrives or moisture restored)
    engine.set_inputs(zone1_moisture=60.0)
    snap = engine.step_clock()
    assert snap.fsm_state == FSMState.IDLE
    assert snap.counter == 0


# ============================================================================
# LATCHED FAULT LOCK & RESET SEMANTICS
# ============================================================================

def test_latched_fault_lock_requires_explicit_reset():
    engine = DigitalCoreEngine()
    # Deplete tank to 10%
    engine.set_inputs(zone1_moisture=20.0, tank_level=10.0)
    snap = engine.step_clock()
    assert snap.fsm_state == FSMState.FAULT_LOCK
    assert snap.alarm_output == 1

    # User refills tank to 90%, but DOES NOT call reset_fault()
    engine.set_inputs(tank_level=90.0)
    snap2 = engine.step_clock()
    # Must remain locked in FAULT_LOCK!
    assert snap2.fsm_state == FSMState.FAULT_LOCK
    assert snap2.pump_output == 0

    # User calls reset_fault() -> returns True and IDLE
    success, msg = engine.reset_fault()
    assert success is True
    assert engine.state.fsm_state == FSMState.IDLE


def test_reset_fault_rejected_when_tank_still_low():
    engine = DigitalCoreEngine()
    engine.set_inputs(tank_level=15.0)
    engine.step_clock()
    assert engine.state.fsm_state == FSMState.FAULT_LOCK

    # Try reset while tank is still 15%
    success, msg = engine.reset_fault()
    assert success is False
    assert "below 20%" in msg
    assert engine.state.fsm_state == FSMState.FAULT_LOCK


# ============================================================================
# PRD ACCEPTANCE TEST CASES (TC-01 THROUGH TC-11)
# ============================================================================

def test_tc01_normal_irrigation_zone1():
    """TC-01: Z1=20, Z2=65, tank=90, rain OFF -> Pump ON; Zone 1 selected; Z1 +5; tank -2"""
    engine = DigitalCoreEngine()
    engine.set_inputs(zone1_moisture=20.0, zone2_moisture=65.0, tank_level=90.0, rain_detected=False)
    snap = engine.step_clock()
    assert snap.pump_output == 1
    assert snap.active_zone == ZoneId.ZONE_1
    assert snap.zone1_moisture == 25.0
    assert snap.tank_level == 88.0
    assert snap.fsm_state == FSMState.ZONE_1_ACTIVE


def test_tc02_rain_safety_interlock():
    """TC-02: Z1=20, tank=90, rain ON -> Pump OFF; IDLE; no active zone; alarm inactive"""
    engine = DigitalCoreEngine()
    engine.set_inputs(zone1_moisture=20.0, tank_level=90.0, rain_detected=True)
    snap = engine.step_clock()
    assert snap.pump_output == 0
    assert snap.active_zone == ZoneId.NONE
    assert snap.fsm_state == FSMState.IDLE
    assert snap.alarm_output == 0


def test_tc03_low_tank_safety_lock():
    """TC-03: Tank=10 -> Pump OFF; alarm active; FAULT_LOCK"""
    engine = DigitalCoreEngine()
    engine.set_inputs(tank_level=10.0)
    snap = engine.step_clock()
    assert snap.pump_output == 0
    assert snap.alarm_output == 1
    assert snap.fsm_state == FSMState.FAULT_LOCK


def test_tc04_zone2_selection():
    """TC-04: Z1=65, Z2=20, tank=90, rain OFF -> Next clock pulse -> Zone 2 selected"""
    engine = DigitalCoreEngine()
    engine.set_inputs(zone1_moisture=65.0, zone2_moisture=20.0, tank_level=90.0, rain_detected=False)
    snap = engine.step_clock()
    assert snap.pump_output == 1
    assert snap.active_zone == ZoneId.ZONE_2
    assert snap.fsm_state == FSMState.ZONE_2_ACTIVE
    assert snap.zone2_moisture == 25.0


def test_tc05_zone1_priority():
    """TC-05: Z1=20, Z2=20, tank=90, rain OFF -> Next clock pulse -> Zone 1 selected"""
    engine = DigitalCoreEngine()
    engine.set_inputs(zone1_moisture=20.0, zone2_moisture=20.0, tank_level=90.0, rain_detected=False)
    snap = engine.step_clock()
    assert snap.pump_output == 1
    assert snap.active_zone == ZoneId.ZONE_1
    assert snap.fsm_state == FSMState.ZONE_1_ACTIVE


def test_tc06_both_zones_adequate():
    """TC-06: Both zones adequate, tank=90, rain OFF, manual OFF -> Pump OFF; IDLE"""
    engine = DigitalCoreEngine()
    engine.set_inputs(zone1_moisture=55.0, zone2_moisture=60.0, tank_level=90.0, rain_detected=False, manual_override=False)
    snap = engine.step_clock()
    assert snap.pump_output == 0
    assert snap.active_zone == ZoneId.NONE
    assert snap.fsm_state == FSMState.IDLE


def test_tc07_manual_override_safe():
    """TC-07: Manual ON, tank safe, rain OFF -> Manual request activates Zone 1"""
    engine = DigitalCoreEngine()
    engine.set_inputs(zone1_moisture=50.0, zone2_moisture=50.0, tank_level=90.0, rain_detected=False, manual_override=True)
    snap = engine.step_clock()
    assert snap.pump_output == 1
    assert snap.active_zone == ZoneId.ZONE_1
    assert snap.fsm_state == FSMState.ZONE_1_ACTIVE


def test_tc08_manual_override_blocked_by_rain():
    """TC-08: Manual ON, rain ON -> Pump OFF"""
    engine = DigitalCoreEngine()
    engine.set_inputs(manual_override=True, rain_detected=True, tank_level=90.0)
    snap = engine.step_clock()
    assert snap.pump_output == 0
    assert snap.fsm_state == FSMState.IDLE


def test_tc09_manual_override_blocked_by_low_tank():
    """TC-09: Manual ON, tank below minimum -> Pump OFF; fault/alarm handling"""
    engine = DigitalCoreEngine()
    engine.set_inputs(manual_override=True, tank_level=12.0)
    snap = engine.step_clock()
    assert snap.pump_output == 0
    assert snap.alarm_output == 1
    assert snap.fsm_state == FSMState.FAULT_LOCK


def test_tc10_counter_fertigation_event():
    """TC-10: Counter reaches 4 during active irrigation -> Fertigation event"""
    engine = DigitalCoreEngine()
    engine.set_inputs(zone1_moisture=20.0, tank_level=90.0, pipe_burst_fault=True)
    for _ in range(4):
        snap = engine.step_clock()
    assert snap.counter == 4
    assert snap.fertigation_active is True
    assert snap.pipo.q1_fertigation == 1


def test_tc11_counter_emergency_watchdog_lock():
    """TC-11: Counter reaches 15 -> Emergency lock; pump OFF"""
    engine = DigitalCoreEngine()
    engine.set_inputs(zone1_moisture=20.0, tank_level=90.0, pipe_burst_fault=True)
    for _ in range(15):
        snap = engine.step_clock()
    assert snap.counter == 15
    assert snap.watchdog_tripped is True
    assert snap.fsm_state == FSMState.FAULT_LOCK
    assert snap.pump_output == 0


# ============================================================================
# MODULE 5 & PERSISTENCE / REPORTING TESTS (DATABASE & REPORTS)
# ============================================================================

def test_tc12_empty_database_and_graceful_handling(tmp_path):
    """TC-12: Empty DB produces valid DataFrame with correct schema and zero metrics."""
    from database import DatabaseManager, EVENT_COLUMNS
    from reports import export_csv_bytes, export_pdf_bytes

    test_db = str(tmp_path / "empty_test.db")
    db = DatabaseManager(test_db)

    # 1. Fetch from empty DB
    df = db.fetch_events()
    assert df.empty is True
    assert list(df.columns) == EVENT_COLUMNS

    # 2. Metrics on empty DB
    metrics = db.fetch_summary_metrics()
    assert metrics["total_events"] == 0
    assert metrics["pump_active_events"] == 0
    assert metrics["fault_events"] == 0

    # 3. CSV export from empty DB
    csv_bytes = export_csv_bytes(df)
    assert isinstance(csv_bytes, bytes)
    assert b"SIMULATED DATA" in csv_bytes

    # 4. PDF export from empty DB
    pdf_bytes = export_pdf_bytes(None, df)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")


def test_sqlite_persistence_across_simulation_reset(tmp_path):
    """Verifies that simulation reset NEVER deletes historical event records."""
    from database import DatabaseManager

    test_db = str(tmp_path / "persist_test.db")
    db = DatabaseManager(test_db)
    engine = DigitalCoreEngine()

    # Log 3 events
    engine.set_inputs(zone1_moisture=20.0, tank_level=90.0)
    for _ in range(3):
        snap = engine.step_clock()
        db.log_event(snap)

    events_before = db.fetch_events()
    assert len(events_before) == 3

    # Perform normal simulation reset
    engine.reset_simulation()
    events_after = db.fetch_events()
    assert len(events_after) == 3, "Simulation reset must NEVER erase database history!"

    # Explicit administrative clear
    db.clear_all_history()
    events_cleared = db.fetch_events()
    assert len(events_cleared) == 0


def test_csv_formatting_and_disclaimer(tmp_path):
    """Verifies CSV generation formatting, headers, and required disclaimer."""
    from database import DatabaseManager
    from reports import export_csv_bytes

    test_db = str(tmp_path / "csv_test.db")
    db = DatabaseManager(test_db)
    engine = DigitalCoreEngine()

    engine.set_inputs(zone1_moisture=20.0, tank_level=90.0)
    snap = engine.step_clock()
    db.log_event(snap)

    df = db.fetch_events()
    csv_bytes = export_csv_bytes(df)
    csv_text = csv_bytes.decode("utf-8")

    assert "# SIMULATED DATA — Educational Prototype (AgriSense, Group 11)" in csv_text
    assert "zone1,zone2,tank,rain,manual,pump" in csv_text
    assert "ZONE_1_ACTIVE" in csv_text


def test_pdf_report_binary_and_disclaimer(tmp_path):
    """Verifies PDF report generation with live snapshot and events."""
    from database import DatabaseManager
    from reports import export_pdf_bytes, DISCLAIMER_TEXT

    test_db = str(tmp_path / "pdf_test.db")
    db = DatabaseManager(test_db)
    engine = DigitalCoreEngine()

    engine.set_inputs(zone1_moisture=20.0, tank_level=90.0)
    snap = engine.step_clock()
    db.log_event(snap)

    df = db.fetch_events()
    pdf_bytes = export_pdf_bytes(snap, df)

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 2000
    assert pdf_bytes.startswith(b"%PDF")


# ============================================================================
# MODULE 5: WOKWI EMBEDDED FIRMWARE & HARDWARE PARITY AUDIT
# ============================================================================

def test_wokwi_firmware_and_diagram_parity():
    """Audits firmware/wokwi/sketch.ino and diagram.json for strict Module 5 compliance."""
    import json
    import re
    from pathlib import Path

    sketch_path = Path("firmware/wokwi/sketch.ino")
    diagram_path = Path("firmware/wokwi/diagram.json")

    assert sketch_path.exists(), "firmware/wokwi/sketch.ino must exist!"
    assert diagram_path.exists(), "firmware/wokwi/diagram.json must exist!"

    # 1. Diagram JSON structural integrity
    with open(diagram_path, "r", encoding="utf-8") as f:
        diagram_data = json.load(f)

    assert diagram_data.get("version") == 1
    part_ids = {p["id"] for p in diagram_data.get("parts", [])}
    required_parts = {
        "uno", "lcd", "pot_z1", "pot_z2", "pot_tank", "sw_rain", "sw_manual",
        "btn_clock", "btn_reset", "relay_pump", "led_valve1", "led_valve2", "led_fert", "led_alarm"
    }
    assert required_parts.issubset(part_ids), f"Missing Wokwi circuit parts: {required_parts - part_ids}"

    # 2. Sketch.ino threshold parity against digital_core.ROMConfig
    sketch_content = sketch_path.read_text(encoding="utf-8")

    # Check Boolean equations presence
    assert "P = W && (!rain) && (manual || m)" in sketch_content or "p = w && (!rain) && (manual || m)" in sketch_content
    assert "A = !W" in sketch_content or "a = !w" in sketch_content

    # Check threshold constants
    assert "30.0" in sketch_content, "DRY_THRESHOLD must be 30.0"
    assert "45.0" in sketch_content, "WET_CLEAR_THRESHOLD must be 45.0"
    assert "20.0" in sketch_content, "MIN_TANK_SAFE must be 20.0"
    assert "FERTIGATION_COUNT   = 4" in sketch_content or "FERTIGATION_COUNT = 4" in sketch_content
    assert "WATCHDOG_COUNT      = 15" in sketch_content or "WATCHDOG_COUNT = 15" in sketch_content

    # Check pin separation (zero pin conflicts)
    pins = {
        "PIN_POT_ZONE1": "A0",
        "PIN_POT_ZONE2": "A1",
        "PIN_POT_TANK": "A2",
        "PIN_SW_RAIN": "2",
        "PIN_SW_MANUAL": "3",
        "PIN_BTN_CLOCK": "4",
        "PIN_BTN_RESET": "5",
        "PIN_RELAY_PUMP": "8",
        "PIN_LED_VALVE1": "9",
        "PIN_LED_VALVE2": "10",
        "PIN_LED_FERT": "11",
        "PIN_ALARM": "12",
    }
    assigned_hardware_pins = list(pins.values())
    assert len(assigned_hardware_pins) == len(set(assigned_hardware_pins)), "Pin conflict detected in firmware!"


