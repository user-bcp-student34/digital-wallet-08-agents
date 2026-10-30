# W1 Registro y activación

Esta API simula la verificación de identidad, llamada KYC, y crea una wallet. Úsala para que la pantalla de registro distinga una cuenta activa, una pendiente de revisión y una rechazada.

## Flujo de registro

1. Envía `POST /kyc/verifications` con `{"documentType":"TEST","document":"TEST-001","scenario":"APPROVED"}`. Usa documentos ficticios con prefijo `TEST-`.
2. Guarda los identificadores de la verificación y de la wallet que devuelve la API.
3. Consulta `GET /kyc/verifications/{id}` para ver la verificación y `GET /wallets/{id}` para ver la cuenta y sus saldos.
4. Si elegiste `MANUAL_REVIEW`, consulta `GET /support/cases`. Para simular la decisión humana, envía `POST /kyc/verifications/{id}/decision` con `{"decision":"ACTIVE"}` o `{"decision":"REJECTED"}`.

## Qué debes comprobar

- `APPROVED` crea una wallet `ACTIVE` con saldo cero. La wallet precargada `wallet-demo` permite probar pagos con fondos.
- `MANUAL_REVIEW` deja la cuenta en `PENDING` y abre un caso de soporte. La interfaz debe explicar que falta una decisión.
- `REJECTED` crea una cuenta rechazada. Intentar pagar con ella devuelve `409`.
- `UNAVAILABLE` devuelve `503` y no crea una cuenta. Permite probar el mensaje de indisponibilidad del servicio.

La verificación es simulada. No valida documentos reales ni evita registros repetidos. Una decisión final repetida conserva el resultado; intentar cambiarla devuelve `409`.

## APIs de esta historia

### `POST /kyc/verifications`

Crea una verificación y una wallet con saldo cero. APPROVED, valor predeterminado, activa; REJECTED rechaza; MANUAL_REVIEW deja PENDING y abre soporte. UNAVAILABLE devuelve 503 KYC_UNAVAILABLE sin crear wallet. Solo documentType TEST y document con prefijo TEST-. No evita altas repetidas.

Campos del cuerpo JSON:

- `documentType`: string, obligatorio. Solo TEST. No enviar documentos reales. Valores: TEST.
- `document`: string, obligatorio. Documento ficticio con prefijo TEST-.
- `scenario`: string, opcional. Escenario del proveedor simulado. Predeterminado APPROVED. Valores: APPROVED, REJECTED, MANUAL_REVIEW, UNAVAILABLE.

Respuestas HTTP: `201`, `400`, `503`, `413`, `429`.

Campos de respuesta: `id`, `wallet_id`, `scenario`, `status`.

### `GET /kyc/verifications/{id}`

Consulta la verificación por su ID kyc, distinto al wallet_id. Devuelve 404 NOT_FOUND si no existe en el grupo.

Respuestas HTTP: `200`, `404`.

Campos de respuesta: `id`, `wallet_id`, `scenario`, `status`.

### `POST /kyc/verifications/{id}/decision`

Decide ACTIVE o REJECTED sobre una verificación PENDING, actualiza su wallet y resuelve su caso de soporte. Repetir la misma decisión devuelve 200; cambiar una decisión final devuelve 409 DECISION_CONFLICT. Decisión inválida: 400 INVALID_DECISION.

Campos del cuerpo JSON:

- `decision`: string, obligatorio. Decisión final del operador sobre la verificación. Valores: ACTIVE, REJECTED.

Respuestas HTTP: `200`, `400`, `404`, `409`, `413`, `429`.

Campos de respuesta: `id`, `wallet_id`, `scenario`, `status`.

### `GET /wallets/{id}`

Consulta estado y saldos en céntimos. available = balance - reserved. Solo los pagos PENDING reservan saldo. wallet-demo empieza ACTIVE con 100000. Wallet inexistente: 404 NOT_FOUND.

Respuestas HTTP: `200`, `404`.

Campos de respuesta: `id`, `status`, `balance`, `reserved`, `available`, `currency`.

## Material relacionado

[Leer la historia de usuario](/dia-05/packages/user-stories/user-onboarding-mvp-completion.sp.html)

[Conectar y confirmar pagos](/dia-04/mocks/)

[Controles para preparar escenarios](/dia-04/mocks/controles.html)

[Cobertura frente a los criterios del reto](/dia-04/mocks/alcance.html)
