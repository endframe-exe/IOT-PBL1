# Segment 01: Setup, Dependencies & Spec Lock Devlog

### [2026-11-24 02:03] Update #1: Devlog & Workspace Rules Bootstrap
- **Syllabus / System Scope:** Infrastructure
- **Files Changed:** `.agents/rules/auto-devlog.md`, `GEMINI.md`, `docs/devlog/INDEX.md`, `docs/devlog/01_setup_spec_lock.md`
- **What Changed:**
  - Configured workspace rule `.agents/rules/auto-devlog.md` with `trigger: always_on` enforcing segment mapping and required entry templates.
  - Established root directive `GEMINI.md` anchoring `AgriSense_Smart_Irrigation_PRD.md`, virtual environment test requirements (`pytest -v`), and devlog enforcement.
  - Initialized master index `docs/devlog/INDEX.md` and initial segment log `docs/devlog/01_setup_spec_lock.md`.
- **Why (Engineering Reasoning):** Establishes an immutable audit trail and automated change-tracking regime across all upcoming development phases to prevent undocumented technical debt and verify compliance with PRD specifications.
- **Verification Status:** File verification and directory check via PowerShell `Get-ChildItem -Recurse` completed (PASS).

### [2026-11-24 02:08] Update #2: Environment Bootstrap, Directory Structure & Spec Lock v1.1
- **Syllabus / System Scope:** Infrastructure & Modules 1–5 Specification Lock
- **Files Changed:** `.venv/`, `.gitignore`, `requirements.txt`, `SPEC_LOCK.md`, `scripts/`, `firmware/wokwi/`
- **What Changed:**
  - Initialized isolated virtual environment `.venv` with Python 3.13.14.
  - Created `.gitignore` ignoring virtual environments, Python caches, database files, and report artifacts.
  - Defined minimal `requirements.txt` containing `streamlit`, `pandas`, `plotly`, `reportlab`, and `pytest`.
  - Created directory scaffolding `scripts/` and `firmware/wokwi/`.
  - Authored binding architecture specification `SPEC_LOCK.md` locking the 5-file architecture, Boolean safety interlocks ($P = W \cdot \overline{R} \cdot (O + M)$, $A = \overline{W}$), Schmitt-trigger hysteresis ($<30\%$ dry, $\ge 45\%$ clear), manual override routing resolution, MOD-16 counter semantics (count 4 fertigation, count 15 emergency lock, pipe-burst simulation), PIPO bit assignments, and standalone Wokwi Arduino Uno hardware parity.
- **Why (Engineering Reasoning):** Prevents architectural drift and code bloat (replacing 16 fragmented modules with 5 cohesive files) while mathematically resolving edge-case conflicts between combinational Boolean outputs and sequential FSM states.
- **Verification Status:** Virtual environment verified (`python -m venv .venv`), directory structure verified, dependencies installed via pip, and test runner verified with `.\.venv\Scripts\pytest --version` -> `pytest 9.2.0` (PASS).

