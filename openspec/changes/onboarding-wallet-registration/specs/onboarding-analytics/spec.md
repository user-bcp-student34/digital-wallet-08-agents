# Spec Delta

## Purpose

Define la instrumentación necesaria para medir el tiempo y avance del onboarding y evaluar la activación y adquisición del MVP.

## ADDED Requirements

### Requirement: El sistema mide inicio, pasos y cierre del onboarding

El sistema SHALL registrar eventos de inicio de onboarding, finalización de cada paso y cierre del flujo. El inicio SHALL corresponder a la primera visualización de la pantalla de onboarding; la finalización exitosa SHALL corresponder a la landing disponible después de crear la wallet. SHALL conservar timestamps suficientes para calcular la duración y la finalización mediana.

#### Scenario: La pantalla de onboarding se hace visible
- **WHEN** el usuario inicia el onboarding y la pantalla queda visible
- **THEN** el sistema registra el evento de inicio y su timestamp

#### Scenario: El usuario completa un paso
- **WHEN** el usuario completa un paso del flujo
- **THEN** el sistema registra la finalización del paso y su timestamp

#### Scenario: El usuario finaliza el registro
- **WHEN** se crea la wallet y la landing está disponible
- **THEN** el sistema registra el cierre exitoso con su timestamp
- **AND** puede calcular la duración desde la primera visualización

#### Scenario: El usuario abandona el flujo
- **WHEN** el usuario cierra o abandona el onboarding antes de la finalización
- **THEN** el sistema registra el cierre incompleto sin clasificarlo como alta exitosa

### Requirement: La analítica protege secretos y datos personales

Los eventos analíticos SHALL excluir contraseñas y datos personales del cliente. SHALL permitir relacionar eventos del mismo flujo mediante un identificador no personal y SHALL registrar solo los atributos mínimos necesarios para medir inicio, pasos, cierre y activación.

#### Scenario: Se emite un evento de onboarding
- **WHEN** el sistema registra un evento del funnel
- **THEN** el evento no contiene contraseña ni datos personales y permite asociar el avance al mismo flujo sin identificar al usuario por datos personales

### Requirement: La salida analítica permite evaluar objetivos del MVP

La salida analítica SHALL incluir conteos mensuales de nuevos usuarios activos y la atribución de gasto de adquisición necesaria para calcular MAU y CAC por usuario nuevo. Los resultados SHALL permitir evaluar el rango de 1,000 a 2,000 MAU y el objetivo de CAC de PEN 10 durante los primeros tres meses posteriores al lanzamiento.

#### Scenario: Se consulta el resultado mensual
- **WHEN** se genera el reporte de un mes dentro de los primeros tres meses posteriores al lanzamiento
- **THEN** el reporte incluye nuevos usuarios activos y gasto de adquisición atribuido para calcular MAU y CAC

### Requirement: El onboarding mide el objetivo de duración

La medición SHALL permitir comparar la mediana de duración del onboarding con la línea base de 8 minutos y el objetivo de 3 minutos dentro del trimestre posterior al lanzamiento.

#### Scenario: Se evalúa la mediana de duración
- **WHEN** se analiza la cohorte MVP de Perú durante el trimestre posterior al lanzamiento
- **THEN** los datos permiten calcular y comparar la mediana de finalización con la línea base de 8 minutos y el objetivo de 3 minutos
