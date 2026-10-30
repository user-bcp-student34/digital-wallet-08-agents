# Revisión Chapter de Ingenieria de Software
VEREDICTO: APROBADO (alcance de esta iteración: CA-01 a CA-05 de HU01)

> Rol: **Chapter** (ver [agents/chapter.py](agents/chapter.py)). Revisión final de las entregas de
> los roles **Architect** ([architect.md](architect.md)), **Backend** ([src/main.py](src/main.py)),
> **Frontend** ([src/frontend_mock.py](src/frontend_mock.py)) y **Testing**
> ([testing_report.md](testing_report.md)), para la historia **HU01 — Creación de wallet**
> (`HU01 - Creacion de wallet.md`) y las especificaciones en
> `openspec/changes/onboarding-wallet-registration/`.
> No se ejecutó un rol **Security** ni **Data** dedicado en esta iteración (el flujo solicitado fue
> architect → backend → frontend → testing → chapter); esto se refleja como brecha explícita en la
> columna de seguridad de la matriz, no se presenta evidencia inexistente.

## Motivos del veredicto

El alcance acordado para esta iteración —"básico funcional"— es el registro guiado (CA-01, CA-02),
la creación/consulta de wallet contra el mock real de KYC (CA-03, CA-04) y los límites de
`ACTIVE_BASIC` (CA-05). Para ese alcance:

- La arquitectura, el contrato OpenAPI local y el contrato externo documentado coinciden con lo
  implementado: verifiqué manualmente que los endpoints, esquemas y mapeos de estado descritos en
  `architect.md` existen tal cual en `src/main.py` (mismos nombres de campo, mismos códigos HTTP).
- Las pruebas de `testing_report.md` **se ejecutaron realmente** en esta sesión contra el backend,
  el frontend y el mock externo en vivo (no son resultados reportados sin evidencia): Karate
  `6/6 passed`, Selenium/pytest `1 passed in 15.49s`, más verificaciones manuales de límites y
  escenarios alternos con salidas HTTP reales adjuntas en el propio informe.
- Durante esta revisión se detectó y corrigió un hallazgo real: `testScenario` (gancho de prueba)
  no tenía ninguna restricción de entorno en el código entregado por Backend. Se corrigió en
  `src/main.py` (bloqueo por `APP_ENV=production`) y se verificó en caliente que (a) se bloquea en
  producción con `400 TEST_SCENARIO_NOT_ALLOWED` y (b) el flujo normal sigue funcionando sin
  regresiones. Este hallazgo y su corrección quedan documentados aquí y en `architect.md`.
- Los criterios CA-06 a CA-13 (verificación de correo/celular, biometría simulada, `ACTIVE_FULL`,
  datos personales) están **fuera de alcance de esta iteración**, decisión tomada explícitamente
  con el usuario y documentada en `openspec/changes/onboarding-wallet-registration/design.md`
  (Non-Goals). No se cuentan como incumplimiento de esta entrega, pero quedan pendientes para una
  iteración siguiente y se listan abajo sin cobertura.

No hay contratos incompatibles entre Architect/Backend/Frontend/Testing para el alcance cubierto,
ni hallazgos pendientes que bloqueen esta entrega parcial.

## Matriz de criterios de aceptación

| Criterio | Arquitectura | Persistencia | Implementación | Pruebas | Seguridad | Resultado y brechas |
|---|---|---|---|---|---|---|
| CA-01 (inicio y seguimiento) | `architect.md` §SECUENCIA, nota analítica | En memoria (`_events`, no hay base de datos; no se activó rol `data`) | `POST /analytics/events`; frontend emite `start`/`step` | Verificado manualmente (`202 {"accepted": true}`); sin prueba automatizada dedicada | N/D | **Cubierto parcialmente**: falta prueba automatizada de analítica; persistencia solo en memoria (aceptado para esta demo) |
| CA-02 (datos de registro) | `architect.md` §OPENAPI (`RegistrationRequest`, `/username-availability`) | En memoria (`_usernames`) | `src/main.py` (regex de nombres/apellidos/usuario, robustez de contraseña en frontend) | Karate: nombre inválido → `422` PASÓ; usuario duplicado → `400` PASÓ; Selenium: feedback en vivo PASÓ | Contraseña nunca se persiste/loguea (verificado por lectura de código); sin análisis estático automatizado | **Cubierto** |
| CA-03 (creación de cuenta básica) | `architect.md` §SECUENCIA (camino APPROVED) | Wallet/kyc en memoria (`_wallets`) | `create_kyc_verification` + `get_wallet_remote` en `src/main.py` | Karate PASÓ (`201`, `ACTIVE_BASIC`, saldo 0); Selenium PASÓ (landing real) | Documento sintético `TEST-`, no se solicita DNI real | **Cubierto** |
| CA-04 (aviso de perfil pendiente) | `architect.md` §INFORME | — | Mensaje en landing del frontend | Selenium verifica el mensaje de landing; no verifica el aviso de "perfil pendiente" como texto literal | N/D | **Cubierto parcialmente**: falta aserción explícita sobre el texto del aviso de perfil pendiente |
| CA-05 (operaciones `ACTIVE_BASIC`) | `architect.md` §OPENAPI (`/recharges`, `/payments`) | Ledger diario en memoria (`_ledger`), no persistente entre reinicios | `_apply_ledger_movement` con límites parametrizables por entorno | Verificado manualmente: límite por operación y diario exactos (S/20, S/60) con salidas HTTP reales | Bloqueo de operaciones sobre wallets no `ACTIVE` (`409`) verificado | **Cubierto**; sin prueba automatizada Karate específica de límites (solo manual) |
| CA-06 a CA-09 (correo/celular/biometría) | No diseñado en esta iteración | — | No implementado | No aplica | No aplica | **Fuera de alcance** (decisión documentada en `design.md`) |
| CA-10 (datos personales / biometría real) | No diseñado en esta iteración | — | No implementado | No aplica | No aplica | **Fuera de alcance** |
| CA-11 (documentos y video) | No diseñado en esta iteración | — | No implementado | No aplica | No aplica | **Fuera de alcance** |
| CA-12 (activación `ACTIVE_FULL`) | No diseñado en esta iteración | — | No implementado | No aplica | No aplica | **Fuera de alcance** |
| CA-13 (operaciones `ACTIVE_FULL`) | No diseñado en esta iteración | — | No implementado | No aplica | No aplica | **Fuera de alcance** |

