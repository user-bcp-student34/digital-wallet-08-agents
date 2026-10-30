"""Wallet Onboarding Service (MVP básico funcional) — HU01.

Rol: Backend (ver agents/backend.py). Implementa el contrato OpenAPI local
definido en architect.md (sección <<<OPENAPI>>>) y consume el mock externo
documentado en client/openapi/kyc-wallet-mock.yaml.

Alcance de esta iteración (ver openspec/changes/onboarding-wallet-registration):
- Registro guiado (CA-01/CA-02).
- Creación y consulta de wallet contra el mock real de KYC (CA-03), incluyendo
  los escenarios APPROVED, MANUAL_REVIEW, REJECTED y UNAVAILABLE (CA-04).
- Límites de operación de ACTIVE_BASIC (CA-05), simulados sobre un ledger
  diario en memoria porque el mock no expone endpoints de pago/recarga reales.

No incluye (fuera de alcance de esta entrega): verificación de correo/celular,
biometría simulada, nivel ACTIVE_FULL ni agregación de métricas MAU/CAC.

Persistencia: en memoria del proceso. Se reinicia con el servidor; no hay
base de datos en esta iteración (no se activó el rol `data`).
"""
from __future__ import annotations

import os
import re
import uuid
from datetime import datetime, date
from typing import Literal, Optional
from zoneinfo import ZoneInfo

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------

MOCK_BASE_URL = os.environ.get(
    "KYC_WALLET_MOCK_BASE_URL",
    "https://bcp-wallet-mock.yefri.workers.dev/groups/8",
)
PERU_TZ = ZoneInfo("America/Lima")

# Entorno de ejecución: solo development/test habilitan el gancho de prueba
# `testScenario`. En production, forzar un escenario del mock se rechaza.
APP_ENV = os.environ.get("APP_ENV", "development").lower()

# Límites de ACTIVE_BASIC (céntimos de PEN). Parametrizables vía entorno,
# conforme a "Los límites por nivel son parametrizables" en wallet-tier-limits.
ACTIVE_BASIC_PER_OPERATION = int(os.environ.get("ACTIVE_BASIC_PER_OPERATION_CENTS", "2000"))  # S/20
ACTIVE_BASIC_DAILY_TOTAL = int(os.environ.get("ACTIVE_BASIC_DAILY_TOTAL_CENTS", "6000"))  # S/60

NAME_RE = re.compile(r"^[A-Za-zÁÉÍÓÚÑÜáéíóúñü]+(?: [A-Za-zÁÉÍÓÚÑÜáéíóúñü]+)*$")
SURNAME_RE = re.compile(r"^[A-Za-zÁÉÍÓÚÑÜáéíóúñü]+$")
USERNAME_RE = re.compile(r"^[A-Za-z0-9._-]+$")

app = FastAPI(
    title="Wallet Onboarding Service (MVP básico funcional)",
    version="0.1.0",
    description="Orquesta el registro de HU01 contra el mock de KYC & Wallet.",
)

# ---------------------------------------------------------------------------
# Almacenes en memoria (sin base de datos en esta iteración)
# ---------------------------------------------------------------------------

_usernames: dict[str, dict] = {}
_wallets: dict[str, dict] = {}
_ledger: dict[str, dict] = {}
_events: list[dict] = []


def _today_peru() -> date:
    return datetime.now(PERU_TZ).date()


# ---------------------------------------------------------------------------
# Esquemas
# ---------------------------------------------------------------------------

class UsernameAvailability(BaseModel):
    username: str
    available: bool
    suggestions: list[str] = Field(default_factory=list)


