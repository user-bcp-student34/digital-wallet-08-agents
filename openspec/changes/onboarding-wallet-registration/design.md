# Design

## Context

Las fuentes combinan una historia detallada de creación de wallet con objetivos de onboarding y métricas de negocio de una épica más amplia. La historia delimita el alta, los estados de validación y los límites por nivel; el detalle funcional define el funnel y la medición de adquisición. La épica también incluye checkout, pagos y QR, pero esos recorridos no se especifican en esta propuesta.

El proyecto no contiene especificaciones OpenSpec anteriores ni código de producto que determine contratos de API o políticas técnicas propias. La creación y consulta de saldo sí tienen un contrato concreto: `mock_flujo_registro.md` documenta los endpoints, escenarios (`APPROVED`, `REJECTED`, `MANUAL_REVIEW`, `UNAVAILABLE`), estados de wallet (`ACTIVE`, `PENDING`, `REJECTED`) y códigos HTTP (`201`, `400`, `404`, `409`, `413`, `429`, `503`) del mock referenciado por la HU01. Esta propuesta prioriza un recorrido básico funcional demostrable contra ese mock (registro + creación/consulta de wallet), dejando las verificaciones de correo, celular y biometría como simulaciones locales independientes del mock.

## Goals / Non-Goals

**Goals:**
- Convertir los criterios de aceptación y objetivos aplicables en requisitos verificables.
- Delimitar los estados, límites y medidas analíticas del onboarding.
- Especificar el registro y la creación de wallet contra el contrato concreto del mock de KYC/wallet para habilitar un recorrido básico funcional demostrable.
- Dejar explícitos los puntos que requieren decisión de producto o contrato externo.

**Non-Goals:**
- Implementar el onboarding o las operaciones financieras.
- Integrar proveedores reales de correo, SMS o biometría.
- Procesar imágenes de DNI o video biométrico.
- Especificar el checkout, los pagos QR, la conciliación o la integración de rieles descritos en la épica.
- Construir una consola de operaciones/soporte para resolver manualmente casos `MANUAL_REVIEW`; en esta entrega la única vía de resolución especificada es la simulación biométrica exitosa.

## Decisions

- **Separar por capacidad:** se definen cuatro capacidades independientes para que el flujo de alta, la verificación, los límites y la analítica puedan evolucionar sin mezclar responsabilidades.
- **Medición de duración:** se usa como inicio la pantalla visible y como final exitoso la landing después de crear la wallet, alineado a CA-01/CA-03. También se registran pasos y abandonos conforme al detalle funcional.
- **Protección analítica:** los eventos pueden enlazarse con un identificador no personal del flujo, pero no incluir contraseñas ni datos personales. La instrumentación de métricas de adquisición no justifica incorporar PII.
- **Mocks acotados:** los OTP y la biometría son simulados localmente (sin contrato propio documentado). La creación/consulta de wallet sí usa el contrato documentado en `mock_flujo_registro.md`.
- **Documento sintético:** el registro básico no solicita un documento de identidad real; el sistema genera un `document` con prefijo `TEST-` y `documentType` `TEST` únicamente para cumplir el contrato del mock.
- **Escenario por defecto:** el flujo de usuario normal omite `scenario` (equivalente a `APPROVED`). Los escenarios `REJECTED`, `MANUAL_REVIEW` y `UNAVAILABLE` se usan para validar los caminos alternos descritos en "Qué debes comprobar" de `mock_flujo_registro.md`.
- **Mapeo de estados:** el estado `status` del mock (`ACTIVE`/`PENDING`/`REJECTED`) gobierna si la wallet puede operar; el nivel de aplicación (`ACTIVE_BASIC`/`ACTIVE_FULL`) es un atributo adicional que solo aplica sobre una verificación `ACTIVE`.
- **Resolución de `PENDING`:** esta entrega resuelve una verificación `MANUAL_REVIEW` únicamente a través de la simulación biométrica exitosa, que invoca `POST /kyc/verifications/{id}/decision` con `ACTIVE`. No se construye una consola de soporte independiente.
- **Límites:** se representan por nivel y son parametrizables. Los topes diarios se reinician al cambiar la fecha según la zona horaria de Perú y el reloj del servidor.
- **Prioridad de alcance:** la HU01 aporta los criterios específicos; `mvp_detallefuncional.md` aporta la forma de medirlos; `epic.md` aporta contexto y objetivos de negocio más amplios; `mock_flujo_registro.md` aporta el contrato técnico del mock de KYC/wallet. Las metas de checkout no se convierten en requisitos de esta historia.

## Risks / Trade-offs

- La política exacta de robustez de contraseña y los caracteres permitidos para nombres de usuario no están definidos; necesitan una decisión antes de implementar validaciones consistentes.
- La HU01 define `PENDING_MOVIL` como estado inicial, pero no especifica el identificador de estado posterior a validar el celular; el modelo de dominio debe confirmar esa nomenclatura.
- El límite por operación de recarga para `ACTIVE_FULL` no está especificado; esta propuesta aplica únicamente el tope diario indicado.
- La forma segura de exponer los OTP de prueba del servicio mock local (correo/celular) no está descrita. Debe definirse sin registrarlos en logs o analítica de producción.
- El detalle funcional y la HU01 expresan el objetivo de duración desde perspectivas distintas; se adopta el límite explícito de CA-01/CA-03 y se registra el cierre del flujo para analizar abandonos.
- Los controles y periodos concretos de retención/eliminación deberán definirse antes de una futura integración biométrica real.
- `mock_flujo_registro.md` no define una política de reintentos/backoff para `503 UNAVAILABLE` ni mensajes de UX para `429` (límite de tasa) o `413` (payload excedido); la implementación deberá definir estos mensajes sin contradecir el contrato.
- Reutilizar `POST /kyc/verifications/{id}/decision` como mecanismo de resolución de `MANUAL_REVIEW` a través de la biometría simulada es una decisión de esta propuesta, no un requisito explícito de la HU01; si se decide construir una consola de operaciones real más adelante, ambos caminos deberán coexistir sin violar la regla de "decisión final" (`409 DECISION_CONFLICT`) del mock.
