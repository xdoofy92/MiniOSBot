import os

def _get_token():
    """Lee el token de cualquier variable de entorno habitual (Railway puede usar mayúsculas)."""
    return (
        os.environ.get("tok3n") or
        os.environ.get("TOK3N") or
        os.environ.get("BOT_TOKEN") or
        os.environ.get("bot_token") or
        ""
    ).strip()

def _get_owner_id():
    """ID de Telegram del propietario del bot (quien lo creó en BotFather). Solo ese usuario puede usarlo."""
    raw = (os.environ.get("OWNER_ID") or os.environ.get("owner_id") or "").strip()
    if not raw or not raw.lstrip("-").isdigit():
        return None
    return int(raw)


class Config():
  # Token: siempre leer de env (varias posibles claves por compatibilidad con Railway/plataformas)
  BOT_TOKEN = _get_token()
  # Solo el propietario puede usar el bot (pon en OWNER_ID tu user id de Telegram)
  OWNER_ID = _get_owner_id()
  ENV = bool(os.environ.get("ENV", False)) or bool(BOT_TOKEN)
  if ENV:
    DATABASE_URL = os.environ.get("DATABASE_URL") or ""
    _sudo = (os.environ.get("SUDO_USERS") or "").strip()
    SUDO_USERS = list(set(int(x) for x in _sudo.split() if x.isdigit()))
  else:
    DATABASE_URL = ""
    SUDO_USERS = []

  # Mensaje para quien no sea el propietario (GitHub = enlace al proyecto original)
  FORK_MSG = (
    "Este bot es un fork exclusivo para @dprojects. "
    "Si quieres usarlo en tus grupos este es el proyecto original en "
    "<a href=\"https://github.com/viperadnan-git/force-subscribe-telegram-bot\">GitHub</a>."
  )


class Messages():
      HELP_MSG = [
        ".",

        "**Suscripción obligatoria**\n__Obligo a los miembros del grupo a unirse a uno o más canales antes de escribir.\nSilencio a quien no se haya unido; pueden desilenciarse uniéndose y tocando el botón.__",

        "**Configuración**\n__Primero agrégame al grupo como administrador (con permiso de banear) y al canal como administrador.\nSolo el creador del grupo puede configurarme; me voy del chat si no soy admin.__",

        "**Comandos**\n__/ForceSubscribe - Ver configuración actual.\n/ForceSubscribe off - Desactivar.\n/ForceSubscribe @canal (o varios @c1 @c2) - Activar y elegir canal(es).\n/ForceSubscribe clear - Mensaje para desilenciar.\n\n/FSub es un atajo de /ForceSubscribe.__",
      ]

      START_MSG = "**Hola [{}](tg://user?id={})**\n__Obligare a los usuarios de tu grupo unirse a tu canal.__"
