# Spec Delta

## Purpose

Define el recorrido de registro guiado que crea una wallet básica y permite al usuario continuar hacia la activación de su perfil.

## ADDED Requirements

### Requirement: El onboarding guía y valida el registro

El sistema SHALL mostrar la secuencia de pasos y el paso actual durante el onboarding. SHALL validar los campos mientras el usuario ingresa datos, bloquear el avance ante campos obligatorios incompletos o inválidos y mostrar mensajes accionables.

#### Scenario: El usuario revisa el avance del onboarding
- **WHEN** el usuario inicia o continúa el flujo
- **THEN** el sistema muestra la secuencia y el paso actual
- **AND** registra el inicio cuando la pantalla de onboarding se hace visible

#### Scenario: Un campo obligatorio es inválido
- **WHEN** el usuario intenta avanzar con un campo obligatorio incompleto o inválido
- **THEN** el sistema bloquea el avance y señala cómo corregir el campo

### Requirement: El registro valida nombres y apellidos

El sistema SHALL aceptar nombres de hasta 30 caracteres alfabéticos, con espacios entre nombres. SHALL aceptar apellido paterno y apellido materno de hasta 20 caracteres alfabéticos cada uno.

#### Scenario: Se ingresan nombres y apellidos válidos
- **WHEN** el usuario ingresa nombres y apellidos dentro de las longitudes permitidas y con caracteres alfabéticos
- **THEN** el sistema marca los campos como válidos

#### Scenario: Se supera una longitud o se ingresa un carácter no permitido
- **WHEN** un campo de nombre o apellido supera su límite o contiene caracteres no alfabéticos
- **THEN** el sistema informa el error y no permite completar el paso

### Requirement: El registro valida disponibilidad de usuario

El sistema SHALL validar la disponibilidad del usuario, con una longitud máxima de 20 caracteres. SHALL ofrecer sugerencias disponibles basadas en nombres, apellidos y números cuando el usuario elegido no esté disponible; las sugerencias SHALL excluir símbolos.

#### Scenario: El nombre de usuario está disponible
- **WHEN** el usuario ingresa un nombre que cumple las reglas admitidas y está disponible
- **THEN** el sistema permite continuar con ese nombre

#### Scenario: El nombre de usuario no está disponible
- **WHEN** el usuario ingresa un nombre que ya está registrado
- **THEN** el sistema informa que no está disponible y presenta sugerencias disponibles sin símbolos

### Requirement: El registro protege la contraseña

El sistema SHALL permitir símbolos en la contraseña, mostrar su evaluación de robustez y alertar al usuario si no cumple la política de robustez configurada. SHALL excluir la contraseña de eventos analíticos y logs.

#### Scenario: El usuario ingresa una contraseña
- **WHEN** el usuario escribe o modifica la contraseña
- **THEN** el sistema muestra la evaluación de robustez y una alerta accionable cuando corresponda
- **AND** ningún evento analítico ni log contiene la contraseña

### Requirement: El registro invoca el mock de verificación KYC para crear la wallet

Al completar el registro, el sistema SHALL invocar `POST /kyc/verifications` del mock descrito en `mock_flujo_registro.md`, con un `document` sintético con prefijo `TEST-` y `documentType` `TEST`, sin indicar `scenario` (valor predeterminado `APPROVED`). SHALL conservar el `id` de verificación y el `wallet_id` devueltos.

#### Scenario: Se invoca la creación de verificación y wallet
- **WHEN** el usuario completa todos los pasos obligatorios del registro
- **THEN** el sistema envía `documentType` `TEST` y un `document` sintético con prefijo `TEST-`, sin campo `scenario`
- **AND** conserva el `id` de verificación y el `wallet_id` de la respuesta

### Requirement: El registro consulta el estado de la wallet creada

El sistema SHALL consultar `GET /wallets/{wallet_id}` para obtener saldo y estado antes de presentar la landing, y no SHALL presentar la landing sin esa confirmación.

