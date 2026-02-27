import logging
import sys
from telegram.ext import Application
from Config import Config

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

if not Config.BOT_TOKEN:
    logging.error(
        "No se encontró el token del bot. Añade la variable de entorno 'tok3n' (o 'BOT_TOKEN') con el token de @BotFather."
    )
    sys.exit(1)


def main():
    app = Application.builder().token(Config.BOT_TOKEN).build()

    from plugins import forceSubscribe, help as help_plugin
    forceSubscribe.register(app)
    help_plugin.register(app)

    app.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()
