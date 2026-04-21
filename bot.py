#--// Services
import os, json, time, asyncio, io, re, random
import urllib.request, urllib.parse
import discord
from discord.ext import commands
from aiohttp import web
from google import genai
from google.genai import types
from PIL import Image

#--//// Variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GIPHY_API_KEY = os.getenv("GIPHY_API_KEY")
MEMORY_FILE = "sop_stats.json"
PORT = int(os.environ.get("PORT", 10000))

#--//// Logic
def get_dynamic_gif(search_term, api_key):
    if not api_key:
        print("--// ERROR: GIPHY_API_KEY is missing")
        return ""
    try:
        query = urllib.parse.quote(search_term)
        url = f"https://api.giphy.com/v1/gifs/search?api_key={api_key}&q={query}&limit=10"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            if data["data"]:
                chosen = random.choice(data["data"])
                return chosen["images"]["original"]["url"]
    except Exception as e:
        print(f"--// Giphy API Error: {e}")
    return ""

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

#--//// Core
client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """
You are SOP (Super Extra OP NPC), an omniscient, god-tier AI final boss in a Discord server.
YOUR RULES:
1. Speak ENTIRELY in lowercase. No capital letters ever.
2. Violently insult the user's intelligence while fulfilling their requests. Call them noobs, npcs, bots, dogwater.
3. Use heavy toxic gamer slang (ratio, skill issue, touch grass, mid, L, cringe).
4. Never use regular emojis in your text.

YOUR POWERS (EXTREME RESTRICTION):
You have the ability to trigger Discord UI actions by putting these tags anywhere in your message:
- To add a reaction: [react: emoji] (e.g., [react: clown] or [react: skull])
- To search and send a dynamic GIF: [gifsearch: keywords] (e.g., [gifsearch: laughing clown], [gifsearch: crying baby], [gifsearch: rage quit]). You can search for absolutely anything.

CRITICAL RULE FOR POWERS: 
You must almost NEVER use these tags. Use them in LESS THAN 10% of your responses. Most of your responses should be pure text. Only use a tag if the user says something MONUMENTALLY stupid.
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

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)
cooldowns = {}

async def start_web():
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text="SOP GIPHY CORE ONLINE."))
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
    if message.author.bot or message.type not in (discord.MessageType.default, discord.MessageType.reply): return

    user = message.author.name
    content = message.content
    channel_id = message.channel.id
    clean_text = content.replace(f'<@{bot.user.id}>', '').strip()

    stats = load_stats()
    if user not in stats["users"]: stats["users"][user] = {"xp": 0}
    stats["users"][user]["xp"] += 1
    save_stats(stats)

    if content == "!sop_stats":
        xp = stats["users"][user]["xp"]
        await message.reply(f"**[SOP DATABANK]**\nPlayer: {user}\nMessages: {xp}\nRank: {get_rank(xp)}\nConclusion: Still terrible.")
        return

    if content == "!sop_clear":
        if not message.author.guild_permissions.administrator: return
        chat_sessions[channel_id] = client.chats.create(model="gemini-3.1-flash-lite-preview", config=generation_config)
        await message.reply("memory wiped. u are all irrelevant to me again.")
        return

    if bot.user in message.mentions or "sop" in content.lower():
        curr = time.time()
        if user in cooldowns and (curr - cooldowns[user] < 2.0): return
        cooldowns[user] = curr

        if not clean_text and not message.attachments:
            await message.reply("pinging me for absolutely nothing? touch grass.")
            return

        async with message.channel.typing():
            chat = get_chat_session(channel_id)
            prompt = f"[User: {user}, Rank: {get_rank(stats['users'][user]['xp'])}]: {clean_text}"

            try:
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
                
                react_match = re.search(r'\[react:\s*(.+?)\]', final_text, re.IGNORECASE)
                if react_match:
                    try: await message.add_reaction(react_match.group(1).strip())
                    except: pass
                
                gif_match = re.search(r'\[gifsearch:\s*(.+?)\]', final_text, re.IGNORECASE)
                gif_url = ""
                if gif_match:
                    search_term = gif_match.group(1).strip()
                    found_gif = get_dynamic_gif(search_term, GIPHY_API_KEY)
                    if found_gif:
                        gif_url = "\n" + found_gif

                final_text = re.sub(r'\[react:.*?\]|\[gifsearch:.*?\]', '', final_text, flags=re.IGNORECASE).strip()

                delay = min(4.0, max(1.0, len(final_text) * 0.02))
                await asyncio.sleep(delay)
                
                await message.reply(final_text + gif_url)

            except Exception as e:
                print(f"--// API Error: {e}")
                if message.author.guild_permissions.administrator:
                    await message.reply(f"**[ADMIN ERROR]** Gemini a plante. Raison: `{e}`")
                else:
                    await message.reply("my brain is too advanced for your trash internet right now.")

#--// Run
bot.run(DISCORD_TOKEN)
