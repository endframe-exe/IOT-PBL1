/*
  =============================================================================
  AgriSense: Smart Irrigation Hardware Controller Firmware (Wokwi Arduino Uno)
  =============================================================================
  Course: DEC0101 / DEC0151 - Digital Electronics & IoT Systems PBL
  Team: Group 11
  Target Platform: Arduino Uno (ATmega328P) in Wokwi Simulation

  -----------------------------------------------------------------------------
  SYLLABUS MODULE 5 PARITY:
  - Demonstrates physical computing, analog-to-digital sensor conditioning,
    optically isolated relay actuation, debounced synchronous clocking,
    and embedded serial telemetry output.
  - Implements EXACT same digital electronics logic as digital_core.py:
      1. Boolean Pump Equation: P = W && !R && (O || M)
      2. Low Tank Alarm Equation: A = !W
      3. Schmitt-Trigger Moisture Hysteresis: <30% dry trip, >=45% wet clear
      4. 2-Bit Sequential State Machine: IDLE (00), ZONE_1 (01), ZONE_2 (10), FAULT (11)
      5. Synchronous MOD-16 Counter (4-bit binary, Count 4 Fertigation, Count 15 Watchdog)
      6. 4-Bit PIPO Latched Status Register (Q3: Valve 1, Q2: Valve 2, Q1: Fert, Q0: Alarm)
  -----------------------------------------------------------------------------
  SAFETY & ELECTRICAL DESIGN NOTE:
  Pin D8 drives a 5V Optocoupler Relay Module. Microcontroller GPIO pins MUST NEVER
  directly drive an inductive pump motor due to back-EMF flyback spikes.
  =============================================================================
*/

#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// =============================================================================
// PIN DEFINITIONS (STRICTLY PARTITIONED - ZERO CONFLICTS)
// =============================================================================

// Analog Sensor Inputs (ADC 10-Bit: 0 to 1023 -> 0.0% to 100.0%)
const uint8_t PIN_POT_ZONE1  = A0; // Soil Moisture Sensor Zone 1
const uint8_t PIN_POT_ZONE2  = A1; // Soil Moisture Sensor Zone 2
const uint8_t PIN_POT_TANK   = A2; // Water Reservoir Level Sensor
// A4 = I2C SDA (Dedicated to LCD)
// A5 = I2C SCL (Dedicated to LCD)

// Digital Control & Environmental Inputs
const uint8_t PIN_SW_RAIN    = 2;  // Rain Sensor Digital Switch (HIGH = Rain Detected)
const uint8_t PIN_SW_MANUAL  = 3;  // Manual Override Slide Switch (HIGH = Manual ON)
const uint8_t PIN_BTN_CLOCK  = 4;  // Synchronous Clock Step Button (Active LOW, INPUT_PULLUP)
const uint8_t PIN_BTN_RESET  = 5;  // Fault Lockout Reset Button (Active LOW, INPUT_PULLUP)

// Actuator & Indicator Outputs
const uint8_t PIN_RELAY_PUMP = 8;  // Optocoupler Relay Drive for Main Irrigation Pump
const uint8_t PIN_LED_VALVE1 = 9;  // Zone 1 Solenoid Valve Indicator LED
const uint8_t PIN_LED_VALVE2 = 10; // Zone 2 Solenoid Valve Indicator LED
const uint8_t PIN_LED_FERT   = 11; // Fertigation Solenoid Pulse LED (Count 4)
const uint8_t PIN_ALARM      = 12; // Low Tank / Watchdog Fault Alarm LED + Buzzer

// =============================================================================
// SYSTEM THRESHOLDS & ENGINEERING CONSTANTS (LOCKED TO SPEC_LOCK.md)
// =============================================================================
const float DRY_THRESHOLD         = 30.0f; // Moisture < 30.0% asserts dry demand
const float WET_CLEAR_THRESHOLD   = 45.0f; // Moisture >= 45.0% clears dry demand
const float MIN_TANK_SAFE         = 20.0f; // Tank Level < 20.0% trips low water alarm
const uint8_t FERTIGATION_COUNT   = 4;     // MOD-16 Count 4 triggers fertigation pulse
const uint8_t WATCHDOG_COUNT      = 15;    // MOD-16 Count 15 trips emergency watchdog
const uint8_t COUNTER_MODULUS     = 16;    // 4-bit counter modulus (0 to 15)

