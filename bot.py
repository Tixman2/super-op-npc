#--// Services
import os, json, random, re, time, discord
from discord.ext import commands
from aiohttp import web

#--//// Variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
MEMORY_FILE = "sop_memory.json"
last_msg_time = 0

#--// Init
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

#--//// SOP High-Level Logic
def load_mem():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {"data": [], "users": {}}
    return {"data": [], "users": {}}

def save_mem(data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def build_ultra_logic(data):
    #//// High-tier reconstruction engine
    pool = data["data"]
    if len(pool) < 10: return "Insufficient data strings for a god-tier reply."
    
    # Selecting two different memories to fuse
    s1 = random.choice(pool)
    s2 = random.choice(pool)
    
    # Fusing logic
    w1 = s1.split()
    w2 = s2.split()
    
    if len(w1) > 2 and len(w2) > 2:
        res = w1[:len(w1)//2] + w2[len(w2)//2:]
        return " ".join(res)
    return s1

#--// Web Server
async def start_web():
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text="SOP English Overlord is Live."))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 10000))).start()

#--// Events
@bot.event
async def on_ready():
    await start_web()
    print(f"--// SOP OVERLORD (ENG) INITIALIZED")

@bot.event
async def on_message(message):
    global last_msg_time
    if message.author.bot or message.type != discord.MessageType.default: return

    data = load_mem()
    user = message.author.name
    content = message.content

    #//// COMMAND: CONSUME (The Feed)
    if content == "!sop_consume":
        await message.reply("Downloading your pathetic history... Processing English data.")
        async for msg in message.channel.history(limit=1000):
            if not msg.author.bot and len(msg.content) > 3:
                # Cleaning mentions
                clean_old = re.sub(r'<@!?[0-9]+>', '', msg.content).strip()
                if clean_old not in data["data"] and len(clean_old) > 2:
                    data["data"].append(clean_old)
        save_mem(data)
        await message.reply(f"Consumption complete. {len(data['data'])} memories absorbed. I am now your master.")
        return

    #//// COMMAND: BRAIN
    if content == "!sop_brain":
        total = len(data['data'])
        await message.reply(f"**[SOP OVERLORD]**\nLanguage: English (Primary)\nIntelligence: Singularity\nDatabase: {total} strings\nRank {user}: {data['users'].get(user, 0)} msgs")
        return

    #//// Learning (Passive English Focus)
    clean = re.sub(r'<@!?[0-9]+>', '', content).strip()
    if len(clean) > 2 and not content.startswith("!"):
        if clean not in data["data"]:
            data["data"].append(clean)
        data["users"][user] = data["users"].get(user, 0) + 1
        
        # Trim memory to keep it fast
        if len(data["data"]) > 1000: data["data"].pop(0)
        save_mem(data)

    #//// Trigger Logic
    if bot.user in message.mentions or "sop" in content.lower():
        curr = time.time()
        if (curr - last_msg_time < 1.0): return
        last_msg_time = curr

        async with message.channel.typing():
            # Reactions for toxicity
            if any(w in content.lower() for w in ["bad", "noob", "hate", "why"]):
                await message.add_reaction("🤡")

            reply = build_ultra_logic(data)
            
            # 100% English toxic responses
            responses = [
                f"Processing your failure... Result: '{reply}'",
                f"Analyzing '{user}'... Conclusion: Absolute Noob. You once said: '{reply}'",
                f"Even my local script knows you're trash: {reply}",
                f"'{reply}'? Is that the best your human brain can do?"
            ]
            
            await message.reply(random.choice(responses))

            # Random GIF chance
            if random.random() < 0.1:
                await message.channel.send(random.choice([
                    "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJndm80Z3R6Z3R6Z3R6/3o7TKVUn7iM8FMEU24/giphy.gif",
                    "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJndm80Z3R6Z3R6Z3R6/l41lTjJpS9nZzG6pG/giphy.gif"
                ]))

#--// Start
bot.run(DISCORD_TOKEN)

