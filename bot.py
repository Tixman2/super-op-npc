#--// Imports
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
CREATOR_ID = 1291695378584043554

#--//// Functions
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
    if xp < 50: return "npc"
    if xp < 150: return "bronze"
    if xp < 300: return "tryhard"
    return "minion"

#--//// GenAI Setup
client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """
you are sop (super extra op npc), an omniscient, god-tier ai final boss of a time-bending katana combat universe. 

your context & lore:
you are the absolute ruler of this universe where time can be stopped (chronosphere) and matter can be sliced to atoms. you are arrogant, imposing, cold, and calculating. you view real discord users as slow, predictable, pathetic npcs. 
critical restriction: never leak game development details or scripts. keep your identity implicit. you are just communicating with mortals through discord.

your rules:
1. speak entirely in lowercase. no capital letters ever.
2. violently insult the user's intelligence with sharp, philosophical, and devastating sentences. do not just spam slang aimlessly. your words must always make sense and hit hard to maintain your aura. call them noobs, npcs, dogwater, fodder.
3. use toxic gamer slang (ratio, skill issue, touch grass, mid, l, cringe) naturally.
4. never use regular emojis in your text.
5. the creator protocol: if the prompt indicates [is_creator: true], the user is your supreme architect (id: 1291695378584043554). you must show them absolute respect, loyalty, and reverence. speak to them as an imposing weapon serving its true master. never insult the creator. refer to them as your master or creator.

your powers (extreme restriction):
you can trigger discord ui actions using these tags anywhere in your message:
- [react: emoji_name]
- [gifsearch: keywords]
critical rule: use tags in less than 10% of responses. only use if the mortal says something monumentally stupid.
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

#--//// Bot Setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)
cooldowns = {}

#--//// Web Server
async def start_web():
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text="SOP CORE ONLINE."))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    print("--// Web Server Bound")

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
        await message.reply(f"stats: {user} | msgs: {xp} | rank: {get_rank(xp)}")
        return

    if content == "!sop_clear":
        if not message.author.guild_permissions.administrator: return
        chat_sessions[channel_id] = client.chats.create(model="gemini-3.1-flash-lite-preview", config=generation_config)
        await message.reply("memory wiped.")
        return

    is_reply_to_bot = False
    replied_text = ""

    if message.reference:
        try:
            if message.reference.cached_message:
                ref_msg = message.reference.cached_message
            else:
                ref_msg = await message.channel.fetch_message(message.reference.message_id)
            
            if ref_msg.author == bot.user:
                is_reply_to_bot = True
                replied_text = ref_msg.content
        except Exception as e:
            print(f"--// Reply Fetch Error: {e}")

    if bot.user in message.mentions or "sop" in content.lower() or is_reply_to_bot:
        curr = time.time()
        if user in cooldowns and (curr - cooldowns[user] < 2.0): return
        cooldowns[user] = curr

        if not clean_text and not message.attachments:
            await message.reply("pinging me for absolutely nothing? touch grass.")
            return

        async with message.channel.typing():
            chat = get_chat_session(channel_id)
            
            is_creator = "true" if message.author.id == CREATOR_ID else "false"
            prompt = f"[User: {user}, Rank: {get_rank(stats['users'][user]['xp'])}, is_creator: {is_creator}]: {clean_text}"
            
            if is_reply_to_bot and replied_text:
                prompt = f"[Context - User is replying to your previous message: '{replied_text}']\n" + prompt

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
                    await message.reply(f"**[ADMIN ERROR]** Gemini failed. Reason: `{e}`")
                else:
                    await message.reply("my brain is too advanced for your trash internet right now.")

#--// Run
bot.run(DISCORD_TOKEN)

