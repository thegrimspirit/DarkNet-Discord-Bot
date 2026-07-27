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

# ==========================
# CONFIG — EDYTUJ TUTAJ
# ==========================
GUILD_ID           = 1234567890123456789   # <-- ID Twojego serwera
LOG_CHANNEL_ID     = 1317868408171270146   # kanał logów (join/leave/powroty)
WELCOME_CHANNEL_ID = 1317868408171270146   # kanał powitalny (może być inny)
REPORT_CHANNEL_ID  = 1317868408171270146   # kanał dziennego raportu (może być inny)
COUNTER_CHANNEL_ID = 1234567890000000001   # <-- kanał z licznikiem członków (voice/text)

# Reaction Roles
ROLE_CHANNEL_ID  = 1448324147024236836
ROLE_MESSAGE_IDS = [
    1448324524801003591,
    1448324598012842106
]
EMOJI_ROLE_MAP = {
    "❄️": 1317873265959633006,
    # "🔥": 1234567890000000001,
}

# Auto-rola przy dołączeniu (None = wyłączone)
AUTO_ROLE_ID = None

# DM powitalne
SEND_WELCOME_DM = True

# Próg wieku konta — poniżej = nowe konto (dni)
NEW_ACCOUNT_DAYS = 7

# ==========================
# STAŁE TEKSTOWE
# ==========================
FOOTER = "DarkNet Alliance • AI Monitoring System - Powered by The_Grim_Net • ❄️ Winter Edition"

# ==========================
# PAMIĘĆ BOTA (w RAM — resetuje się po restarcie)
# Przechowuje ID użytkowników którzy kiedyś wyszli
# ==========================
left_members: set[int] = set()

# Liczniki dziennego raportu
daily_joins: int = 0
daily_leaves: int = 0

# ==========================
# BOT SETUP
# ==========================
intents = discord.Intents.default()
intents.members = True
intents.guilds = True
intents.reactions = True
intents.message_content = True

client = discord.Client(intents=intents)


# ==========================
# UTILITIES
# ==========================
def now_utc() -> str:
    return datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M UTC")


def account_age_days(member: discord.Member) -> int:
    """Zwraca wiek konta w dniach."""
    return (datetime.now(timezone.utc) - member.created_at).days


def join_color(member: discord.Member) -> int:
    """Kolor embeda zależny od wieku konta."""
    age = account_age_days(member)
    if age < NEW_ACCOUNT_DAYS:
        return 0xff4444   # czerwony — nowe konto (podejrzane)
    elif age < 30:
        return 0xffaa00   # pomarańczowy — młode konto
    else:
        return 0x00cc66   # zielony — stare konto (zaufane)


def make_embed(title: str, description: str, color: int) -> Embed:
    embed = Embed(title=title, description=description, color=color)
    embed.set_footer(text=FOOTER)
    return embed


async def safe_send(channel, embed: Embed):
    for attempt in range(3):
        try:
            return await channel.send(embed=embed)
        except discord.Forbidden:
            print(f"[ERROR] Brak uprawnień do wysłania na kanał #{channel.name}")
            return None
        except Exception as e:
            print(f"[WARN] Próba {attempt + 1}/3 nie powiodła się: {e}")
            await asyncio.sleep(2)
    print("[ERROR] Nie można wysłać embeda po 3 próbach.")
    return None


async def safe_send_dm(member, embed: Embed):
    try:
        await member.send(embed=embed)
        print(f"[DM] Wysłano powitanie do {member.name}")
    except discord.Forbidden:
        print(f"[DM] {member.name} ma zablokowane DM — pominięto")
    except Exception as e:
        print(f"[DM] Błąd DM do {member.name}: {e}")


async def update_member_counter(guild: discord.Guild):
    """Aktualizuje nazwę kanału z licznikiem członków."""
    channel = guild.get_channel(COUNTER_CHANNEL_ID)
    if not channel:
        return
    new_name = f"👥 Members: {guild.member_count:,}"
    try:
        if channel.name != new_name:
            await channel.edit(name=new_name, reason="Member count update")
            print(f"[COUNTER] Zaktualizowano: {new_name}")
    except discord.Forbidden:
        print("[ERROR] Brak uprawnień do zmiany nazwy kanału licznika")
    except Exception as e:
        print(f"[ERROR] Licznik: {e}")


