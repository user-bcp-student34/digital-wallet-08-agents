# Proposal

## Why

El MVP necesita un flujo de alta que permita iniciar operaciones de bajo monto con límites acordes al nivel de validación. La historia de usuario define el recorrido de creación de wallet y activación; el detalle funcional y la épica añaden la guía del flujo, la medición del funnel y los objetivos de negocio que deben poder verificarse.

## What Changes

- Definir el flujo guiado de registro, sus validaciones y la creación de una wallet `ACTIVE_BASIC` contra el mock de KYC/wallet de `mock_flujo_registro.md`, incluyendo el manejo de sus cuatro escenarios (`APPROVED`, `MANUAL_REVIEW`, `REJECTED`, `UNAVAILABLE`).
- Definir las verificaciones complementarias de correo, celular y biometría simulada, incluyendo sus estados.
- Especificar los límites parametrizables de operación para `ACTIVE_BASIC` y `ACTIVE_FULL`.
- Definir eventos y resultados analíticos que midan el onboarding sin exponer datos personales ni secretos.
- Mantener fuera de alcance las integraciones reales de correo, SMS y biometría, así como la ejecución de pagos y cobros QR.

## Capabilities

### New Capabilities

- `wallet-onboarding`: recorrido guiado, validación de datos, creación de cuenta y landing inicial.
- `profile-verification`: estados y flujos mock para validar correo, celular e identidad.
- `wallet-tier-limits`: operaciones permitidas y topes diarios por nivel de wallet.
- `onboarding-analytics`: medición del funnel de onboarding y resultados analíticos del MVP.

### Modified Capabilities

## Impact

- **Fuentes:** `HU01 - Creacion de wallet.md`, `mvp_detallefuncional.md`, `epic.md` y el contrato de API simulada `mock_flujo_registro.md`.
- **Integraciones referenciadas:** mock de KYC/wallet con `POST /kyc/verifications`, `GET /kyc/verifications/{id}`, `POST /kyc/verifications/{id}/decision`, `GET /wallets/{id}` y `GET /support/cases`, bajo el prefijo de grupo indicado en la historia de usuario (p. ej. `/groups/8/...`).
- **Alcance de esta propuesta:** especificación funcional orientada a un recorrido básico funcional demostrable (registro + creación/consulta de wallet contra este mock); no implementa código ni habilita integraciones reales.
- Los objetivos de abandono de checkout y los flujos de pago/QR pertenecen al alcance general de la épica, pero no se detallan en esta historia de onboarding.
