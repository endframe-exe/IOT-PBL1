# Product Requirements Document (PRD)

## Smart Irrigation Monitoring System

**Project codename:** AgriSense\
**Document type:** Developer-focused Product Requirements Document\
**Version:** 1.0\
**Project context:** First-year B.Tech PBL --- Digital Electronics & IoT
Systems (DEC0101)\
**Team:** Group 11\
**Status:** Finalized baseline specification for implementation and
handover

------------------------------------------------------------------------

## 1. Purpose

This PRD is the technical reference for developers, teammates, faculty
reviewers, and future contributors. It defines the product scope,
architecture, technology stack, functional behaviour, data model,
interfaces, testing requirements, deployment approach, and known
limitations.

It distinguishes the current software simulation from planned
integrations. It does not claim that planned hardware connectivity or
every reporting feature has already been implemented and verified.

## 2. Product summary

The Smart Irrigation Monitoring System is an educational IoT and
digital-electronics prototype that simulates a small agricultural field
with two irrigation zones.

The system accepts soil-moisture, reservoir-level, rainfall, and
manual-control inputs. A Python control engine evaluates the inputs,
applies safety rules, updates irrigation state, and simulates pump and
valve behaviour. A Streamlit web application presents the virtual farm,
controller status, analytics, and downloadable reports.

The initial prototype is software-first. Wokwi ESP32 simulation is a
planned optional input source that may later send virtual sensor
telemetry to the same Python application.

### 2.1 Goals

1.  Demonstrate automatic irrigation decisions based on soil moisture
    and water availability.
2.  Stop irrigation when rainfall is detected or the reservoir is below
    the safety threshold.
3.  Demonstrate Boolean logic, a finite-state machine, clocked state
    updates, a MOD-16 counter, and a PIPO output register.
4.  Provide a browser-based virtual farm that an examiner can operate.
5.  Record simulation events and present historical trends.
6.  Generate downloadable PDF and CSV reports.
7.  Keep the application understandable and achievable within a
    first-year PBL scope.

### 2.2 Non-goals

The first release does not provide actual field deployment, physical
pump control, real sensor measurements, laboratory soil analysis,
NPK/pH/EC measurement, machine-learning predictions, crop diagnosis,
yield prediction, weather forecasting, commercial farm management, or
mandatory Wokwi connectivity.

## 3. Users and use cases

### Primary users

-   **Examiner/faculty:** Operates the simulator, observes decisions,
    and reviews reports.
-   **Project team/developer:** Runs, tests, and maintains the
    application.
-   **Demonstrator:** Uses repeatable scenarios during the presentation.

### Primary use cases

1.  View current moisture, reservoir, rainfall, pump, zone, and
    controller status.
2.  Change both zone moisture values and reservoir level.
3.  Toggle rainfall and manual override.
4.  Advance the simulation by one clock step.
5.  Observe pump, alarm, active-zone, counter, and FSM outputs.
6.  Inspect the digital-logic truth table.
7.  Review simulation history and charts.
8.  Download PDF and CSV reports.
9.  In a later optional integration, receive virtual sensor readings
    from Wokwi ESP32.

## 4. Scope

### 4.1 In scope

  -----------------------------------------------------------------------
  ID                      Feature                 Status
  ----------------------- ----------------------- -----------------------
  SCOPE-01                Two-zone virtual farm   Core

  SCOPE-02                Soil moisture input for Core
                          both zones              

  SCOPE-03                Water reservoir level   Core
                          input                   

  SCOPE-04                Rainfall ON/OFF input   Core

  SCOPE-05                Manual override input   Core

  SCOPE-06                Pump and zone-valve     Core
                          simulation              

  SCOPE-07                Rain and low-water      Core
                          safety interlocks       

  SCOPE-08                Boolean logic and       Core
                          truth-table view        

  SCOPE-09                Four-state irrigation   Core
                          FSM                     

  SCOPE-10                Manual clock-step       Core
                          control                 

  SCOPE-11                MOD-16 counter and PIPO Core
                          status representation   

  SCOPE-12                SQLite event history    Core

  SCOPE-13                Monitoring dashboard    Core
                          and analytics           

  SCOPE-14                PDF and CSV export      Core target

  SCOPE-15                Wokwi ESP32 telemetry   Planned optional
                          input                   integration

  SCOPE-16                Public web deployment   Planned
  -----------------------------------------------------------------------

### 4.2 Out of scope