# ==========================
# DZIENNY RAPORT (pętla)
# ==========================
async def daily_report_loop():
    """Czeka do północy UTC i wysyła raport każdego dnia."""
    global daily_joins, daily_leaves
    await client.wait_until_ready()

    while not client.is_closed():
        now = datetime.now(timezone.utc)
        # Czas do następnej północy UTC
        midnight = (now + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        wait_seconds = (midnight - now).total_seconds()
        await asyncio.sleep(wait_seconds)

        guild = discord.utils.get(client.guilds, id=GUILD_ID)
        if not guild:
            continue

        report_ch = guild.get_channel(REPORT_CHANNEL_ID)
        if not report_ch:
            print("[REPORT] Kanał raportu nie znaleziony")
            daily_joins = 0
            daily_leaves = 0
            continue

        date_str = datetime.now(timezone.utc).strftime("%d.%m.%Y")
        embed = make_embed(
            title="📊 Dzienny Raport — DarkNet Alliance",
            description=(
                f"📅 **{date_str}**\n\n"
                f"📥 Dołączyło: **{daily_joins}** osób\n"
                f"📤 Wyszło: **{daily_leaves}** osób\n"
                f"👥 Aktualnie na serwerze: **{guild.member_count:,}**\n"
                f"📈 Bilans: **{'+' if daily_joins >= daily_leaves else ''}{daily_joins - daily_leaves}**"
            ),
            color=0x7289da
        )
        await safe_send(report_ch, embed)
        print(f"[REPORT] Raport wysłany: +{daily_joins} / -{daily_leaves}")

        # Reset liczników
        daily_joins = 0
        daily_leaves = 0


# ==========================
# BOT READY
# ==========================
@client.event
async def on_ready():
    print(f"🟢 [DarkNet Alliance] Online jako: {client.user}")
    print(f"🕒 Start: {now_utc()}")

    guild = discord.utils.get(client.guilds, id=GUILD_ID)
    if not guild:
        print(f"❌ BŁĄD: Nie znaleziono serwera o ID {GUILD_ID}!")
        return

    log_ch      = guild.get_channel(LOG_CHANNEL_ID)
    welcome_ch  = guild.get_channel(WELCOME_CHANNEL_ID)
    report_ch   = guild.get_channel(REPORT_CHANNEL_ID)
    counter_ch  = guild.get_channel(COUNTER_CHANNEL_ID)

    print(f"{'✔️' if log_ch     else '❌'} Log channel:     {'OK' if log_ch     else 'NIE ZNALEZIONO'}")
    print(f"{'✔️' if welcome_ch else '❌'} Welcome channel: {'OK' if welcome_ch else 'NIE ZNALEZIONO'}")
    print(f"{'✔️' if report_ch  else '❌'} Report channel:  {'OK' if report_ch  else 'NIE ZNALEZIONO'}")
    print(f"{'✔️' if counter_ch else '❌'} Counter channel: {'OK' if counter_ch else 'NIE ZNALEZIONO'}")

    # Ustaw licznik od razu po starcie
    await update_member_counter(guild)

    # Uruchom pętlę dziennego raportu
    asyncio.ensure_future(daily_report_loop())

    print("Bot w pełni uruchomiony.")


# ==========================
# MEMBER JOIN
# ==========================
@client.event
async def on_member_join(member):
    global daily_joins
    daily_joins += 1

    guild  = member.guild
    age    = account_age_days(member)
    color  = join_color(member)

    # Znacznik nowego konta
    age_warning = ""
    if age < NEW_ACCOUNT_DAYS:
        age_warning = f"\n⚠️ **NOWE KONTO** — {age} dni!"

    # Znacznik powrotu
    returning = ""
    if member.id in left_members:
        returning = "\n🔄 **Użytkownik wrócił na serwer!**"
        left_members.discard(member.id)

    # --- Auto-rola ---
    if AUTO_ROLE_ID:
        role = guild.get_role(AUTO_ROLE_ID)
        if role and guild.me.top_role > role:
            try:
                await member.add_roles(role, reason="Auto-role on join")
                print(f"[AUTO-ROLE] Nadano {role.name} → {member.name}")
            except Exception as e:
                print(f"[ERROR] Auto-role: {e}")

    # --- Embed powitalny ---
    welcome_ch = guild.get_channel(WELCOME_CHANNEL_ID)
    if welcome_ch:
        embed = make_embed(
            title="❄ New Arrival at DarkNet Alliance",
            description=(
                f"✨ Witaj {member.mention}!\n"
                f"👥 Jesteś **{guild.member_count:,}** członkiem serwera\n"
                f"🗓️ Wiek konta: **{age} dni**\n"
                f"🕒 {now_utc()}"
                f"{age_warning}{returning}"
            ),
            color=color
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await safe_send(welcome_ch, embed)

    # --- Log (jeśli inny kanał) ---
    log_ch = guild.get_channel(LOG_CHANNEL_ID)
    if log_ch and log_ch.id != WELCOME_CHANNEL_ID:
        log_embed = make_embed(
            title="📥 Member Joined",
            description=(
                f"👤 {member.mention} (`{member.id}`)\n"
                f"🗓️ Konto ma {age} dni\n"
                f"🕒 {now_utc()}"
                f"{age_warning}{returning}"
            ),
            color=color
        )
        log_embed.set_thumbnail(url=member.display_avatar.url)
        await safe_send(log_ch, log_embed)

    # --- DM powitalne ---
    if SEND_WELCOME_DM:
        dm_embed = make_embed(
            title="👋 Witaj w DarkNet Alliance!",
            description=(
                "Miło Cię widzieć na serwerze!\n"
                "Sprawdź kanały z rolami i zasadami.\n\n"
                "*DarkNet Alliance AI System*"
            ),
            color=0x00aaff
        )
        await safe_send_dm(member, dm_embed)

    # Zaktualizuj licznik
    await update_member_counter(guild)

    print(f"[JOIN] {member} dołączył (konto: {age}d, kolor: {'🔴' if age < 7 else '🟠' if age < 30 else '🟢'}). Łącznie: {guild.member_count}")


# ==========================
# MEMBER LEAVE
# ==========================
@client.event
async def on_member_remove(member):
    global daily_leaves
    daily_leaves += 1

    guild = member.guild

    # Zapamiętaj że wyszedł (do wykrywania powrotów)
    left_members.add(member.id)

    log_ch = guild.get_channel(LOG_CHANNEL_ID)
    if log_ch:
        embed = make_embed(
            title="❄ Departure from DarkNet Alliance",
            description=(
                f"✨ {member.mention} opuścił serwer\n"
                f"🕒 {now_utc()}"
            ),
            color=0xaa0000
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await safe_send(log_ch, embed)

    # Zaktualizuj licznik
    await update_member_counter(guild)

    print(f"[LEAVE] {member} wyszedł.")


# ==========================
# REACTION ROLES — DODAJ
# ==========================
@client.event
async def on_raw_reaction_add(payload):
    if payload.channel_id != ROLE_CHANNEL_ID:
        return
    if payload.message_id not in ROLE_MESSAGE_IDS:
        return

    emoji = str(payload.emoji)
    if emoji not in EMOJI_ROLE_MAP:
        return

    guild  = client.get_guild(payload.guild_id)
    member = guild.get_member(payload.user_id)
    if not member or member.bot:
        return

    role = guild.get_role(EMOJI_ROLE_MAP[emoji])
    if not role:
        return
    if guild.me.top_role <= role:
        print(f"[WARN] Hierarchia — nie mogę nadać {role.name}")
        return
    try:
        await member.add_roles(role, reason="Reaction role")
        print(f"[ROLE+] {role.name} → {member.name}")
    except Exception as e:
        print(f"[ERROR] add_roles: {e}")


# ==========================
# REACTION ROLES — USUŃ
# ==========================
@client.event
async def on_raw_reaction_remove(payload):
    if payload.channel_id != ROLE_CHANNEL_ID:
        return
    if payload.message_id not in ROLE_MESSAGE_IDS:
        return

    emoji = str(payload.emoji)
    if emoji not in EMOJI_ROLE_MAP:
        return

    guild  = client.get_guild(payload.guild_id)
    member = guild.get_member(payload.user_id)
    if not member or member.bot:
        return

    role = guild.get_role(EMOJI_ROLE_MAP[emoji])
    if not role:
        return
    if guild.me.top_role <= role:
        print(f"[WARN] Hierarchia — nie mogę usunąć {role.name}")
        return
    try:
        await member.remove_roles(role, reason="Reaction role removed")
        print(f"[ROLE-] {role.name} ← {member.name}")
    except Exception as e:
        print(f"[ERROR] remove_roles: {e}")


# ==========================
# ERROR HANDLER
# ==========================
@client.event
async def on_error(event, *args, **kwargs):
    import traceback
    print(f"[ERROR] Błąd w evencie: {event}")
    traceback.print_exc()


# ==========================
# URUCHOMIENIE
# ==========================
if __name__ == "__main__":
    if not TOKEN:
        print("❌ BŁĄD: DISCORD_TOKEN nie ustawiony w .env!")
        exit(1)
    print("🚀 Uruchamianie DarkNet Alliance Bot...")
    client.run(TOKEN)
