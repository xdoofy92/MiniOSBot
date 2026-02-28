from sqlalchemy import Column, String, BigInteger, Integer, PrimaryKeyConstraint
from sql_helpers import SESSION, BASE


class forceSubscribe(BASE):
    __tablename__ = "forceSubscribe"
    __table_args__ = (PrimaryKeyConstraint("chat_id", "channel", name="forceSubscribe_pkey"),)
    chat_id = Column(BigInteger, primary_key=True)  # BigInteger evita SAWarning con SQLite y es correcto para IDs de Telegram
    channel = Column(String, primary_key=True)

    def __init__(self, chat_id, channel):
        self.chat_id = chat_id
        self.channel = channel


forceSubscribe.__table__.create(checkfirst=True)


class MutedUser(BASE):
    """Usuarios muteados por el bot en cada chat (para desilenciado masivo con /ForceSubscribe clear)."""
    __tablename__ = "muted_users"
    __table_args__ = (PrimaryKeyConstraint("chat_id", "user_id", name="muted_users_pkey"),)
    chat_id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, primary_key=True)

    def __init__(self, chat_id, user_id):
        self.chat_id = int(chat_id)
        self.user_id = int(user_id)


MutedUser.__table__.create(checkfirst=True)


class NotificationMessage(BASE):
    """Último mensaje de notificación enviado a cada usuario en cada chat (para borrar el anterior)."""
    __tablename__ = "notification_message"
    __table_args__ = (PrimaryKeyConstraint("chat_id", "user_id", name="notification_message_pkey"),)
    chat_id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, primary_key=True)
    message_id = Column(BigInteger, nullable=False)

    def __init__(self, chat_id, user_id, message_id):
        self.chat_id = int(chat_id)
        self.user_id = int(user_id)
        self.message_id = int(message_id)


NotificationMessage.__table__.create(checkfirst=True)


class UnverifiedCount(BASE):
    """Mensajes enviados sin verificar por (chat_id, user_id). Mute si > 5."""
    __tablename__ = "unverified_count"
    __table_args__ = (PrimaryKeyConstraint("chat_id", "user_id", name="unverified_count_pkey"),)
    chat_id = Column(BigInteger, primary_key=True)
    user_id = Column(BigInteger, primary_key=True)
    count = Column(Integer, nullable=False, default=0)

    def __init__(self, chat_id, user_id, count=0):
        self.chat_id = int(chat_id)
        self.user_id = int(user_id)
        self.count = int(count)


UnverifiedCount.__table__.create(checkfirst=True)


def get_unverified_count(chat_id, user_id):
    """Devuelve cuántos mensajes ha enviado sin verificar (0 si no existe)."""
    try:
        row = SESSION.query(UnverifiedCount).filter(
            UnverifiedCount.chat_id == int(chat_id),
            UnverifiedCount.user_id == int(user_id),
        ).first()
        return row.count if row else 0
    except Exception:
        return 0
    finally:
        SESSION.close()


def increment_unverified_count(chat_id, user_id):
    """Incrementa el contador y devuelve el nuevo valor."""
    try:
        cid, uid = int(chat_id), int(user_id)
        row = SESSION.query(UnverifiedCount).filter(
            UnverifiedCount.chat_id == cid,
            UnverifiedCount.user_id == uid,
        ).first()
        if row:
            row.count += 1
            new_count = row.count
        else:
            SESSION.add(UnverifiedCount(chat_id=cid, user_id=uid, count=1))
            new_count = 1
        SESSION.commit()
        return new_count
    except Exception:
        return 1
    finally:
        SESSION.close()


def clear_unverified_count(chat_id, user_id):
    """Resetea el contador al verificar."""
    try:
        SESSION.query(UnverifiedCount).filter(
            UnverifiedCount.chat_id == int(chat_id),
            UnverifiedCount.user_id == int(user_id),
        ).delete()
        SESSION.commit()
    except Exception:
        pass
    finally:
        SESSION.close()


def clear_unverified_count_for_chat(chat_id):
    """Borra todos los contadores del chat (tras /ForceSubscribe clear)."""
    try:
        SESSION.query(UnverifiedCount).filter(UnverifiedCount.chat_id == int(chat_id)).delete()
        SESSION.commit()
    except Exception:
        pass
    finally:
        SESSION.close()


def get_notification_message_id(chat_id, user_id):
    """Devuelve el message_id del último mensaje de notificación para este usuario en el chat, o None."""
    try:
        row = SESSION.query(NotificationMessage).filter(
            NotificationMessage.chat_id == int(chat_id),
            NotificationMessage.user_id == int(user_id),
        ).first()
        return row.message_id if row else None
    except Exception:
        return None
    finally:
        SESSION.close()


