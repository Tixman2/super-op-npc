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
            return {"fr": [], "en": [], "users": {}}
    return {"fr": [], "en": [], "users": {}}

def save_mem(data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def is_english(text):
    en_words = ["the", "you", "and", "have", "with", "what", "is", "are"]
    return any(w in text.lower().split() for w in en_words)

#--// Web
async def start_web():
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text="SOP is watching."))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 10000))).start()

#--// Events
@bot.event
async def on_ready():
    await start_web()
    print(f"--// SOP System Ready")

@bot.event
async def on_message(message):
    if message.author.bot: return
    
    data = load_mem()
    user = message.author.name
    
    #//// Command to see the brain
    if message.content == "!sop_brain":
        stats = f"**[SOP BRAIN STATE]**\n- Phrases FR: {len(data['fr'])}\n- Phrases EN: {len(data['en'])}\n- Top User: {user} ({data['users'].get(user, 0)} msgs)"
        await message.reply(stats)
        return

    #//// Cleaning (Ignore usernames and mentions)
    clean = re.sub(r'<@!?[0-9]+>', '', message.content).strip()
    
    #//// Feeding
    if len(clean) > 3 and not message.content.startswith('!'):
        lang = "en" if is_english(clean) else "fr"
        if clean not in data[lang]:
            data[lang].append(clean)
        
        data["users"][user] = data["users"].get(user, 0) + 1
        if len(data[lang]) > 200: data[lang].pop(0)
        save_mem(data)

    #//// Reaction
    if bot.user in message.mentions or "sop" in message.content.lower():
        async with message.channel.typing():
            lang = "en" if is_english(message.content) else "fr"
            if not data[lang]:
                await message.reply("Memory empty. Feed me.")
                return

            pick = random.choice(data[lang])
            
            #//// English vs French responses
            if lang == "en":
                options = [f"I found this trash: '{pick}'", f"Analyzing... you said '{pick}'? Lame.", f"Your data is corrupted: {pick}"]
            else:
                options = [f"Donnée récupérée : '{pick}'... C'est nul.", f"Tu as vraiment écrit '{pick}' ?", f"Remodelage de : {pick}"]
            
            await message.reply(random.choice(options))

            #//// Ultra rare GIF (5% chance to avoid spam)
            if random.random() < 0.05:
                gifs = ["https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJndm80Z3R6Z3R6Z3R6/l41lTjJpS9nZzG6pG/giphy.gif", "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJndm80Z3R6Z3R6Z3R6/3o7TKVUn7iM8FMEU24/giphy.gif"]
                await message.channel.send(random.choice(gifs))

#--// Start
bot.run(DISCORD_TOKEN)
