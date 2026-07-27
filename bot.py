import os
import discord
import asyncio
from datetime import datetime, timezone, timedelta
from discord import Embed
from dotenv import load_dotenv

# ==========================
# LOAD ENVIRONMENT (.env)
# ==========================
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")


# ============================================================
# MODULE 1 CONFIG — POWITANIE / POŻEGNANIE
# ============================================================
GUILD_ID           = 1234567890123456789   # <-- ID Twojego serwera
WELCOME_CHANNEL_ID = 1317868408171270146   # kanał powitalny
LOG_CHANNEL_ID     = 1317868408171270146   # kanał logów join/leave

SEND_WELCOME_DM    = True                  # DM powitalne True/False
NEW_ACCOUNT_DAYS   = 7                     # próg nowego konta w dniach
AUTO_ROLE_ID       = None                  # auto-rola przy join (None = wył.)

# Reaction Roles
ROLE_CHANNEL_ID  = 1448324147024236836
ROLE_MESSAGE_IDS = [1448324524801003591, 1448324598012842106]
EMOJI_ROLE_MAP   = {
    "❄️": 1317873265959633006,
    # "🔥": 111222333444555666,
}


# ============================================================
# MODULE 2 CONFIG — RAPORTY
# ============================================================
REPORT_CHANNEL_ID  = 1317868408171270146   # kanał raportów dziennych
WEEKLY_CHANNEL_ID  = 1317868408171270146   # kanał raportu tygodniowego (może być inny)


# ============================================================
# MODULE 3 CONFIG — STATYSTYKI (kanały voice)
# ============================================================
# Ustaw ID kanałów voice. None = kanał wyłączony / nie tworzony.
# UWAGA: kanały voice aktualizują się co STATS_UPDATE_INTERVAL sekund
# Discord rate-limit: max 2 zmiany nazwy na 10 minut!
STATS_UPDATE_INTERVAL = 300   # 300 sekund = 5 minut (nie zmniejszaj!)

STAT_CHANNELS = {
    "members":  1234567890000000001,   # 👥 Members: X  — wszyscy członkowie
    "online":   1234567890000000002,   # 🟢 Online: X   — status online
    "away":     1234567890000000003,   # 🟡 Away: X     — status idle (away)
    "dnd":      1234567890000000004,   # 🔴 DnD: X      — do not disturb
    "offline":  1234567890000000005,   # ⚫ Offline: X  — offline / invisible
    "bots":     1234567890000000006,   # 🤖 Bots: X     — liczba botów
}

# Format nazw kanałów — można zmienić emoji i tekst
STAT_FORMATS = {
    "members":  "👥 Members: {}",
    "online":   "🟢 Online: {}",
    "away":     "🟡 Away: {}",
    "dnd":      "🔴 DnD: {}",
    "offline":  "⚫ Offline: {}",
    "bots":     "🤖 Bots: {}",
}


# ============================================================
# STAŁE
# ============================================================
FOOTER = "DarkNet Alliance • AI Monitoring System - Powered by The_Grim_Net • ❄️ Winter Edition"


# ============================================================
# BOT SETUP
# ============================================================
intents = discord.Intents.default()
intents.members        = True
intents.guilds         = True
intents.reactions      = True
intents.message_content = True
intents.presences      = True   # wymagane do odczytu statusów online/away/dnd

client = discord.Client(intents=intents)


# ============================================================
# RAM STORAGE
# ============================================================
left_members: set[int] = set()   # IDs które kiedyś wyszli
daily_joins:  int = 0
daily_leaves: int = 0
weekly_joins: int = 0
weekly_leaves: int = 0


# ============================================================
# UTILITIES
# ============================================================
def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M UTC")


def account_age_days(member: discord.Member) -> int:
    return (datetime.now(timezone.utc) - member.created_at).days


def join_color(member: discord.Member) -> int:
    age = account_age_days(member)
    if age < NEW_ACCOUNT_DAYS:  return 0xff4444   # czerwony
    elif age < 30:              return 0xffaa00   # pomarańczowy
    else:                       return 0x00cc66   # zielony


def make_embed(title: str, description: str, color: int) -> Embed:
    e = Embed(title=title, description=description, color=color)
    e.set_footer(text=FOOTER)
    return e


