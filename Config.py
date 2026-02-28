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

class Config():
  # Token: siempre leer de env (varias posibles claves por compatibilidad con Railway/plataformas)
  BOT_TOKEN = _get_token()
  ENV = bool(os.environ.get("ENV", False)) or bool(BOT_TOKEN)
  if ENV:
    DATABASE_URL = os.environ.get("DATABASE_URL") or ""
    _sudo = (os.environ.get("SUDO_USERS") or "").strip()
    SUDO_USERS = list(set(int(x) for x in _sudo.split() if x.isdigit()))
  else:
    DATABASE_URL = ""
    SUDO_USERS = []


class Messages():
      HELP_MSG = [
        ".",

        "**Suscripción obligatoria**\n__Obligo a los miembros del grupo a unirse a uno o más canales antes de escribir.\nSilencio a quien no se haya unido; pueden desilenciarse uniéndose y tocando el botón.__",

        "**Configuración**\n__Primero agrégame al grupo como administrador (con permiso de banear) y al canal como administrador.\nSolo el creador del grupo puede configurarme; me voy del chat si no soy admin.__",

        "**Comandos**\n__/ForceSubscribe - Ver configuración actual.\n/ForceSubscribe off - Desactivar.\n/ForceSubscribe @canal (o varios @c1 @c2) - Activar y elegir canal(es).\n/ForceSubscribe clear - Mensaje para desilenciar.\n\n/FSub es un atajo de /ForceSubscribe.__",

        "**Un mod creado por @xdoofy92 del proyecto de @viperadnan**"
      ]

      START_MSG = "**Hola [{}](tg://user?id={})**\n__Puedo obligar a los miembros a unirse a un canal antes de escribir en el grupo.\nMás info en /help__"
