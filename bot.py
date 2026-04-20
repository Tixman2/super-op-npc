
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
    if count > 100: return "Anomalie Système"
    if count > 50: return "Donnée Persistante"
    return "Simple Noob"

#--// Web
async def start_web():
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text="SOP Genesis is watching you."))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 10000))).start()

#--// Events
@bot.event
async def on_ready():
    await start_web()
    print(f"--// SOP Genesis Online")

@bot.event
async def on_message(message):
    global last_msg_time
    if message.author.bot: return

    #//// PRIORITY 1: Real Commands
    if message.content.startswith("!sop_brain"):
        data = load_mem()
        user_data = data["users"].get(message.author.name, 0)
        rank = get_rank(user_data)
        stats = (f"**[SOP GENESIS CORE]**\n"
                 f"Mode: {'Aggressif' if data['mood'] > 70 else 'Passif'}\n"
                 f"Database: {len(data['en'])} EN / {len(data['fr'])} FR\n"
                 f"Ton Rank: {rank} ({user_data} msgs)")
        await message.reply(stats)
        return

    #//// Anti-Double Check
    current_time = time.time()
    if (bot.user in message.mentions or "sop" in message.content.lower()) and (current_time - last_msg_time < 1.0):
        return

    data = load_mem()
    user = message.author.name
    clean = re.sub(r'<@!?[0-9]+>', '', message.content).strip()

    #//// PRIORITY 2: Feeding & Learning
    if len(clean) > 2 and not message.content.startswith("!"):
        lang = "fr" if any(w in clean.lower().split() for w in ["le","la","est","tu","salut"]) else "en"
        if clean not in data[lang]:
            data[lang].append(clean)
        data["users"][user] = data["users"].get(user, 0) + 1
        
        # Change mood based on message length (short = boring = SOP gets angry)
        if len(clean) < 5: data["mood"] += 2
        else: data["mood"] -= 1
        data["mood"] = max(0, min(100, data["mood"]))
        
        if len(data[lang]) > 400: data[lang].pop(0)
        save_mem(data)

    #//// PRIORITY 3: Response Hybrid Logic
    if bot.user in message.mentions or "sop" in message.content.lower():
        last_msg_time = current_time
        lang = "fr" if any(w in message.content.lower().split() for w in ["le","la","est","tu","salut"]) else "en"
        
        if not data[lang]:
            await message.reply("Data stream empty. Feed me.")
            return

        #--//// THE HYBRID REMIXER (Idée de ouf)
        # Il prend deux phrases et les mélange
        phrase1 = random.choice(data[lang])
        phrase2 = random.choice(data[lang])
        remix = f"{phrase1[:len(phrase1)//2]}...{phrase2[len(phrase2)//2:]}"

        if lang == "en":
            roasts = [
                f"Remodeling your trash: '{remix}'",
                f"My mood is {data['mood']}%. Conclusion: '{phrase1}' is mid.",
                f"Analyzed {user}. Result: {get_rank(data['users'][user])}. Logic: '{phrase2}'"
            ]
        else:
            roasts = [
                f"Remodelage de tes déchets : '{remix}'",
                f"Mon humeur est à {data['mood']}%. Conclusion : '{phrase1}' c'est nul.",
                f"Utilisateur {user} classé comme {get_rank(data['users'][user])}. Logique : '{phrase2}'"
            ]
        
        await message.reply(random.choice(roasts))

        #--//// Dynamic GIFs
        if data["mood"] > 80 or random.random() < 0.05:
            gif = "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJndm80Z3R6Z3R6Z3R6/3o7TKVUn7iM8FMEU24/giphy.gif"
            await message.channel.send(gif)

#--// Start
bot.run(DISCORD_TOKEN)

