# Tasks

## 1. Onboarding y creación de wallet

- [ ] 1.1 Implementar el flujo guiado, validaciones en línea y mensajes accionables de nombres, apellidos y usuario.
- [ ] 1.2 Implementar evaluación de robustez de contraseña y comprobar que no se envía a logs ni analítica.
- [ ] 1.3 Integrar `POST /kyc/verifications` (documento sintético `TEST-`, `documentType` `TEST`, `scenario` omitido para `APPROVED`) y `GET /wallets/{wallet_id}`; validar `wallet_id`, saldo inicial y estado `ACTIVE`.
- [ ] 1.4 Implementar el manejo de `MANUAL_REVIEW` (estado `PENDING`, enlace a `GET /support/cases`), `REJECTED` y `UNAVAILABLE` (`503`), incluyendo mensajes y reintento.
- [ ] 1.5 Manejar errores `400`, `413` y `429` de la creación de wallet con mensajes accionables.
- [ ] 1.6 Presentar la landing de bienvenida, condiciones de operación y aviso de perfil pendiente para el camino `APPROVED`.
- [ ] 1.7 Probar inicio, finalización de pasos y bloqueo del avance ante datos incompletos o inválidos.

## 2. Verificaciones del perfil

- [ ] 2.1 Implementar estados pendientes y verificación mock de correo con unicidad, expiración e intervalo de OTP.
- [ ] 2.2 Implementar verificación mock de celular con prefijo `+51` no editable y las mismas reglas de OTP.
- [ ] 2.3 Implementar el flujo biométrico simulado solo para desarrollo y pruebas, sin capturar datos biométricos reales.
- [ ] 2.4 Integrar `POST /kyc/verifications/{id}/decision` (`ACTIVE`) cuando la simulación biométrica exitosa resuelva una verificación `PENDING`; manejar `409 DECISION_CONFLICT` cuando la verificación ya esté `REJECTED`.
- [ ] 2.5 Probar transiciones de estado, expiración, reintentos y verificaciones en cualquier orden.
- [ ] 2.6 Comprobar que logs y analítica no contienen datos personales ni secretos.

## 3. Límites por nivel

- [ ] 3.1 Implementar el bloqueo de operaciones cuando la verificación KYC de la wallet no esté `ACTIVE` (`PENDING` o `REJECTED`).
- [ ] 3.2 Implementar configuración de límites por estado de wallet y aplicación de topes antes de autorizar operaciones.
- [ ] 3.3 Implementar límites diarios y reinicio según fecha de Perú calculada por el servidor.
- [ ] 3.4 Probar los casos de límite exacto, exceso por operación y exceso por acumulado diario para ambos niveles, y el rechazo de operaciones sobre wallets no `ACTIVE`.

## 4. Analítica del MVP

- [ ] 4.1 Instrumentar eventos de inicio visible, finalización de pasos, cierre incompleto y finalización exitosa.
- [ ] 4.2 Implementar medidas para duración mediana, nuevos usuarios activos mensuales y atribución del gasto de adquisición.
- [ ] 4.3 Verificar la ausencia de PII y contraseñas en eventos y probar que los reportes permiten evaluar objetivos de onboarding, MAU y CAC.