class RegistrationRequest(BaseModel):
    nombres: str = Field(max_length=30)
    apellidoPaterno: str = Field(max_length=20)
    apellidoMaterno: str = Field(max_length=20)
    username: str = Field(max_length=20)
    password: str
    flowId: str
    testScenario: Optional[Literal["APPROVED", "REJECTED", "MANUAL_REVIEW", "UNAVAILABLE"]] = None

    @field_validator("nombres")
    @classmethod
    def _validate_nombres(cls, v: str) -> str:
        if not NAME_RE.fullmatch(v):
            raise ValueError("nombres solo admite letras y espacios entre nombres")
        return v

    @field_validator("apellidoPaterno", "apellidoMaterno")
    @classmethod
    def _validate_apellido(cls, v: str) -> str:
        if not SURNAME_RE.fullmatch(v):
            raise ValueError("los apellidos solo admiten caracteres alfabéticos")
        return v

    @field_validator("username")
    @classmethod
    def _validate_username(cls, v: str) -> str:
        if not USERNAME_RE.fullmatch(v):
            raise ValueError("el usuario admite letras, números y los símbolos . _ -")
        return v


class RegistrationResult(BaseModel):
    username: str
    kycId: str
    walletId: str
    kycStatus: Literal["ACTIVE", "PENDING", "REJECTED"]
    appTier: Optional[Literal["ACTIVE_BASIC"]] = None
    balance: int
    currency: str = "PEN"
    supportCase: Optional[dict] = None
    message: str


class WalletLimits(BaseModel):
    perOperation: int
    dailyRemaining: int


class WalletView(BaseModel):
    walletId: str
    kycStatus: Literal["ACTIVE", "PENDING", "REJECTED"]
    appTier: Optional[Literal["ACTIVE_BASIC"]] = None
    balance: int
    reserved: int
    available: int
    currency: str
    limits: Optional[WalletLimits] = None


class KycStatusView(BaseModel):
    kycId: str
    walletId: str
    status: Literal["ACTIVE", "PENDING", "REJECTED"]
    supportCase: Optional[dict] = None


class AmountRequest(BaseModel):
    amount: int = Field(gt=0, description="Monto en céntimos de PEN.")


class LedgerEntry(BaseModel):
    walletId: str
    type: Literal["RECHARGE", "PAYMENT"]
    amount: int
    dailyTotal: int
    dailyRemaining: int
    timestamp: datetime


class AnalyticsEvent(BaseModel):
    flowId: str
    type: Literal["start", "step", "complete", "abandon"]
    step: Optional[str] = None
    timestamp: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Cliente del mock externo
# ---------------------------------------------------------------------------

async def _mock_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(base_url=MOCK_BASE_URL, timeout=10.0)


async def create_kyc_verification(document: str, scenario: Optional[str]) -> dict:
    payload: dict = {"documentType": "TEST", "document": document}
    if scenario:
        payload["scenario"] = scenario
    async with await _mock_client() as client:
        try:
            response = await client.post("/kyc/verifications", json=payload)
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=503,
                detail={"code": "KYC_UNAVAILABLE", "message": f"No se pudo contactar al mock: {exc}"},
            ) from exc

    if response.status_code == 503:
        raise HTTPException(status_code=503, detail=_safe_json(response))
    if response.status_code in (400, 413, 429):
        raise HTTPException(status_code=response.status_code, detail=_safe_json(response))
    if response.status_code != 201:
        raise HTTPException(
            status_code=502,
            detail={"code": "KYC_UNEXPECTED", "message": f"Respuesta inesperada ({response.status_code})"},
        )
    return response.json()


async def get_wallet_remote(wallet_id: str) -> dict:
    async with await _mock_client() as client:
        try:
            response = await client.get(f"/wallets/{wallet_id}")
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=503,
                detail={"code": "KYC_UNAVAILABLE", "message": f"No se pudo contactar al mock: {exc}"},
            ) from exc
    if response.status_code == 404:
        raise HTTPException(status_code=404, detail=_safe_json(response))
    if response.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail={"code": "WALLET_UNEXPECTED", "message": f"Respuesta inesperada ({response.status_code})"},
        )
    return response.json()


async def list_support_cases() -> list[dict]:
    async with await _mock_client() as client:
        try:
            response = await client.get("/support/cases")
        except httpx.RequestError:
            return []
    if response.status_code != 200:
        return []
    return response.json()


def _safe_json(response: httpx.Response) -> dict:
    try:
        return response.json()
    except ValueError:
        return {"code": "UNKNOWN", "message": response.text}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/username-availability", response_model=UsernameAvailability)
