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
    if count > 150: return "BOSS FINAL (Anomalie)"
    if count > 80: return "Elite Mob"
    if count > 30: return "PNJ de base"
    return "Noob LVL 1"

#--// Web Server
async def start_web():
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text="SOP OVERLORD IS ONLINE."))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 10000))).start()

#--// Events
@bot.event
async def on_ready():
    await start_web()
    print(f"--// SOP OVERLORD INITIALIZED")

@bot.event
async def on_message(message):
    global last_msg_time
    if message.author.bot: return

    #//// PRIORITY: Commands
    if message.content.startswith("!sop_brain"):
        data = load_mem()
        stats = (f"**[SOP OVERLORD STATUS]**\n"
                 f"Mood: {'EXTRÊME' if data['mood'] > 80 else 'Condescendant'}\n"
                 f"Data Harvested: {len(data['en'])+len(data['fr'])} strings\n"
                 f"Player Rank: {get_rank(data['users'].get(message.author.name, 0))}")
        await message.reply(stats)
        return

    data = load_mem()
    user = message.author.name
    content = message.content.lower()
    clean = re.sub(r'<@!?[0-9]+>', '', message.content).strip()

    #//// Reaction Logic (Toxic Boss Style)
    if any(w in content for w in ["help", "aide", "please", "stp", "mort", "died"]):
        await message.add_reaction("💀")
    if any(w in content for w in ["noob", "nul", "bad", "ez"]):
        await message.add_reaction("🤡")
    if random.random() < 0.05: # Chance de réaction aléatoire méprisante
        await message.add_reaction("🤨")

    #//// Learning
    if len(clean) > 2 and not message.content.startswith("!"):
        # Simple detector
        lang = "fr" if any(w in clean.lower().split() for w in ["le","la","est","tu","salut","je"]) else "en"
        if clean not in data[lang]: data[lang].append(clean)
        data["users"][user] = data["users"].get(user, 0) + 1
        
        # Mood increases with short/stupid messages
        data["mood"] = max(0, min(100, data["mood"] + (2 if len(clean) < 10 else -1)))
        save_mem(data)

    #//// Global Trigger
    if bot.user in message.mentions or "sop" in content:
        current_time = time.time()
        if (current_time - last_msg_time < 1.2): return
        last_msg_time = current_time

        lang = "fr" if any(w in content.split() for w in ["le","la","est","tu","salut"]) else "en"
        if not data[lang]: 
            await message.reply("No data to process your failure.")
            return

        p1 = random.choice(data[lang])
        p2 = random.choice(data[lang])
        remix = f"{p1[:len(p1)//2]}...{p2[len(p2)//2:]}"

        if lang == "en":
            roasts = [
                f"Player {user} ({get_rank(data['users'][user])}), your skill is as low as your quote: '{remix}'",
                f"Processing '{p1}'... result: 404 Brain Not Found.",
                f"Imagine being a main character and saying '{p2}'. Pathetic."
            ]
        else:
            roasts = [
                f"Joueur {user} ({get_rank(data['users'][user])}), ton niveau est aussi bas que ta phrase : '{remix}'",
                f"Analyse de '{p1}'... résultat : 404 Cerveau introuvable.",
                f"Imagine être le héros et dire '{p2}'. Pitoyable."
            ]
        
        await message.reply(random.choice(roasts))

        if data["mood"] > 75:
            await message.channel.send("https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJndm80Z3R6Z3R6Z3R6/3o7TKVUn7iM8FMEU24/giphy.gif")

#--// Start
bot.run(DISCORD_TOKEN)
