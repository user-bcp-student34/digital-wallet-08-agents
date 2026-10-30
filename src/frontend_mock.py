"""Frontend mock del onboarding de HU01 (MVP básico funcional).

Rol: Frontend (ver agents/frontend.py). Cliente Streamlit que consume la API
local expuesta por src/main.py (FastAPI, por defecto en http://localhost:8000).

Ejecutar:
    streamlit run src/frontend_mock.py

Variable de entorno opcional:
    WALLET_API_BASE_URL (por defecto http://127.0.0.1:8000)
"""
from __future__ import annotations

import os
import re
import uuid
from datetime import datetime, timezone

import requests
import streamlit as st

API_BASE_URL = os.environ.get("WALLET_API_BASE_URL", "http://127.0.0.1:8000")
STEPS = ["Datos personales", "Usuario", "Contraseña", "Confirmación"]

NAME_RE = re.compile(r"^[A-Za-zÁÉÍÓÚÑÜáéíóúñü]+(?: [A-Za-zÁÉÍÓÚÑÜáéíóúñü]+)*$")
SURNAME_RE = re.compile(r"^[A-Za-zÁÉÍÓÚÑÜáéíóúñü]+$")
USERNAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")


# ---------------------------------------------------------------------------
# Utilidades de validación y analítica (sin enviar contraseñas ni PII a eventos)
# ---------------------------------------------------------------------------

def _password_strength(password: str) -> tuple[int, str]:
    """Heurística simple de robustez. La contraseña nunca se registra en logs/analítica."""
    if not password:
        return 0, "Vacía"
    score = 0
    score += 1 if len(password) >= 8 else 0
    score += 1 if re.search(r"[A-Z]", password) else 0
    score += 1 if re.search(r"[a-z]", password) else 0
    score += 1 if re.search(r"\d", password) else 0
    score += 1 if re.search(r"[^A-Za-z0-9]", password) else 0
    levels = {0: "Muy débil", 1: "Muy débil", 2: "Débil", 3: "Media", 4: "Fuerte", 5: "Muy fuerte"}
    return score, levels[score]