Actual nutrient measurement, physical actuator wiring, hardware
calibration, AI/ML, and production-grade reliability are not part of the
first release.

## 5. Assumptions and configurable thresholds

  ------------------------------------------------------------------------
  Parameter                            Initial value Meaning
  --------------------- ---------------------------- ---------------------
  Zone 1 dry threshold                     Below 30% Zone 1 requests
                                                     irrigation

  Zone 2 dry threshold                     Below 30% Zone 2 requests
                                                     irrigation

  Moisture                                       40% Demonstration
  target/reference                                   reference

  Minimum safe tank                              20% Pump safety threshold
  level                                              

  Moisture gain per              5 percentage points Virtual soil response
  active step                                        

  Tank decrease per              2 percentage points Virtual water-use
  active step                                        response

  Demonstration pump                         5 L/min Illustrative
  flow                                               configurable value

  Counter size                                4 bits MOD-16

  Fertigation                                Count 4 Simulated digital
  demonstration trigger                              output

  Emergency counter                         Count 15 Fault-lock
  trigger                                            demonstration
  ------------------------------------------------------------------------

These are simulation assumptions, not universal agricultural thresholds
or measured hardware specifications.

### 5.1 Simulation time model

The first release uses discrete, user-triggered clock steps. One active
irrigation step evaluates inputs, performs one control decision, updates
the selected zone's moisture, decreases virtual tank level, advances the
counter according to the counter policy, and records the event.

The counter policy in this PRD is **one count per active irrigation
simulation step**, not a real-time hardware clock frequency.

## 6. Technology stack

  -----------------------------------------------------------------------
  Technology              Role                    Requirement
  ----------------------- ----------------------- -----------------------
  Python 3.10+            Main application and    Required
                          control logic           

  Streamlit               Browser application and Required
                          controls                

  Pandas                  Tabular processing and  Required
                          CSV preparation         

  SQLite                  Local event-history     Required
                          database                

  Plotly or Streamlit     Historical              Preferred
  charts                  visualizations          

  ReportLab               PDF report generation   Required for PDF export

  Wokwi                   Virtual ESP32 and       Planned
                          sensor simulation       

  MQTT or HTTP            Optional telemetry      To be selected during
                          transport               integration

  GitHub                  Source control and      Recommended
                          collaboration           

  Streamlit Community     Optional public         Planned
  Cloud                   deployment              
  -----------------------------------------------------------------------

### 6.1 Rationale

-   **Python:** One language can implement control logic, simulation,
    data processing, and reporting.
-   **Streamlit:** Provides a browser interface without a separate
    frontend/backend framework.
-   **SQLite:** Provides simple local persistence without a database
    server.
-   **Pandas:** Simplifies event-history processing and CSV export.
-   **ReportLab:** Generates structured PDF reports.
-   **Wokwi:** Provides optional virtual microcontroller simulation
    without physical components.

React, Node.js, MongoDB, and a separate API server are intentionally
excluded from the first release.

## 7. High-level architecture

``` text
+-----------------------------------------------------------+
|                  VIRTUAL FARM ENVIRONMENT                 |
|   Zone 1 moisture | Zone 2 moisture | Tank | Rain | Manual|
+-----------------------------+-----------------------------+
                              |
                +-------------+-------------+
                |                           |
        SOFTWARE INPUT                PLANNED INPUT
        Streamlit controls            Wokwi ESP32
                |                     Virtual sensors
                +-------------+-------------+
                              |
                    INPUT / ADAPTER LAYER
              Validation, normalization, source
                       selection
                              |
                    DIGITAL CONTROL ENGINE
             Boolean logic | Safety interlocks
             FSM | Clock-step | Counter | PIPO
                              |
                  +-----------+-----------+
                  |                       |
            ACTUATOR MODEL          RECOMMENDATION RULES
         Pump | Zone valves          Alerts and advice
                  +-----------+-----------+
                              |
                       DATA SERVICES
                 SQLite | Event history
                 Aggregation | Report data
                              |
                       STREAMLIT UI
             Overview | Simulator | Logic
             Analytics | Reports | Settings
```

### Architecture principles

1.  The control engine is the authority for pump and controller
    decisions.
2.  UI components collect inputs and display outputs; they must not
    duplicate control decisions.
3.  Software-simulator and Wokwi inputs must be normalized into the same
    internal input structure.
