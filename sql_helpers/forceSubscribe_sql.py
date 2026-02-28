from sqlalchemy import Column, String, Numeric, PrimaryKeyConstraint
from sql_helpers import SESSION, BASE


class forceSubscribe(BASE):
    __tablename__ = "forceSubscribe"
    __table_args__ = (PrimaryKeyConstraint("chat_id", "channel", name="forceSubscribe_pkey"),)
    chat_id = Column(Numeric, primary_key=True)
    channel = Column(String, primary_key=True)

    def __init__(self, chat_id, channel):
        self.chat_id = chat_id
        self.channel = channel


forceSubscribe.__table__.create(checkfirst=True)


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
