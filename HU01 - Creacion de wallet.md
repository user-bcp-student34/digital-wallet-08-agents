## 📖 Descripción de la Historia de Usuario

**Como** persona natural que realiza compras, pagos y recargas de montos pequeños,  
**quiero** crear mi cuenta billetera digital mediante un flujo de onboarding sencillo y completar los datos de mi perfil de usuario,  
**para** empezar a utilizar la wallet con los límites correspondientes a mi nivel de validación.

---

## 🎯 Criterios de Aceptación (Definition of Done)

- **CA-01 (Inicio y seguimiento):** La medición del tiempo de registro inicia cuando la pantalla de onboarding es visible. El sistema registra el tiempo y los pasos completados. Los campos muestran el resultado de su validación mientras el usuario ingresa cada valor.

- **CA-02 (Datos de registro):** La pantalla inicial solicita:
  - **Nombres:** solo caracteres alfabéticos, longitud máxima de 30 caracteres y espacios permitidos entre letras.
  - **Apellido paterno:** solo caracteres alfabéticos, longitud máxima de 20 caracteres.
  - **Apellido materno:** solo caracteres alfabéticos, longitud máxima de 20 caracteres.
  - **Usuario:** caracteres alfabéticos, puede incluir símbolos, longitud máxima de 20 caracteres. Se valida su disponibilidad. Si no está disponible, se muestran sugerencias disponibles basadas en nombres, apellidos y números, sin símbolos.
  - **Contraseña:** permite símbolos, valida su robustez y alerta al usuario. No se envía a herramientas de analítica ni se registra en logs.

- **CA-03 (Creación de cuenta básica):** Al finalizar el registro, se crea una cuenta digital con saldo inicial de S/0 y estado `ACTIVE_BASIC`. Se presenta la landing, se da la bienvenida al usuario por su nombre real y se muestran las condiciones de las operaciones permitidas. En este momento finaliza la medición del tiempo de registro. La cuenta deber tener un wallet_id valido. Creacion del wallet https://bcp-wallet-mock.yefri.workers.dev/groups/8/kyc/verifications, obtener saldo https://bcp-wallet-mock.yefri.workers.dev/groups/8/wallets/{wallet_id}

- **CA-04 (Aviso de perfil pendiente):** La landing incluye un mensaje visible para que el usuario complete los datos de su perfil.

- **CA-05 (Operaciones de `ACTIVE_BASIC`):** La cuenta puede recibir recargas propias y realizar pagos. Se permite un máximo de S/20 por operación y S/60 diarios para pagos y recargas. Los topes son parametrizables para el estado ACTIVE_BASIC. La zona horaria es la de Perú y el contador se reinicia al cambio de día de acuerdo con la hora del servidor.

- **CA-06 (Registro complementario):** La pantalla de perfil permite completar, en cualquier orden y a requerimiento del usuario, las validaciones de correo electrónico, número de celular e identidad. Los estados iniciales, son estados adicionales para el perfil de usuario y estos son:
  - `ESTADO_C1: PENDING_EMAIL`
  - `ESTADO_C2: PENDING_MOVIL`
  - `ESTADO_C3: PENDING_BIOM`

- **CA-07 (Validación de correo):** Se valida el formato del correo electrónico y que no esté registrado por otro usuario. La validación se realiza mediante OTP, con una vigencia de 60 segundos. Se puede solicitar un OTP cada 45 segundos y la generación de uno nuevo invalida los anteriores. Al validar el OTP, el estado cambia a `ESTADO_C1: ACTIVE_EMAIL`. El envío de correo esta fuera de alcance en esta entrega, se genera OTP y continua. La generacion del OTP sera con un servicio mock.

- **CA-08 (Validación de celular):** Se valida el número de celular y que no esté registrado por otro usuario. El prefijo predeterminado es `+51 Perú` y no es editable. La validación se realiza mediante OTP, con una vigencia de 60 segundos. Se puede solicitar uno cada 45 segundos y la generación de uno nuevo invalida los anteriores. El envío de SMS esta fuera de alcance en esta entrega, se genera OTP y continua. La generacion del OTP sera con un servicio mock.

- **CA-09 (Alcance de la validación biométrica):** La integración y validación biométrica real están fuera del alcance de esta entrega. En los ambientes de desarrollo y pruebas se incluye un flujo mock que permite simular la validación y probar el registro completo hasta el estado `ACTIVE_FULL`. El flujo mock no realiza verificaciones biométricas reales solo verifica los inputs y continua.

- **CA-10 (Datos personales):** El usuario acepta el manejo de sus datos personales para la verificación biométrica real, mediante aceptacion de terminos y condiciones. Se definen controles de acceso, protección, retención y eliminación de información. Los datos del cliente no se envían a analítica ni se registran en logs. El flujo mock utiliza datos simulados y no requiere cargar ni procesar fotografías reales del DNI o videos biométricos.

- **CA-11 (Documentos y video para futura integración):** Para la futura validación biométrica real, se contempla el ingreso de fotografías de ambas caras del DNI, con un máximo de 2 MB, y un video de 5 a 10 segundos tomado con el celular, con un tamaño máximo de 10 MB. Se deberá indicar al usuario que las imágenes sean nítidas. La validación biométrica deberá verificar que los metadatos indiquen que el video fue grabado en los últimos 10 minutos. Estos requisitos no implican implementar la validación real en esta entrega.

- **CA-12 (Activación completa simulada):** Al simular una validación biométrica exitosa en el flujo mock, el usuario alcanza el estado `ACTIVE_FULL` para probar el recorrido completo. Este estado habilita operaciones reales de nivel `ACTIVE_FULL`.

- **CA-13 (Operaciones de `ACTIVE_FULL`):** La cuenta podrá recibir recargas propias y de terceros, hasta un máximo de S/1,000 diarios, y realizar pagos de hasta S/500 por operación y S/1,000 diarios. La zona horaria es la de Perú y el contador se reinicia al cambio de día de acuerdo con la hora del servidor.

---

## 📋 Contexto y Alineación con la Épica

- **Modelo de negocio:** Billetera digital dirigida a personas naturales que realizan compras, pagos y recargas de montos pequeños.
- **Contribución de negocio:** Permite iniciar operaciones con una cuenta básica y probar el recorrido de registro hasta la activación completa. La validación biométrica real, envío de SMS y envio de correo, queda fuera del alcance de esta entrega.

---

## ⚙️ Supuestos Técnicos y Regulatorios

1. Los topes de operación indicados son parametrizables.
2. El prefijo del celular es `+51 Perú` y no es editable.
3. Los datos personales del cliente no se envían a analítica ni se registran en logs.
4. Las validaciones de correo y celular pueden completarse en cualquier orden, a requerimiento del usuario.
5. El flujo mock de biometría solo está disponible en ambientes de desarrollo y pruebas.
6. La integración con un proveedor de biometría real se implementará en una entrega posterior.
7. La integración con un proveedor de envío de SMS real se implementará en una entrega posterior.
8. La integración con un proveedor de envío de correo real se implementará en una entrega posterior.
---

## ❓ Preguntas Abiertas / Fronteras de Análisis

- **Validación biométrica real:** queda fuera del alcance de esta entrega; se implementará el flujo visual y los cambios de estado.
