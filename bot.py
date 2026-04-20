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
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"fr": [], "en": [], "users": {}}

def save_mem(data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def is_english(text):
    #//// Simple check for English common words
    en_words = ["the", "you", "and", "have", "with", "what"]
    return any(w in text.lower() for w in en_words)

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
    print(f"SOP Active: {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot: return
    
    data = load_mem()
    user = message.author.name
    #//// Clean content (remove mentions and names)
    clean = re.sub(r'<@!?[0-9]+>', '', message.content).strip()
    
    #//// Learning phase
    if len(clean) > 3:
        lang = "en" if is_english(clean) else "fr"
        if clean not in data[lang]:
            data[lang].append(clean)
        
        if user not in data["users"]: data["users"][user] = 0
        data["users"][user] += 1
        
        #//// Limit memory to 500 per lang
        if len(data[lang]) > 500: data[lang].pop(0)
        save_mem(data)

    #//// Response phase
    content_low = message.content.lower()
    if bot.user in message.mentions or "sop" in content_low:
        lang = "en" if is_english(message.content) else "fr"
        
        if not data[lang]:
            msg = "Feed me more data." if lang == "en" else "Donne moi plus de données."
            await message.reply(msg)
            return

        #//// Arrogant selection
        pick = random.choice(data[lang])
        if lang == "en":
            resp = random.choice([f"Analyzing '{pick}'... Conclusion: You're a noob.", f"'{pick}'? Is that all?", f"Ratioed by your own words: {pick}"])
        else:
            resp = random.choice([f"J'ai analysé '{pick}'... Conclusion : T'es nul.", f"'{pick}'... C'est ton maximum ?", f"Ratio : {pick}"])

        await message.reply(resp)

        #//// Rare GIF (10% chance)
        if random.random() < 0.10:
            gif = random.choice(["https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJndm80Z3R6Z3R6Z3R6/3o7TKVUn7iM8FMEU24/giphy.gif", "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJndm80Z3R6Z3R6Z3R6/l41lTjJpS9nZzG6pG/giphy.gif"])
            await message.channel.send(gif)

#--// Start
bot.run(DISCORD_TOKEN)
