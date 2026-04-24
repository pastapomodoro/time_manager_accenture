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
    body {{ font-family: system-ui, sans-serif; max-width: 42rem; margin: 2rem auto; padding: 0 1rem; line-height: 1.5; }}
    code {{ background: #f4f4f5; padding: 0.15rem 0.35rem; border-radius: 4px; }}
    a {{ color: #2563eb; }}
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

