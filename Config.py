import os

class Config():
  ENV = bool(os.environ.get('ENV', False))
  if ENV:
    BOT_TOKEN = os.environ.get("tok3n", None)
    DATABASE_URL = os.environ.get("DATABASE_URL", None)
    APP_ID = int(os.environ.get("APP_ID", 6))
    API_HASH = os.environ.get("API_HASH", None)
    _sudo = os.environ.get("SUDO_USERS", "").strip()
    SUDO_USERS = list(set(int(x) for x in _sudo.split() if x.isdigit()))
  else:
    BOT_TOKEN = ""
    DATABASE_URL = ""
    APP_ID = ""
    API_HASH = ""
    SUDO_USERS = []


class Messages():
      HELP_MSG = [
        ".",

        "**Force Subscribe**\n__Force group members to join one or more channels before sending messages.\nI will mute members who haven't joined and they can unmute by joining and pressing the button.__",
        
        "**Setup**\n__First of all add me in the group as admin with ban users permission and in the channel as admin.\nNote: Only creator of the group can setup me and i will leave the chat if i am not an admin in the chat.__",
        
        "**Commands**\n__/ForceSubscribe - Current settings.\n/ForceSubscribe off - Disable.\n/ForceSubscribe @channel (or several @ch1 @ch2) - Enable and set channel(s).\n/ForceSubscribe clear - Unmute all members muted by me.\n\nNote: /FSub is an alias of /ForceSubscribe__",
        
        "**Developed by @viperadnan**"
      ]

      START_MSG = "**Hey [{}](tg://user?id={})**\n__I can force members to join a specific channel before writing messages in the group.\nLearn more at /help__"