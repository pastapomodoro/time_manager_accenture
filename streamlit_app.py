"""
Entry point per Streamlit Community Cloud (campo predefinito: streamlit_app.py).

Avvia l'AI Team Estimator. Per il solo CM1 Estimator imposta come main file
`cm1_estimator.py` nelle impostazioni dell'app su share.streamlit.io.
"""

from pathlib import Path
import runpy

_root = Path(__file__).resolve().parent
runpy.run_path(str(_root / "ai_team_estimator.py"), run_name="__main__")
