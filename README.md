# DarkNet Alliance — Discord Bot

Multipurpose Discord bot. Działa na dedyku, zero komend — cała konfiguracja w `bot.py`.

---

## Moduły

### 🟦 Moduł 1 — Powitanie / Pożegnanie
- Embed powitalny z avatarem, wiekiem konta, licznikiem członków
- Kolor embeda zależny od wieku konta (🔴 <7d / 🟠 <30d / 🟢 stare)
- Ostrzeganie o nowych kontach (<7 dni)
- Wykrywanie powracających użytkowników
- DM powitalne (opcjonalne)
- Auto-rola przy dołączeniu (opcjonalne)
- Reaction Roles (emoji → rola, z obsługą usuwania)

### 🟨 Moduł 2 — Raporty
- **Dzienny raport** o północy UTC: ile joinów, leaveów, bilans
- **Tygodniowy raport** w każdy poniedziałek 00:00 UTC
- Kolor raportu: zielony (bilans+) / czerwony (bilans-)

### 🟥 Moduł 3 — Statystyki (kanały voice)
| Kanał | Opis |
|---|---|
| 👥 Members: X | Wszyscy członkowie |
| 🟢 Online: X | Status online |
| 🟡 Away: X | Status idle/away |
| 🔴 DnD: X | Do Not Disturb |
| ⚫ Offline: X | Offline / invisible |
| 🤖 Bots: X | Liczba botów |

Aktualizacja co 5 minut (Discord rate-limit!).

---

## Konfiguracja — sekcja CONFIG w bot.py

### Moduł 1
| Zmienna | Opis |
|---|---|
| `GUILD_ID` | ID serwera |
| `WELCOME_CHANNEL_ID` | Kanał powitalny |
| `LOG_CHANNEL_ID` | Kanał logów |
| `SEND_WELCOME_DM` | True/False |
| `NEW_ACCOUNT_DAYS` | Próg nowego konta (dni) |
| `AUTO_ROLE_ID` | Auto-rola (None = wył.) |
| `EMOJI_ROLE_MAP` | Reaction roles |

### Moduł 2
| Zmienna | Opis |
|---|---|
| `REPORT_CHANNEL_ID` | Kanał raportów dziennych |
| `WEEKLY_CHANNEL_ID` | Kanał raportu tygodniowego |

### Moduł 3
| Zmienna | Opis |
|---|---|
| `STAT_CHANNELS` | Słownik key → ID kanału voice |
| `STAT_FORMATS` | Format nazwy kanału |
| `STATS_UPDATE_INTERVAL` | Częstotliwość aktualizacji (sek, min 300) |

---

## Instalacja

```bash
pip install -r requirements.txt
cp .env.example .env
nano .env        # wstaw token
nano bot.py      # ustaw GUILD_ID i ID kanałów
python bot.py
```

## Wymagania
- Python 3.10+
- discord.py 2.3+
- Uprawnienia bota: `Manage Roles`, `Manage Channels`, `Send Messages`, `Read Message History`
- Intenty w Discord Developer Portal:
  - **Server Members Intent** ✅
  - **Message Content Intent** ✅
  - **Presence Intent** ✅ (wymagane dla Online/Away/DnD)

## ⚠️ UWAGA — Discord Rate Limit
Zmiana nazwy kanału jest ograniczona do **2 razy na 10 minut**.
Nie zmniejszaj `STATS_UPDATE_INTERVAL` poniżej 300 sekund!
