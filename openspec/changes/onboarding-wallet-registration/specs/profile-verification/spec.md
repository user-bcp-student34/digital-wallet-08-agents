# Spec Delta

## Purpose

Define las verificaciones mock del perfil y las transiciones de estado que permiten probar el recorrido hasta la activación completa.

## ADDED Requirements

### Requirement: El correo se verifica con OTP mock

El sistema SHALL validar formato y unicidad del correo antes de iniciar la verificación. SHALL generar el OTP mediante un servicio mock, darle una vigencia de 60 segundos y permitir una nueva solicitud cada 45 segundos. La generación de un OTP SHALL invalidar cualquier OTP anterior. Al validar el OTP vigente, el sistema SHALL cambiar el estado a `ACTIVE_EMAIL`. El envío real de correo está fuera de alcance.

#### Scenario: Se solicita un OTP de correo
- **WHEN** el correo tiene formato válido, no está registrado y no hay una solicitud dentro del intervalo de 45 segundos
- **THEN** el servicio mock genera un OTP válido durante 60 segundos

#### Scenario: Se solicita un OTP antes de que transcurran 45 segundos
- **WHEN** el usuario vuelve a solicitar un OTP antes de que se cumpla el intervalo
- **THEN** el sistema no genera otro OTP y comunica cuándo podrá volver a solicitarlo

#### Scenario: Se genera un nuevo OTP
- **WHEN** el usuario solicita un nuevo OTP después del intervalo permitido
- **THEN** el OTP anterior deja de ser válido y el nuevo expira 60 segundos después de su generación

#### Scenario: Se valida un OTP vigente
- **WHEN** el usuario presenta el OTP vigente y correcto
- **THEN** el sistema cambia el estado del correo a `ACTIVE_EMAIL`

### Requirement: El celular se verifica con OTP mock

El sistema SHALL validar el número de celular y su unicidad antes de iniciar la verificación. SHALL mostrar el prefijo `+51 Perú` como valor predeterminado no editable y aplicar al OTP las mismas reglas de vigencia, intervalo de solicitud e invalidación que al correo. Al validar el OTP vigente, el sistema SHALL marcar la validación del celular como completada. El envío real de SMS está fuera de alcance.

#### Scenario: Se solicita un OTP de celular
- **WHEN** el número es válido, no está registrado y no hay una solicitud dentro del intervalo de 45 segundos
- **THEN** el servicio mock genera un OTP válido durante 60 segundos
- **AND** el prefijo mostrado es `+51 Perú` y no se puede editar

#### Scenario: Se solicita un OTP de celular antes de tiempo
- **WHEN** el usuario vuelve a solicitar un OTP antes de que se cumpla el intervalo de 45 segundos
- **THEN** el sistema no genera otro OTP y comunica cuándo podrá volver a solicitarlo

#### Scenario: Se valida un OTP vigente para celular
- **WHEN** el usuario presenta el OTP vigente y correcto
- **THEN** el sistema marca la validación del celular como completada

### Requirement: El OTP controla expiración y reintentos

El sistema SHALL rechazar OTP vencidos o inválidos. SHALL permitir verificar el canal de correo o celular independientemente, sin requerir completar primero el otro canal.

#### Scenario: Se presenta un OTP vencido o incorrecto
- **WHEN** el usuario intenta verificar un canal con un OTP vencido o incorrecto
- **THEN** el sistema mantiene el estado del canal como pendiente e informa que la verificación no fue exitosa

#### Scenario: Se verifican correo y celular en cualquier orden
- **WHEN** el usuario completa primero cualquiera de los dos canales
- **THEN** el sistema conserva el estado independiente de cada canal y permite completar el otro después

### Requirement: La biometría se simula solo en desarrollo y pruebas

El sistema SHALL ofrecer un flujo de validación biométrica mock únicamente en ambientes de desarrollo y pruebas. El mock SHALL validar solo los inputs simulados, no SHALL realizar verificaciones biométricas reales y no SHALL requerir ni procesar fotografías reales de DNI o videos biométricos. Una simulación exitosa SHALL cambiar el nivel de la wallet a `ACTIVE_FULL`.

#### Scenario: Se ejecuta una simulación biométrica exitosa
- **WHEN** el usuario completa inputs simulados válidos en un ambiente permitido y la verificación KYC de su wallet está `ACTIVE`
- **THEN** el sistema marca la validación mock como exitosa y cambia el nivel a `ACTIVE_FULL`

#### Scenario: Se intenta iniciar la simulación en producción
- **WHEN** el usuario intenta acceder al flujo mock en un ambiente de producción
- **THEN** el sistema no ofrece ni permite ejecutar la simulación

#### Scenario: El mock solicita material biométrico real
- **WHEN** se ejecuta el flujo mock
- **THEN** el sistema no solicita ni procesa imágenes reales del DNI ni videos biométricos

### Requirement: La biometría exitosa resuelve una verificación KYC pendiente

Si la verificación KYC subyacente de la wallet (`mock_flujo_registro.md`) permanece en `PENDING` (creada bajo el escenario `MANUAL_REVIEW`), la simulación biométrica exitosa SHALL resolverla invocando `POST /kyc/verifications/{id}/decision` con `{"decision":"ACTIVE"}` antes de cambiar el nivel a `ACTIVE_FULL`. Si la verificación ya está `ACTIVE`, el sistema SHALL omitir esa llamada.

#### Scenario: Se resuelve una verificación pendiente al simular la biometría
- **WHEN** la wallet tiene una verificación KYC `PENDING` y el usuario completa la simulación biométrica exitosamente
- **THEN** el sistema invoca la decisión `ACTIVE` sobre la verificación, el mock cambia su `status` a `ACTIVE` y el sistema cambia el nivel de la wallet a `ACTIVE_FULL`

#### Scenario: La verificación ya fue rechazada
- **WHEN** la wallet tiene una verificación KYC `REJECTED` y el usuario intenta simular la biometría
- **THEN** el sistema no invoca una nueva decisión, informa que la cuenta fue rechazada y no permite alcanzar `ACTIVE_FULL`

### Requirement: El tratamiento de datos personales está protegido

El sistema SHALL excluir datos personales del cliente de analítica y logs. Antes de recolectar o procesar datos para una futura verificación biométrica real, SHALL requerir aceptación de términos y definir controles de acceso, protección, retención y eliminación. La futura integración real de biometría está fuera de alcance de esta entrega.

#### Scenario: Se registra actividad del perfil
- **WHEN** se registra un evento analítico o log asociado al proceso de perfil
- **THEN** el evento o log no contiene datos personales ni secretos del usuario

#### Scenario: Se prepara la validación biométrica real
- **WHEN** una futura integración real vaya a recolectar o procesar datos biométricos
- **THEN** el usuario debe aceptar los términos aplicables y deben estar definidos los controles de acceso, protección, retención y eliminación antes del procesamiento