def username_availability(username: str) -> UsernameAvailability:
    if not USERNAME_RE.fullmatch(username) or len(username) > 20:
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_USERNAME", "message": "El usuario admite letras, números y . _ -, máx. 20 caracteres."},
        )
    taken = username.lower() in _usernames
    suggestions: list[str] = []
    if taken:
        base = re.sub(r"[^A-Za-z]", "", username) or "usuario"
        for n in (1, 2, 3):
            candidate = f"{base}{uuid.uuid4().int % 10000:04d}{n}"[:20]
            if candidate.lower() not in _usernames:
                suggestions.append(candidate)
    return UsernameAvailability(username=username, available=not taken, suggestions=suggestions)


@app.post("/registrations", response_model=RegistrationResult, status_code=201)
async def create_registration(payload: RegistrationRequest) -> RegistrationResult:
    if payload.testScenario is not None and APP_ENV == "production":
        raise HTTPException(
            status_code=400,
            detail={
                "code": "TEST_SCENARIO_NOT_ALLOWED",
                "message": "testScenario solo está disponible fuera de producción.",
            },
        )
    if payload.username.lower() in _usernames:
        raise HTTPException(
            status_code=400,
            detail={"code": "USERNAME_TAKEN", "message": "El usuario no está disponible."},
        )

    # No se solicita ni recolecta un documento real en esta entrega: se genera
    # un documento sintético TEST- únicamente para cumplir el contrato del mock.
    synthetic_document = f"TEST-{uuid.uuid4().hex[:12].upper()}"
    verification = await create_kyc_verification(synthetic_document, payload.testScenario)

    kyc_id = verification["id"]
    wallet_id = verification["wallet_id"]
    status = verification["status"]

    support_case = None
    app_tier = None
    balance = 0
    currency = "PEN"
    message = ""

    if status == "ACTIVE":
        wallet = await get_wallet_remote(wallet_id)
        balance = wallet["balance"]
        currency = wallet["currency"]
        app_tier = "ACTIVE_BASIC"
        message = "Cuenta creada y activa. Completa tu perfil para desbloquear más operaciones."
    elif status == "PENDING":
        cases = await list_support_cases()
        support_case = next((c for c in cases if c.get("resource") == kyc_id), None)
        message = "Tu cuenta está en revisión manual. Te avisaremos cuando se resuelva."
    elif status == "REJECTED":
        message = "Tu verificación fue rechazada. No es posible operar con esta cuenta."

    # La contraseña nunca se persiste, registra en logs ni se incluye en
    # eventos analíticos o respuestas: se recibe únicamente para validar el
    # registro y se descarta tras procesar la solicitud (no se guarda en
    # ninguno de los almacenes en memoria de esta demo).
    _usernames[payload.username.lower()] = {
        "nombres": payload.nombres,
        "walletId": wallet_id,
        "kycId": kyc_id,
    }
    _wallets[wallet_id] = {
        "kycId": kyc_id,
        "username": payload.username,
        "status": status,
        "appTier": app_tier,
    }

    _events.append(
        {
            "flowId": payload.flowId,
            "type": "complete" if status == "ACTIVE" else "abandon",
            "step": "registration",
            "timestamp": datetime.now(PERU_TZ).isoformat(),
        }
    )

    return RegistrationResult(
        username=payload.username,
        kycId=kyc_id,
        walletId=wallet_id,
        kycStatus=status,
        appTier=app_tier,
        balance=balance,
        currency=currency,
        supportCase=support_case,
        message=message,
    )


def _wallet_limits(wallet_id: str) -> WalletLimits:
    today = _today_peru().isoformat()
    entry = _ledger.get(wallet_id)
    daily_total = entry["total"] if entry and entry["day"] == today else 0
    remaining = max(ACTIVE_BASIC_DAILY_TOTAL - daily_total, 0)
    return WalletLimits(perOperation=ACTIVE_BASIC_PER_OPERATION, dailyRemaining=remaining)


