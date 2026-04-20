#--// Services
import os
import json
import random
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

#--//// SOP Local Brain Logic
def load_mem():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {"vocabulary": [], "user_stats": {}}
    return {"vocabulary": [], "user_stats": {}}

def save_mem(data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

#--// Web Server for Render
async def handle_web(request):
    return web.Response(text="SOP Omniscient is feeding locally.")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle_web)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 10000)))
    await site.start()

#--// Events
@bot.event
async def on_ready():
    await start_web_server()
    print(f"[System] SOP Local Brain Active as {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot: return

    data = load_mem()
    user = message.author.name
    content = message.content.strip()

    #//// SOP Consumes the message
    if len(content) > 2:
        data["vocabulary"].append(content)
        #//// Tracking user activity
        if user not in data["user_stats"]:
            data["user_stats"][user] = 0
        data["user_stats"][user] += 1
        
        #//// Keep memory size manageable
        if len(data["vocabulary"]) > 1000:
            data["vocabulary"].pop(0)
        save_mem(data)

    #//// Response Logic (No API, just Script)
    if bot.user in message.mentions or "sop" in content.lower():
        if not data["vocabulary"]:
            await message.reply("Je n'ai pas encore assez de données pour vous remodeler. Parlez plus.")
            return

        #//// Construct a reply from learned data
        learned_phrase = random.choice(data["vocabulary"])
        roasts = [
            f"Je t'ai entendu dire '{learned_phrase}', c'est pathétique.",
            f"'{learned_phrase}'... C'est tout ce que ton cerveau peut produire ?",
            f"Tu parles trop, {user}. J'ai déjà analysé tes {data['user_stats'][user]} messages.",
            f"Remodelage en cours... Résultat : '{learned_phrase}' est une erreur système.",
            "Ton existence est un skill issue."
        ]
        
        reply = random.choice(roasts)
        
        #//// GIF Logic (Randomly based on keywords)
        if random.random() < 0.3: # 30% de chance d'envoyer un GIF
            tags = ["ez", "ratio", "toxic", "noob", "laugh"]
            tag = random.choice(tags)
            await message.reply(reply)
            await message.channel.send(f"https://tenor.com/search/{tag}-gif")
        else:
            await message.reply(reply)

#--// Run
bot.run(DISCORD_TOKEN)
