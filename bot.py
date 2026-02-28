import logging
import os
import sys
from telegram.ext import Application
from Config import Config

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
# Evitar que httpx registre cada petición de polling (getUpdates) en los logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# Token: Config + fallback leyendo env al arrancar (por si la plataforma inyecta vars después)
_token = Config.BOT_TOKEN or os.environ.get("tok3n") or os.environ.get("TOK3N") or os.environ.get("BOT_TOKEN") or ""
if not _token or not _token.strip():
    logging.error(
        "No se encontró el token del bot. Añade la variable de entorno 'tok3n' (o 'BOT_TOKEN') con el token de @BotFather. "
        "En Railway: Variables → nombre exacto 'tok3n', valor = token del bot."
    )
    sys.exit(1)
BOT_TOKEN = _token.strip()


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    from plugins import forceSubscribe, help as help_plugin
    forceSubscribe.register(app)
    help_plugin.register(app)

    app.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