## Contratos incompatibles y hallazgos pendientes

| # | Hallazgo | Evidencia | Responsable | Cambio requerido | Verificación |
|---|---|---|---|---|---|
| 1 | *(Resuelto durante esta revisión)* `testScenario` sin restricción de entorno | `src/main.py` antes del fix no tenía ningún chequeo de `APP_ENV` | Backend | Bloquear en producción | Ya corregido y verificado en esta sesión con `APP_ENV=production` → `400 TEST_SCENARIO_NOT_ALLOWED`; flujo normal sin regresión (`201` con nombre válido) |
| 2 | El ledger de límites de `ACTIVE_BASIC` es una simulación local; no modifica el saldo real de la wallet en el mock (el mock no expone endpoints de pago/recarga) | `architect.md` §INFORME, "Supuestos"; `src/main.py::_apply_ledger_movement` | Arquitecto/Backend | Si se requiere saldo real, se necesita un endpoint real de movimientos en el mock o un ledger propio persistente que se concilie con `GET /wallets/{id}` | Pendiente de decisión de producto; no aplica a esta demo |
| 3 | Sin prueba automatizada de límites (`ACTIVE_BASIC`) en Karate; solo se verificó manualmente en esta sesión | `testing_report.md` §2 "Pruebas manuales de API complementarias" | Testing | Añadir escenarios Karate para límite por operación y límite diario | **NO EJECUTADO** como prueba automatizada; comando disponible: agregar `@CA-05` scenarios a `tests/karate/registro_wallet.feature` |
| 4 | Sin aserción automatizada sobre el texto exacto del aviso de "perfil pendiente" (CA-04) | `src/frontend_mock.py::_render_landing` (mensaje existe) vs. `tests/selenium/test_onboarding_ui.py` (no lo verifica) | Testing | Añadir `assert` sobre el texto del aviso en `test_onboarding_happy_path` | **NO EJECUTADO** |
| 5 | No se ejecutó un rol de seguridad dedicado (sin análisis estático/dinámico, sin revisión de dependencias) | Ausente en esta iteración (flujo solicitado no lo incluyó) | Chapter/PO | Decidir si se incorpora el rol `security` (`agents/security.py`) antes de pasar a producción | **NO EJECUTADO** |
| 6 | Persistencia en memoria: el estado del backend se pierde al reiniciar el proceso | `architect.md` Non-Goals; `src/main.py` (diccionarios globales) | Arquitecto/Datos | Si se requiere persistencia real, activar el rol `data` (`agents/data.py`) y diseñar el esquema | Aceptado explícitamente para esta demo |

## Pruebas pendientes

| Prueba | Comando disponible | Estado |
|---|---|---|
| Límites de `ACTIVE_BASIC` como escenarios Karate automatizados | No existe aún; se ejecutaría con `java -jar tools/karate.jar tests/karate/registro_wallet.feature` tras agregarlos | **NO EJECUTADO** |
| Aserción del aviso de "perfil pendiente" en Selenium | Se ejecutaría con `pytest tests/selenium/test_onboarding_ui.py -v` tras agregar el assert | **NO EJECUTADO** |
| Análisis de seguridad estático/dinámico | Correspondería a `agents/security.py`, no invocado en este flujo | **NO EJECUTADO** |
| Pruebas de concurrencia sobre el ledger en memoria | No diseñadas | **NO EJECUTADO** |

Todas las pruebas marcadas como "PASÓ" en este documento corresponden a ejecuciones reales
realizadas en esta sesión (ver `testing_report.md` para los comandos y salidas completas); ninguna
se presenta como ejecutada sin evidencia.

---

Este veredicto es una recomendación técnica basada en la evidencia disponible en esta sesión; no
sustituye la aprobación humana del flujo ni la de ningún responsable de producto o seguridad.