4.  Combinational outputs are evaluated from current inputs.
5.  Sequential state changes occur only on a clock-step or defined reset
    event.
6.  Simulation events should be stored separately from transient UI
    state.
7.  The UI must label readings as simulated unless they originate from
    an explicitly connected hardware source.

## 8. Functional requirements

Priority: **P0** required for the demonstrable first release; **P1**
important follow-up; **P2** optional.

### 8.1 Virtual farm and inputs

  -----------------------------------------------------------------------
  ID                      Priority                Requirement
  ----------------------- ----------------------- -----------------------
  FR-001                  P0                      Provide Zone 1
                                                  soil-moisture input
                                                  from 0% to 100%.

  FR-002                  P0                      Provide Zone 2
                                                  soil-moisture input
                                                  from 0% to 100%.

  FR-003                  P0                      Provide reservoir-level
                                                  input from 0% to 100%.

  FR-004                  P0                      Provide rainfall ON/OFF
                                                  control.

  FR-005                  P0                      Provide manual-override
                                                  ON/OFF control.

  FR-006                  P0                      Provide a control to
                                                  advance one simulation
                                                  clock step.

  FR-007                  P1                      Provide stop/evaluate
                                                  control.

  FR-008                  P1                      Provide
                                                  reset-simulation
                                                  control.

  FR-009                  P1                      Provide predefined
                                                  demonstration
                                                  scenarios.
  -----------------------------------------------------------------------

### 8.2 Irrigation control and safety

  -----------------------------------------------------------------------
  ID                      Priority                Requirement
  ----------------------- ----------------------- -----------------------
  FR-010                  P0                      Pump shall remain OFF
                                                  when rainfall is ON.

  FR-011                  P0                      Pump shall remain OFF
                                                  when tank is below the
                                                  minimum safe level.

  FR-012                  P0                      Manual override shall
                                                  not bypass rainfall or
                                                  low-tank interlocks.

  FR-013                  P0                      Zone 1 shall have
                                                  priority when both
                                                  zones request
                                                  irrigation.

  FR-014                  P0                      Zone 2 shall be
                                                  selected when it
                                                  requests irrigation and
                                                  Zone 1 does not.

  FR-015                  P0                      Pump shall be OFF when
                                                  neither zone requests
                                                  irrigation and manual
                                                  override is OFF.

  FR-016                  P0                      Display active zone and
                                                  pump state.

  FR-017                  P0                      Low-water condition
                                                  shall activate an alarm
                                                  and enter FAULT_LOCK.

  FR-018                  P0                      A fault shall require a
                                                  reset action after the
                                                  condition is safe.

  FR-019                  P1                      Simulate moisture
                                                  increase and tank
                                                  decrease during
                                                  irrigation.

  FR-020                  P1                      Record stop, fault,
                                                  reset, and irrigation
                                                  events.
  -----------------------------------------------------------------------

### 8.3 Digital logic and sequential controller

  -----------------------------------------------------------------------
  ID                      Priority                Requirement
  ----------------------- ----------------------- -----------------------
  FR-021                  P0                      Display normalized
                                                  binary inputs M, W, R,
                                                  and O.

  FR-022                  P0                      Display pump and alarm
                                                  logic outputs.

  FR-023                  P0                      Provide a complete
                                                  16-row truth table.

  FR-024                  P0                      Represent IDLE,
                                                  ZONE_1_ACTIVE,
                                                  ZONE_2_ACTIVE, and
                                                  FAULT_LOCK.

  FR-025                  P0                      Update sequential state
                                                  on a defined clock-step
                                                  event.

  FR-026                  P0                      Represent a 4-bit
                                                  MOD-16 counter.

  FR-027                  P0                      Count 4 shall produce a
                                                  fertigation
                                                  demonstration event.

  FR-028                  P0                      Count 15 shall activate
                                                  the emergency lock.

  FR-029                  P0                      Display a four-bit
                                                  PIPO-style output
                                                  status.

  FR-030                  P1                      Explain state
                                                  transitions in the UI.
  -----------------------------------------------------------------------

### 8.4 Dashboard and analytics

  -----------------------------------------------------------------------
  ID                      Priority                Requirement
  ----------------------- ----------------------- -----------------------
  FR-031                  P0                      Overview shall display
                                                  both zone moisture
                                                  readings.

  FR-032                  P0                      Overview shall display
                                                  tank, rainfall, pump,
                                                  active zone, and FSM
                                                  state.

  FR-033                  P1                      Display historical
                                                  moisture and tank
                                                  trends.

  FR-034                  P1                      Display event history.

  FR-035                  P1                      Display rule-based
                                                  recommendations.

  FR-036                  P1                      Visually distinguish
                                                  normal, warning, and
                                                  fault states.
  -----------------------------------------------------------------------

