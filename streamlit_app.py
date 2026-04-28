"""Entry point for Streamlit Community Cloud (default file: streamlit_app.py)."""

from pathlib import Path
import runpy

_root = Path(__file__).resolve().parent
runpy.run_path(str(_root / "ai_team_estimator.py"), run_name="__main__")