// =============================================================================
// 2-BIT FINITE STATE MACHINE (FSM) ENUMERATION
// =============================================================================
enum FSMState {
  STATE_IDLE          = 0, // Code: 00 (No active irrigation)
  STATE_ZONE_1_ACTIVE = 1, // Code: 01 (Zone 1 valve open, pump running)
  STATE_ZONE_2_ACTIVE = 2, // Code: 10 (Zone 2 valve open, pump running)
  STATE_FAULT_LOCK    = 3  // Code: 11 (Latched safety interlock, pump blocked)
};

// =============================================================================
// GLOBAL OPERATING STATE (RAM REGISTERS)
// =============================================================================
FSMState currentState = STATE_IDLE;
uint8_t  stepCounter  = 0;          // Synchronous 4-bit MOD-16 counter (0-15)
uint32_t totalTicks   = 0;          // Lifetime simulation pulse count

// Hysteresis Memory Flip-Flops (Schmitt-Trigger Latches)
bool zone1DryDemand = false;
bool zone2DryDemand = false;
bool watchdogTripped = false;

// Debounce Tracking for Pushbuttons
unsigned long lastClockDebounceTime = 0;
unsigned long lastResetDebounceTime = 0;
const unsigned long DEBOUNCE_DELAY  = 50; // 50 ms debounce threshold
int lastClockBtnState = HIGH;
int lastResetBtnState = HIGH;

// I2C 16x2 Liquid Crystal Display Instance (Standard Address 0x27)
LiquidCrystal_I2C lcd(0x27, 16, 2);

// =============================================================================
// HELPER FUNCTIONS: ADC SCALING & HYSTERESIS EVALUATION
// =============================================================================

// Converts 10-bit ADC reading (0-1023) to floating point percentage (0.0% to 100.0%)
float readPotAsPercentage(uint8_t pin) {
  int raw = analogRead(pin);
  return (float)raw * (100.0f / 1023.0f);
}

// Evaluates Schmitt-Trigger Moisture Hysteresis
void updateHysteresis(float z1, float z2) {
  // Zone 1 Hysteresis
  if (z1 < DRY_THRESHOLD) {
    zone1DryDemand = true;
  } else if (z1 >= WET_CLEAR_THRESHOLD) {
    zone1DryDemand = false;
  }

  // Zone 2 Hysteresis
  if (z2 < DRY_THRESHOLD) {
    zone2DryDemand = true;
  } else if (z2 >= WET_CLEAR_THRESHOLD) {
    zone2DryDemand = false;
  }
}

// Updates I2C LCD Display
void updateLCD(float z1, float z2, float tank, bool pump, uint8_t count) {
  lcd.setCursor(0, 0);
  // Line 1: State, Pump, and Counter (e.g., "IDLE P:0 C:00 [00]")
  lcd.print(currentState == STATE_FAULT_LOCK ? "FAULT" :
           (currentState == STATE_ZONE_1_ACTIVE ? "ZONE1" :
           (currentState == STATE_ZONE_2_ACTIVE ? "ZONE2" : "IDLE ")));
  lcd.print(" P:");
  lcd.print(pump ? "1" : "0");
  lcd.print(" C:");
  if (count < 10) lcd.print("0");
  lcd.print(count);
  lcd.print(" [");
  lcd.print((currentState >> 1) & 1);
  lcd.print(currentState & 1);
  lcd.print("]");

  // Line 2: Moisture and Reservoir readings (e.g., "Z:25/65% T:88%")
  lcd.setCursor(0, 1);
  lcd.print("Z:");
  lcd.print((int)z1);
  lcd.print("/");
  lcd.print((int)z2);
  lcd.print("% T:");
  lcd.print((int)tank);
  lcd.print("%  ");
}