### 8.5 Reporting

  -----------------------------------------------------------------------
  ID                      Priority                Requirement
  ----------------------- ----------------------- -----------------------
  FR-037                  P0                      Download event history
                                                  as CSV.

  FR-038                  P0                      Provide a PDF
                                                  simulation report.

  FR-039                  P1                      PDF should include
                                                  timestamp, current
                                                  snapshot, controller
                                                  state, latest message,
                                                  and recent events.

  FR-040                  P1                      Reports shall identify
                                                  values as simulated.

  FR-041                  P1                      Reports shall not claim
                                                  physical sensor
                                                  accuracy or measured
                                                  field performance.
  -----------------------------------------------------------------------

### 8.6 Planned Wokwi integration

  -----------------------------------------------------------------------
  ID                      Priority                Requirement
  ----------------------- ----------------------- -----------------------
  FR-042                  P2                      Wokwi ESP32 simulation
                                                  may provide virtual
                                                  sensor readings.

  FR-043                  P2                      A telemetry adapter
                                                  shall validate and
                                                  normalize readings.

  FR-044                  P2                      Wokwi inputs shall use
                                                  the same control engine
                                                  as the software
                                                  simulator.

  FR-045                  P2                      UI should identify the
                                                  active input source.

  FR-046                  P2                      Stale or unavailable
                                                  telemetry shall be
                                                  indicated; old readings
                                                  must not silently
                                                  appear live.
  -----------------------------------------------------------------------

## 9. Digital control specification

This section records the selected prototype policy. It must remain
consistent across implementation, truth tables, diagrams, tests, and the
academic report.

### 9.1 Input definitions

  Symbol   Meaning                Binary interpretation
  -------- ---------------------- ------------------------------------------
  M        Soil moisture demand   1 when at least one eligible zone is dry
  W        Water tank safe        1 when tank level is at or above 20%
  R        Rainfall               1 when rain is detected
  O        Manual override        1 when manual override is enabled

For two zones, M is the OR of the zone dry-demand flags. Zone selection
is performed separately by the zone-priority controller.

### 9.2 Selected safety-adjusted Boolean equations

Selected policy: - Rain always blocks the pump. - Insufficient tank
level always blocks the pump. - Manual override may request irrigation
but cannot bypass safety interlocks.

Pump equation:

