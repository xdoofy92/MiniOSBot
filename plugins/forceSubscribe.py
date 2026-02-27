import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import ContextTypes, MessageHandler, CommandHandler, CallbackQueryHandler, filters
from telegram.error import BadRequest, Forbidden

from Config import Config
from sql_helpers import forceSubscribe_sql as sql

logger = logging.getLogger(__name__)


def _channel_ref(channel: str) -> str:
    """Devuelve @channel para uso en get_chat_member y enlaces."""
    return channel if channel.startswith("@") else f"@{channel}"


async def _on_unmute_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query or query.data != "onUnMuteRequest":
        return
    user_id = query.from_user.id if query.from_user else 0
    chat_id = query.message.chat.id if query.message else 0
    channels = sql.get_channels(chat_id)
    if not channels:
        return
    bot = context.bot
    try:
        member = await bot.get_chat_member(chat_id, user_id)
    except (BadRequest, Forbidden):
        return
    # Si está restringido (muteado), comprobar si ya se unió a todos los canales
    if member.status == "restricted" and not getattr(member, "can_send_messages", True):
        missing = []
        for ch in channels:
            ref = _channel_ref(ch)
            try:
                await bot.get_chat_member(ref, user_id)
            except BadRequest:
                missing.append(ch)
        if not missing:
            try:
                await bot.unban_chat_member(chat_id, user_id)
                if query.message and query.message.reply_to_message and query.message.reply_to_message.from_user and query.message.reply_to_message.from_user.id == user_id:
                    try:
                        await query.message.delete()
                    except Exception:
                        pass
            except Exception:
                pass
            await query.answer()
        else:
            await query.answer(
                "❗ Join all the required channel(s) and press 'UnMute Me' again.",
                show_alert=True,
            )
        return
    if member.status != "restricted":
        try:
            me = await bot.get_chat_member(chat_id, (await bot.get_me()).id)
            if me.status not in ("administrator", "creator"):
                name = query.from_user.first_name if query.from_user else "User"
                await context.bot.send_message(
                    chat_id,
                    f"**{name}** is trying to UnMute himself but I can't (I'm not admin). _#Leaving this chat..._",
                    parse_mode="Markdown",
                )
                await bot.leave_chat(chat_id)
            else:
                await query.answer("❗ Don't click the button if you can already speak.", show_alert=True)
        except Exception:
            await query.answer("❗ Don't click the button if you can already speak.", show_alert=True)
    else:
        await query.answer("❗ You are muted by admins for other reasons.", show_alert=True)


async def _check_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if not message or not message.chat or message.chat.type == "private":
        return
    chat_id = message.chat.id
    channels = sql.get_channels(chat_id)
    if not channels:
        return
    user = message.from_user
    if not user:
        return
    user_id = user.id
    bot = context.bot
    try:
        member = await bot.get_chat_member(chat_id, user_id)
    except Exception:
        return
    if member.status in ("administrator", "creator") or user_id in Config.SUDO_USERS:
        return
    missing = []
    for ch in channels:
        ref = _channel_ref(ch)
        try:
            await bot.get_chat_member(ref, user_id)
        except BadRequest:
            missing.append(ch)
        except Forbidden:
            await message.reply_text(
                f"**I am not an admin** in @{ch}. Add me as admin there and try again. _#Leaving..._",
                parse_mode="Markdown",
            )
            try:
                await bot.leave_chat(chat_id)
            except Exception:
                pass
            return
    if not missing:
        return
    channel_links = ", ".join(f"[{ch}](https://t.me/{ch})" for ch in missing)
    name = f"[{user.first_name}](tg://user?id={user.id})" if user else "You"
    text = (
        f"{name}, you are **not subscribed** to the required channel(s) yet. "
        f"Please join: {channel_links} and **press the button below** to unmute yourself."
    )
    try:
        await message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("UnMute Me", callback_data="onUnMuteRequest")],
            ]),
        )
        await bot.restrict_chat_member(
            chat_id,
            user_id,
            permissions=ChatPermissions(can_send_messages=False),
        )
    except Forbidden:
        try:
            await message.reply_text("**I am not an admin here.** Make me admin with ban permission. _#Leaving..._", parse_mode="Markdown")
        except Exception:
            pass
        try:
            await bot.leave_chat(chat_id)
        except Exception:
            pass


async def _cmd_forcesubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if not message or not message.from_user or not message.chat or message.chat.type == "private":
        return
    try:
        member = await context.bot.get_chat_member(message.chat.id, message.from_user.id)
    except Exception:
        await message.reply_text("Could not verify your role.")
        return
    if member.status != "creator" and message.from_user.id not in Config.SUDO_USERS:
        await message.reply_text("**Group Creator Required** — Only the group creator (or SUDO) can do that.", parse_mode="Markdown")
        return
    chat_id = message.chat.id
    args = (context.args or [])
    input_parts = [p.replace("@", "").strip() for p in args if p and p.strip()]
    first = (input_parts[0].lower() if input_parts else "") or ""

    if first in ("off", "no", "disable"):
        sql.disapprove(chat_id)
        await message.reply_text("**Force Subscribe is Disabled.**", parse_mode="Markdown")
        return
    if first == "clear":
        await message.reply_text(
            "✅ In this version, muted users must use the **UnMute Me** button after joining the channel(s). "
            "There is no bulk unmute."
        )
        return

    if not input_parts:
        channels = sql.get_channels(chat_id)
        if channels:
            channels_links = ", ".join(f"[{c}](https://t.me/{c})" for c in channels)
            await message.reply_text(
                f"**Force Subscribe is enabled.** Required channel(s): {channels_links}",
            parse_mode="Markdown",
            )
        else:
            await message.reply_text("**Force Subscribe is disabled** in this chat.", parse_mode="Markdown")
        return

    channels_to_set = [p for p in input_parts if p.lower() not in ("off", "no", "disable", "clear")]
    if not channels_to_set:
        await message.reply_text("❗ Provide at least one channel username (e.g. /ForceSubscribe @channel).")
        return
    failed = []
    for ch in channels_to_set:
        ref = _channel_ref(ch)
        try:
            await context.bot.get_chat_member(ref, (await context.bot.get_me()).id)
        except BadRequest:
            failed.append(ch)
        except Forbidden:
            failed.append(ch)
    if failed:
        await message.reply_text(
            f"❗ Invalid or I'm not admin in: {', '.join('@' + c for c in failed)}. "
            "Add me as admin in the channel(s) and use valid usernames."
        )
        return
    sql.set_channels(chat_id, channels_to_set)
    channels_links = ", ".join(f"[{c}](https://t.me/{c})" for c in channels_to_set)
    await message.reply_text(
        f"**Force Subscribe enabled.** Members must join: {channels_links}",
        parse_mode="Markdown",
    )


def register(app):
    app.add_handler(CallbackQueryHandler(_on_unmute_request, pattern="^onUnMuteRequest$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.GROUPS, _check_member))
    app.add_handler(CommandHandler(["forcesubscribe", "fsub"], _cmd_forcesubscribe))
