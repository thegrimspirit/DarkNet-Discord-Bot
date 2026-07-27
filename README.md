# DarkNet Alliance — Discord Bot

Multipurpose Discord bot dla serwera DarkNet Alliance.  
Działa na dedyku, zero komend — cała konfiguracja w pliku `bot.py`.

## Funkcje
- ❄️ Powitania / pożegnania (embed z avatarem)
- 🎨 Kolor embeda zależny od wieku konta (🔴 nowe / 🟠 młode / 🟢 stare)
- 👥 Automatyczny licznik członków w nazwie kanału
- 📊 Dzienny raport o północy UTC (ile osób dołączyło/wyszło)
- 🔄 Wykrywanie powracających użytkowników
- 📥 Auto-rola przy dołączeniu (opcjonalne)
- 💌 DM powitalne (opcjonalne)
- 🎭 Reaction Roles (emoji → rola, z obsługą usuwania)
- 📋 Logowanie zdarzeń
- 🔁 Retry przy błędach wysyłania
- ⏰ Czas UTC

## Konfiguracja — sekcja CONFIG w bot.py

| Zmienna | Opis |
|---|---|
| `GUILD_ID` | ID Twojego serwera |
| `LOG_CHANNEL_ID` | Kanał logów |
| `WELCOME_CHANNEL_ID` | Kanał powitalny |
| `REPORT_CHANNEL_ID` | Kanał dziennego raportu |
| `COUNTER_CHANNEL_ID` | Kanał z licznikiem członków (voice lub text) |
| `EMOJI_ROLE_MAP` | Słownik emoji → ID roli |
| `AUTO_ROLE_ID` | Rola nadawana automatycznie (None = wyłączone) |
| `SEND_WELCOME_DM` | True/False |
| `NEW_ACCOUNT_DAYS` | Próg w dniach dla nowego konta (domyślnie 7) |

## Instalacja

```bash
pip install -r requirements.txt
cp .env.example .env
nano .env          # wstaw token
nano bot.py        # ustaw ID kanałów i serwera
python bot.py
```

## Wymagania
- Python 3.10+
- discord.py 2.3+
- Uprawnienia bota: `Manage Roles`, `Manage Channels`, `Send Messages`, `Read Message History`
- Intenty w Discord Developer Portal: **Server Members Intent**, **Message Content Intent**

## Uwaga — licznik członków
Kanał `COUNTER_CHANNEL_ID` może być kanałem voice (zalecane — widoczne bez wchodzenia).  
Bot musi mieć uprawnienie `Manage Channels` na tym kanale.

## Uwaga — wykrywanie powrotów
Pamięć powrotów działa tylko w RAM — resetuje się po restarcie bota.  
Jeśli chcesz trwałą pamięć, potrzebna jest baza danych (SQLite).