def _emit_event(event_type: str, step: str | None = None) -> None:
    """Emite un evento analítico del funnel de onboarding sin datos personales."""
    try:
        requests.post(
            f"{API_BASE_URL}/analytics/events",
            json={
                "flowId": st.session_state["flow_id"],
                "type": event_type,
                "step": step,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            timeout=5,
        )
    except requests.RequestException:
        pass  # La analítica no debe bloquear el onboarding.


def _init_state() -> None:
    if "flow_id" not in st.session_state:
        st.session_state["flow_id"] = str(uuid.uuid4())
        st.session_state["step"] = 0
        st.session_state["form"] = {}
        st.session_state["result"] = None
        st.session_state["started_at"] = datetime.now(timezone.utc)
        _emit_event("start")


# ---------------------------------------------------------------------------
# Llamadas al backend
# ---------------------------------------------------------------------------

def _check_username(username: str) -> dict:
    response = requests.get(f"{API_BASE_URL}/username-availability", params={"username": username}, timeout=10)
    response.raise_for_status()
    return response.json()


def _submit_registration(form: dict, test_scenario: str | None) -> tuple[int, dict]:
    payload = {**form, "flowId": st.session_state["flow_id"]}
    if test_scenario:
        payload["testScenario"] = test_scenario
    response = requests.post(f"{API_BASE_URL}/registrations", json=payload, timeout=20)
    try:
        body = response.json()
    except ValueError:
        body = {"message": response.text}
    return response.status_code, body


def _get_wallet(wallet_id: str) -> dict | None:
    try:
        response = requests.get(f"{API_BASE_URL}/wallets/{wallet_id}", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None


def _post_movement(wallet_id: str, kind: str, amount_soles: float) -> tuple[int, dict]:
    amount_cents = int(round(amount_soles * 100))
    response = requests.post(
        f"{API_BASE_URL}/wallets/{wallet_id}/{kind}",
        json={"amount": amount_cents},
        timeout=10,
    )
    try:
        body = response.json()
    except ValueError:
        body = {"message": response.text}
    return response.status_code, body


# ---------------------------------------------------------------------------
# Pasos del onboarding
# ---------------------------------------------------------------------------

def _step_personal_data() -> None:
    st.subheader("1. Datos personales")
    form = st.session_state["form"]
    nombres = st.text_input("Nombres", value=form.get("nombres", ""), max_chars=30)
    paterno = st.text_input("Apellido paterno", value=form.get("apellidoPaterno", ""), max_chars=20)
    materno = st.text_input("Apellido materno", value=form.get("apellidoMaterno", ""), max_chars=20)

    errors = []
    if nombres and not NAME_RE.fullmatch(nombres):
        errors.append("Nombres: solo letras y espacios entre nombres (máx. 30 caracteres).")
    if paterno and not SURNAME_RE.fullmatch(paterno):
        errors.append("Apellido paterno: solo caracteres alfabéticos (máx. 20).")
    if materno and not SURNAME_RE.fullmatch(materno):
        errors.append("Apellido materno: solo caracteres alfabéticos (máx. 20).")
    for e in errors:
        st.error(e)

    valid = bool(nombres and paterno and materno and not errors)
    if st.button("Siguiente", disabled=not valid, key="next_1"):
        form.update(nombres=nombres, apellidoPaterno=paterno, apellidoMaterno=materno)
        st.session_state["step"] = 1
        _emit_event("step", "datos_personales")
        st.rerun()


def _step_username() -> None:
    st.subheader("2. Nombre de usuario")
    form = st.session_state["form"]
    username = st.text_input("Usuario", value=form.get("username", ""), max_chars=20)

    availability = None
    if username:
        if not USERNAME_RE.fullmatch(username):
            st.error("El usuario admite letras, números y los símbolos . _ - (máx. 20 caracteres).")
        else:
            try:
                availability = _check_username(username)
            except requests.RequestException as exc:
                st.warning(f"No se pudo validar la disponibilidad ahora mismo: {exc}")

    if availability:
        if availability["available"]:
            st.success("¡Usuario disponible!")
        else:
            st.error("Ese usuario ya está en uso.")
            if availability["suggestions"]:
                st.info("Sugerencias disponibles: " + ", ".join(availability["suggestions"]))

    valid = bool(availability and availability["available"])
    col1, col2 = st.columns(2)
    if col1.button("Atrás", key="back_2"):
        st.session_state["step"] = 0
        st.rerun()
    if col2.button("Siguiente", disabled=not valid, key="next_2"):
        form["username"] = username
        st.session_state["step"] = 2
        _emit_event("step", "usuario")
        st.rerun()


def _step_password() -> None:
    st.subheader("3. Contraseña")
    password = st.text_input("Contraseña", type="password")
    score, level = _password_strength(password)
    st.progress(score / 5)
    st.caption(f"Robustez: {level}")
    if password and score < 3:
        st.warning("Tu contraseña es débil. Usa mayúsculas, minúsculas, números y símbolos.")

    valid = score >= 3
    col1, col2 = st.columns(2)
    if col1.button("Atrás", key="back_3"):
        st.session_state["step"] = 1
        st.rerun()
    if col2.button("Siguiente", disabled=not valid, key="next_3"):
        st.session_state["form"]["password"] = password
        st.session_state["step"] = 3
        _emit_event("step", "contraseña")
        st.rerun()


def _step_confirmation() -> None:
    st.subheader("4. Confirmación")
    form = st.session_state["form"]
    st.write(f"**Nombres:** {form.get('nombres')}")
    st.write(f"**Apellidos:** {form.get('apellidoPaterno')} {form.get('apellidoMaterno')}")
    st.write(f"**Usuario:** {form.get('username')}")

    with st.expander("Opciones de prueba (QA) — no disponibles en producción"):
        test_scenario = st.selectbox(
            "Forzar escenario del mock de KYC",
            options=[None, "APPROVED", "MANUAL_REVIEW", "REJECTED", "UNAVAILABLE"],
            format_func=lambda v: "Automático (APPROVED)" if v is None else v,
        )

    col1, col2 = st.columns(2)
    if col1.button("Atrás", key="back_4"):
        st.session_state["step"] = 2
        st.rerun()
    if col2.button("Crear mi wallet", key="submit"):
        status, body = _submit_registration(form, test_scenario)
        st.session_state["result"] = {"status": status, "body": body}
        st.rerun()


def _render_landing(result: dict) -> None:
    status, body = result["status"], result["body"]

    if status == 201 and body.get("kycStatus") == "ACTIVE":
        st.balloons()
        st.success(f"¡Bienvenido/a, {st.session_state['form']['nombres']}!")
        st.metric("Saldo disponible", f"S/ {body['balance'] / 100:.2f}")
        st.info(
            "Tu cuenta está **ACTIVE_BASIC**: hasta S/20 por operación y S/60 diarios en "
            "pagos y recargas. Completa tu perfil (correo, celular, identidad) para desbloquear "
            "más límites (próxima iteración)."
        )
        _render_operations_panel(body["walletId"])
    elif status == 201 and body.get("kycStatus") == "PENDING":
        st.warning("Tu cuenta está **en revisión manual**. Te avisaremos cuando se resuelva.")
        case = body.get("supportCase")
        if case:
            st.caption(f"Caso de soporte: {case['id']} ({case['status']})")
    elif status == 201 and body.get("kycStatus") == "REJECTED":
        st.error("Tu verificación fue **rechazada**. No es posible operar con esta cuenta.")
    elif status == 503:
        st.error("El servicio de verificación no está disponible en este momento.")
        if st.button("Reintentar registro"):
            st.session_state["result"] = None
            st.rerun()
    else:
        st.error(f"No fue posible completar el registro: {body}")
        if st.button("Reintentar"):
            st.session_state["result"] = None
            st.rerun()


def _render_operations_panel(wallet_id: str) -> None:
    st.divider()
    st.subheader("Panel de operaciones (demo de límites ACTIVE_BASIC)")
    wallet = _get_wallet(wallet_id)
    if wallet and wallet.get("limits"):
        st.caption(
            f"Límite por operación: S/{wallet['limits']['perOperation'] / 100:.2f} · "
            f"Restante hoy: S/{wallet['limits']['dailyRemaining'] / 100:.2f}"
        )

    col1, col2 = st.columns(2)
    with col1:
        recharge_amount = st.number_input("Monto a recargar (S/)", min_value=0.0, step=1.0, key="recharge_amount")
        if st.button("Recargar"):
            status, body = _post_movement(wallet_id, "recharges", recharge_amount)
            (st.success if status == 201 else st.error)(body)
    with col2:
        payment_amount = st.number_input("Monto a pagar (S/)", min_value=0.0, step=1.0, key="payment_amount")
        if st.button("Pagar"):
            status, body = _post_movement(wallet_id, "payments", payment_amount)
            (st.success if status == 201 else st.error)(body)


def main() -> None:
    st.set_page_config(page_title="Wallet Onboarding — MVP básico funcional", page_icon="💳")
    st.title("💳 Crea tu wallet")
    _init_state()

    if st.session_state["result"] is not None:
        _render_landing(st.session_state["result"])
        return

    step = st.session_state["step"]
    st.caption(" → ".join(f"**{s}**" if i == step else s for i, s in enumerate(STEPS)))

    {0: _step_personal_data, 1: _step_username, 2: _step_password, 3: _step_confirmation}[step]()


if __name__ == "__main__":
    main()
