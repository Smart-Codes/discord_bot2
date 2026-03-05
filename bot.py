
import asyncio
import datetime
import logging
import os

import discord
import requests
from discord import Client
from dotenv import load_dotenv

load_dotenv()
DISCORD_USER_TOKEN   = os.getenv("DISCORD_USER_TOKEN")
TELEGRAM_BOT_TOKEN   = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID     = os.getenv("TELEGRAM_CHAT_ID")


# Leave empty list [] to monitor EVERY server the account is in
MONITORED_SERVERS = []   # ← you already set this — good


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("DiscordMonitorPoC")


def send_to_telegram(text: str) -> None:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.error("Telegram config missing – check .env file")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_notification": False
    }

    try:
        resp = requests.post(url, data=payload, timeout=10)
        resp.raise_for_status()
        logger.info("Telegram alert sent successfully")
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")


def build_join_message(member: discord.Member, guild: discord.Guild) -> str:
    now_str = datetime.datetime.now().strftime("%b %d, %Y, %I:%M:%S %p")
    
    username = f"{member.name}#{member.discriminator}" if member.discriminator != "0" else member.name

    return (
        f"**New Member Joined!**\n"
        f"Username: {username}\n"
        f"Server: {guild.name}\n"
        f"• Time: {now_str}"
    )


client = Client()

@client.event
async def on_ready() -> None:
    guilds_count = len(client.guilds)
    logger.info(f"Logged in as {client.user} (ID {client.user.id})")
    logger.info(f"→ Monitoring {guilds_count} server{'s' if guilds_count != 1 else ''}")
    if MONITORED_SERVERS:
        logger.info(f"→ Limited to: {', '.join(MONITORED_SERVERS)}")
    else:
        logger.info("→ Monitoring ALL servers this account is in")

@client.event
async def on_member_join(member: discord.Member) -> None:
    guild = member.guild

    if MONITORED_SERVERS and guild.name not in MONITORED_SERVERS:
        return

    if member.bot or member.id == client.user.id:
        return

    alert = build_join_message(member, guild)
    logger.info(f"Join detected → {alert}")

    
    send_to_telegram(alert)


async def main() -> None:
    if not DISCORD_USER_TOKEN:
        logger.critical("DISCORD_USER_TOKEN missing in .env – cannot start")
        return

    print("""
    ╔════════════════════════════════════════════════════╗
    ║                         DISCORD                    ║
    ║                                                    ║
    ╚════════════════════════════════════════════════════╝
    """)

    try:
        await client.start(DISCORD_USER_TOKEN)  
    except discord.LoginFailure:
        logger.critical("Invalid or expired user token – re-extract from browser dev tools")
    except Exception as e:
        logger.exception(f"Startup / runtime error: {e}")
    finally:
        await client.close()
        logger.info("Client closed")

if __name__ == "__main__":
    asyncio.run(main())