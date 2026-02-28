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


# Para desmutear: solo permitir enviar mensajes (compatible con todas las versiones de PTB)
_FULL_PERMISSIONS = ChatPermissions(can_send_messages=True)


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
                # Solo quitar la restricción (desmutear), nunca expulsar/banear a nadie
                await bot.restrict_chat_member(chat_id, user_id, permissions=_FULL_PERMISSIONS)
                sql.remove_muted(chat_id, user_id)
                sql.clear_notification_message_id(chat_id, user_id)
                try:
                    await query.message.delete()
                except Exception:
                    pass
            except Exception:
                pass
            await query.answer()
        else:
            await query.answer(
                "Únete a todos los canales indicados y toca de nuevo «Verificar».",
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
                    f"**{name}** quiere desilenciarse pero no puedo (no soy admin). _Me voy del chat…_",
                    parse_mode="Markdown",
                )
                await bot.leave_chat(chat_id)
            else:
                await query.answer("No toques el botón si ya puedes hablar.", show_alert=True)
        except Exception:
            await query.answer("No toques el botón si ya puedes hablar.", show_alert=True)
    else:
        await query.answer("Te silenciaron los admins por otro motivo.", show_alert=True)


async def _check_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    try:
        await _check_member_impl(update, context)
    except Exception as e:
        logger.exception("Error en _check_member (chat=%s): %s", getattr(update.message.chat, "id", None), e)


async def _check_member_impl(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Lógica: recibe message → extrae user_id → get_chat_member(canal, user_id).
    Si no es member/administrator/creator del canal → borra mensaje, aplica restrict (mute), envía enlace.
    Si está suscrito → no hace nada.
    """
    message = update.message
    if not message or not message.chat:
        return
    chat_id = message.chat.id
    chat_type = getattr(message.chat, "type", None)
    user = message.from_user
    if chat_type == "private" or not user:
        return
    user_id = user.id
    bot = context.bot

    try:
        channels = sql.get_channels(int(chat_id))
    except Exception as e:
        logger.exception("Error al obtener canales para chat_id=%s: %s", chat_id, e)
        return
    if not channels:
        logger.info("Chat %s sin canales. Usar /ForceSubscribe @canal en el grupo.", chat_id)
        return

    # Admins/creador del grupo o lista Admin: no comprobar canal
    try:
        member = await bot.get_chat_member(chat_id, user_id)
    except Exception as e:
        logger.warning("No se pudo obtener miembro chat=%s user=%s: %s", chat_id, user_id, e)
        return
    if member.status in ("administrator", "creator") or user_id in Config.SUDO_USERS:
        logger.info("Usuario %s no se restringe (es %s o Admin)", user_id, member.status)
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
                    f"No soy administrador en @{ch}. Agrégame como admin ahí e intenta de nuevo. _Me voy del chat…_",
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
        # Está suscrito a todos los canales → no hacer nada
        logger.info("Usuario %s ya está en todos los canales %s", user_id, channels)
        return

    # No está suscrito: borrar mensaje, mutear, enviar enlace
    logger.info("Usuario %s no está en %s → borrar mensaje, mutear, enviar enlace", user_id, missing)

    try:
        await message.delete()
    except Exception as e:
        logger.warning("No se pudo borrar el mensaje: %s", e)

    try:
        await bot.restrict_chat_member(
            chat_id,
            user_id,
            permissions=ChatPermissions(can_send_messages=False),
        )
        sql.add_muted(chat_id, user_id)
    except Forbidden as e:
        logger.error("Bot sin permiso para restringir en chat %s: %s", chat_id, e)
        try:
            await bot.send_message(
                chat_id,
                "No tengo permiso para restringir usuarios. Dame permiso de administrador para «restringir miembros» o «banear usuarios».",
            )
        except Exception:
            pass
        return
    except Exception as e:
        logger.exception("Error al restringir usuario %s en chat %s: %s", user_id, chat_id, e)
        return

    # Eliminar la notificación anterior de este usuario (solo una notificación por usuario, la última)
    old_msg_id = sql.get_notification_message_id(chat_id, user_id)
    if old_msg_id:
        try:
            await bot.delete_message(chat_id, old_msg_id)
        except Exception:
            pass

    name_escaped = _escape_html(user.first_name or "Usuario")
    mention = f'<a href="tg://user?id={user_id}">{name_escaped}</a>'
    text = (
        f"{mention}, para participar debes unirte al canal oficial.\n\n"
        "🚫 Si no estás suscrito, no podrás enviar mensajes.\n"
        "🔔 Toca <b>Unirme</b> para ir al canal y luego <b>Verificar</b>."
    )
    # Botón "Unirme" (enlace al primer canal) y Verificar en la misma fila
    first_channel = missing[0]
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
    try:
        member = await context.bot.get_chat_member(message.chat.id, message.from_user.id)
    except Exception:
        await message.reply_text("No pude verificar tu rol.")
        return
    if member.status != "creator" and message.from_user.id not in Config.SUDO_USERS:
        await message.reply_text("**Solo el creador del grupo** (o un Admin) puede hacer esto.", parse_mode="Markdown")
        return
    chat_id = message.chat.id
    args = (context.args or [])
    input_parts = [p.replace("@", "").strip() for p in args if p and p.strip()]
    first = (input_parts[0].lower() if input_parts else "") or ""

    if first in ("off", "no", "disable"):
        sql.disapprove(chat_id)
        await message.reply_text("**Suscripción obligatoria desactivada.**", parse_mode="Markdown")
        return
    if first == "clear":
        muted_ids = sql.get_muted_users(chat_id)
        if not muted_ids:
            await message.reply_text("No hay usuarios silenciados por el bot en este chat.")
            return
        bot = context.bot
        count = 0
        for uid in muted_ids:
            try:
                old_msg_id = sql.get_notification_message_id(chat_id, uid)
                if old_msg_id:
                    try:
                        await bot.delete_message(chat_id, old_msg_id)
                    except Exception:
                        pass
                await bot.restrict_chat_member(chat_id, uid, permissions=_FULL_PERMISSIONS)
                count += 1
            except (BadRequest, Forbidden):
                pass
        sql.clear_muted_for_chat(chat_id)
        await message.reply_text(f"**Desilenciado masivo:** se quitaron las restricciones a {count} usuario(s).", parse_mode="Markdown")
        return

    if not input_parts:
        channels = sql.get_channels(chat_id)
        if channels:
            channels_links = ", ".join(f"[{c}](https://t.me/{c})" for c in channels)
            await message.reply_text(
                f"**Suscripción obligatoria activa.** Canal(es) requeridos: {channels_links}",
                parse_mode="Markdown",
            )
        else:
            await message.reply_text("**Suscripción obligatoria desactivada** en este chat.", parse_mode="Markdown")
        return

    channels_to_set = [p for p in input_parts if p.lower() not in ("off", "no", "disable", "clear")]
    if not channels_to_set:
        await message.reply_text("Indica al menos un canal (ej: /ForceSubscribe @canal).")
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
            f"Canales inválidos o no soy admin en: {', '.join('@' + c for c in failed)}. "
            "Agrégame como admin en el/los canal(es) y usa nombres válidos."
        )
        return
    sql.set_channels(chat_id, channels_to_set)
    channels_links = ", ".join(f"[{c}](https://t.me/{c})" for c in channels_to_set)
    await message.reply_text(
        f"**Suscripción obligatoria activada.** Los miembros tienen que unirse a: {channels_links}",
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
