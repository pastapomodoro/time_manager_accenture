"""Supabase wrapper — profiles, presets, xlsx storage."""
import streamlit as st
from supabase import create_client, Client

BUCKET = "xlsx"
XLSX_PATH = "ai_team_data.xlsx"


@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_ANON_KEY"]
    return create_client(url, key)


def is_supabase_configured() -> bool:
    try:
        return bool(st.secrets.get("SUPABASE_URL") and st.secrets.get("SUPABASE_ANON_KEY"))
    except Exception:
        return False


# ── AUTH ──────────────────────────────────────────────────────

def sign_in(email: str, password: str):
    return get_supabase().auth.sign_in_with_password({"email": email, "password": password})


def sign_out():
    get_supabase().auth.sign_out()
    st.session_state.pop("sb_session", None)


# ── PROFILES ──────────────────────────────────────────────────

def load_profiles_db() -> list[dict]:
    rows = get_supabase().table("profiles").select("*").order("id").execute()
    return rows.data or []


def save_profiles_db(profiles: list[dict]):
    sb = get_supabase()
    sb.table("profiles").delete().neq("id", 0).execute()
    if profiles:
        sb.table("profiles").insert(profiles).execute()


# ── PRESETS ───────────────────────────────────────────────────

def load_presets_db() -> dict:
    rows = get_supabase().table("presets").select("nome,data").execute()
    return {r["nome"]: r["data"] for r in (rows.data or [])}


def save_preset_db(nome: str, data: dict):
    sb = get_supabase()
    sb.table("presets").upsert({"nome": nome, "data": data}, on_conflict="nome").execute()


def delete_preset_db(nome: str):
    get_supabase().table("presets").delete().eq("nome", nome).execute()


# ── XLSX STORAGE ──────────────────────────────────────────────

def load_xlsx_from_storage() -> bytes | None:
    try:
        import httpx
        url = st.secrets["SUPABASE_URL"]
        pub_url = f"{url}/storage/v1/object/public/{BUCKET}/{XLSX_PATH}"
        r = httpx.get(pub_url, timeout=10)
        if r.status_code == 200:
            return r.content
        return None
    except Exception:
        return None


def upload_xlsx_to_storage(file_bytes: bytes):
    sb = get_supabase()
    try:
        sb.storage.from_(BUCKET).remove([XLSX_PATH])
    except Exception:
        pass
    sb.storage.from_(BUCKET).upload(XLSX_PATH, file_bytes,
                                    file_options={"content-type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"})
