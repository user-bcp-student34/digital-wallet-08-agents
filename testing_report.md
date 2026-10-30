# Informe de Pruebas — HU01 Creación de Wallet (MVP básico funcional)

> Rol: **Testing** (ver [agents/testing.py](agents/testing.py)).
> Alcance verificado: registro guiado + alta/consulta de wallet contra el mock real de KYC
> (`client/openapi/kyc-wallet-mock.yaml`) y límites de `ACTIVE_BASIC`, según
> [architect.md](architect.md) y `openspec/changes/onboarding-wallet-registration`.
> Todas las pruebas de este informe **fueron ejecutadas realmente** contra el backend
> (`src/main.py`) y el frontend (`src/frontend_mock.py`) en ejecución local, que a su vez
> llamó al mock externo en vivo. No hay resultados inventados ni simulados.

## 1. Prerrequisitos y preparación

1. Entorno virtual Python con dependencias instaladas:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```
2. Backend en ejecución (puerto 8000), con estado en memoria limpio antes de cada corrida de
   Karate (se reinicia el proceso para no arrastrar usuarios/ledger de corridas previas):
   ```powershell
   .\.venv\Scripts\python.exe -m uvicorn src.main:app --host 127.0.0.1 --port 8000
   ```
3. Frontend en ejecución (puerto 8501), para la prueba Selenium:
   ```powershell
   .\.venv\Scripts\python.exe -m streamlit run src\frontend_mock.py --server.headless true --server.port 8501
   ```
4. Karate standalone (`tools/karate.jar`, v2.1.4) y Java 21 instalados para las pruebas de API.
5. Microsoft Edge instalado; Selenium 4.52 resuelve el driver automáticamente (Selenium Manager).
6. Datos de prueba sintéticos: usuarios `k_*` / `sel_*` + sufijo aleatorio (UUID), contraseñas de
   prueba que nunca se registran en logs ni analítica (ver `src/main.py`, comentario sobre
   almacenamiento en memoria). El mock solo acepta `documentType: TEST` y `document` con prefijo
   `TEST-`, generado automáticamente por el backend (nunca se usan documentos reales).

## 2. Pruebas de API (Karate DSL)

Archivo: [tests/karate/registro_wallet.feature](tests/karate/registro_wallet.feature)
Configuración: [tests/karate/karate-config.js](tests/karate/karate-config.js) (`baseUrl = http://127.0.0.1:8000`)

Comando ejecutado:
```powershell
cd tests\karate
java -jar ..\..\tools\karate.jar registro_wallet.feature
```

**Resultado real obtenido** (salida de consola de la ejecución):
```
feature: registro_wallet.feature
scenarios:  6 | passed:  6 | passed | time: 9.3780
=========================================================
elapsed:   9.50s | threads:   1 | efficiency: 0.99
features:    1 | passed:    1 | all passed
scenarios:   6 | passed:    6 | all passed
```
Reporte HTML generado: `tests/karate/target/karate-reports/karate-summary.html` (no versionado;
se regenera en cada corrida).

### Matriz de trazabilidad — API

| Criterio | Escenario Karate | Resultado esperado | Estado |
|---|---|---|---|
| CA-03 | `Registro feliz crea una wallet ACTIVE_BASIC con saldo cero (escenario APPROVED)` | `201`, `kycStatus=ACTIVE`, `appTier=ACTIVE_BASIC`, `balance=0`, límites `2000/6000` céntimos | **EJECUTADO — PASÓ** |
| CA-04 | `Escenario MANUAL_REVIEW deja la wallet en PENDING y abre un caso de soporte` | `201`, `kycStatus=PENDING`, `appTier=null`, `supportCase.status=OPEN` | **EJECUTADO — PASÓ** |
| CA-04 | `Escenario REJECTED bloquea la cuenta y los pagos devuelven 409` | `201` con `kycStatus=REJECTED`; pago posterior → `409 WALLET_NOT_OPERATIONAL` | **EJECUTADO — PASÓ** |
| CA-04 | `Escenario UNAVAILABLE no crea wallet y responde 503` | `503` sin wallet creada | **EJECUTADO — PASÓ** |
| CA-02 | `El registro rechaza nombres con caracteres no alfabéticos` | `422` (validación Pydantic) | **EJECUTADO — PASÓ** |
| CA-02 | `El nombre de usuario repetido no está disponible y se informa el conflicto` | 1er registro `201`; 2º con mismo usuario → `400 USERNAME_TAKEN` | **EJECUTADO — PASÓ** |

### Pruebas manuales de API complementarias (evidencia en esta sesión, no automatizadas en `.feature`)

Estas llamadas se ejecutaron directamente contra el backend en vivo durante el desarrollo para
validar comportamientos no cubiertos arriba; se documentan por transparencia:

| Verificación | Resultado real observado | Estado |
|---|---|---|
| `GET /username-availability` con usuario disponible | `200 {"available": true, "suggestions": []}` | EJECUTADO |
| Límite por operación `ACTIVE_BASIC` (S/20 = 2000 céntimos) | Pago de 2500 céntimos → `403 PER_OPERATION_LIMIT_EXCEEDED` | EJECUTADO |
| Límite diario combinado `ACTIVE_BASIC` (S/60 = 6000 céntimos) | 3 pagos de 2000 céntimos tras una recarga de 1500 → el 4º pago (hubiera superado 6000) → `403 DAILY_LIMIT_EXCEEDED` | EJECUTADO |
| `GET /wallets/{id}/kyc` con wallet `PENDING` | `200` con `status=PENDING` y `supportCase` enlazado | EJECUTADO |
| `POST /analytics/events` | `202 {"accepted": true}` | EJECUTADO |

## 3. Pruebas de interfaz (Selenium)

Archivo: [tests/selenium/test_onboarding_ui.py](tests/selenium/test_onboarding_ui.py)

Comandos ejecutados (ambos se corrieron realmente; se documentan las dos formas soportadas):
```powershell
# Como script:
.\.venv\Scripts\python.exe tests\selenium\test_onboarding_ui.py

# Como prueba pytest:
.\.venv\Scripts\python.exe -m pytest tests\selenium\test_onboarding_ui.py -v
```

**Resultado real obtenido (pytest):**
```
tests/selenium/test_onboarding_ui.py::test_onboarding_happy_path PASSED  [100%]
============================= 1 passed in 15.49s ==============================
```

Capturas de evidencia generadas en `tests/selenium/screenshots/` (no versionadas; se regeneran en
cada corrida): `01_datos_personales.png`, `02_usuario_disponible.png`, `03_password_strength.png`,
`04_confirmacion.png`, `05_landing.png`. La última muestra el saludo de bienvenida, el saldo
`S/ 0.00` y el aviso de nivel `ACTIVE_BASIC`.

### Matriz de trazabilidad — Interfaz

| Criterio | Verificación en `test_onboarding_happy_path` | Estado |
|---|---|---|
| CA-02 (validación de nombres/apellidos) | Completa el paso 1 solo con datos válidos; el botón permanece deshabilitado hasta que los tres campos son válidos | **EJECUTADO — PASÓ** |
| CA-02 (usuario con feedback en vivo) | Espera el mensaje "disponible" antes de avanzar (ya validado manualmente también con un usuario duplicado, ver §4) | **EJECUTADO — PASÓ** |
| CA-02 (robustez de contraseña) | Espera a que el botón "Siguiente" se habilite tras calcular la robustez | **EJECUTADO — PASÓ** |
| CA-03 (landing de bienvenida) | Verifica textos "Bienvenido", "ACTIVE_BASIC" y "S/" en la página final | **EJECUTADO — PASÓ** |

## 4. Verificación manual adicional en navegador (evidencia de esta sesión)

Además de la prueba Selenium automatizada, se recorrió manualmente el flujo completo con el
navegador integrado para validar interacción real (no instrumentada):
- Usuario ya tomado (`juanp01`) → mensaje "Ese usuario ya está en uso" + 3 sugerencias sin símbolos
  (cumple CA-02).
- Usuario disponible (`jcrivera_qa`) → mensaje "¡Usuario disponible!".
- Contraseña fuerte → "Robustez: Muy fuerte" y habilitación del botón.
- Registro completo → landing con balloons, bienvenida, saldo y panel de límites
  (`Límite por operación: S/20.00 · Restante hoy: S/60.00`).

## 5. Brechas y pendientes (declarados explícitamente)

- **No hay pruebas de integración cruzada automatizadas** que arranquen backend+frontend+Selenium
  en un único comando (se ejecutan por separado). Pendiente: un script `run_e2e.ps1` que levante
  ambos servicios y luego corra Karate y Selenium. **NO EJECUTADO** — no se implementó en esta
  iteración por alcance.
- **Verificación de correo/celular (OTP) y biometría simulada**: fuera de alcance de esta
  iteración (ver `architect.md`); no existen pruebas porque la funcionalidad no fue implementada
  aún. **NO EJECUTADO**.
- **Nivel `ACTIVE_FULL`**: no implementado en esta iteración; sin pruebas. **NO EJECUTADO**.
- **Persistencia**: no hay pruebas de reinicio del backend con datos persistidos porque el
  almacenamiento es en memoria por diseño de esta iteración (ver `architect.md`, Non-Goals).
- **Pruebas de carga/concurrencia** sobre el ledger diario en memoria (condiciones de carrera entre
  solicitudes simultáneas a la misma wallet): no se diseñaron ni ejecutaron. **NO EJECUTADO**.
- El mock externo es un servicio real compartido del workshop; estas pruebas crean verificaciones
  y wallets reales en él (prefijo `TEST-`), consistente con lo documentado en
  `mock_flujo_registro.md` ("no evita altas repetidas").

## 6. Comandos de limpieza

No se crean recursos persistentes locales más allá de archivos de evidencia. Para limpiar:
```powershell
Remove-Item -Recurse -Force tests\karate\target, tests\selenium\screenshots, .pytest_cache -ErrorAction SilentlyContinue
```
El mock externo no expone un endpoint de borrado; las verificaciones/wallets de prueba (`TEST-`)
quedan en su almacenamiento compartido, igual que para cualquier equipo que use el mock del taller.
