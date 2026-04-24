"""Minimal ASGI entrypoint for Vercel. Streamlit apps are not supported on Vercel's Python runtime."""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(title="Time Manager Accenture")

REPO = "https://github.com/pastapomodoro/time_manager_accenture"


@app.get("/", response_class=HTMLResponse)
def root() -> str:
    return f"""<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1"/>
  <title>Time Manager Accenture</title>
  <style>
    body {{
      font-family: "Inter", system-ui, -apple-system, sans-serif;
      max-width: 40rem;
      margin: 0 auto;
      padding: 2.5rem 1.25rem 3rem;
      line-height: 1.6;
      color: #1E1535;
      background: linear-gradient(180deg, #FAF8FF 0%, #F5F0FF 100%);
      min-height: 100vh;
    }}
    h1 {{
      font-weight: 600;
      letter-spacing: -0.03em;
      color: #2E1065;
      margin: 0 0 0.5rem;
      font-size: 1.65rem;
    }}
    p {{ margin: 0.85rem 0; color: #3D3558; }}
    code {{
      background: #EDE9FE;
      color: #4C1D95;
      padding: 0.15rem 0.4rem;
      border-radius: 6px;
      font-size: 0.9em;
    }}
    pre {{
      background: #F1EBFF;
      border: 1px solid #DDD6FE;
      border-radius: 10px;
      padding: 1rem 1.1rem;
      overflow-x: auto;
      font-size: 0.85rem;
    }}
    a {{ color: #6D28D9; text-decoration: none; font-weight: 500; }}
    a:hover {{ text-decoration: underline; }}
  </style>
</head>
<body>
  <h1>Time Manager Accenture</h1>
  <p>Questo progetto è un&apos;app <strong>Streamlit</strong>. Vercel espone qui solo una pagina informativa:
  il runtime serverless non esegue <code>streamlit run</code>.</p>
  <p><strong>Esegui in locale:</strong></p>
  <pre><code>pip install -r requirements.txt
streamlit run ai_team_estimator.py
# oppure
streamlit run cm1_estimator.py</code></pre>
  <p><strong>Deploy Streamlit consigliato:</strong> collega il repo a
  <a href="https://share.streamlit.io/">Streamlit Community Cloud</a>
  e imposta il file principale (<code>ai_team_estimator.py</code> o <code>cm1_estimator.py</code>).</p>
  <p><a href="{REPO}">Repository su GitHub</a></p>
</body>
</html>
"""

