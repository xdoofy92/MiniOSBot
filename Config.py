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


def is_owner(user_id: int) -> bool:
    """True si el usuario es el propietario del bot o si OWNER_ID no está configurado."""
    if Config.OWNER_ID is None:
        return True
    return user_id == Config.OWNER_ID


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

  # Mensaje para quien no sea el propietario (con botones de descarga)
  FORK_MSG = (
    "Este bot es un fork exclusivo para @dprojects. "
    "Si quieres usarlo en tus grupos te dejo las descargas."
  )
  # Botones (texto, url) para el mensaje de no propietario: una fila, dos botones
  FORK_BUTTONS = (
    ("Fork Doofy", "https://github.com/xdoofy92/MiniOSBot"),
    ("Bot Viperadnan", "https://github.com/viperadnan-git/force-subscribe-telegram-bot"),
  )


Config.is_owner = is_owner  # Uso: Config.is_owner(user_id)


class Messages():
      HELP_MSG = [
        ".",

        "📌 **Suscripción obligatoria**\n__Obligo a miembros a unirse al canal antes de escribir. Quien no se una queda silenciado; al unirse y tocar Verificar se desilencia.__",

        "⚙️ **Configuración**\n__Agrégame como admin al grupo y al canal. Solo el creador del grupo puede configurarme. Si no soy admin, me voy del chat.__",

        "📋 **Comandos**\n__/FSub — Ver estado.\n/FSub off — Desactivar.\n/FSub @canal — Activar canal(es).\n/FSub clear — Desilenciar a todos.__",

        "🔗 **Sobre este bot**\n__Este es un fork creado por @xdoofy92 para @dprojects. Si quieres descargarlo lo puedes hacer aquí.__",
      ]

      START_MSG = "👋 **Hola [{}](tg://user?id={})**\n__Obligo a los usuarios de tu grupo a unirse a tu canal.__"
