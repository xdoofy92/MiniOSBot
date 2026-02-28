# Changelog

Cambios de este fork respecto al bot original [force-subscribe-telegram-bot](https://github.com/viperadnan-git/force-subscribe-telegram-bot) de [@viperadnan-git](https://github.com/viperadnan-git).

---

## Stack y dependencias

| Original | Este fork |
|---------|-----------|
| Pyrogram (APP_ID, API_HASH, BOT_TOKEN) | **python-telegram-bot** (solo BOT_TOKEN) |
| Requiere APP_ID y API_HASH de Telegram | No requiere APP_ID ni API_HASH |
| Token en Config o env | Token desde env: `tok3n`, `TOK3N` o `BOT_TOKEN` |

- Añadido **runtime.txt** (Python 3.10) para despliegue en Railway.
- Base de datos: SQLite por defecto; PostgreSQL opcional vía `DATABASE_URL`.

---

## Uso solo por el propietario (evitar tráfico innecesario)

- El bot está pensado para que **solo lo use el propietario** (quien lo creó en BotFather), configurando la variable **OWNER_ID** con su user ID de Telegram.
- Con esto se evita **tráfico y uso innecesario**: usuarios ajenos no pueden usar comandos ni añadir el bot a sus grupos, por lo que el bot solo responde cuando lo usa el propietario.
- Solo el propietario puede:
  - Usar el bot (comandos en privado y en grupos).
  - Añadir el bot a un grupo (si lo añade otro usuario, el bot envía un mensaje y sale del chat).
- Si un no propietario usa un **comando** (p. ej. `/start`), recibe el mensaje del fork con enlace al proyecto original; si escribe texto/foto sin comando, el bot **no responde** (ignora).

---

## Comandos: ForceSubscribe sustituido por FSub

- El comando **`/ForceSubscribe`** del bot original se **sustituyó por completo** por **`/FSub`**.
- No existe alias ni variante: el único comando para configurar la suscripción obligatoria es **`/FSub`** (p. ej. `/FSub @canal`, `/FSub off`, `/FSub clear`).
- Subcomandos: sin args (ver estado), `off`, `@canal`, `clear`.
- Solo el **creador del grupo** (o usuarios en `SUDO_USERS`) puede ejecutar `/FSub` en el grupo.

---

## Comportamiento Force Subscribe

### Límite de 10 mensajes antes del mute

- **Original**: puede mutear o restringir al no suscrito de forma inmediata (según versión).
- **Este fork**:
  - El usuario no suscrito puede publicar **hasta 10 mensajes**: el bot **elimina** cada uno y envía (o mantiene) una notificación con botones Unirme y Verificar.
  - **Después del décimo mensaje** sin verificar, el bot **mutea** al usuario (restricción de envío de mensajes). Hasta entonces solo se borran los mensajes.
  - Al unirse al canal y pulsar **Verificar** (o escribir y estar ya suscrito), se desmutea y se resetea el contador.
  - El límite (10) es configurable en código (`_MSG_LIMIT_BEFORE_MUTE`).

### Canal como remitente

- Si el mensaje lo envía el **propio canal** (p. ej. publicaciones en grupo vinculado), el bot **no** lo borra ni exige verificación.

### Sin expulsar ni banear

- El bot **no** usa `kick`, `ban` ni elimina usuarios del grupo/canal; solo:
  - Restringe permisos (mute: `can_send_messages=False`).
  - Borra mensajes.
  - Sale del chat si no es admin o si quien lo añade no es el propietario.

---

## Base de datos (SQL)

- Tablas del original (forceSubscribe, etc.) mantenidas.
- Añadidas/uso explícito:
  - **UnverifiedCount**: contador de mensajes sin verificar por (chat_id, user_id) para aplicar mute tras N mensajes.
  - **MutedUser**, **NotificationMessage**: para mute y notificaciones.
- **clear_muted_for_chat** (p. ej. tras `/FSub clear`): borra muteados, notificaciones y **contadores de no verificados** de ese chat.

---

## Interfaz, opciones y traducción al español

### Traducción y textos

- Toda la interfaz y mensajes del bot están **traducidos al español** (español de México).
- Los textos son **cortos y claros**, con **emoji** al inicio en respuestas (estado, errores, confirmaciones).

### Cambios en las opciones (flujo de configuración)

- **/start** (propietario): mensaje de bienvenida + botón **Continuar** (abre las opciones; ya no se usa “Opciones” como etiqueta del botón).
- **Opciones / ayuda**: flujo por **páginas** (Suscripción obligatoria → Configuración → Comandos → Sobre este bot).
- Botones de navegación: **Continuar** y **← Anterior** (sustituyen a “Siguiente”).
- Comando **/help** eliminado: la ayuda solo se abre desde el botón **Continuar** en /start.

### Página final «Sobre este bot»

- Texto: *"Este es un fork creado por @xdoofy92 para @dprojects. Si quieres descargarlo lo puedes hacer aquí."*
- Tres botones:
  - **Fork xdoofy92** → [github.com/xdoofy92/MiniOSBot](https://github.com/xdoofy92/MiniOSBot)
  - **Original viperadnan** → [github.com/viperadnan-git/force-subscribe-telegram-bot](https://github.com/viperadnan-git/force-subscribe-telegram-bot)
  - **Salir** → cierra el mensaje de opciones (borra el mensaje con los botones).

### Mensaje para no propietarios

- Mensaje fijo con enlace al proyecto original (GitHub), sin mencionar el límite de mensajes ni detalles técnicos.

---

## Resumen de archivos tocados

- **bot.py**: entrada con python-telegram-bot, `run_polling`, una sola instancia.
- **Config.py**: `BOT_TOKEN`, `OWNER_ID`, `FORK_MSG`, `SUDO_USERS`, `Messages` (HELP_MSG, START_MSG), `Config.is_owner`.
- **plugins/help.py**: /start, botón Continuar, callback de opciones (páginas + botones Fork xdoofy92, Original viperadnan, Salir), sin /help.
- **plugins/forceSubscribe.py**: lógica de mute tras N mensajes, excepción para el canal, solo comando `/FSub`, comprobación de propietario.
- **sql_helpers/forceSubscribe_sql.py**: tablas y funciones para UnverifiedCount, muteados, notificaciones y clear por chat.

---

## Despliegue

- Probado en **Railway** con variable **tok3n** para el token.
- Una sola instancia (evitar `Conflict` de Telegram); en Railway usar 1 réplica.
- Requiere que el bot sea **admin** en el grupo (restringir miembros) y en el canal.

---

*Fork mantenido por [@xdoofy92](https://github.com/xdoofy92) para [@dprojects](https://t.me/dprojects). Proyecto original: [viperadnan-git/force-subscribe-telegram-bot](https://github.com/viperadnan-git/force-subscribe-telegram-bot).*
