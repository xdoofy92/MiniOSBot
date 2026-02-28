# 🤖 Introducción

**Bot de Telegram que obliga a los usuarios a unirse a un canal antes de poder enviar mensajes en un grupo.**

---

## ✨ Características

- 📌 Suscripción obligatoria a **uno o más canales** por grupo
- 👥 Admins configurables por variable de entorno (IDs de administradores)
- 🗄️ SQLite como respaldo cuando no se define `DATABASE_URL` (desarrollo local)

---

## 🚀 Despliegue (Railway)

Este proyecto está pensado para desplegarse en [Railway](https://railway.app/):

1. Crea un proyecto en Railway y conecta este repositorio de GitHub.
2. En **Variables** añade al menos **tok3n** y **OWNER_ID** (ver [Configuración](#-configuración) más abajo).
3. Railway usará el `Procfile` y ejecutará `python bot.py`. ⚠️ Deja **1 réplica** (una sola instancia).

### 📋 Requisitos previos (instalación local)

En Ubuntu 18.04 o superior:

```sh
sudo apt-get install git python3 python3-pip libpq-dev
```

### 📥 Instalación

Clona el repositorio y entra en la carpeta:

```sh
git clone https://github.com/xdoofy92/MiniOSBot
cd MiniOSBot
```

Instala las dependencias:

```sh
pip3 install -r requirements.txt
```

---

## ⚙️ Configuración

Todas las variables se definen en el entorno (en Railway: **Variables** del proyecto). No se usa `APP_ID` ni `API_HASH`; el bot usa solo [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot).

| Variable       | Obligatoria | Descripción |
|----------------|-------------|-------------|
| **tok3n**      | ✅ Sí       | Token del bot ([@BotFather](https://t.me/botfather)) |
| **OWNER_ID**   | ✅ Sí       | Tu UserID de Telegram. Solo ese usuario podrá usarlo y añadirlo a grupos. |
| **SUDO_USERS** | No          | IDs de usuarios separados por espacios (pueden usar /FSub en el grupo). |
| **DATABASE_URL** | No        | URL de PostgreSQL. Si no se define, se usa SQLite (archivo local). |

---

## ⚠️ Importante: una sola instancia

Telegram permite **una** conexión de polling por bot. Si ves error `Conflict: terminated by other getUpdates request`:

- 🚂 **Railway:** en el servicio del bot, deja **1 réplica** (Settings → Replicas = 1). No dupliques el servicio.
- 💻 **No ejecutes el bot en tu PC** si ya está desplegado en Railway (o al revés). Solo uno debe estar encendido.
- ⏱️ Si cambias de entorno, espera unos segundos antes de arrancar el otro.

---

## 👑 Cómo usar el bot en el grupo

1. **En el grupo:** el bot debe ser **administrador** con permiso **«Restringir miembros»** o **«Banear usuarios»**.
2. **En el canal:** el bot debe ser **administrador** para poder comprobar suscripciones.
3. **En @BotFather:** si el bot no es admin del grupo, activa **Bot Settings → Group Privacy → Disable** para que reciba todos los mensajes; si el bot ya es admin, no hace falta.
4. **En el grupo:** el creador (o un sudo) ejecuta `/FSub @tu_canal` para definir el canal obligatorio.

---

## ▶️ Ejecución local

```sh
pip install -r requirements.txt
python bot.py
```

---

## 🙏 Agradecimientos

- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- Proyecto original: [viperadnan-git/force-subscribe-telegram-bot](https://github.com/viperadnan-git/force-subscribe-telegram-bot).
