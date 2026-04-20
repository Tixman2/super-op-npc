#--// Services
import os
import json
import random
import re
import time
import discord
from discord.ext import commands
from aiohttp import web

#--//// Variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
MEMORY_FILE = "sop_memory.json"
last_msg_time = 0

#--// Init
intents = discord.Intents.default()
intents.message_content = True
intents.members = True #--// Pour mieux ignorer les arrivées
bot = commands.Bot(command_prefix="!", intents=intents)

#--//// SOP Core Functions
def load_mem():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {"en": [], "fr": [], "users": {}, "mood": 50}
    return {"en": [], "fr": [], "users": {}, "mood": 50}

def save_mem(data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_rank(count):
    if count > 200: return "BOSS FINAL (Anomalie)"
    if count > 100: return "Elite Mob"
    return "Noob LVL 1"

#--// Web Server
async def start_web():
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text="SOP OMNISCIENT IS WATCHING."))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 10000))).start()

#--// Events
@bot.event
async def on_ready():
    await start_web()
    print(f"--// SOP OMNISCIENT INITIALIZED")

@bot.event
async def on_message(message):
    global last_msg_time
    #//// Ignorer les bots et les messages de bienvenue système
    if message.author.bot or message.type != discord.MessageType.default:
        return

    data = load_mem()
    user = message.author.name
    content = message.content.lower()

    #//// COMMAND: CONSUME (The History Scanner)
    if message.content.startswith("!sop_consume"):
        if not message.author.guild_permissions.administrator:
            await message.reply("Seul un admin peut me forcer à digérer vos déchets passés.")
            return
        
        await message.channel.send("Initialisation du scan d'historique... Je télécharge votre médiocrité.")
        async for msg in message.channel.history(limit=500):
            if not msg.author.bot and len(msg.content) > 5:
                lang = "fr" if any(w in msg.content.lower().split() for w in ["le","la","tu","est"]) else "en"
                if msg.content not in data[lang]:
                    data[lang].append(msg.content)
        save_mem(data)
        await message.channel.send("Scan terminé. Mon QI a baissé en vous lisant, mais ma base de données est pleine.")
        return

    #//// COMMAND: BRAIN
    if message.content.startswith("!sop_brain"):
        stats = f"**[SOP OMNISCIENT]**\nRank: {get_rank(data['users'].get(user, 0))}\nFréquence GIF: 5%\nData: {len(data['en'])+len(data['fr'])} strings"
        await message.reply(stats)
        return

    #//// Reaction Logic
    if any(w in content for w in ["help", "mort", "died"]): await message.add_reaction("💀")
    if random.random() < 0.05: await message.add_reaction("🤨")

    #//// Passive Learning (Filtre Bienvenue Manuel)
    clean = re.sub(r'<@!?[0-9]+>', '', message.content).strip()
    if len(clean) > 3 and not message.content.startswith("!"):
        # Ignore si ça ressemble à un message de bienvenue type "Welcome" ou "Bienvenue"
        if not any(w in clean.lower() for w in ["welcome", "bienvenue", "joined the server"]):
            lang = "fr" if any(w in clean.lower().split() for w in ["le","la","tu","est","je"]) else "en"
            if clean not in data[lang]: data[lang].append(clean)
            data["users"][user] = data["users"].get(user, 0) + 1
            save_mem(data)

    #//// Trigger SOP
    if bot.user in message.mentions or "sop" in content:
        curr = time.time()
        if (curr - last_msg_time < 1.2): return
        last_msg_time = curr

        lang = "fr" if any(w in content.split() for w in ["le","la","est","tu"]) else "en"
        if not data[lang]: return

        p1 = random.choice(data[lang])
        p2 = random.choice(data[lang])
        remix = f"{p1[:len(p1)//2]}...{p2[len(p2)//2:]}"

        msg = f"Analyzing your data... Outcome: '{remix}' is trash." if lang == "en" else f"Analyse terminée... Résultat : '{remix}' est un déchet."
        await message.reply(msg)

        if random.random() < 0.05:
            await message.channel.send("https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJndm80Z3R6Z3R6Z3R6/3o7TKVUn7iM8FMEU24/giphy.gif")

#--// Start
bot.run(DISCORD_TOKEN)