\[ P = W `\cdot `{=tex}R' `\cdot `{=tex}(O + M) \]

Low-water alarm:

\[ A = W' \]

Where P is pump output/request and A is low-water alarm.

**Academic-documentation note:** The earlier Progress Report II contains
different equations, including a pump equation that permits manual
override during rainfall and a different alarm expression. Update the
truth table, K-map, and written report to match the selected safety
policy. Do not present the old equations and new implementation as
identical.

### 9.3 Truth-table acceptance conditions

The truth table must contain all 16 combinations of M, W, R, and O.
Tests must confirm:

-   W=0 always gives P=0 and A=1.
-   R=1 always gives P=0.
-   W=1, R=0, M=1, O=0 gives P=1.
-   W=1, R=0, M=0, O=1 gives P=1.
-   W=1, R=0, M=0, O=0 gives P=0.
-   Manual override never bypasses W or R safety.

### 9.4 FSM definition

  -----------------------------------------------------------------------
  State                   Meaning                 Required behaviour
  ----------------------- ----------------------- -----------------------
  IDLE                    No irrigation zone      Pump OFF
                          active                  

  ZONE_1_ACTIVE           Zone 1 irrigating       Zone 1 valve active;
                                                  pump ON subject to
                                                  safety

  ZONE_2_ACTIVE           Zone 2 irrigating       Zone 2 valve active;
                                                  pump ON subject to
                                                  safety

  FAULT_LOCK              Safety or timeout lock  Pump OFF; alarm/lock
                                                  indication active
  -----------------------------------------------------------------------

Zone priority: 1. Zone 1 if Zone 1 requests irrigation. 2. Otherwise
Zone 2 if Zone 2 requests irrigation. 3. Otherwise IDLE.

Safety conditions take priority over zone selection. Any safety fault
forces pump OFF. FAULT_LOCK is cleared only through a defined reset
after the underlying condition is safe.

### 9.5 Sequential logic

The software model represents a D flip-flop using:

\[ Q\_{n+1}=D \]

The next state is calculated from current state and inputs, then stored
only when the user advances the clock step. This is a software model,
not a physical flip-flop circuit.

### 9.6 Counter and PIPO

-   Counter width: 4 bits.
-   Sequence: 0000 through 1111.
-   One count per active irrigation simulation step.
-   Count 4: fertigation demonstration event.
-   Count 15: emergency lock.
-   PIPO-style output representation:

  Bit   Signal
  ----- ----------------------------------
  Q3    Zone 1 valve
  Q2    Zone 2 valve
  Q1    Fertigation demonstration signal
  Q0    Alarm

The PIPO is a software representation of parallel status storage. The
developer must ensure displayed bits reflect the chosen latched/current
register semantics and document that choice.

## 10. Recommendation engine

The first release uses deterministic rules, not machine learning.

  Condition                       Recommendation
  ------------------------------- -----------------------------------------
  Zone moisture below threshold   Irrigation required for that zone
  Moisture adequate               No irrigation currently required
  Tank below minimum              Refill reservoir; pump blocked
  Rain detected                   Suspend irrigation
  FAULT_LOCK active               Clear fault condition and perform reset
  Counter timeout reached         Inspect simulated system before reset

Recommendations must be tied to actual system state and avoid
unsupported agronomic claims.

## 11. User interface requirements

The Streamlit application should provide the following pages.

### 11.1 Overview

Display Zone 1 and Zone 2 moisture, reservoir level, rainfall, pump,
active zone, FSM state, counter, current recommendation, and historical
condition chart when available.

### 11.2 Farm Simulator

Display: - Zone 1 moisture slider. - Zone 2 moisture slider. -
Tank-level slider. - Rainfall toggle. - Manual-override toggle. - Next
Clock Pulse. - Stop/Evaluate. - Reset Simulation. - Reset Fault when
applicable. - Current pump, alarm, zone, and controller outputs.

### 11.3 Logic Control

Display: - M, W, R, O inputs. - Selected Boolean equations. - Pump and
alarm outputs. - Complete 16-row truth table. - FSM state. - Counter in
binary and decimal. - PIPO output bits.

### 11.4 Analytics & Reports

Display: - Event count. - Pump-active event count. - Fault count. -
Rain-related event count. - Moisture and tank trend chart. - Recent
event log. - PDF and CSV downloads.

### 11.5 Visual design

Use a clean agricultural technology style: - Forest-green and neutral
palette. - Clear status cards. - Green for normal operation, amber for
warnings, red for faults. - Responsive laptop-friendly layout. - Clear
labels distinguishing simulated data from real measurements.

## 12. Data model

SQLite is the first-release persistence layer.

### 12.1 Event table

Suggested table: `events`

  Column        Type                  Description
  ------------- --------------------- ----------------------------
  id            INTEGER PRIMARY KEY   Event identifier
  timestamp     TEXT                  Event timestamp
  zone1         REAL                  Zone 1 moisture percentage
  zone2         REAL                  Zone 2 moisture percentage
  tank          REAL                  Reservoir percentage
  rain          INTEGER               0/1 rainfall status
  manual        INTEGER               0/1 manual override
  pump          INTEGER               0/1 pump status
  active_zone   TEXT                  NONE, ZONE_1, or ZONE_2
  fsm_state     TEXT                  Current FSM state
  counter       INTEGER               Counter value 0--15
  alarm         INTEGER               0/1 alarm status
  message       TEXT                  Event explanation

### 12.2 Data-handling requirements

-   Store timestamps consistently.
-   Store booleans as 0/1.
-   Preserve event order.
-   Do not erase history during a normal simulation reset.
-   Provide an explicit history-clearing operation only if required and
    clearly labelled.
-   Handle an empty database without crashing charts or reports.
-   Treat local SQLite as suitable for a single-user demonstration, not
    concurrent production use.

## 13. Proposed source-code structure

``` text
agrisense/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── core/
│   ├── boolean_logic.py
│   ├── fsm_controller.py
│   ├── counter.py
│   ├── register.py
│   └── irrigation_engine.py
├── simulation/
│   ├── virtual_sensors.py
│   ├── farm_environment.py
│   └── actuator_simulator.py
├── iot/
│   ├── input_adapter.py
│   └── wokwi_receiver.py
├── analytics/
│   ├── recommendations.py
│   ├── statistics.py
│   └── report_generator.py
├── database/
│   ├── db.py
│   └── schema.sql
└── tests/
    ├── test_logic.py
    ├── test_fsm.py
    └── test_scenarios.py
```

This is the recommended maintainable structure. The current MVP may be a
simpler single-file implementation; refactoring into modules is a
recommendation, not a claim that these files already exist.

### Module responsibilities

  Module                    Responsibility
  ------------------------- ------------------------------------------
  `app.py`                  Streamlit entry point and page routing
  `boolean_logic.py`        Boolean functions and input conversion
  `fsm_controller.py`       State transitions and fault lock
  `counter.py`              MOD-16 counter and trigger events
  `register.py`             PIPO status representation
  `irrigation_engine.py`    Orchestrates one control/simulation step
  `virtual_sensors.py`      Software-generated input values
  `farm_environment.py`     Virtual soil and tank behaviour
  `actuator_simulator.py`   Pump and valve output model
  `input_adapter.py`        Common input interface
  `wokwi_receiver.py`       Planned telemetry receiver
  `recommendations.py`      Rule-based messages
  `statistics.py`           History aggregation
  `report_generator.py`     PDF and CSV report preparation
  `db.py`                   SQLite connection and persistence
  `tests/`                  Automated logic and scenario validation

## 14. Wokwi integration --- planned optional extension

**Wokwi:** https://wokwi.com/

The planned virtual setup may include: - ESP32 development board. -
Soil-moisture sensor or potentiometer-based analogue input. -
Water-level representation using a suitable simulated input. - Rain
sensor or digital switch input. - Serial or network telemetry output.

### 14.1 Planned integration flow

``` text
Wokwi ESP32
    |
Virtual sensor readings
    |
MQTT or HTTP transport (to be selected and tested)
    |
Python telemetry receiver
    |
Input validation and normalization
    |
Shared irrigation control engine
    |
Streamlit dashboard and SQLite history
```

### 14.2 Integration constraints

-   Wokwi is planned, not confirmed as connected.
-   Select MQTT or HTTP after testing the simplest reliable route.
-   Confirm the Wokwi simulation supports the chosen network workflow.
-   Validate payload structure, ranges, source identity, and timestamps.
-   Display connection status and stale-data warnings.
-   Keep the software simulator usable if Wokwi is offline.
-   Do not claim virtual Wokwi sensors are physical field measurements.

## 15. Non-functional requirements

  -----------------------------------------------------------------------
  ID                                  Requirement
  ----------------------------------- -----------------------------------
  NFR-001                             Application should start locally
                                      using documented commands.

  NFR-002                             Core irrigation decision should be
                                      deterministic for identical inputs
                                      and state.

  NFR-003                             Safety interlocks must take
                                      precedence over manual override and
                                      zone demand.

  NFR-004                             UI should be usable on a typical
                                      laptop display.

  NFR-005                             Invalid or out-of-range inputs must
                                      be rejected or constrained.

  NFR-006                             Empty history must be handled
                                      gracefully.

  NFR-007                             Reports must label readings as
                                      simulated.

  NFR-008                             Control logic should be separated
                                      from UI rendering where practical.

  NFR-009                             Simulation reset must not
                                      unexpectedly erase persistent event
                                      history.

  NFR-010                             Primary demonstration must not
                                      require physical hardware.
  -----------------------------------------------------------------------

## 16. Testing and acceptance criteria

### 16.1 Core scenario tests

  ------------------------------------------------------------------------
  Test ID           Initial           Action             Expected result
                    conditions                           
  ----------------- ----------------- ------------------ -----------------
  TC-01             Z1=20, Z2=65,     Next clock pulse   Pump ON; Zone 1
                    tank=90, rain OFF                    selected; Z1 +5;
                                                         tank -2

  TC-02             Z1=20, tank=90,   Next clock pulse   Pump OFF; IDLE;
                    rain ON                              no active zone;
                                                         alarm inactive

  TC-03             Tank=10           Next clock pulse   Pump OFF; alarm
                                                         active;
                                                         FAULT_LOCK

  TC-04             Z1=65, Z2=20,     Next clock pulse   Zone 2 selected
                    tank=90, rain OFF                    

  TC-05             Z1=20, Z2=20,     Next clock pulse   Zone 1 selected
                    tank=90, rain OFF                    

  TC-06             Both zones        Evaluate           Pump OFF; IDLE
                    adequate,                            
                    tank=90, rain                        
                    OFF, manual OFF                      

  TC-07             Manual ON, tank   Evaluate/clock     Manual request
                    safe, rain OFF    step               may activate Zone
                                                         1

  TC-08             Manual ON, rain   Evaluate/clock     Pump OFF
                    ON                step               

  TC-09             Manual ON, tank   Evaluate/clock     Pump OFF;
                    below minimum     step               fault/alarm
                                                         handling

  TC-10             Counter reaches 4 Clock step         Fertigation
                    during active                        demonstration
                    irrigation                           event

  TC-11             Counter reaches   Clock step         Emergency lock;
                    15                                   pump OFF

  TC-12             No database       Open               No crash;
                    events            analytics/report   empty-state and
                                      page               valid report
                                                         behaviour
  ------------------------------------------------------------------------

### 16.2 Acceptance criteria

The first release is acceptable when: 1. All 16 Boolean combinations
produce expected outputs. 2. Rainfall and low tank always block the
pump. 3. Zone priority is deterministic. 4. Four FSM states can be
demonstrated. 5. Counter and PIPO outputs are displayed consistently. 6.
Low-water and timeout faults stop the pump. 7. Event history is
persisted and reviewable. 8. CSV export works. 9. PDF export produces a
readable report. 10. The application clearly states that values are
simulated.

## 17. Current implementation status

This is a handover snapshot based on the development work observed
during the project conversation. Update it after further verification.

  -----------------------------------------------------------------------
  Component               Status                  Evidence / note
  ----------------------- ----------------------- -----------------------
  Initial Streamlit       Implemented             Application launched in
  application                                     browser

  Virtual two-zone inputs Implemented in MVP      Sliders and toggles
                                                  demonstrated

  Normal irrigation       Tested successfully     Pump ON and Zone 1
                                                  selected

  Low-water safety        Tested successfully     Pump OFF, alarm active,
                                                  fault lock

  Rainfall safety         Tested successfully     Pump OFF, IDLE, alarm
                                                  inactive

  Dashboard redesign      Packaged; verification  Updated version
                          pending                 prepared

  SQLite event history    Included in updated     Persistence should be
                          build                   retested

  Analytics charts        Included in updated     Verification pending
                          build                   

  CSV export              Included in updated     Verification pending
                          build                   

  PDF export              Included in updated     Verification pending
                          build                   

  Streamlit widget-state  Packaged                Corrected keys; runtime
  correction                                      verification pending

  Wokwi ESP32 integration Planned                 Not connected or
                                                  verified

  Public deployment       Planned                 Not confirmed
  -----------------------------------------------------------------------

Do not mark a feature complete merely because code was generated. Mark
it complete only after running and testing it in the actual environment.

## 18. Known technical risks and decisions

### 18.1 Equation/report inconsistency

The original academic progress report describes a pump equation that
permits manual override during rainfall. The selected prototype policy
prohibits this. Update the academic truth table, K-map, and written
explanation to match the final policy.

### 18.2 Fault reset

A low-water fault remains locked until the tank is restored to a safe
level and the user performs the reset action. Changing the tank slider
alone must not silently clear the fault.

### 18.3 Streamlit session state

Widget keys must be distinct from internal simulation-state variable
names. Do not assign to a widget's session-state key after the widget
has been instantiated. Keep widget state and control-engine state
separate, or synchronize them with a safe callback/key pattern.

### 18.4 Counter semantics

The counter is defined as an irrigation simulation-step counter. The
academic report previously uses both cycle and clock-pulse language.
Update the report so one count has one unambiguous meaning.

### 18.5 Simulation realism

Moisture gain and tank reduction are simplified deterministic values.
They demonstrate control behaviour but are not a physical water-flow or
soil-hydrology model.

### 18.6 Wokwi connectivity

External telemetry adds network and integration risk. It must not block
the software simulator or core demonstration.

## 19. Deployment and execution

### 19.1 Local development

Install Python 3.10 or later, open the project directory in VS Code,
create a virtual environment, install dependencies, and start Streamlit.

``` bash
python -m venv .venv
```

Windows PowerShell:

``` powershell
.venv\Scripts\Activate.ps1
```

Install:

``` bash
python -m pip install -r requirements.txt
```

Run:

``` bash
streamlit run app.py
```

### 19.2 Dependency list

The first-release `requirements.txt` should include packages actually
used by the application, for example:

``` text
streamlit
pandas
reportlab
plotly
```

Pin tested versions before final deployment and remove unused
dependencies.

### 19.3 Source control

Recommended GitHub repository contents: - Application source. -
Requirements file. - README and setup instructions. - Architecture
diagrams. - Test cases. - Example screenshots. - No secrets,
credentials, or private connection tokens. - Avoid committing generated
databases unless a sanitized sample database is intentionally required.

### 19.4 Public deployment

Proposed hosting:
https://docs.streamlit.io/deploy/streamlit-community-cloud

Before deployment: - Confirm the application works from a clean
environment. - Declare required dependencies. - Confirm PDF generation
works in the hosting environment. - Consider that local SQLite
persistence may not be durable across all hosting lifecycle events. - Do
not expose private telemetry credentials. - Verify the public URL and
test the deployed app.

## 20. Development priorities

1.  Stabilize and test the current Streamlit MVP.
2.  Verify all 16 Boolean combinations.
3.  Verify FSM transitions, counter, PIPO, and fault reset.
4.  Verify event persistence and history.
5.  Verify analytics and CSV export.
6.  Verify PDF report generation.
7.  Improve final dashboard layout and presentation.
8.  Add Wokwi integration only if time and connectivity permit.
9.  Deploy and rehearse the final demonstration.

### Demonstration sequence

1.  Open Overview and explain farm metrics.
2.  Set Zone 1 moisture low and tank level safe.
3.  Advance one clock pulse and show Zone 1 irrigation.
4.  Enable rainfall and show pump safety stop.
5.  Set tank below safe threshold and show FAULT_LOCK.
6.  Open Logic Control and explain Boolean inputs and truth table.
7.  Demonstrate FSM and counter behaviour.
8.  Open Analytics & Reports and download CSV/PDF.
9.  If Wokwi integration is completed, show the ESP32 sensor-input path
    as an additional demonstration.

## 21. Future scope

Potential extensions after the first release: - Physical ESP32 and real
soil-moisture sensors. - Actual water-level and rain sensors. - Pump and
solenoid-valve hardware. - Crop-specific moisture thresholds supported
by agricultural references. - Multi-field and multi-user support. -
Improved water-flow modelling. - Sensor calibration and data-quality
checks. - Weather API integration. - Nutrient sensing only with suitable
sensors and validation. - Predictive analytics only with a suitable
dataset and evaluation.

## 22. Glossary

  -----------------------------------------------------------------------
  Term                                Meaning
  ----------------------------------- -----------------------------------
  Virtual farm                        Software representation of the
                                      field and its conditions

  Soil moisture                       Simulated percentage representing
                                      water content in soil

  Reservoir/tank level                Simulated available irrigation
                                      water

  Boolean logic                       Binary decision logic for pump and
                                      alarm outputs

  FSM                                 Finite-state machine representing
                                      controller states

  D flip-flop                         Sequential element model storing
                                      next-state input on a clock edge

  MOD-16                              Four-bit counter with 16 possible
                                      values

  PIPO                                Parallel-in, parallel-out register
                                      representation

  Interlock                           Safety condition preventing an
                                      unsafe action

  Telemetry                           Data transmitted from a device or
                                      simulator to an application

  Wokwi                               Online microcontroller and
                                      electronics simulator

  Streamlit                           Python framework for interactive
                                      browser applications
  -----------------------------------------------------------------------

## 23. Reference links

-   Streamlit: https://docs.streamlit.io/
-   Streamlit Community Cloud:
    https://docs.streamlit.io/deploy/streamlit-community-cloud
-   Wokwi: https://docs.wokwi.com/
-   Python: https://docs.python.org/3/
-   SQLite: https://www.sqlite.org/docs.html
-   Pandas: https://pandas.pydata.org/docs/
-   Plotly: https://plotly.com/python/
-   ReportLab: https://docs.reportlab.com/

------------------------------------------------------------------------

## Document control

**Document:** Smart Irrigation Monitoring System --- Developer PRD\
**Project codename:** AgriSense\
**Version:** 1.0\
**Purpose:** Product definition, technical handover, implementation
guidance, and validation baseline\
**Status:** Finalized baseline; implementation status must be maintained
as development progresses

**End of document.**
