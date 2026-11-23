# AgriSense - Engineering Guidelines & Workspace Directives

## 1. Core Specifications & Rules Reference
- **PRD Specification:** See [AgriSense_Smart_Irrigation_PRD.md](file:///c:/Users/akhil/Downloads/PBL%20PROJECTS/IOT%20PBL/gemini%20project/AgriSense_Smart_Irrigation_PRD.md) for complete architectural requirements, system design, sensor specs, and project scope.
- **Automated Devlog Rule:** See [.agents/rules/auto-devlog.md](file:///c:/Users/akhil/Downloads/PBL%20PROJECTS/IOT%20PBL/gemini%20project/.agents/rules/auto-devlog.md) for mandatory changelog requirements.

## 2. Test & Environment Standards
- **Python Environment:** Python 3.10+ within virtual environment (`.venv`).
- **Standard Verification Command:** `pytest -v`
- Never report code or fixes as verified without actually running test commands.

## 3. Definition of Done
No task or turn is complete until:
1. **Tests Pass:** All targeted verification commands (including `pytest -v`) execute with zero errors/regressions.
2. **Devlog Updated:** An entry adhering strictly to the template in `.agents/rules/auto-devlog.md` has been appended to the matching segment file under `docs/devlog/`, and recorded in `docs/devlog/INDEX.md`.