@app.get("/wallets/{wallet_id}", response_model=WalletView)
async def get_wallet(wallet_id: str) -> WalletView:
    local = _wallets.get(wallet_id)
    if local is None:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Wallet no registrada localmente."})

    remote = await get_wallet_remote(wallet_id)
    local["status"] = remote["status"]
    if remote["status"] == "ACTIVE" and local["appTier"] is None:
        local["appTier"] = "ACTIVE_BASIC"
    if remote["status"] != "ACTIVE":
        local["appTier"] = None

    limits = _wallet_limits(wallet_id) if local["appTier"] == "ACTIVE_BASIC" else None

    return WalletView(
        walletId=wallet_id,
        kycStatus=remote["status"],
        appTier=local["appTier"],
        balance=remote["balance"],
        reserved=remote["reserved"],
        available=remote["available"],
        currency=remote["currency"],
        limits=limits,
    )


@app.get("/wallets/{wallet_id}/kyc", response_model=KycStatusView)
async def get_wallet_kyc(wallet_id: str) -> KycStatusView:
    local = _wallets.get(wallet_id)
    if local is None:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Wallet no registrada localmente."})

    remote = await get_wallet_remote(wallet_id)
    support_case = None
    if remote["status"] == "PENDING":
        cases = await list_support_cases()
        support_case = next((c for c in cases if c.get("resource") == local["kycId"]), None)

    return KycStatusView(
        kycId=local["kycId"],
        walletId=wallet_id,
        status=remote["status"],
        supportCase=support_case,
    )


def _apply_ledger_movement(wallet_id: str, amount: int, movement_type: Literal["RECHARGE", "PAYMENT"]) -> LedgerEntry:
    local = _wallets.get(wallet_id)
    if local is None:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Wallet no registrada localmente."})
    if local["status"] != "ACTIVE" or local["appTier"] != "ACTIVE_BASIC":
        raise HTTPException(
            status_code=409,
            detail={
                "code": "WALLET_NOT_OPERATIONAL",
                "message": f"La wallet está en estado {local['status']} y no admite operaciones.",
            },
        )
    if amount > ACTIVE_BASIC_PER_OPERATION:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "PER_OPERATION_LIMIT_EXCEEDED",
                "message": f"El monto supera el límite de {ACTIVE_BASIC_PER_OPERATION} céntimos por operación de ACTIVE_BASIC.",
            },
        )

    today = _today_peru().isoformat()
    entry = _ledger.setdefault(wallet_id, {"day": today, "total": 0})
    if entry["day"] != today:
        entry["day"] = today
        entry["total"] = 0

    if entry["total"] + amount > ACTIVE_BASIC_DAILY_TOTAL:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "DAILY_LIMIT_EXCEEDED",
                "message": f"El total diario combinado de ACTIVE_BASIC es de {ACTIVE_BASIC_DAILY_TOTAL} céntimos.",
            },
        )

    entry["total"] += amount
    remaining = max(ACTIVE_BASIC_DAILY_TOTAL - entry["total"], 0)
    return LedgerEntry(
        walletId=wallet_id,
        type=movement_type,
        amount=amount,
        dailyTotal=entry["total"],
        dailyRemaining=remaining,
        timestamp=datetime.now(PERU_TZ),
    )


@app.post("/wallets/{wallet_id}/recharges", response_model=LedgerEntry, status_code=201)
def create_recharge(wallet_id: str, payload: AmountRequest) -> LedgerEntry:
    return _apply_ledger_movement(wallet_id, payload.amount, "RECHARGE")


@app.post("/wallets/{wallet_id}/payments", response_model=LedgerEntry, status_code=201)
def create_payment(wallet_id: str, payload: AmountRequest) -> LedgerEntry:
    return _apply_ledger_movement(wallet_id, payload.amount, "PAYMENT")


@app.post("/analytics/events", status_code=202)
def record_event(event: AnalyticsEvent) -> dict:
    _events.append(
        {
            "flowId": event.flowId,
            "type": event.type,
            "step": event.step,
            "timestamp": (event.timestamp or datetime.now(PERU_TZ)).isoformat(),
        }
    )
    return {"accepted": True}
