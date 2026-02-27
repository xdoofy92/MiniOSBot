import time
import logging
from Config import Config
from pyrogram import Client, filters
from sql_helpers import forceSubscribe_sql as sql
from pyrogram.types import ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors.exceptions.bad_request_400 import UserNotParticipant, UsernameNotOccupied, ChatAdminRequired, PeerIdInvalid

logging.basicConfig(level=logging.INFO)

static_data_filter = filters.create(lambda _, __, query: query.data == "onUnMuteRequest")


@Client.on_callback_query(static_data_filter)
def _onUnMuteRequest(client, cb):
    user_id = cb.from_user.id
    chat_id = cb.message.chat.id
    channels = sql.get_channels(chat_id)
    if not channels:
        return
    chat_member = client.get_chat_member(chat_id, user_id)
    if chat_member.restricted_by:
        if chat_member.restricted_by.id == (client.get_me()).id:
            missing = []
            for channel in channels:
                try:
                    client.get_chat_member(channel, user_id)
                except UserNotParticipant:
                    missing.append(channel)
            if not missing:
                try:
                    client.unban_chat_member(chat_id, user_id)
                    if cb.message.reply_to_message and cb.message.reply_to_message.from_user.id == user_id:
                        cb.message.delete()
                except Exception:
                    pass
            else:
                client.answer_callback_query(
                    cb.id,
                    text="❗ Join all the required channel(s) and press 'UnMute Me' again.",
                    show_alert=True
                )
        else:
            client.answer_callback_query(cb.id, text="❗ You are muted by admins for other reasons.", show_alert=True)
    else:
        try:
            bot_member = client.get_chat_member(chat_id, (client.get_me()).id)
            if bot_member.status != "administrator" and bot_member.status != "creator":
                client.send_message(
                    chat_id,
                    f"❗ **{cb.from_user.mention}** is trying to UnMute himself but I can't (I'm not admin). __#Leaving this chat...__"
                )
                client.leave_chat(chat_id)
            else:
                client.answer_callback_query(cb.id, text="❗ Don't click the button if you can already speak.", show_alert=True)
        except Exception:
            client.answer_callback_query(cb.id, text="❗ Don't click the button if you can already speak.", show_alert=True)


@Client.on_message(filters.text & ~filters.private, group=1)
def _check_member(client, message):
    chat_id = message.chat.id
    channels = sql.get_channels(chat_id)
    if not channels:
        return
    user_id = message.from_user.id
    try:
        member = client.get_chat_member(chat_id, user_id)
    except Exception:
        return
    if member.status in ("administrator", "creator") or user_id in Config.SUDO_USERS:
        return
    missing = []
    for channel in channels:
        try:
            client.get_chat_member(channel, user_id)
        except UserNotParticipant:
            missing.append(channel)
        except ChatAdminRequired:
            client.send_message(
                chat_id,
                text=f"❗ **I am not an admin** in @{channel}. Add me as admin there and try again. __#Leaving...__"
            )
            client.leave_chat(chat_id)
            return
    if not missing:
        return
    channel_links = ", ".join(f"[{ch}](https://t.me/{ch})" for ch in missing)
    text = (
        f"{message.from_user.mention}, you are **not subscribed** to the required channel(s) yet. "
        f"Please join: {channel_links} and **press the button below** to unmute yourself."
    )
    try:
        sent_message = message.reply_text(
            text,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("UnMute Me", callback_data="onUnMuteRequest")]]
            )
        )
        client.restrict_chat_member(chat_id, user_id, ChatPermissions(can_send_messages=False))
    except ChatAdminRequired:
        try:
            sent_message.edit("❗ **I am not an admin here.** Make me admin with ban permission. __#Leaving...__")
        except Exception:
            client.send_message(chat_id, "❗ **I am not an admin here.** __#Leaving...__")
        client.leave_chat(chat_id)


@Client.on_message(filters.command(["forcesubscribe", "fsub"]) & ~filters.private)
def config(client, message):
    try:
        user = client.get_chat_member(message.chat.id, message.from_user.id)
    except Exception:
        message.reply_text("❗ Could not verify your role.")
        return
    if user.status != "creator" and message.from_user.id not in Config.SUDO_USERS:
        message.reply_text("❗ **Group Creator Required** — Only the group creator (or SUDO) can do that.")
        return
    chat_id = message.chat.id
    if len(message.command) > 1:
        input_parts = [p.replace("@", "").strip() for p in message.command[1:] if p.strip()]
        first = input_parts[0].lower() if input_parts else ""
        if first in ("off", "no", "disable"):
            sql.disapprove(chat_id)
            message.reply_text("❌ **Force Subscribe is Disabled.**")
        elif first == "clear":
            sent_message = message.reply_text("**Unmuting all members muted by me...**")
            try:
                for chat_member in client.get_chat_members(message.chat.id, filter="restricted"):
                    if chat_member.restricted_by and chat_member.restricted_by.id == (client.get_me()).id:
                        client.unban_chat_member(chat_id, chat_member.user.id)
                        time.sleep(1)
                sent_message.edit("✅ **UnMuted all members who were muted by me.**")
            except ChatAdminRequired:
                sent_message.edit("❗ I am not an admin here. Make me admin with ban permission.")
        else:
            # Uno o más canales: @ch1 @ch2 ...
            channels_to_set = []
            for part in input_parts:
                part_lower = part.lower()
                if part_lower in ("off", "no", "disable", "clear"):
                    continue
                channels_to_set.append(part)
            if not channels_to_set:
                message.reply_text("❗ Provide at least one channel username (e.g. /ForceSubscribe @channel).")
                return
            failed = []
            for ch in channels_to_set:
                try:
                    client.get_chat_member(ch, "me")
                except UserNotParticipant:
                    failed.append(ch)
                except (UsernameNotOccupied, PeerIdInvalid):
                    failed.append(ch)
            if failed:
                message.reply_text(
                    f"❗ Invalid or I'm not admin in: {', '.join('@' + c for c in failed)}. "
                    "Add me as admin in the channel(s) and use valid usernames."
                )
                return
            sql.set_channels(chat_id, channels_to_set)
            channels_links = ", ".join(f"[{c}](https://t.me/{c})" for c in channels_to_set)
            message.reply_text(
                f"✅ **Force Subscribe enabled.** Members must join: {channels_links}",
                disable_web_page_preview=True
            )
    else:
        channels = sql.get_channels(chat_id)
        if channels:
            channels_links = ", ".join(f"[{c}](https://t.me/{c})" for c in channels)
            message.reply_text(
                f"✅ **Force Subscribe is enabled.** Required channel(s): {channels_links}",
                disable_web_page_preview=True
            )
        else:
            message.reply_text("❌ **Force Subscribe is disabled** in this chat.")
