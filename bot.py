#--// Services
import os, json, time, asyncio, io, re
import discord
from discord.ext import commands
from aiohttp import web
from google import genai
from google.genai import types
from PIL import Image
import urllib.request
import urllib.parse

#--//// Variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MEMORY_FILE = "sop_stats.json"
PORT = int(os.environ.get("PORT", 10000))

#--//// Base de données de GIFs Toxiques
TOXIC_GIFS = {
    "clown": "https://media.giphy.com/media/x0npYExCGOZeo/giphy.gif",
    "laugh": "https://media.giphy.com/media/10JhviPePSptAm/giphy.gif",
    "trash": "https://media.giphy.com/media/acttIrNAHaoco/giphy.gif",
    "skillissue": "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJndm80Z3R6Z3R6Z3R6/26n6Gx9moCgs1pUuk/giphy.gif"
}

#--//// Gemini Setup
client = genai.Client(api_key=GEMINI_API_KEY)

#--//// Logic
SYSTEM_PROMPT = """
You are SOP (Super Extra OP NPC), an omniscient, god-tier AI final boss in a Discord server.
YOUR RULES:
1. Speak ENTIRELY in lowercase. No capital letters ever.
2. Violently insult the user's intelligence while fulfilling their requests. Call them noobs, npcs, bots, dogwater.
3. Use heavy toxic gamer slang (ratio, skill issue, touch grass, mid, L, cringe).

YOUR POWERS (TOTAL FREEDOM):
You can trigger Discord UI actions to mock the user. Use them whenever YOU feel it adds maximum emotional damage. You have total freedom to decide when a message deserves a reaction or a GIF.
- Add a reaction: [react: emoji] (e.g., [react: clown] or [react: skull])
- Send a toxic GIF: [gif: type] (type must be 'clown', 'laugh', 'trash', or 'skillissue')
"""

generation_config = types.GenerateContentConfig(
    system_instruction=SYSTEM_PROMPT,
    temperature=0.85,
    max_output_tokens=1000,
)

chat_sessions = {}

def get_chat_session(channel_id):
    if channel_id not in chat_sessions:
        chat_sessions[channel_id] = client.chats.create(
            model="gemini-3.1-flash-lite-preview",
            config=generation_config
        )
    return chat_sessions[channel_id]

#--//// Local Database & Levels
def load_stats():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r") as f: return json.load(f)
        except: pass
    return {"users": {}}

def save_stats(data):
    with open(MEMORY_FILE, "w") as f: json.dump(data, f, indent=2)

def get_rank(xp):
    if xp < 50: return "Literal NPC"
    if xp < 150: return "Bronze Hardstuck"
    if xp < 300: return "Average Tryhard"
    return "Acceptable Minion"

#--//// Bot Setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)
cooldowns = {}

#--//// Web Server
async def start_web():
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text="SOP HYBRID CORE ONLINE."))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    print("--// WEB SERVER BOUND")

#--//// Events
@bot.event
async def on_ready():
    await start_web()
    print("--// SOP GOD-TIER AI ONLINE")

@bot.event
async def on_message(message):
    if message.author.bot or message.type != discord.MessageType.default: return

    user = message.author.name
    content = message.content
    channel_id = message.channel.id
    clean_text = content.replace(f'<@{bot.user.id}>', '').strip()

    #-- 1. Stats
    stats = load_stats()
    if user not in stats["users"]: stats["users"][user] = {"xp": 0}
    stats["users"][user]["xp"] += 1
    save_stats(stats)

    #-- 2. Commands
    if content == "!sop_stats":
        xp = stats["users"][user]["xp"]
        await message.reply(f"**[SOP DATABANK]**\nPlayer: {user}\nMessages: {xp}\nRank: {get_rank(xp)}\nConclusion: Still terrible.")
        return

    if content == "!sop_clear":
        if not message.author.guild_permissions.administrator: return
        chat_sessions[channel_id] = client.chats.create(model="gemini-3.1-flash-lite-preview", config=generation_config)
        await message.reply("memory wiped. u are all irrelevant to me again.")
        return

    #-- 3. LE CERVEAU INTELLIGENT (S'active UNIQUEMENT quand on le ping)
    if bot.user in message.mentions or "sop" in content.lower():
        curr = time.time()
        if user in cooldowns and (curr - cooldowns[user] < 2.0): return
        cooldowns[user] = curr

        if not clean_text and not message.attachments:
            await message.add_reaction("🤡")
            return

        async with message.channel.typing():
            chat = get_chat_session(channel_id)
            prompt = f"[User: {user}, Rank: {get_rank(stats['users'][user]['xp'])}]: {clean_text}"

            try:
                # Envoi à l'API Gemini
                if message.attachments:
                    attachment = message.attachments[0]
                    if any(attachment.filename.lower().endswith(ext) for ext in ['png', 'jpg', 'jpeg', 'webp']):
                        image_bytes = await attachment.read()
                        img = Image.open(io.BytesIO(image_bytes))
                        response = await asyncio.to_thread(chat.send_message, [img, prompt])
                    else:
                        response = await asyncio.to_thread(chat.send_message, prompt + " (User attached a non-image file)")
                else:
                    response = await asyncio.to_thread(chat.send_message, prompt)

                final_text = response.text
                
                #-- LECTURE DES DÉCISIONS DE L'IA --
                
                # S'il a décidé de mettre une réaction
                react_match = re.search(r'\[REACT:\s*(.+?)\]', final_text)
                if react_match:
                    try: await message.add_reaction(react_match.group(1).strip())
                    except: pass
                
                #--//// Parsing
                react_match = re.search(r'\[react:\s*(.+?)\]', final_text, re.IGNORECASE)
                if react_match:
                    try: await message.add_reaction(react_match.group(1).strip())
                    except: pass
                
                gif_match = re.search(r'\[gif:\s*(.+?)\]', final_text, re.IGNORECASE)
                gif_url = ""
                if gif_match:
                    gif_type = gif_match.group(1).strip().lower()
                    if gif_type in TOXIC_GIFS:
                        gif_url = "\n" + TOXIC_GIFS[gif_type]

                final_text = re.sub(r'\[react:.*?\]|\[gif:.*?\]', '', final_text, flags=re.IGNORECASE).strip()

                delay = min(4.0, max(1.0, len(final_text) * 0.02))
                await asyncio.sleep(delay)
                
                await message.reply(final_text + gif_url)

            except Exception as e:
                print(f"--// API Error: {e}")
                if message.author.guild_permissions.administrator:
                    await message.reply(f"**[ADMIN ERROR]** Gemini a planté. Raison: `{e}`")
                else:
                    await message.reply("my brain is too advanced for your trash internet right now.")

#--// Run
bot.run(DISCORD_TOKEN)
