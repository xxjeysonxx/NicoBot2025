import os
import asyncio
from datetime import datetime, timedelta, timezone

import discord
from discord import Intents
from dotenv import load_dotenv

# ---------- CARGAR VARIABLES DESDE .env ----------
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
TARGET_CHANNEL_ID = int(os.getenv("TARGET_CHANNEL_ID"))
MOD_LOG_CHANNEL_ID = os.getenv("MOD_LOG_CHANNEL_ID")
# Eliminamos ACTION y MUTE_DURATION_DAYS porque siempre ban
# --------------------------------------------------

# ---------- CONFIG INTENTS ----------
intents = Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
client = discord.Client(intents=intents)

# ---------- UTILS ----------
def utc_now():
    return datetime.now(timezone.utc)

async def mod_log(guild: discord.Guild, text: str):
    if not MOD_LOG_CHANNEL_ID:
        print("[MOD LOG]", text)
        return
    try:
        cid = int(MOD_LOG_CHANNEL_ID)
        ch = guild.get_channel(cid) or await guild.fetch_channel(cid)
        await ch.send(text)
    except Exception as e:
        print("[MOD LOG ERROR]", e)
        print("[MOD LOG]", text)

# ---------- EVENTOS ----------
@client.event
async def on_ready():
    print(f"✅ Conectado como {client.user} (id: {client.user.id})")
    print(f"✅ Protegiendo canal trampa: {TARGET_CHANNEL_ID}")

@client.event
async def on_message(message: discord.Message):
    # Ignorar si no es el canal trampa o si es un bot
    if message.channel.id != TARGET_CHANNEL_ID:
        return
    if message.author.bot:
        return

    guild = message.guild
    member = message.author

    # 1) Borra el mensaje
    try:
        await message.delete()
    except Exception:
        pass

    # 2) Borra los últimos mensajes de 24h del mismo autor en este canal
    cutoff = utc_now() - timedelta(days=1)
    deleted_count = 0
    async for msg in message.channel.history(limit=500, after=cutoff):
        if msg.author.id == member.id:
            try:
                await msg.delete()
                deleted_count += 1
            except:
                pass

    # 3) Banea inmediatamente al usuario
    action_results = []
    try:
        await guild.ban(member, reason="Envió mensaje en canal trampa", delete_message_days=0)
        action_results.append("Baneado inmediatamente")
    except Exception as e:
        action_results.append(f"Fallo ban: {e}")

    # 4) Log
    log_text = (
        f"a new spammer appears\n"
        f"- Usuario: {member} ({member.id})\n"
        f"- Mensajes eliminados (24h): {deleted_count}\n"
        f"- Acciones: {' | '.join(action_results)}"
    )
    await mod_log(guild, log_text)

    # 5) Intentar DM
    try:
        await member.send(
            "Has enviado un mensaje en un canal prohibido. Se aplicó un ban inmediato."
        )
    except:
        pass

# ---------- RUN ----------
if __name__ == "__main__":
    if not BOT_TOKEN:
        print("ERROR: No hay BOT_TOKEN en el .env.")
    else:
        client.run(BOT_TOKEN)
