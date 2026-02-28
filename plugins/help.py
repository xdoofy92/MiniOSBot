import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler

from Config import Config, Messages as tr

logger = logging.getLogger(__name__)


def _help_buttons(pos: int):
    if pos == 1:
        return [[InlineKeyboardButton(text="Continuar", callback_data="help+2")]]
    if pos == len(tr.HELP_MSG) - 1:
        return [
            [InlineKeyboardButton(text="Fork", url="https://github.com/xdoofy92/MiniOSBot")],
            [InlineKeyboardButton(text="Original", url="https://github.com/viperadnan-git/force-subscribe-telegram-bot")],
            [InlineKeyboardButton(text="Inicio", callback_data="help+1")],
        ]
    return [
        [
            InlineKeyboardButton(text="← Anterior", callback_data=f"help+{pos-1}"),
            InlineKeyboardButton(text="Continuar", callback_data=f"help+{pos+1}"),
        ],
    ]


async def _start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.from_user:
        return
    user = update.message.from_user
    if not Config.is_owner(user.id):
        await update.message.reply_text(Config.FORK_MSG, parse_mode="HTML")
        return
    await update.message.reply_text(
        tr.START_MSG.format(user.first_name, user.id),
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(text="Continuar", callback_data="help+1")]]),
    )


async def _help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query or not query.data or not query.data.startswith("help+"):
        return
    if query.from_user and not Config.is_owner(query.from_user.id):
        await query.answer(Config.FORK_MSG, show_alert=True)
        return
    await query.answer()
    try:
        pos = int(query.data.split("+")[1])
    except (IndexError, ValueError):
        return
    if pos < 1 or pos >= len(tr.HELP_MSG):
        return
    if query.message:
        await query.message.edit_text(
            tr.HELP_MSG[pos],
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(_help_buttons(pos)),
        )


def register(app):
    app.add_handler(CommandHandler("start", _start))
    app.add_handler(CallbackQueryHandler(_help_callback, pattern="^help\+"))
