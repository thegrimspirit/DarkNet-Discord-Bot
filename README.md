# DarkNet Alliance — Discord Bot

Multipurpose Discord bot dla serwera DarkNet Alliance.
Działa na dedyku, zero komend — cała konfiguracja w pliku `bot.py`.

## Funkcje
- ❄️ Powitania / pożegnania (embed z avatarem)
- 📥 Auto-rola przy dołączeniu
- 💌 DM powitalne (opcjonalne)
- 🎭 Reaction Roles (emoji → rola, z obsługą usuwania)
- 📋 Logowanie zdarzeń
- 🔁 Retry przy błędach wysyłania
- ⏰ Czas UTC (nie lokalny)

## Konfiguracja

1. Skopiuj `.env.example` → `.env` i wstaw token bota
2. W `bot.py` edytuj sekcję `CONFIG — EDYTUJ TUTAJ`:
   - `GUILD_ID` — ID Twojego serwera
   - `LOG_CHANNEL_ID` — kanał logów
   - `WELCOME_CHANNEL_ID` — kanał powitalny
   - `ROLE_CHANNEL_ID` + `ROLE_MESSAGE_IDS` — reaction roles
   - `EMOJI_ROLE_MAP` — emoji i odpowiadające im role ID
   - `AUTO_ROLE_ID` — rola nadawana automatycznie (None = wyłączone)
   - `SEND_WELCOME_DM` — True/False

## Instalacja

```bash
pip install -r requirements.txt
python bot.py
```

## Wymagania
- Python 3.10+
- discord.py 2.3+
- Uprawnienia bota: `Manage Roles`, `Send Messages`, `Read Message History`
- Intenty: `Server Members Intent`, `Message Content Intent` (włącz w Discord Developer Portal)