// Emits Structured Telemetry via Serial Port (JSON format at 9600 baud)
void transmitTelemetry(float z1, float z2, float tank, bool rain, bool manual,
                       bool m, bool w, bool p, bool a, bool fert) {
  totalTicks++;
  
  // Compute 4-bit PIPO Word: Q3=Valve1, Q2=Valve2, Q1=Fert, Q0=Alarm
  uint8_t q3 = (currentState == STATE_ZONE_1_ACTIVE) ? 1 : 0;
  uint8_t q2 = (currentState == STATE_ZONE_2_ACTIVE) ? 1 : 0;
  uint8_t q1 = fert ? 1 : 0;
  uint8_t q0 = (a || currentState == STATE_FAULT_LOCK) ? 1 : 0;
  uint8_t pipoInt = (q3 << 3) | (q2 << 2) | (q1 << 1) | q0;

  Serial.print(F("{\"tick\":"));
  Serial.print(totalTicks);
  Serial.print(F(",\"z1\":"));
  Serial.print(z1, 1);
  Serial.print(F(",\"z2\":"));
  Serial.print(z2, 1);
  Serial.print(F(",\"tank\":"));
  Serial.print(tank, 1);
  Serial.print(F(",\"M\":"));
  Serial.print(m ? 1 : 0);
  Serial.print(F(",\"W\":"));
  Serial.print(w ? 1 : 0);
  Serial.print(F(",\"R\":"));
  Serial.print(rain ? 1 : 0);
  Serial.print(F(",\"O\":"));
  Serial.print(manual ? 1 : 0);
  Serial.print(F(",\"P\":"));
  Serial.print(p ? 1 : 0);
  Serial.print(F(",\"A\":"));
  Serial.print(a ? 1 : 0);
  Serial.print(F(",\"fsm\":\""));
  Serial.print(currentState == STATE_FAULT_LOCK ? F("FAULT_LOCK") :
              (currentState == STATE_ZONE_1_ACTIVE ? F("ZONE_1_ACTIVE") :
              (currentState == STATE_ZONE_2_ACTIVE ? F("ZONE_2_ACTIVE") : F("IDLE"))));
  Serial.print(F("\",\"fsm_code\":\""));
  Serial.print((currentState >> 1) & 1);
  Serial.print(currentState & 1);
  Serial.print(F("\",\"cnt\":"));
  Serial.print(stepCounter);
  Serial.print(F(",\"pipo_bin\":\""));
  Serial.print(q3);
  Serial.print(q2);
  Serial.print(q1);
  Serial.print(q0);
  Serial.print(F("\",\"pipo_hex\":\"0x"));
  Serial.print(pipoInt, HEX);
  Serial.println(F("\"}"));
}

