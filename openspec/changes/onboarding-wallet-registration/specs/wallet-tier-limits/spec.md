# Spec Delta

## Purpose

Define los tipos de operación y límites monetarios que corresponden a cada nivel de activación de la wallet.

## ADDED Requirements

### Requirement: Solo una wallet con verificación ACTIVE puede operar

El sistema SHALL bloquear pagos y recargas mientras la verificación KYC subyacente de la wallet (`mock_flujo_registro.md`) no tenga `status` `ACTIVE`. Las wallets en `PENDING` o `REJECTED` no SHALL tener habilitados los límites de `ACTIVE_BASIC` ni `ACTIVE_FULL`.

#### Scenario: Se intenta operar con una wallet pendiente o rechazada
- **WHEN** el usuario intenta un pago o una recarga y la verificación KYC de su wallet está `PENDING` o `REJECTED`
- **THEN** el sistema rechaza la operación e informa el estado de la cuenta sin aplicar los topes de `ACTIVE_BASIC` ni `ACTIVE_FULL`

### Requirement: Los límites por nivel son parametrizables

El sistema SHALL obtener los límites operativos de la configuración asociada al estado de la wallet, sin codificar los topes de manera inmutable. SHALL aplicar los topes antes de autorizar una operación y comunicar al usuario cuando una operación exceda un límite.

#### Scenario: Se modifica un límite configurado
- **WHEN** se actualiza la configuración de topes para un nivel
- **THEN** las operaciones posteriores de wallets de ese nivel usan el nuevo límite

#### Scenario: Una operación excede un límite
- **WHEN** un pago o recarga propuesto supera un límite aplicable
- **THEN** el sistema rechaza la operación e indica qué límite se excedió

### Requirement: ACTIVE_BASIC permite operaciones de bajo monto

Una wallet `ACTIVE_BASIC` SHALL permitir recargas propias y pagos. SHALL limitar cada operación permitida a S/20 y el total diario combinado de pagos y recargas a S/60. SHALL aplicar el día calendario de Perú según el reloj del servidor.

#### Scenario: El usuario realiza una operación básica dentro de los topes
- **WHEN** una recarga propia o un pago no excede S/20 y el acumulado diario combinado no excede S/60
- **THEN** el sistema permite la operación si las demás validaciones aplicables son satisfactorias

#### Scenario: Se excede el tope por operación o diario
- **WHEN** una operación supera S/20 o llevaría el total combinado diario por encima de S/60
- **THEN** el sistema rechaza la operación

#### Scenario: Se alcanza un nuevo día en Perú
- **WHEN** el reloj del servidor pasa a una nueva fecha en la zona horaria de Perú
- **THEN** el acumulado diario de pagos y recargas de `ACTIVE_BASIC` comienza de nuevo

### Requirement: ACTIVE_FULL habilita topes ampliados

Una wallet `ACTIVE_FULL` SHALL poder recibir recargas propias y de terceros hasta un total de S/1,000 por día. SHALL permitir pagos de hasta S/500 por operación y S/1,000 diarios. SHALL aplicar el día calendario de Perú según el reloj del servidor.

#### Scenario: Se recibe una recarga dentro del límite diario
- **WHEN** una wallet `ACTIVE_FULL` recibe una recarga propia o de un tercero y el total diario de recargas no supera S/1,000
- **THEN** el sistema permite la recarga si las demás validaciones aplicables son satisfactorias

#### Scenario: Se excede el límite diario de recargas
- **WHEN** una recarga llevaría el total diario recibido por encima de S/1,000
- **THEN** el sistema rechaza la recarga

#### Scenario: Se realiza un pago dentro de los topes
- **WHEN** el pago no supera S/500 por operación ni S/1,000 en el acumulado diario
- **THEN** el sistema permite el pago si las demás validaciones aplicables son satisfactorias

#### Scenario: Se excede un límite de pago
- **WHEN** el pago supera S/500 por operación o llevaría el acumulado diario por encima de S/1,000
- **THEN** el sistema rechaza el pago

#### Scenario: Se alcanza un nuevo día en Perú
- **WHEN** el reloj del servidor pasa a una nueva fecha en la zona horaria de Perú
- **THEN** los acumulados diarios de pagos y recargas de `ACTIVE_FULL` comienzan de nuevo
