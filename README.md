# Introduction
**A Telegram Bot to force users to join a specific channel before sending messages in a group.**

## Features
- Force subscribe to **one or more channels** per group
- SUDO users configurable via env (no hardcoded IDs)
- SQLite fallback when `DATABASE_URL` is not set (local development)

## Deploy


[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

### Installing Prerequisite
- On Ubuntu 18.04 or later
```sh
sudo apt-get install git python3 python3-pip libpq-dev
```

### Installation
- Clone this repo
```sh
git clone https://github.com/viperadnan-git/force-subscribe-telegram-bot
```
- Change directory
```sh
cd force-subscribe-telegram-bot
```
- Install requirements
```sh
pip3 install -r requirements.txt
```

### Configuration
Solo necesitas el **token del bot** ([@BotFather](https://t.me/botfather)). En Railway define la variable **tok3n** con ese token. Opcional: **SUDO_USERS** (IDs separados por espacios), **DATABASE_URL** (PostgreSQL). No se requiere APP_ID ni API_HASH (usa [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)).

### Ejecución (solo Python)
```sh
pip install -r requirements.txt
python bot.py
```

## Thanks to
- [python-telegram-bot](https://github.com/python-telegram-bot/python-telegram-bot)
- [Hasibul Kabir](https://GitHub.com/hasibulkabir) and [Spechide](https://GitHub.com/spechide) for helping.