// =============================================================================
// SYNCHRONOUS CLOCK TICK EXECUTION (D FLIP-FLOP NEXT-STATE LOGIC)
// =============================================================================
void executeClockStep() {
  // 1. Sample ADC and Digital Inputs
  float z1   = readPotAsPercentage(PIN_POT_ZONE1);
  float z2   = readPotAsPercentage(PIN_POT_ZONE2);
  float tank = readPotAsPercentage(PIN_POT_TANK);
  bool rain   = (digitalRead(PIN_SW_RAIN) == HIGH);
  bool manual = (digitalRead(PIN_SW_MANUAL) == HIGH);

  // 2. Evaluate Hysteresis
  updateHysteresis(z1, z2);
  bool m = zone1DryDemand || zone2DryDemand;
  bool w = (tank >= MIN_TANK_SAFE);

  // 3. Evaluate Combinational Safety-Adjusted Equations
  //    P = W && !R && (O || M)
  //    A = !W
  bool p = w && (!rain) && (manual || m);
  bool a = !w;

  bool fertPulse = false;
  FSMState nextState = currentState;
  bool effectivePump = false;

  // 4. Sequential FSM Next-State Evaluation (Q_next = D)
  if (currentState == STATE_FAULT_LOCK) {
    // Latched fault: cannot leave without explicit reset
    nextState = STATE_FAULT_LOCK;
    effectivePump = false;
  } else if (!w) {
    // Low water interlock trip: force FAULT_LOCK
    nextState = STATE_FAULT_LOCK;
    effectivePump = false;
  } else if (watchdogTripped) {
    // Watchdog trip: force FAULT_LOCK
    nextState = STATE_FAULT_LOCK;
    effectivePump = false;
  } else if (rain) {
    // Rain interlock: return or stay IDLE
    nextState = STATE_IDLE;
    effectivePump = false;
  } else if (p) {
    // Irrigation approved: apply Zone Priority Encoder
    if (zone1DryDemand) {
      nextState = STATE_ZONE_1_ACTIVE;
    } else if (zone2DryDemand) {
      nextState = STATE_ZONE_2_ACTIVE;
    } else if (manual) {
      // Manual override with both zones wet: route to Zone 1
      nextState = STATE_ZONE_1_ACTIVE;
    }
    effectivePump = true;
  } else {
    // All zones satisfied and no manual override
    nextState = STATE_IDLE;
    effectivePump = false;
  }

  // 5. MOD-16 Synchronous Counter Evaluation
  if (effectivePump) {
    stepCounter = (stepCounter + 1) % COUNTER_MODULUS;
    if (stepCounter == FERTIGATION_COUNT) {
      fertPulse = true;
    } else if (stepCounter == WATCHDOG_COUNT) {
      watchdogTripped = true;
      nextState = STATE_FAULT_LOCK;
      effectivePump = false;
    }
  } else {
    if (nextState == STATE_IDLE) {
      stepCounter = 0; // Synchronously clear counter on return to IDLE
    }
  }

  // Latch Flip-Flop State
  currentState = nextState;

  // 6. Drive Physical Actuators & Indicators (PIPO Output Stage)
  digitalWrite(PIN_RELAY_PUMP, effectivePump ? HIGH : LOW);
  digitalWrite(PIN_LED_VALVE1, (currentState == STATE_ZONE_1_ACTIVE) ? HIGH : LOW);
  digitalWrite(PIN_LED_VALVE2, (currentState == STATE_ZONE_2_ACTIVE) ? HIGH : LOW);
  digitalWrite(PIN_LED_FERT,   fertPulse ? HIGH : LOW);
  digitalWrite(PIN_ALARM,      (a || currentState == STATE_FAULT_LOCK) ? HIGH : LOW);

  // 7. Update Displays & Telemetry
  updateLCD(z1, z2, tank, effectivePump, stepCounter);
  transmitTelemetry(z1, z2, tank, rain, manual, m, w, effectivePump, a, fertPulse);
}

// Attempts to clear FAULT_LOCK state
void executeFaultReset() {
  float tank = readPotAsPercentage(PIN_POT_TANK);
  if (tank < MIN_TANK_SAFE) {
    // Safety violation: Reject reset attempt
    Serial.println(F("{\"event\":\"RESET_REJECTED\",\"reason\":\"TANK_BELOW_20%\"}"));
    lcd.setCursor(0, 1);
    lcd.print("RST REJECT: LOW!");
    delay(800);
    return;
  }

  // Safety verified: Return system to IDLE
  currentState = STATE_IDLE;
  watchdogTripped = false;
  stepCounter = 0;

  digitalWrite(PIN_RELAY_PUMP, LOW);
  digitalWrite(PIN_LED_VALVE1, LOW);
  digitalWrite(PIN_LED_VALVE2, LOW);
  digitalWrite(PIN_LED_FERT,   LOW);
  digitalWrite(PIN_ALARM,      LOW);

  Serial.println(F("{\"event\":\"FAULT_CLEARED\",\"state\":\"IDLE\"}"));
  lcd.setCursor(0, 1);
  lcd.print("FAULT CLEARED   ");
  delay(500);
}

