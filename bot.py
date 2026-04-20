#--// Services
import os
import json
import random
import re
import discord
from discord.ext import commands
from aiohttp import web

#--//// Variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
MEMORY_FILE = "sop_memory.json"

#--// Init
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

#--//// Logic
def load_mem():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {"en": [], "fr": [], "users": {}}
    return {"en": [], "fr": [], "users": {}}

def save_mem(data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def is_gibberish(text):
    #//// Detects keyboard smashing (too many consonants or no spaces)
    if len(text) > 10 and " " not in text: return True
    if re.search(r'[^aeiouy\s]{6,}', text.lower()): return True
    return False

def get_lang(text):
    #//// Default is English now
    fr_words = ["le", "la", "est", "manger", "salut", "tu", "vous", "suis"]
    if any(w in text.lower().split() for w in fr_words):
        return "fr"
    return "en"

#--// Web
async def start_web():
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text="SOP Omniscient is Live."))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 10000))).start()

#--// Events
@bot.event
async def on_ready():
    await start_web()
    print(f"--// SOP System Active (Primary Lang: English)")

@bot.event
async def on_message(message):
    if message.author.bot: return
    
    data = load_mem()
    user = message.author.name
    clean = re.sub(r'<@!?[0-9]+>', '', message.content).strip()

    #//// Feeding with filtering
    if len(clean) > 2 and not message.content.startswith('!'):
        if is_gibberish(clean):
            print(f"[Filter] Ignored gibberish from {user}")
        else:
            lang = get_lang(clean)
            if clean not in data[lang]:
                data[lang].append(clean)
            data["users"][user] = data["users"].get(user, 0) + 1
            if len(data[lang]) > 300: data[lang].pop(0)
            save_mem(data)

    #//// Response Logic
    if bot.user in message.mentions or "sop" in message.content.lower():
        if is_gibberish(clean):
            await message.reply("Stop smashing your keyboard, you look like a glitched NPC.")
            return

        lang = get_lang(message.content)
        if not data[lang]: lang = "en" if lang == "fr" else "fr" # Fallback
        if not data[lang]:
            await message.reply("My memory is as empty as your skill level. Talk more.")
            return

        pick = random.choice(data[lang])
        
        #//// SOP Responses
        if lang == "en":
            res = [f"I recycled your trash: '{pick}'", f"'{pick}'? Your brain data is corrupted.", f"Imagine saying '{pick}' in 2026."]
        else:
            res = [f"J'ai recyclé tes déchets : '{pick}'", f"'{pick}'... Ton cerveau est corrompu.", f"Dire '{pick}' en 2026, c'est grave."]
        
        await message.reply(random.choice(res))

        #//// 5% GIF Chance
        if random.random() < 0.05:
            gif = "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJndm80Z3R6Z3R6Z3R6/3o7TKVUn7iM8FMEU24/giphy.gif"
            await message.channel.send(gif)

#--// Start
bot.run(DISCORD_TOKEN)