async def safe_send(channel, embed: Embed):
    for attempt in range(3):
        try:
            return await channel.send(embed=embed)
        except discord.Forbidden:
            print(f"[ERROR] Brak uprawnień: #{channel.name}")
            return None
        except Exception as e:
            print(f"[WARN] Próba {attempt+1}/3: {e}")
            await asyncio.sleep(2)
    print("[ERROR] Nie udało się wysłać embeda.")
    return None


async def safe_send_dm(member, embed: Embed):
    try:
        await member.send(embed=embed)
    except discord.Forbidden:
        print(f"[DM] {member.name} zablokowane DM")
    except Exception as e:
        print(f"[DM] Błąd: {e}")


async def safe_rename(channel, new_name: str):
    """Zmienia nazwę kanału tylko gdy inna niż aktualna."""
    if channel and channel.name != new_name:
        try:
            await channel.edit(name=new_name, reason="Stats update")
        except discord.Forbidden:
            print(f"[ERROR] Brak uprawnień do zmiany nazwy: {channel.name}")
        except Exception as e:
            print(f"[ERROR] Rename: {e}")


# ============================================================
# MODULE 1 — POWITANIE / POŻEGNANIE
# ============================================================

async def handle_join(member: discord.Member):
    global daily_joins, weekly_joins
    daily_joins  += 1
    weekly_joins += 1

    guild = member.guild
    age   = account_age_days(member)
    color = join_color(member)

    extras = ""
    if age < NEW_ACCOUNT_DAYS:
        extras += f"\n⚠️ **NOWE KONTO** — {age} dni!"
    if member.id in left_members:
        extras += "\n🔄 **Użytkownik wrócił na serwer!**"
        left_members.discard(member.id)

    # Auto-rola
    if AUTO_ROLE_ID:
        role = guild.get_role(AUTO_ROLE_ID)
        if role and guild.me.top_role > role:
            try:
                await member.add_roles(role, reason="Auto-role")
            except Exception as e:
                print(f"[ERROR] Auto-role: {e}")

    # Embed powitalny
    welcome_ch = guild.get_channel(WELCOME_CHANNEL_ID)
    if welcome_ch:
        embed = make_embed(
            title="❄ New Arrival at DarkNet Alliance",
            description=(
                f"✨ Witaj {member.mention}!\n"
                f"👥 Jesteś **{guild.member_count:,}** członkiem\n"
                f"🗓️ Wiek konta: **{age} dni**\n"
                f"🕒 {now_utc()}{extras}"
            ),
            color=color
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await safe_send(welcome_ch, embed)

    # Log (tylko jeśli inny kanał)
    log_ch = guild.get_channel(LOG_CHANNEL_ID)
    if log_ch and log_ch.id != WELCOME_CHANNEL_ID:
        log_embed = make_embed(
            title="📥 Member Joined",
            description=(
                f"👤 {member.mention} (`{member.id}`)\n"
                f"🗓️ Konto: {age} dni\n"
                f"🕒 {now_utc()}{extras}"
            ),
            color=color
        )
        log_embed.set_thumbnail(url=member.display_avatar.url)
        await safe_send(log_ch, log_embed)

    # DM
    if SEND_WELCOME_DM:
        dm = make_embed(
            title="👋 Witaj w DarkNet Alliance!",
            description="Miło Cię widzieć!\nSprawdź kanały z rolami i zasadami.\n\n*DarkNet Alliance AI System*",
            color=0x00aaff
        )
        await safe_send_dm(member, dm)

    print(f"[JOIN] {member} | konto: {age}d | {'\ud83d\udd34' if age<7 else '\ud83d\udfe0' if age<30 else '\ud83d\udfe2'} | łącznie: {guild.member_count}")


async def handle_leave(member: discord.Member):
    global daily_leaves, weekly_leaves
    daily_leaves  += 1
    weekly_leaves += 1
    left_members.add(member.id)

    log_ch = member.guild.get_channel(LOG_CHANNEL_ID)
    if log_ch:
        embed = make_embed(
            title="❄ Departure from DarkNet Alliance",
            description=f"✨ {member.mention} opuścił serwer\n🕒 {now_utc()}",
            color=0xaa0000
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await safe_send(log_ch, embed)

    print(f"[LEAVE] {member}")


# ============================================================
# MODULE 2 — RAPORTY
# ============================================================

def build_report_embed(title: str, period_label: str, joins: int, leaves: int, total: int) -> Embed:
    balance = joins - leaves
    sign    = "+" if balance >= 0 else ""
    color   = 0x00cc66 if balance >= 0 else 0xff4444
    return make_embed(
        title=title,
        description=(
            f"📅 **{period_label}**\n\n"
            f"📥 Dołączyło:  **{joins}**\n"
            f"📤 Wyszło:    **{leaves}**\n"
            f"👥 Łącznie:   **{total:,}**\n"
            f"📈 Bilans:    **{sign}{balance}**"
        ),
        color=color
    )


async def daily_report_loop():
    global daily_joins, daily_leaves
    await client.wait_until_ready()

    while not client.is_closed():
        now      = datetime.now(timezone.utc)
        midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        await asyncio.sleep((midnight - now).total_seconds())

        guild = discord.utils.get(client.guilds, id=GUILD_ID)
        if not guild:
            daily_joins = daily_leaves = 0
            continue

        ch = guild.get_channel(REPORT_CHANNEL_ID)
        if ch:
            date_str = datetime.now(timezone.utc).strftime("%d.%m.%Y")
            embed = build_report_embed(
                title="📊 Dzienny Raport — DarkNet Alliance",
                period_label=date_str,
                joins=daily_joins,
                leaves=daily_leaves,
                total=guild.member_count
            )
            await safe_send(ch, embed)
            print(f"[DAILY] Raport: +{daily_joins} / -{daily_leaves}")

        daily_joins = daily_leaves = 0


async def weekly_report_loop():
    global weekly_joins, weekly_leaves
    await client.wait_until_ready()

    while not client.is_closed():
        now = datetime.now(timezone.utc)
        # Czeka do następnego poniedziałku 00:00 UTC
        days_ahead = (7 - now.weekday()) % 7 or 7
        next_monday = (now + timedelta(days=days_ahead)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        await asyncio.sleep((next_monday - now).total_seconds())

        guild = discord.utils.get(client.guilds, id=GUILD_ID)
        if not guild:
            weekly_joins = weekly_leaves = 0
            continue

        ch = guild.get_channel(WEEKLY_CHANNEL_ID)
        if ch:
            # Zakres tygodnia
            week_end   = datetime.now(timezone.utc)
            week_start = week_end - timedelta(days=7)
            period = f"{week_start.strftime('%d.%m')} — {week_end.strftime('%d.%m.%Y')}"
            embed = build_report_embed(
                title="📆 Tygodniowy Raport — DarkNet Alliance",
                period_label=period,
                joins=weekly_joins,
                leaves=weekly_leaves,
                total=guild.member_count
            )
            await safe_send(ch, embed)
            print(f"[WEEKLY] Raport: +{weekly_joins} / -{weekly_leaves}")

        weekly_joins = weekly_leaves = 0


# ============================================================
# MODULE 3 — STATYSTYKI (kanały voice)
# ============================================================

def get_status_counts(guild: discord.Guild) -> dict:
    """Zlicza memberów wg statusów. Wymaga intents.presences."""
    counts = {"online": 0, "away": 0, "dnd": 0, "offline": 0, "bots": 0}
    for member in guild.members:
        if member.bot:
            counts["bots"] += 1
            continue
        status = str(member.status)
        if status == "online":             counts["online"]  += 1
        elif status in ("idle", "away"):   counts["away"]    += 1
        elif status == "dnd":              counts["dnd"]      += 1
        else:                              counts["offline"]  += 1
    return counts


async def update_stat_channels(guild: discord.Guild):
    """Aktualizuje wszystkie kanały statystyk."""
    counts = get_status_counts(guild)
    counts["members"] = guild.member_count

    for key, channel_id in STAT_CHANNELS.items():
        if not channel_id:
            continue
        channel = guild.get_channel(channel_id)
        if not channel:
            continue
        new_name = STAT_FORMATS[key].format(counts.get(key, 0))
        await safe_rename(channel, new_name)


async def stats_update_loop():
    """Pętla aktualizująca kanały co STATS_UPDATE_INTERVAL sekund."""
    await client.wait_until_ready()
    while not client.is_closed():
        guild = discord.utils.get(client.guilds, id=GUILD_ID)
        if guild:
            await update_stat_channels(guild)
        await asyncio.sleep(STATS_UPDATE_INTERVAL)


# ============================================================
# EVENTS
# ============================================================

@client.event
async def on_ready():
    print(f"🟢 [DarkNet Alliance] Online: {client.user}")
    print(f"🕒 {now_utc()}")

    guild = discord.utils.get(client.guilds, id=GUILD_ID)
    if not guild:
        print(f"❌ Nie znaleziono serwera {GUILD_ID}")
        return

    # Sprawdzenie kanałów
    checks = {
        "Welcome":        guild.get_channel(WELCOME_CHANNEL_ID),
        "Log":            guild.get_channel(LOG_CHANNEL_ID),
        "Daily Report":   guild.get_channel(REPORT_CHANNEL_ID),
        "Weekly Report":  guild.get_channel(WEEKLY_CHANNEL_ID),
    }
    for name, ch in checks.items():
        print(f"  {'✔️' if ch else '❌'} {name}: {'OK' if ch else 'NIE ZNALEZIONO'}")

    for key, cid in STAT_CHANNELS.items():
        ch = guild.get_channel(cid) if cid else None
        print(f"  {'✔️' if ch else '❌'} Stats [{key}]: {'OK' if ch else 'NIE ZNALEZIONO lub None'}")

    # Uruchom pętle
    asyncio.ensure_future(daily_report_loop())
    asyncio.ensure_future(weekly_report_loop())
    asyncio.ensure_future(stats_update_loop())

    print("🚀 Wszystkie moduły uruchomione.")


@client.event
async def on_member_join(member):
    await handle_join(member)
    await update_stat_channels(member.guild)


@client.event
async def on_member_remove(member):
    await handle_leave(member)
    await update_stat_channels(member.guild)


@client.event
async def on_presence_update(before, after):
    """Aktualizuje statystyki gdy ktoś zmienia status (online/away/dnd/offline)."""
    # Nie aktualizuj przy każdej zmianie — pętla stats_update_loop robi to co X minut
    # Ten event jest opcjonalny — zakomentuj jeśli za dużo requestów
    pass


@client.event
async def on_raw_reaction_add(payload):
    if payload.channel_id != ROLE_CHANNEL_ID: return
    if payload.message_id not in ROLE_MESSAGE_IDS: return
    emoji = str(payload.emoji)
    if emoji not in EMOJI_ROLE_MAP: return
    guild  = client.get_guild(payload.guild_id)
    member = guild.get_member(payload.user_id)
    if not member or member.bot: return
    role = guild.get_role(EMOJI_ROLE_MAP[emoji])
    if not role or guild.me.top_role <= role: return
    try:
        await member.add_roles(role, reason="Reaction role")
        print(f"[ROLE+] {role.name} → {member.name}")
    except Exception as e:
        print(f"[ERROR] add_roles: {e}")


@client.event
async def on_raw_reaction_remove(payload):
    if payload.channel_id != ROLE_CHANNEL_ID: return
    if payload.message_id not in ROLE_MESSAGE_IDS: return
    emoji = str(payload.emoji)
    if emoji not in EMOJI_ROLE_MAP: return
    guild  = client.get_guild(payload.guild_id)
    member = guild.get_member(payload.user_id)
    if not member or member.bot: return
    role = guild.get_role(EMOJI_ROLE_MAP[emoji])
    if not role or guild.me.top_role <= role: return
    try:
        await member.remove_roles(role, reason="Reaction role removed")
        print(f"[ROLE-] {role.name} ← {member.name}")
    except Exception as e:
        print(f"[ERROR] remove_roles: {e}")


@client.event
async def on_error(event, *args, **kwargs):
    import traceback
    print(f"[ERROR] {event}")
    traceback.print_exc()


# ============================================================
# URUCHOMIENIE
# ============================================================
if __name__ == "__main__":
    if not TOKEN:
        print("❌ DISCORD_TOKEN nie ustawiony w .env!")
        exit(1)
    print("🚀 Uruchamianie DarkNet Alliance Bot...")
    client.run(TOKEN)