#### Scenario: Se consulta el estado de la wallet tras la creación
- **WHEN** el mock confirma la creación de la verificación y el `wallet_id`
- **THEN** el sistema consulta `GET /wallets/{wallet_id}` antes de mostrar cualquier pantalla posterior

### Requirement: El registro muestra la landing cuando la verificación queda activa

Cuando la respuesta tenga `status` `ACTIVE` (escenario `APPROVED`), el sistema SHALL establecer el saldo inicial en S/0 y el estado `ACTIVE_BASIC`, y SHALL mostrar la landing de bienvenida con el nombre real del usuario, las condiciones de operación permitidas y un aviso visible para completar el perfil. El tiempo de onboarding SHALL finalizar cuando la landing esté disponible.

#### Scenario: La creación de wallet termina correctamente (APPROVED)
- **WHEN** el mock responde `201` con `status` `ACTIVE` y un `wallet_id` válido
- **THEN** el sistema establece el saldo inicial en S/0, el estado `ACTIVE_BASIC` y muestra la landing de bienvenida
- **AND** informa las operaciones permitidas y que el perfil está pendiente de completar

#### Scenario: El mock no confirma la creación
- **WHEN** el mock responde con error (`400`, `413` o `429`) o no devuelve un `wallet_id` válido
- **THEN** el sistema no presenta el onboarding como finalizado ni muestra una wallet creada
- **AND** informa que no fue posible completar el registro y permite reintentar

### Requirement: El registro muestra la revisión manual de la verificación

Cuando el escenario de verificación sea `MANUAL_REVIEW`, el sistema SHALL mostrar la wallet con estado `PENDING`, informar que la cuenta está en revisión manual, SHALL permitir consultar el caso abierto en `GET /support/cases` y no SHALL habilitar operaciones de `ACTIVE_BASIC` ni `ACTIVE_FULL` mientras la verificación permanezca `PENDING`.

#### Scenario: La verificación queda en revisión manual
- **WHEN** la verificación KYC responde `status` `PENDING` (escenario `MANUAL_REVIEW`)
- **THEN** el sistema muestra la wallet como pendiente de revisión, enlaza el caso de soporte abierto y bloquea operaciones hasta que la verificación cambie a `ACTIVE`

### Requirement: El registro muestra el rechazo de la verificación

Cuando el escenario sea `REJECTED`, el sistema SHALL mostrar la wallet con estado `REJECTED`, informar que la cuenta fue rechazada y no SHALL permitir operaciones; cualquier intento de pago contra esa wallet SHALL reflejar el `409` devuelto por el mock.

#### Scenario: La verificación es rechazada
- **WHEN** la verificación KYC responde `status` `REJECTED`
- **THEN** el sistema muestra la cuenta como rechazada y no permite iniciar pagos ni recargas

### Requirement: El registro informa la indisponibilidad del servicio de verificación

Cuando el mock responda `503` (`KYC_UNAVAILABLE`), el sistema no SHALL crear ni mostrar una wallet, SHALL informar que el servicio de verificación no está disponible en ese momento y SHALL permitir reintentar el registro.

#### Scenario: El servicio de verificación no está disponible
- **WHEN** el mock responde `503 KYC_UNAVAILABLE`
- **THEN** el sistema informa que el servicio no está disponible, no crea una wallet y ofrece reintentar el registro

### Requirement: El perfil inicia con validaciones pendientes

Una wallet nueva SHALL iniciar las validaciones complementarias en `PENDING_EMAIL`, `PENDING_MOVIL` y `PENDING_BIOM`. El usuario SHALL poder completar cada validación a requerimiento propio y en cualquier orden.

#### Scenario: Se crea el perfil
- **WHEN** el sistema crea la wallet básica
- **THEN** inicializa los tres estados de validación como pendientes

#### Scenario: El usuario selecciona una validación complementaria
- **WHEN** existe una o más validaciones pendientes
- **THEN** el usuario puede iniciar cualquiera de ellas sin un orden obligatorio
