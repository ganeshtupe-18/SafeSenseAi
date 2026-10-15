# SafeSense AI

AI-Powered Food & Consumer Product Safety Platform.

## Team modules
- Ganesh: Phase 1 — Streamlit frontend, authentication UI, navigation and shared theme.
- Dnyandip: Phase 2 — Food Safety and ML.
- Akash: Phase 3 — Food Complaint System and NLP.

## Shared theme
All team members must use `shared/theme/` for common colors, CSS and UI components.

## Setup
1. Create and activate a Python virtual environment.
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill values locally.
4. Run the Streamlit frontend: `streamlit run frontend/app.py`
5. Run the FastAPI backend separately: `uvicorn backend.main:app --reload`

This is an initial scaffold. Backend integrations and authentication must be implemented and tested before production use.