def set_notification_message_id(chat_id, user_id, message_id):
    """Guarda o actualiza el message_id del mensaje de notificación (uno por usuario por chat)."""
    try:
        cid, uid, mid = int(chat_id), int(user_id), int(message_id)
        existing = SESSION.query(NotificationMessage).filter(
            NotificationMessage.chat_id == cid,
            NotificationMessage.user_id == uid,
        ).first()
        if existing:
            existing.message_id = mid
        else:
            SESSION.add(NotificationMessage(chat_id=cid, user_id=uid, message_id=mid))
        SESSION.commit()
    except Exception:
        pass
    finally:
        SESSION.close()


def clear_notification_message_id(chat_id, user_id):
    """Borra el registro del mensaje de notificación (tras verificar)."""
    try:
        SESSION.query(NotificationMessage).filter(
            NotificationMessage.chat_id == int(chat_id),
            NotificationMessage.user_id == int(user_id),
        ).delete()
        SESSION.commit()
    except Exception:
        pass
    finally:
        SESSION.close()


def get_all_notification_message_ids(chat_id):
    """Devuelve todos los message_id de notificaciones en este chat (para /ForceSubscribe clear)."""
    try:
        rows = SESSION.query(NotificationMessage).filter(NotificationMessage.chat_id == int(chat_id)).all()
        return [r.message_id for r in rows]
    except Exception:
        return []
    finally:
        SESSION.close()


def add_muted(chat_id, user_id):
    """Registra que el bot muteó a este usuario en el chat."""
    try:
        cid, uid = int(chat_id), int(user_id)
        existing = SESSION.query(MutedUser).filter(MutedUser.chat_id == cid, MutedUser.user_id == uid).first()
        if not existing:
            SESSION.add(MutedUser(chat_id=cid, user_id=uid))
            SESSION.commit()
    except Exception:
        pass
    finally:
        SESSION.close()


def remove_muted(chat_id, user_id):
    """Quita de la lista de muteados (al desmutear por Verificar o clear)."""
    try:
        SESSION.query(MutedUser).filter(MutedUser.chat_id == int(chat_id), MutedUser.user_id == int(user_id)).delete()
        SESSION.commit()
    except Exception:
        pass
    finally:
        SESSION.close()


def get_muted_users(chat_id):
    """Devuelve la lista de user_id muteados por el bot en este chat."""
    try:
        rows = SESSION.query(MutedUser).filter(MutedUser.chat_id == int(chat_id)).all()
        return [r.user_id for r in rows]
    except Exception:
        return []
    finally:
        SESSION.close()


def clear_muted_for_chat(chat_id):
    """Borra muteados, notificaciones y contadores de este chat (tras /ForceSubscribe clear)."""
    try:
        cid = int(chat_id)
        SESSION.query(MutedUser).filter(MutedUser.chat_id == cid).delete()
        SESSION.query(NotificationMessage).filter(NotificationMessage.chat_id == cid).delete()
        SESSION.query(UnverifiedCount).filter(UnverifiedCount.chat_id == cid).delete()
        SESSION.commit()
    except Exception:
        pass
    finally:
        SESSION.close()


def get_channels(chat_id):
    """Devuelve la lista de canales configurados para el chat (puede ser vacía)."""
    try:
        cid = int(chat_id)
        rows = SESSION.query(forceSubscribe).filter(forceSubscribe.chat_id == cid).all()
        return [r.channel for r in rows]
    except Exception:
        return []
    finally:
        SESSION.close()


def fs_settings(chat_id):
    """Compatibilidad: devuelve la lista de canales o None si no hay ninguno."""
    channels = get_channels(chat_id)
    if not channels:
        return None
    # Objeto simple con .channel (primero) y .channels (todos) para compatibilidad
    class FsSettings:
        pass
    obj = FsSettings()
    obj.channel = channels[0]
    obj.channels = channels
    return obj


def add_channel(chat_id, channel):
    """Añade un canal al chat (si ya existe, no hace nada)."""
    cid = int(chat_id)
    existing = SESSION.query(forceSubscribe).filter(
        forceSubscribe.chat_id == cid,
        forceSubscribe.channel == channel
    ).first()
    if not existing:
        SESSION.add(forceSubscribe(chat_id=cid, channel=channel))
        SESSION.commit()
    SESSION.close()


def set_channels(chat_id, channels):
    """Reemplaza todos los canales del chat por la lista dada."""
    cid = int(chat_id)
    SESSION.query(forceSubscribe).filter(forceSubscribe.chat_id == cid).delete()
    for ch in channels:
        SESSION.add(forceSubscribe(chat_id=cid, channel=ch))
    SESSION.commit()
    SESSION.close()


def disapprove(chat_id):
    """Desactiva Force Subscribe para el chat (elimina todos los canales)."""
    SESSION.query(forceSubscribe).filter(forceSubscribe.chat_id == int(chat_id)).delete()
    SESSION.commit()
    SESSION.close()
