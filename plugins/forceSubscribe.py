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


def _escape_html(text: str) -> str:
    """Escapa < y & para usar en parse_mode=HTML y evita errores con nombres raros."""
    if not text:
        return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;")


_FULL_PERMISSIONS = ChatPermissions(can_send_messages=True)

# Más de este número de mensajes sin verificar → se mutea
_MSG_LIMIT_BEFORE_MUTE = 10


async def _on_unmute_request(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Usuario pulsó Verificar: si ya está en el canal, se borra la notificación."""
    query = update.callback_query
    if not query or query.data != "onUnMuteRequest":
        return
    user_id = query.from_user.id if query.from_user else 0
    chat_id = query.message.chat.id if query.message else 0
    channels = sql.get_channels(chat_id)
    if not channels:
        return
    bot = context.bot
    missing = []
    for ch in channels:
        ref = _channel_ref(ch)
        try:
            await bot.get_chat_member(ref, user_id)
        except BadRequest:
            missing.append(ch)
    if not missing:
        try:
            await bot.restrict_chat_member(chat_id, user_id, permissions=_FULL_PERMISSIONS)
        except Exception:
            pass
        sql.remove_muted(chat_id, user_id)
        sql.clear_unverified_count(chat_id, user_id)
        sql.clear_notification_message_id(chat_id, user_id)
        try:
            await query.message.delete()
        except Exception:
            pass
        await query.answer("✅ Verificado. Ya puedes participar.", show_alert=False)
    else:
        await query.answer("⚠️ Únete a todos los canales y toca de nuevo «Verificar».", show_alert=True)


async def _check_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        await _check_member_impl(update, context)
    except Exception as e:
        logger.exception("Error en _check_member (chat=%s): %s", getattr(update.message.chat, "id", None), e)


async def _check_member_impl(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Lógica: recibe message → extrae user_id → get_chat_member(canal, user_id).
    Si no está en el canal → solo borra su mensaje y envía notificación (sin mute).
    Si está suscrito → borra la notificación si tenía una.
    """
    message = update.message
    if not message or not message.chat:
        return
    chat_id = message.chat.id
    chat_type = getattr(message.chat, "type", None)
    bot = context.bot

    # Si acaban de añadir al bot al grupo y no es el propietario, avisar y salir (get_me solo si hay nuevos miembros)
    new_members = getattr(message, "new_chat_members", None) or []
    bot_added = False
    if new_members:
        try:
            me = await bot.get_me()
            bot_added = any(getattr(m, "id", None) == me.id for m in new_members)
        except Exception:
            pass
    if bot_added:
        adder = getattr(message, "from_user", None)
        adder_id = adder.id if adder else None
        if Config.OWNER_ID is not None and adder_id != Config.OWNER_ID:
            try:
                await message.reply_text(Config.FORK_MSG, parse_mode="HTML")
            except Exception:
                pass
            try:
                await bot.leave_chat(chat_id)
            except Exception:
                pass
        return

    user = message.from_user
    if chat_type == "private" or not user:
        return
    user_id = user.id

    try:
        channels = sql.get_channels(int(chat_id))
    except Exception as e:
        logger.exception("Error al obtener canales para chat_id=%s: %s", chat_id, e)
        return
    if not channels:
        return

    # Si el mensaje lo envía el propio canal (ej. publicación en grupo vinculado), no borrar ni verificar
    sender_chat = getattr(message, "sender_chat", None)
    if sender_chat and getattr(sender_chat, "type", None) == "channel":
        sender_username = (getattr(sender_chat, "username", None) or "").strip().lower()
        if sender_username:
            channel_names = [ch.lstrip("@").lower() for ch in channels]
            if sender_username in channel_names:
                return

    # Admins/creador del grupo o lista Admin: no comprobar canal
    try:
        member = await bot.get_chat_member(chat_id, user_id)
    except Exception as e:
        logger.warning("No se pudo obtener miembro chat=%s user=%s: %s", chat_id, user_id, e)
        return
    if member.status in ("administrator", "creator") or user_id in Config.SUDO_USERS:
        return

    # Comprobar membresía en canal(es): get_chat_member(CHANNEL_ID, user_id)
    missing = []
    for ch in channels:
        ref = _channel_ref(ch)
        try:
            ch_member = await bot.get_chat_member(ref, user_id)
            # Si está en el canal (member/administrator/creator) no añadir a missing
            if ch_member.status not in ("member", "administrator", "creator", "restricted"):
                missing.append(ch)
        except BadRequest:
            # Usuario no está en el canal
            missing.append(ch)
        except Forbidden as e:
            logger.warning("Bot no admin en canal %s: %s", ch, e)
            try:
                await message.reply_text(
                    f"⚠️ No soy admin en @{ch}. Agrégame como admin ahí. _Me voy del chat…_",
                    parse_mode="Markdown",
                )
            except Exception:
                pass
            try:
                await bot.leave_chat(chat_id)
            except Exception:
                pass
            return

    if not missing:
        # Está suscrito: verificación automática — desmutear si estaba muteado, borrar notificación, resetear contador
        try:
            await bot.restrict_chat_member(chat_id, user_id, permissions=_FULL_PERMISSIONS)
        except Exception:
            pass
        sql.remove_muted(chat_id, user_id)
        sql.clear_unverified_count(chat_id, user_id)
        old_msg_id = sql.get_notification_message_id(chat_id, user_id)
        if old_msg_id:
            try:
                await bot.delete_message(chat_id, old_msg_id)
                sql.clear_notification_message_id(chat_id, user_id)
                logger.info("Usuario %s verificado automáticamente (ya está en el canal)", user_id)
            except Exception as e:
                logger.warning("Error al borrar notificación para %s: %s", user_id, e)
        return

    # No está suscrito: borrar mensaje, incrementar contador; si > 10 mensajes → mutear
    try:
        await message.delete()
    except Exception as e:
        logger.warning("No se pudo borrar el mensaje: %s", e)

    count = sql.increment_unverified_count(chat_id, user_id)
    if count > _MSG_LIMIT_BEFORE_MUTE:
        try:
            await bot.restrict_chat_member(
                chat_id,
                user_id,
                permissions=ChatPermissions(can_send_messages=False),
            )
            sql.add_muted(chat_id, user_id)
            logger.info("Usuario %s muteado tras %s mensajes sin verificar", user_id, count)
        except Forbidden as e:
            logger.error("Bot sin permiso para restringir en chat %s: %s", chat_id, e)
        except Exception as e:
            logger.warning("Error al mutear %s: %s", user_id, e)

    # Enviar notificación solo si aún no tiene una
    old_msg_id = sql.get_notification_message_id(chat_id, user_id)
    if old_msg_id:
        return

    name_escaped = _escape_html(user.first_name or "Usuario")
    mention = f'<a href="tg://user?id={user_id}">{name_escaped}</a>'
    text = (
        f"{mention}, para participar únete al canal.\n\n"
        "🚫 Sin suscripción no podrás escribir.\n"
        "🔔 Toca <b>Unirme</b> y luego <b>Verificar</b>."
    )
    # Botón "Unirme" (enlace al primer canal) y Verificar en la misma fila
    first_channel = missing[0].lstrip("@")
    buttons = [
        InlineKeyboardButton("Unirme", url=f"https://t.me/{first_channel}"),
        InlineKeyboardButton("Verificar", callback_data="onUnMuteRequest"),
    ]
    try:
        sent = await bot.send_message(
            chat_id,
            text,
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([buttons]),
        )
        if sent and sent.message_id:
            sql.set_notification_message_id(chat_id, user_id, sent.message_id)
    except Exception as e:
        logger.warning("No se pudo enviar mensaje con enlace: %s", e)


async def _cmd_forcesubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message
    if not message or not message.from_user or not message.chat or message.chat.type == "private":
        return
    if not Config.is_owner(message.from_user.id):
        await message.reply_text(Config.FORK_MSG, parse_mode="HTML")
        return
    try:
        member = await context.bot.get_chat_member(message.chat.id, message.from_user.id)
    except Exception:
        await message.reply_text("⚠️ No pude verificar tu rol.")
        return
    if member.status != "creator" and message.from_user.id not in Config.SUDO_USERS:
        await message.reply_text("🔒 Solo el creador del grupo (o Admin) puede usar esto.", parse_mode="Markdown")
        return
    chat_id = message.chat.id
    args = (context.args or [])
    input_parts = [p.replace("@", "").strip() for p in args if p and p.strip()]
    first = (input_parts[0].lower() if input_parts else "") or ""

    if first in ("off", "no", "disable"):
        sql.disapprove(chat_id)
        await message.reply_text("✅ Suscripción obligatoria desactivada.", parse_mode="Markdown")
        return
    if first == "clear":
        muted_ids = sql.get_muted_users(chat_id)
        msg_ids = sql.get_all_notification_message_ids(chat_id)
        if not muted_ids and not msg_ids:
            await message.reply_text("ℹ️ No hay muteados ni notificaciones en este chat.")
            return
        bot = context.bot
        for uid in muted_ids:
            try:
                await bot.restrict_chat_member(chat_id, uid, permissions=_FULL_PERMISSIONS)
            except (BadRequest, Forbidden):
                pass
        deleted = 0
        for mid in msg_ids:
            try:
                await bot.delete_message(chat_id, mid)
                deleted += 1
            except (BadRequest, Forbidden):
                pass
        sql.clear_muted_for_chat(chat_id)
        await message.reply_text(
            f"✅ Desmuteados y eliminados {deleted} mensaje(s) de notificación.",
            parse_mode="Markdown",
        )
        return

    if not input_parts:
        channels = sql.get_channels(chat_id)
        if channels:
            channels_links = ", ".join(f"[{c}](https://t.me/{c})" for c in channels)
            await message.reply_text(
                f"📌 Activo. Canal(es): {channels_links}",
                parse_mode="Markdown",
            )
        else:
            await message.reply_text("ℹ️ Suscripción obligatoria desactivada.", parse_mode="Markdown")
        return

    channels_to_set = [p for p in input_parts if p.lower() not in ("off", "no", "disable", "clear")]
    if not channels_to_set:
        await message.reply_text("⚠️ Indica al menos un canal (ej: /ForceSubscribe @canal).")
        return
    failed = []
    try:
        bot_id = (await context.bot.get_me()).id
    except Exception:
        bot_id = None
    for ch in channels_to_set:
        if not bot_id:
            failed.append(ch)
            continue
        ref = _channel_ref(ch)
        try:
            await context.bot.get_chat_member(ref, bot_id)
        except BadRequest:
            failed.append(ch)
        except Forbidden:
            failed.append(ch)
    if failed:
        await message.reply_text(
            f"⚠️ Inválidos o no soy admin: {', '.join('@' + c for c in failed)}. "
            "Agrégame como admin en el canal."
        )
        return
    sql.set_channels(chat_id, channels_to_set)
    channels_links = ", ".join(f"[{c}](https://t.me/{c})" for c in channels_to_set)
    await message.reply_text(
        f"✅ Activado. Miembros deben unirse a: {channels_links}",
        parse_mode="Markdown",
    )


def register(app):
    app.add_handler(CallbackQueryHandler(_on_unmute_request, pattern="^onUnMuteRequest$"))
    # Cualquier mensaje (texto, foto, etc.) en grupo o supergroup, excepto comandos
    app.add_handler(
        MessageHandler(
            (filters.ChatType.GROUP | filters.ChatType.SUPERGROUP) & ~filters.COMMAND,
            _check_member,
        )
    )
    app.add_handler(CommandHandler(["forcesubscribe", "fsub"], _cmd_forcesubscribe))
