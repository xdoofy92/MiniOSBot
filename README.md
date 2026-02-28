# Introduction
**A Telegram Bot to force users to join a specific channel before sending messages in a group.**

## Features
- Force subscribe to **one or more channels** per group
- Admins configurables por variable de entorno (IDs de administradores)
- SQLite fallback when `DATABASE_URL` is not set (local development)

## Deploy


[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

### Installing Prerequisite
- On Ubuntu 18.04 or later
```sh
sudo apt-get install git python3 python3-pip libpq-dev
```

### Installation
- Clone this repo
```sh
git clone https://github.com/viperadnan-git/force-subscribe-telegram-bot
```
- Change directory
```sh
cd force-subscribe-telegram-bot
```
- Install requirements
```sh
pip3 install -r requirements.txt
```

### Configuration
Solo necesitas el **token del bot** ([@BotFather](https://t.me/botfather)). En Railway define la variable **tok3n** con ese token. Opcional: **SUDO_USERS** (IDs de admins separados por espacios), **DATABASE_URL** (PostgreSQL). No se requiere APP_ID ni API_HASH (usa [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)).

### Importante: una sola instancia (evitar error «Conflict»)
Telegram solo permite **una** conexión de polling por bot. Si ves `telegram.error.Conflict: terminated by other getUpdates request`:
- **Railway:** en el servicio del bot, deja **1 réplica** (Settings → Replicas = 1). No dupliques el servicio.
- **No ejecutes el bot en tu PC** si ya está desplegado en Railway (o al revés). Solo uno debe estar encendido.
- Si cambias de entorno, espera unos segundos antes de arrancar el otro.

### Para que el bot mute y avise en el grupo
1. **En el grupo:** el bot debe ser **administrador** con permiso **«Restringir miembros»** o **«Banear usuarios»**.
2. **En el canal:** el bot debe ser **administrador** para poder comprobar suscripciones.
3. **En @BotFather:** si el bot no es admin del grupo, activa **Bot Settings → Group Privacy → Disable** para que reciba todos los mensajes; si el bot ya es admin, no hace falta.
4. **En el grupo:** el creador debe ejecutar `/ForceSubscribe @tu_canal` para definir el canal obligatorio.

### Ejecución (solo Python)
```sh
pip install -r requirements.txt
python bot.py
```

## Thanks to
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- [Hasibul Kabir](https://GitHub.com/hasibulkabir) and [Spechide](https://GitHub.com/spechide) for helping.
