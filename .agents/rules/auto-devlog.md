---
trigger: always_on
description: Enforce automated markdown change-tracking and devlog entries across all AgriSense development
---

# Automated Devlog Rule

After ANY task that creates, edits, refactors, fixes, or deletes code, configuration, tests, or firmware, you MUST automatically log the update inside `docs/devlog/` before finishing your turn.

## Segment Mapping
Append the update to the matching segment file below (create the file if it is missing):
- **Setup, dependencies, or PRD/spec overrides:** `docs/devlog/01_setup_spec_lock.md`
- **`digital_core.py` or core logic tests:** `docs/devlog/02_digital_core.md`
- **`database.py`, `reports.py`, or evidence scripts:** `docs/devlog/03_db_and_reports.md`
- **`app.py` or Streamlit UI/browser checks:** `docs/devlog/04_streamlit_ui.md`
- **`firmware/wokwi/*`:** `docs/devlog/05_wokwi_firmware.md`
- **Cross-cutting bug fixes, README, or release audits:** `docs/devlog/06_fixes_and_release.md`

Do NOT create duplicate files for minor fixes; always append chronologically to the relevant segment file.

## Required Entry Template
Strictly follow this Markdown format for every logged entry:

```markdown
### [YYYY-MM-DD HH:MM] Update #<N>: <Short Action Title>
- **Syllabus / System Scope:** <Module 1–5 or Infrastructure>
- **Files Changed:** `<list of created/modified files>`
- **What Changed:** <concise technical bullet points>
- **Why (Engineering Reasoning):** <root cause, bug fixed, or design trade-off>
- **Verification Status:** <exact command run + PASS/FAIL summary; never claim verified without running>
```

## Master Index Rule
Whenever an entry is added to any segment file:
1. Append a 1-row summary to the master index table in `docs/devlog/INDEX.md`.
2. Format table columns: `| Date/Time | Segment File | Update Title | Syllabus Module | Verification |`.
