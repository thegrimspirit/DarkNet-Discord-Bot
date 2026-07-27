import os
import discord
import asyncio
from datetime import datetime, timezone
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
GUILD_ID          = 1234567890123456789   # <-- ID Twojego serwera
LOG_CHANNEL_ID    = 1317868408171270146   # kanał logów (join/leave)
WELCOME_CHANNEL_ID = 1317868408171270146  # kanał powitalny (może być inny)

# Reaction Roles
ROLE_CHANNEL_ID   = 1448324147024236836
ROLE_MESSAGE_IDS  = [
    1448324524801003591,
    1448324598012842106
]

# Słownik: emoji -> rola ID  (dodaj ile chcesz)
EMOJI_ROLE_MAP = {
    "❄️": 1317873265959633006,
    # "🔥": 1234567890000000001,   # przykład drugiej roli
}

# Auto-rola przy dołączeniu (None = wyłączone)
AUTO_ROLE_ID = None  # np. 1317873265959633006

# Czy wysyłać DM powitalne? True / False
SEND_WELCOME_DM = True

# ==========================
# STAŁE TEKSTOWE
# ==========================
FOOTER = "DarkNet Alliance • AI Monitoring System - Powered by The_Grim_Net • ❄️ Winter Edition"


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
    """Zwraca aktualny czas UTC jako string."""
    return datetime.now(timezone.utc).strftime("%d.%m.%Y %H:%M UTC")


def make_embed(title: str, description: str, color: int) -> Embed:
    embed = Embed(title=title, description=description, color=color)
    embed.set_footer(text=FOOTER)
    return embed


async def safe_send(channel, embed: Embed):
    """Wysyłanie embeda z 3 próbami przy błędzie."""
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
    """Wysyłanie DM — nie crashuje jeśli użytkownik ma zablokowane DM."""
    try:
        await member.send(embed=embed)
        print(f"[DM] Wysłano powitanie do {member.name}")
    except discord.Forbidden:
        print(f"[DM] {member.name} ma zablokowane DM — pominięto")
    except Exception as e:
        print(f"[DM] Błąd wysyłania DM do {member.name}: {e}")


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

    log_ch = guild.get_channel(LOG_CHANNEL_ID)
    welcome_ch = guild.get_channel(WELCOME_CHANNEL_ID)

    print(f"{'✔️' if log_ch else '❌'} Log channel: {'OK' if log_ch else 'NIE ZNALEZIONO'}")
    print(f"{'✔️' if welcome_ch else '❌'} Welcome channel: {'OK' if welcome_ch else 'NIE ZNALEZIONO'}")
    print("Bot w pełni uruchomiony.")


# ==========================
# MEMBER JOIN
# ==========================
@client.event
async def on_member_join(member):
    guild = member.guild
    
    # --- Auto-rola ---
    if AUTO_ROLE_ID:
        role = guild.get_role(AUTO_ROLE_ID)
        if role:
            if guild.me.top_role > role:
                try:
                    await member.add_roles(role, reason="Auto-role on join")
                    print(f"[AUTO-ROLE] Nadano {role.name} → {member.name}")
                except Exception as e:
                    print(f"[ERROR] Auto-role failed: {e}")
            else:
                print(f"[WARN] Bot nie ma uprawnień do nadania roli {role.name} (hierarchia)")
        else:
            print(f"[WARN] Auto-role ID {AUTO_ROLE_ID} nie istnieje")

    # --- Embed na kanale powitalnym ---
    welcome_ch = guild.get_channel(WELCOME_CHANNEL_ID)
    if welcome_ch:
        embed = make_embed(
            title="❄ New Arrival at DarkNet Alliance",
            description=(
                f"✨ Witaj {member.mention}!\n"
                f"👥 Jesteś **{guild.member_count}** członkiem serwera\n"
                f"🕒 {now_utc()}"
            ),
            color=0x00aaff
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await safe_send(welcome_ch, embed)

    # --- Embed do logów ---
    log_ch = guild.get_channel(LOG_CHANNEL_ID)
    if log_ch and log_ch.id != WELCOME_CHANNEL_ID:
        log_embed = make_embed(
            title="📥 Member Joined",
            description=f"👤 {member.mention} (`{member.id}`)\n🕒 {now_utc()}",
            color=0x00ff88
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

    print(f"[JOIN] {member} dołączył. Łącznie: {guild.member_count}")


# ==========================
# MEMBER LEAVE
# ==========================
@client.event
async def on_member_remove(member):
    guild = member.guild
    log_ch = guild.get_channel(LOG_CHANNEL_ID)
    if not log_ch:
        print("[ERROR] Log channel nie znaleziony")
        return

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

    print(f"[LEAVE] {member} wyszedł.")


# ==========================
# REACTION ROLES — DODAJ ROLĘ
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

    guild = client.get_guild(payload.guild_id)
    member = guild.get_member(payload.user_id)

    if not member or member.bot:
        return

    role_id = EMOJI_ROLE_MAP[emoji]
    role = guild.get_role(role_id)
    if not role:
        print(f"[ERROR] Rola {role_id} nie istnieje!")
        return

    if guild.me.top_role <= role:
        print(f"[WARN] Bot nie może nadać roli {role.name} — problem z hierarchią")
        return

    try:
        await member.add_roles(role, reason="Reaction role system")
        print(f"[ROLE+] {role.name} → {member.name}")
    except Exception as e:
        print(f"[ERROR] add_roles: {e}")


# ==========================
# REACTION ROLES — USUŃ ROLĘ
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

    guild = client.get_guild(payload.guild_id)
    member = guild.get_member(payload.user_id)

    if not member or member.bot:
        return

    role_id = EMOJI_ROLE_MAP[emoji]
    role = guild.get_role(role_id)
    if not role:
        return

    if guild.me.top_role <= role:
        print(f"[WARN] Bot nie może usunąć roli {role.name} — problem z hierarchią")
        return

    try:
        await member.remove_roles(role, reason="Reaction role removed")
        print(f"[ROLE-] {role.name} ← {member.name}")
    except Exception as e:
        print(f"[ERROR] remove_roles: {e}")


# ==========================
# GLOBALNY ERROR HANDLER
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
