# Segment 04: Streamlit Web Application Devlog

### [2026-11-24 02:22] Update #5: Streamlit Interactive Dashboard & Control Center
- **Syllabus / System Scope:** User Interface & Presentation Layer (Modules 1–4 Integration)
- **Files Changed:** `app.py`
- **What Changed:**
  - Built production-ready 4-tab Streamlit dashboard (`Overview`, `Farm Simulator`, `Logic Control (Viva View)`, `Analytics & Reports`) adhering to PRD Section 11 & Section 18.3.
  - Resolved session state collision risks by isolating UI widget keys (`ui_z1`, `ui_z2`, `ui_tank`, etc.) from digital engine state, synchronizing via clean unidirectional helpers (`sync_ui_to_engine` / `sync_engine_to_ui`).
  - Implemented AgTech theme with forest green accents (`#1B5E20`), neutral metric cards, status badges, and prominent educational simulation warning banner.
  - Implemented `@st.fragment(run_every="1.5s")` autonomous clock mode with natural evaporation for live hands-free viva demonstrations.
  - Implemented interactive 16-row truth table viewer with active minterm highlighting and arrow pointer (`👉 Active Minterm`).
  - Added export action downloads for UTF-8 CSV datasets and ReportLab PDF audit reports with guarded SQLite history clearing.
- **Why (Engineering Reasoning):** Decouples UI presentation completely from control decisions (all logic delegated to `digital_core.py`), preventing state corruption while providing an intuitive, examiner-friendly interface for viva defense.
- **Verification Status:** Launched via `streamlit run app.py` on port 8501 and verified server initialization with zero console errors (PASS).

### [2026-11-24 03:32] Update #8: 3D Blender-Shaded Virtual Farm Twin & 1-Click Launcher
- **Syllabus / System Scope:** 3D Cyber-Physical Twin, Presentation & Release Automation (Modules 1–5 Integration)
- **Files Changed:** `assets/virtual_farm_twin.html`, `app.py`, `START_AGRISENSE.bat`, `README.md`
- **What Changed:**
  - Built 2.5D Blender-shaded isometric digital twin canvas (`assets/virtual_farm_twin.html`) featuring interactive 1-click controls for Rain, Zone 1 & 2 Irrigation, Manual Pump, NPK Fertigation, Low Tank Fault, and Pipe Burst Watchdog with live HUD and particle animation.
  - Integrated digital twin directly into `app.py` as primary Tab 0 via `streamlit.components.v1.html(..., height=760, scrolling=True)` alongside a direct 1-click link to the Wokwi Arduino Uno hardware simulation.
  - Authored automated Windows demo launcher `START_AGRISENSE.bat` that self-provisions `.venv`, installs requirements, opens the browser, and launches Streamlit.
  - Enriched `README.md` with complete architecture diagram, Group 11 ownership table, and 1-click setup instructions.
- **Why (Engineering Reasoning):** Delivers an immersive, interactive visual representation of the physical farm environment that examiner committees can explore in real-time, bridging high-level agronomy with low-level digital logic and embedded hardware.
- **Verification Status:** `.\.venv\Scripts\pytest -v` (45/45 passed in 3.04s) and `START_AGRISENSE.bat` verified (PASS).