// =============================================================================
// ARDUINO SETUP (HARDWARE INITIALIZATION)
// =============================================================================
void setup() {
  // Initialize Serial Monitor at 9600 baud
  Serial.begin(9600);
  while (!Serial && millis() < 1000); // Allow serial pipeline to settle

  // Configure Digital Input Pins with Internal Pull-Ups where applicable
  pinMode(PIN_SW_RAIN,   INPUT);
  pinMode(PIN_SW_MANUAL, INPUT);
  pinMode(PIN_BTN_CLOCK, INPUT_PULLUP);
  pinMode(PIN_BTN_RESET, INPUT_PULLUP);

  // Configure Digital Output Pins
  pinMode(PIN_RELAY_PUMP, OUTPUT);
  pinMode(PIN_LED_VALVE1, OUTPUT);
  pinMode(PIN_LED_VALVE2, OUTPUT);
  pinMode(PIN_LED_FERT,   OUTPUT);
  pinMode(PIN_ALARM,      OUTPUT);

  // Ensure all actuators begin in safe de-energized state
  digitalWrite(PIN_RELAY_PUMP, LOW);
  digitalWrite(PIN_LED_VALVE1, LOW);
  digitalWrite(PIN_LED_VALVE2, LOW);
  digitalWrite(PIN_LED_FERT,   LOW);
  digitalWrite(PIN_ALARM,      LOW);

  // Initialize I2C Liquid Crystal Display
  lcd.init();
  lcd.backlight();
  lcd.setCursor(0, 0);
  lcd.print("AgriSense Init..");
  lcd.setCursor(0, 1);
  lcd.print("DEC0101 Group 11");
  delay(1200);
  lcd.clear();

  // Print system header to serial console
  Serial.println(F("=================================================="));
  Serial.println(F("AgriSense Embedded Controller Firmware Initialized"));
  Serial.println(F("Module 5 Hardware Parity • DEC0101 PBL Group 11"));
  Serial.println(F("=================================================="));

  // Perform initial combinational evaluation
  float z1   = readPotAsPercentage(PIN_POT_ZONE1);
  float z2   = readPotAsPercentage(PIN_POT_ZONE2);
  float tank = readPotAsPercentage(PIN_POT_TANK);
  updateHysteresis(z1, z2);
  updateLCD(z1, z2, tank, false, stepCounter);
}

// =============================================================================
// ARDUINO MAIN LOOP (EVENT SCANNING & DEBOUNCED TRIGGERING)
// =============================================================================
void loop() {
  int currentClockReading = digitalRead(PIN_BTN_CLOCK);
  int currentResetReading = digitalRead(PIN_BTN_RESET);

  // Detect Falling Edge on Clock Step Button (Pressed = LOW)
  if (currentClockReading != lastClockBtnState) {
    lastClockDebounceTime = millis();
  }
  if ((millis() - lastClockDebounceTime) > DEBOUNCE_DELAY) {
    if (currentClockReading == LOW && lastClockBtnState == HIGH) {
      executeClockStep();
    }
  }
  lastClockBtnState = currentClockReading;

  // Detect Falling Edge on Fault Reset Button (Pressed = LOW)
  if (currentResetReading != lastResetBtnState) {
    lastResetDebounceTime = millis();
  }
  if ((millis() - lastResetDebounceTime) > DEBOUNCE_DELAY) {
    if (currentResetReading == LOW && lastResetBtnState == HIGH) {
      executeFaultReset();
    }
  }
  lastResetBtnState = currentResetReading;

  // Passive telemetry update every 500 ms when idle
  static unsigned long lastPassiveUpdate = 0;
  if (millis() - lastPassiveUpdate > 500) {
    lastPassiveUpdate = millis();
    float z1   = readPotAsPercentage(PIN_POT_ZONE1);
    float z2   = readPotAsPercentage(PIN_POT_ZONE2);
    float tank = readPotAsPercentage(PIN_POT_TANK);
    bool pump  = (currentState == STATE_ZONE_1_ACTIVE || currentState == STATE_ZONE_2_ACTIVE);
    updateLCD(z1, z2, tank, pump, stepCounter);
  }
}
