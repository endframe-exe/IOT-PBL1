"""
AgriSense Digital Core Engine
=============================
DEC0101 / DEC0151 - Digital Electronics & IoT Systems Syllabus Reference Engine.

Modules Implemented:
- Module 1 & 2: Number systems, 4-bit Quantization, 74LS85 4-Bit Magnitude Comparator,
  combinational Boolean algebra (P = W * ~R * (O + M), A = ~W), and complete 16-row Truth Table.
- Module 3: 2-Bit Sequential D Flip-Flop FSM (IDLE, ZONE_1_ACTIVE, ZONE_2_ACTIVE, FAULT_LOCK),
  Schmitt-Trigger soil moisture hysteresis (<30% start, >=45% clear), zone priority logic,
  and manual override target zone resolution.
- Module 4: Synchronous MOD-16 Counter (4-bit binary/decimal 0-15), Fertigation event at Count 4,
  Watchdog emergency fault-lock at Count 15, Pipe-Burst simulation hook,
  and 4-bit PIPO (Parallel-In Parallel-Out) Status Register.
- Deterministic Rule-Based Recommendation Engine (No unsupported ML/Agronomic claims).

Architecture Note:
Zero Streamlit, database, or external library imports. Pure deterministic Python.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Final, List, Tuple, Dict, Any


# ============================================================================
# MODULE 1 & 2: QUANTIZATION, COMPARATOR & COMBINATIONAL DEFINITIONS
# ============================================================================

def clamp(val: float, min_val: float, max_val: float) -> float:
    """Clamps a floating point number to [min_val, max_val]."""
    return max(min_val, min(val, max_val))


def quantize_4bit(percentage: float) -> int:
    """
    Quantizes an analog percentage (0.0% to 100.0%) into a 4-bit unsigned integer (0 to 15).
    Formula: round(clamp(pct, 0, 100) * 15 / 100)
    Syllabus Scope: Module 1 (Number Systems & A/D Quantization Model).
    """
    clamped = clamp(percentage, 0.0, 100.0)
    return int(round((clamped / 100.0) * 15.0))


def dequantize_4bit(quantized_val: int) -> float:
    """Reconstructs continuous percentage estimate from 4-bit integer (0 to 15)."""
    clamped = max(0, min(quantized_val, 15))
    return round((clamped / 15.0) * 100.0, 2)


def to_binary_4bit(value: int) -> str:
    """Formats an integer 0..15 as a 4-bit binary string (e.g., 4 -> '0100')."""
    return f"{max(0, min(value, 15)):04b}"


@dataclass(frozen=True)
class ComparatorOutput:
    """
    Emulates the 3 output pins of a 74LS85 4-Bit Magnitude Comparator.
    Evaluates word A against word B.
    """
    a_lt_b: bool
    a_eq_b: bool
    a_gt_b: bool

    @property
    def bit_tuple(self) -> Tuple[int, int, int]:
        return int(self.a_lt_b), int(self.a_eq_b), int(self.a_gt_b)


def magnitude_comparator_4bit(word_a: int, word_b: int) -> ComparatorOutput:
    """
    Hardware emulation of 74LS85 4-bit magnitude comparator.
    Syllabus Scope: Module 2 (Combinational Arithmetic/Comparison Circuits).
    """
    a_clamped = max(0, min(word_a, 15))
    b_clamped = max(0, min(word_b, 15))
    return ComparatorOutput(
        a_lt_b=(a_clamped < b_clamped),
        a_eq_b=(a_clamped == b_clamped),
        a_gt_b=(a_clamped > b_clamped),
    )


def evaluate_boolean_logic(m: int | bool, w: int | bool, r: int | bool, o: int | bool) -> Tuple[int, int]:
    """
    Evaluates combinational safety-adjusted Boolean equations:
      P = W AND (NOT R) AND (O OR M)
      A = NOT W (Reservoir Low-Level Interlock Alarm)
    
    Returns:
      (P, A) as integer binary flags (0 or 1).
    """
    m_b = bool(m)
    w_b = bool(w)
    r_b = bool(r)
    o_b = bool(o)

    p = int(w_b and (not r_b) and (o_b or m_b))
    a = int(not w_b)
    return p, a


@dataclass(frozen=True)
class TruthTableRow:
    """Represents one row of the 16-row M-W-R-O truth table."""
    row: int
    m: int
    w: int
    r: int
    o: int
    p: int
    a: int
    minterm: str
    description: str


def generate_truth_table() -> List[TruthTableRow]:
    """
    Generates all 16 rows of the M-W-R-O truth table (m0 through m15).
    Syllabus Scope: Module 2 (Boolean Algebra & Truth Table Verification).
    """
    table: List[TruthTableRow] = []
    descriptions = {
        0: "Tank empty; pump cut off; low water alarm active",
        1: "Tank empty; manual override blocked by low-water interlock",
        2: "Tank empty and rain detected; dual safety interlock active",
        3: "Tank empty and rain; manual override safely suppressed",
        4: "Soil moist, tank safe, no rain; system idle (P=0)",
        5: "Manual override active with safe tank and no rain (P=1)",
        6: "Rain detected; automatic irrigation suppressed",
        7: "Rain detected; manual override blocked by rain interlock",
        8: "Soil dry but tank empty; pump blocked by tank interlock",
        9: "Soil dry and manual ON, but tank empty; low water alarm active",
        10: "Soil dry, tank empty, and rain; dual safety interlock active",
        11: "Soil dry, empty tank, rain, manual ON; all safety interlocks active",
        12: "Normal automated irrigation: soil dry, tank safe, no rain (P=1)",
        13: "Automated + manual demand active under safe conditions (P=1)",
        14: "Soil dry but natural rain detected; pump safely suppressed",
        15: "Soil dry, manual ON, but rain detected; rain interlock active",
    }

    for row_idx in range(16):
        # Bit extraction: M=bit3, W=bit2, R=bit1, O=bit0
        m = (row_idx >> 3) & 1
        w = (row_idx >> 2) & 1
        r = (row_idx >> 1) & 1
        o = (row_idx >> 0) & 1
        p, a = evaluate_boolean_logic(m, w, r, o)
        table.append(TruthTableRow(
            row=row_idx,
            m=m,
            w=w,
            r=r,
            o=o,
            p=p,
            a=a,
            minterm=f"m{row_idx}",
            description=descriptions[row_idx],
        ))
    return table


# ============================================================================
# MODULE 3 & 4: SEQUENTIAL FSM, COUNTER, PIPO & STATE DATA STRUCTURES
# ============================================================================

class FSMState(str, Enum):
    """
    2-bit State Assignment for Irrigation FSM:
      IDLE          = '00' (0b00)
      ZONE_1_ACTIVE = '01' (0b01)
      ZONE_2_ACTIVE = '10' (0b10)
      FAULT_LOCK    = '11' (0b11)
    """
    IDLE = "IDLE"
    ZONE_1_ACTIVE = "ZONE_1_ACTIVE"
    ZONE_2_ACTIVE = "ZONE_2_ACTIVE"
    FAULT_LOCK = "FAULT_LOCK"

    @property
    def bit_tuple(self) -> Tuple[int, int]:
        """Returns the 2-bit D flip-flop state vector (Q1, Q0)."""
        mapping = {
            FSMState.IDLE: (0, 0),
            FSMState.ZONE_1_ACTIVE: (0, 1),
            FSMState.ZONE_2_ACTIVE: (1, 0),
            FSMState.FAULT_LOCK: (1, 1),
        }
        return mapping[self]

    @property
    def binary_code(self) -> str:
        q1, q0 = self.bit_tuple
        return f"{q1}{q0}"


class ZoneId(str, Enum):
    """Irrigation zone identifiers."""
    ZONE_1 = "ZONE_1"
    ZONE_2 = "ZONE_2"
    NONE = "NONE"


@dataclass(frozen=True)
class PIPORegister:
    """
    4-Bit Parallel-In Parallel-Out (PIPO) Latched Status Register.
    Syllabus Scope: Module 4 (Registers & Counters).
    Bits:
      Q3: Zone 1 Solenoid Valve Drive (1=Energized, 0=Closed)
      Q2: Zone 2 Solenoid Valve Drive (1=Energized, 0=Closed)
      Q1: Fertigation Demonstration Pulse (1=Asserted at Count 4, 0=Off)
      Q0: Low Tank / Emergency Watchdog Alarm (1=Alarm On, 0=Normal)
    """
    q3_valve1: int = 0
    q2_valve2: int = 0
    q1_fertigation: int = 0
    q0_alarm: int = 0

    @property
    def as_tuple(self) -> Tuple[int, int, int, int]:
        return self.q3_valve1, self.q2_valve2, self.q1_fertigation, self.q0_alarm

    @property
    def as_int(self) -> int:
        return (self.q3_valve1 << 3) | (self.q2_valve2 << 2) | (self.q1_fertigation << 1) | self.q0_alarm

    @property
    def binary_str(self) -> str:
        return f"{self.q3_valve1}{self.q2_valve2}{self.q1_fertigation}{self.q0_alarm}"

    @property
    def hex_str(self) -> str:
        return f"0x{self.as_int:X}"


@dataclass(frozen=True)
class ROMConfig:
    """
    Simulated ROM: Immutable engineering thresholds & physical parameters.
    Syllabus Scope: Module 4 (ROM/RAM Digital System Model).
    """
    dry_threshold: float = 30.0            # Schmitt trigger low trip point (Moisture < 30% asserts dry demand)
    wet_clear_threshold: float = 45.0      # Schmitt trigger high clear point (Moisture >= 45% clears dry demand)
    min_tank_safe: float = 20.0            # Reservoir minimum safe capacity (Tank < 20% trips interlock)
    moisture_gain_per_step: float = 5.0    # Virtual soil hydration delta per active pump pulse (%/step)
    tank_loss_per_step: float = 2.0        # Reservoir water depletion delta per active pump pulse (%/step)
    evaporation_loss_per_step: float = 1.0 # Natural evaporation delta per idle step (%/step)
    fertigation_count: int = 4             # MOD-16 count triggering fertigation solenoid pulse
    watchdog_timeout_count: int = 15       # MOD-16 count triggering emergency runtime lockout
    counter_modulus: int = 16              # 4-bit counter modulus (MOD-16: 0 to 15)


@dataclass
class RAMState:
    """
    Simulated RAM: Mutable volatile operating state of controller and virtual farm.
    Syllabus Scope: Module 4 (ROM/RAM Digital System Model).
    """
    zone1_moisture: float = 50.0
    zone2_moisture: float = 50.0
    tank_level: float = 80.0
    rain_detected: bool = False
    manual_override: bool = False
    manual_target_zone: ZoneId = ZoneId.ZONE_1

    # Internal Latches & Flip-Flops
    zone1_dry_demand: bool = False         # Schmitt-trigger hysteresis memory flip-flop (Zone 1)
    zone2_dry_demand: bool = False         # Schmitt-trigger hysteresis memory flip-flop (Zone 2)
    fsm_state: FSMState = FSMState.IDLE    # Current 2-bit state vector Q = (Q1, Q0)
    counter: int = 0                       # Synchronous 4-bit binary counter value (0-15)
    pipo: PIPORegister = field(default_factory=PIPORegister)

    # Diagnostic & Simulation Overrides
    pipe_burst_fault: bool = False         # When True, moisture delta is clamped to 0.0% during irrigation
    auto_evaporation: bool = False         # When True, idle zones slowly lose moisture
    watchdog_tripped: bool = False         # Latched when counter reaches Count 15
    low_water_tripped: bool = False        # Latched when tank level < min_tank_safe
    step_count: int = 0                    # Total simulation clock ticks elapsed
    last_action_message: str = "System initialized in IDLE state."


@dataclass(frozen=True)
class StepSnapshot:
    """
    Immutable telemetry record returned after each clock-step or evaluation.
    Used for UI rendering, database persistence, and automated verification.
    """
    step_id: int
    zone1_moisture: float
    zone2_moisture: float
    tank_level: float
    rain_detected: bool
    manual_override: bool
    manual_target_zone: ZoneId
    m1_demand: int
    m2_demand: int
    m_demand: int
    w_safe: int
    r_rain: int
    o_override: int
    pump_output: int
    alarm_output: int
    active_zone: ZoneId
    fsm_state: FSMState
    fsm_code: str
    counter: int
    counter_bin: str
    pipo: PIPORegister
    fertigation_active: bool
    watchdog_tripped: bool
    pipe_burst_fault: bool
    recommendations: List[str]
    message: str


# ============================================================================
# CORE DIGITAL IRRIGATION CONTROLLER
# ============================================================================

class DigitalCoreEngine:
    """
    High-cohesion digital electronics controller and virtual agricultural physics engine.
    Orchestrates combinational logic, synchronous state updates, and rule generation.
    """

    def __init__(self, config: ROMConfig | None = None, initial_state: RAMState | None = None) -> None:
        self.config: Final[ROMConfig] = config or ROMConfig()
        self.state: RAMState = initial_state or RAMState()
        # Initialize hysteresis latches based on initial moisture
        self._evaluate_hysteresis_internal()
        self._update_pipo_register(fertigation=False, alarm=False)

    def set_inputs(
        self,
        zone1_moisture: float | None = None,
        zone2_moisture: float | None = None,
        tank_level: float | None = None,
        rain_detected: bool | None = None,
        manual_override: bool | None = None,
        manual_target_zone: ZoneId | None = None,
        pipe_burst_fault: bool | None = None,
        auto_evaporation: bool | None = None,
    ) -> None:
        """Updates continuous environment and operator inputs without clocking sequential state."""
        if zone1_moisture is not None:
            self.state.zone1_moisture = clamp(zone1_moisture, 0.0, 100.0)
        if zone2_moisture is not None:
            self.state.zone2_moisture = clamp(zone2_moisture, 0.0, 100.0)
        if tank_level is not None:
            self.state.tank_level = clamp(tank_level, 0.0, 100.0)
        if rain_detected is not None:
            self.state.rain_detected = bool(rain_detected)
        if manual_override is not None:
            self.state.manual_override = bool(manual_override)
        if manual_target_zone is not None:
            self.state.manual_target_zone = manual_target_zone
        if pipe_burst_fault is not None:
            self.state.pipe_burst_fault = bool(pipe_burst_fault)
        if auto_evaporation is not None:
            self.state.auto_evaporation = bool(auto_evaporation)

        # Update combinational hysteresis latches immediately upon input change
        self._evaluate_hysteresis_internal()

    def _evaluate_hysteresis_internal(self) -> Tuple[bool, bool]:
        """
        Applies Schmitt-Trigger hysteresis to Zone 1 and Zone 2 moisture.
        Rule:
          Moisture < 30.0%  --> Assert demand (1)
          Moisture >= 45.0% --> Clear demand (0)
          30.0% <= M < 45.0% --> Preserve previous demand state (latch)
        """
        # Zone 1
        if self.state.zone1_moisture < self.config.dry_threshold:
            self.state.zone1_dry_demand = True
        elif self.state.zone1_moisture >= self.config.wet_clear_threshold:
            self.state.zone1_dry_demand = False

        # Zone 2
        if self.state.zone2_moisture < self.config.dry_threshold:
            self.state.zone2_dry_demand = True
        elif self.state.zone2_moisture >= self.config.wet_clear_threshold:
            self.state.zone2_dry_demand = False

        return self.state.zone1_dry_demand, self.state.zone2_dry_demand

    def evaluate_combinational(self) -> Dict[str, Any]:
        """
        Pure combinational evaluation of the current inputs.
        Calculates (M, W, R, O) and outputs (P, A) without advancing state flip-flops.
        """
        m1, m2 = self._evaluate_hysteresis_internal()
        m = m1 or m2
        w = (self.state.tank_level >= self.config.min_tank_safe)
        r = self.state.rain_detected
        o = self.state.manual_override

        p, a = evaluate_boolean_logic(m, w, r, o)
        return {
            "m1": int(m1),
            "m2": int(m2),
            "m": int(m),
            "w": int(w),
            "r": int(r),
            "o": int(o),
            "p": int(p),
            "a": int(a),
        }

    def _update_pipo_register(self, fertigation: bool, alarm: bool) -> None:
        """Latches the 4 status signals into the PIPO register."""
        valve1 = 1 if self.state.fsm_state == FSMState.ZONE_1_ACTIVE else 0
        valve2 = 1 if self.state.fsm_state == FSMState.ZONE_2_ACTIVE else 0
        fert = 1 if fertigation else 0
        alm = 1 if (alarm or self.state.fsm_state == FSMState.FAULT_LOCK) else 0

        self.state.pipo = PIPORegister(
            q3_valve1=valve1,
            q2_valve2=valve2,
            q1_fertigation=fert,
            q0_alarm=alm,
        )

    def step_clock(self) -> StepSnapshot:
        """
        Advances the sequential digital controller by one synchronous clock pulse:
          1. Evaluates combinational logic & hysteresis.
          2. Computes Next State D from current state Q and inputs.
          3. Evaluates MOD-16 counter and watchdog triggers.
          4. Updates virtual soil moisture and reservoir levels (physics engine).
          5. Latches state vector Q_next into D flip-flops.
          6. Updates PIPO status register and rule recommendations.
        """
        self.state.step_count += 1
        comb = self.evaluate_combinational()
        m1 = bool(comb["m1"])
        m2 = bool(comb["m2"])
        m = bool(comb["m"])
        w = bool(comb["w"])
        r = bool(comb["r"])
        o = bool(comb["o"])
        p = comb["p"]
        a = comb["a"]

        message = ""
        fertigation_active = False

        # ---------------------------------------------------------------------
        # 1. SEQUENTIAL FSM NEXT-STATE (D FLIP-FLOP) LOGIC
        # ---------------------------------------------------------------------
        current_state = self.state.fsm_state

        if current_state == FSMState.FAULT_LOCK:
            # Latched fault lock cannot be cleared by clock step; requires explicit reset_fault()
            next_state = FSMState.FAULT_LOCK
            p_effective = 0
            active_zone = ZoneId.NONE
            message = "Controller latched in FAULT_LOCK. Clear safety hazard and perform fault reset."

        elif not w:
            # Low water safety trip: immediately latch FAULT_LOCK
            next_state = FSMState.FAULT_LOCK
            self.state.low_water_tripped = True
            p_effective = 0
            active_zone = ZoneId.NONE
            message = f"Reservoir depleted ({self.state.tank_level:.1f}% < 20%). Pump locked OFF; Alarm active."

        elif self.state.watchdog_tripped:
            # Watchdog timeout latch
            next_state = FSMState.FAULT_LOCK
            p_effective = 0
            active_zone = ZoneId.NONE
            message = "Watchdog limit reached (Count 15). Continuous irrigation locked; Alarm active."

        elif r:
            # Natural rainfall: pump suppressed, return/remain IDLE
            next_state = FSMState.IDLE
            p_effective = 0
            active_zone = ZoneId.NONE
            message = "Rainfall detected. Irrigation suspended by safety interlock."

        elif p == 1:
            # Pump energized: select active zone based on strict priority
            if m1:
                next_state = FSMState.ZONE_1_ACTIVE
                active_zone = ZoneId.ZONE_1
                message = "Zone 1 demand active (priority). Irrigating Zone 1."
            elif m2:
                next_state = FSMState.ZONE_2_ACTIVE
                active_zone = ZoneId.ZONE_2
                message = "Zone 2 demand active. Irrigating Zone 2."
            elif o:
                # Manual override with both zones wet: route to selected manual target zone
                target = self.state.manual_target_zone
                if target == ZoneId.ZONE_2:
                    next_state = FSMState.ZONE_2_ACTIVE
                    active_zone = ZoneId.ZONE_2
                    message = "Manual override active. Irrigating Zone 2 (manual target)."
                else:
                    next_state = FSMState.ZONE_1_ACTIVE
                    active_zone = ZoneId.ZONE_1
                    message = "Manual override active. Irrigating Zone 1 (manual target)."
            else:
                next_state = FSMState.IDLE
                active_zone = ZoneId.NONE
                message = "Conditions satisfied. System IDLE."
            p_effective = 1

        else:
            # No irrigation demand or override
            next_state = FSMState.IDLE
            p_effective = 0
            active_zone = ZoneId.NONE
            message = "All zones adequate and no manual request. System IDLE."

        # ---------------------------------------------------------------------
        # 2. MOD-16 SYNCHRONOUS COUNTER LOGIC
        # ---------------------------------------------------------------------
        if p_effective == 1:
            # Active irrigation clock step: increment 4-bit counter
            self.state.counter = (self.state.counter + 1) % self.config.counter_modulus
            if self.state.counter == self.config.fertigation_count:
                fertigation_active = True
                message += " [Fertigation Pulse Triggered at Count 4]"
            elif self.state.counter == self.config.watchdog_timeout_count:
                # Watchdog count 15 reached
                self.state.watchdog_tripped = True
                next_state = FSMState.FAULT_LOCK
                active_zone = ZoneId.NONE
                p_effective = 0
                message += " [Watchdog Triggered at Count 15 - FAULT_LOCK Activated]"
        else:
            # When transitioning cleanly back to IDLE, synchronously reset counter
            if next_state == FSMState.IDLE:
                self.state.counter = 0

        # ---------------------------------------------------------------------
        # 3. VIRTUAL FARM PHYSICAL SIMULATION (SOIL & RESERVOIR HYDRAULICS)
        # ---------------------------------------------------------------------
        if p_effective == 1:
            # Deplete water reservoir
            self.state.tank_level = clamp(
                self.state.tank_level - self.config.tank_loss_per_step, 0.0, 100.0
            )

            # Hydrate target zone soil (unless pipe-burst fault is active)
            gain = 0.0 if self.state.pipe_burst_fault else self.config.moisture_gain_per_step
            if active_zone == ZoneId.ZONE_1:
                self.state.zone1_moisture = clamp(
                    self.state.zone1_moisture + gain, 0.0, 100.0
                )
            elif active_zone == ZoneId.ZONE_2:
                self.state.zone2_moisture = clamp(
                    self.state.zone2_moisture + gain, 0.0, 100.0
                )

        # Ambient evaporation (if enabled) on un-irrigated zones
        if self.state.auto_evaporation:
            if active_zone != ZoneId.ZONE_1:
                self.state.zone1_moisture = clamp(
                    self.state.zone1_moisture - self.config.evaporation_loss_per_step, 0.0, 100.0
                )
            if active_zone != ZoneId.ZONE_2:
                self.state.zone2_moisture = clamp(
                    self.state.zone2_moisture - self.config.evaporation_loss_per_step, 0.0, 100.0
                )

        # Re-evaluate hysteresis after physical step
        self._evaluate_hysteresis_internal()

        # Commit D flip-flop state: Q_next = D
        self.state.fsm_state = next_state
        self.state.last_action_message = message

        # Latch PIPO Register
        alarm_flag = (a == 1) or (next_state == FSMState.FAULT_LOCK)
        self._update_pipo_register(fertigation=fertigation_active, alarm=alarm_flag)

        # Generate deterministic recommendations
        recommendations = self.generate_recommendations()

        return StepSnapshot(
            step_id=self.state.step_count,
            zone1_moisture=round(self.state.zone1_moisture, 2),
            zone2_moisture=round(self.state.zone2_moisture, 2),
            tank_level=round(self.state.tank_level, 2),
            rain_detected=self.state.rain_detected,
            manual_override=self.state.manual_override,
            manual_target_zone=self.state.manual_target_zone,
            m1_demand=int(self.state.zone1_dry_demand),
            m2_demand=int(self.state.zone2_dry_demand),
            m_demand=int(self.state.zone1_dry_demand or self.state.zone2_dry_demand),
            w_safe=int(w),
            r_rain=int(r),
            o_override=int(o),
            pump_output=p_effective,
            alarm_output=int(alarm_flag),
            active_zone=active_zone,
            fsm_state=self.state.fsm_state,
            fsm_code=self.state.fsm_state.binary_code,
            counter=self.state.counter,
            counter_bin=to_binary_4bit(self.state.counter),
            pipo=self.state.pipo,
            fertigation_active=fertigation_active,
            watchdog_tripped=self.state.watchdog_tripped,
            pipe_burst_fault=self.state.pipe_burst_fault,
            recommendations=recommendations,
            message=message,
        )

    def reset_fault(self) -> Tuple[bool, str]:
        """
        Attempts to clear the latched FAULT_LOCK condition:
          - Rejects reset if reservoir level is still below 20%.
          - If reservoir is safe (>=20%) and watchdog is acknowledged:
            resets FSM to IDLE, clears watchdog latch, and clears counter to 0.
        """
        if self.state.tank_level < self.config.min_tank_safe:
            return False, f"Reset rejected: Tank level ({self.state.tank_level:.1f}%) is below 20% safe minimum."

        # Safety confirmed
        self.state.fsm_state = FSMState.IDLE
        self.state.watchdog_tripped = False
        self.state.low_water_tripped = False
        self.state.counter = 0
        self._evaluate_hysteresis_internal()
        self._update_pipo_register(fertigation=False, alarm=False)
        self.state.last_action_message = "Fault cleared. System safely returned to IDLE."
        return True, "Fault cleared. System safely returned to IDLE."

    def reset_simulation(
        self,
        zone1_moisture: float = 50.0,
        zone2_moisture: float = 50.0,
        tank_level: float = 80.0,
    ) -> None:
        """Restores simulation RAM to clean default values without clearing persistent history."""
        self.state = RAMState(
            zone1_moisture=zone1_moisture,
            zone2_moisture=zone2_moisture,
            tank_level=tank_level,
            rain_detected=False,
            manual_override=False,
            manual_target_zone=ZoneId.ZONE_1,
            fsm_state=FSMState.IDLE,
            counter=0,
            pipe_burst_fault=False,
            auto_evaporation=False,
            watchdog_tripped=False,
            low_water_tripped=False,
            step_count=0,
            last_action_message="Simulation reset to clean baseline.",
        )
        self._evaluate_hysteresis_internal()
        self._update_pipo_register(fertigation=False, alarm=False)

    def generate_recommendations(self) -> List[str]:
        """
        Deterministic rule-based advisory generation.
        Reflects current digital control status without unsupported agricultural claims.
        """
        recs: List[str] = []

        if self.state.fsm_state == FSMState.FAULT_LOCK:
            if self.state.tank_level < self.config.min_tank_safe:
                recs.append("CRITICAL: Refill reservoir above 20% minimum threshold, then execute Fault Reset.")
            if self.state.watchdog_tripped:
                recs.append("CRITICAL: Watchdog runtime limit tripped (Count 15). Inspect field for pipe leaks before reset.")
            return recs

        if self.state.tank_level < self.config.min_tank_safe:
            recs.append("WARNING: Water reservoir below 20%. Pump blocked by safety interlock.")

        if self.state.rain_detected:
            recs.append("INFO: Natural precipitation active. Automated irrigation paused to conserve water.")

        if self.state.zone1_dry_demand:
            recs.append("NOTICE: Zone 1 soil moisture depleted below 30%. Irrigation required.")
        elif self.state.zone1_moisture < self.config.wet_clear_threshold:
            recs.append("STATUS: Zone 1 in intermediate moisture band (30%-45%).")
        else:
            recs.append("STATUS: Zone 1 moisture adequate (>=45%).")

        if self.state.zone2_dry_demand:
            recs.append("NOTICE: Zone 2 soil moisture depleted below 30%. Irrigation required.")
        elif self.state.zone2_moisture < self.config.wet_clear_threshold:
            recs.append("STATUS: Zone 2 in intermediate moisture band (30%-45%).")
        else:
            recs.append("STATUS: Zone 2 moisture adequate (>=45%).")

        if self.state.manual_override:
            recs.append(f"MANUAL: Manual override active (Target: {self.state.manual_target_zone.value}).")

        if self.state.counter == self.config.fertigation_count:
            recs.append("NOTIFICATION: Fertigation pulse asserted on PIPO bit Q1.")

        return recs
