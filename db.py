"""Supabase wrapper — profiles, presets, xlsx storage."""
import json
from pathlib import Path

import streamlit as st
from supabase import create_client, Client

BUCKET = "xlsx"
XLSX_PATH = "ai_team_data.xlsx"
SESSION_FILE = Path(__file__).resolve().parent / ".auth_session.json"


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


def sign_up(email: str, password: str):
    return get_supabase().auth.sign_up({"email": email, "password": password})


def sign_out():
    get_supabase().auth.sign_out()
    st.session_state.pop("sb_session", None)
    clear_saved_session()


def save_session_tokens(session) -> None:
    if not session:
        return
    payload = {
        "access_token": getattr(session, "access_token", None),
        "refresh_token": getattr(session, "refresh_token", None),
    }
    if not payload["access_token"] or not payload["refresh_token"]:
        return
    SESSION_FILE.write_text(json.dumps(payload), encoding="utf-8")


def clear_saved_session() -> None:
    try:
        SESSION_FILE.unlink(missing_ok=True)
    except Exception:
        pass


def restore_saved_session():
    if not SESSION_FILE.exists():
        return None
    try:
        payload = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
        access_token = payload.get("access_token")
        refresh_token = payload.get("refresh_token")
        if not access_token or not refresh_token:
            clear_saved_session()
            return None
        res = get_supabase().auth.set_session(access_token, refresh_token)
        return getattr(res, "session", None) or res
    except Exception:
        clear_saved_session()
        return None


# ── PROFILES ──────────────────────────────────────────────────


def get_current_user_id() -> str | None:
    try:
        res = get_supabase().auth.get_user()
        user = getattr(res, "user", None)
        return getattr(user, "id", None)
    except Exception:
        return None

def load_profiles_db() -> list[dict]:
    user_id = get_current_user_id()
    query = get_supabase().table("profiles").select("*").order("id")
    if user_id:
        try:
            rows = query.eq("user_id", user_id).execute()
            return rows.data or []
        except Exception as exc:
            if "profiles.user_id does not exist" not in str(exc):
                raise
    rows = query.execute()
    return rows.data or []


def save_profiles_db(profiles: list[dict]):
    sb = get_supabase()
    user_id = get_current_user_id()
    if user_id:
        try:
            sb.table("profiles").delete().eq("user_id", user_id).execute()
        except Exception as exc:
            if "profiles.user_id does not exist" not in str(exc):
                raise
            sb.table("profiles").delete().neq("id", 0).execute()
    else:
        sb.table("profiles").delete().neq("id", 0).execute()
    if profiles:
        rows = []
        for profile in profiles:
            row = dict(profile)
            if user_id:
                row["user_id"] = user_id
            rows.append(row)
        try:
            sb.table("profiles").insert(rows).execute()
        except Exception as exc:
            if "profiles.user_id does not exist" not in str(exc):
                raise
            fallback_rows = []
            for profile in profiles:
                row = dict(profile)
                row.pop("user_id", None)
                fallback_rows.append(row)
            sb.table("profiles").insert(fallback_rows).execute()


# ── PRESETS ───────────────────────────────────────────────────

def load_presets_db() -> dict:
    rows = get_supabase().table("presets").select("nome,data").execute()
    return {r["nome"]: r["data"] for r in (rows.data or [])}


def save_preset_db(nome: str, data: dict):
    sb = get_supabase()
    sb.table("presets").delete().eq("nome", nome).execute()
    sb.table("presets").insert({"nome": nome, "data": data}).execute()


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


# ── SUBCONTRACTORS ─────────────────────────────────────────────

def load_subcontractors_db() -> list[dict]:
    rows = get_supabase().table("subcontractors").select("*").order("id").execute()
    return rows.data or []


def save_subcontractors_db(subcos: list[dict]):
    sb = get_supabase()
    sb.table("subcontractors").delete().neq("id", 0).execute()
    if subcos:
        rows = [{k: v for k, v in s.items() if k != "id"} for s in subcos]
        sb.table("subcontractors").insert(rows).execute()
