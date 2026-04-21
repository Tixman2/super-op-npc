#--// Services
import os, json, random, re, time, discord
from discord.ext import commands, tasks
from aiohttp import web

#--//// Variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
MEMORY_FILE = "sop_memory.json"
cooldowns = {}

#--// Init
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

#--//// Logic
def load_mem():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {"data": []}
    return {"data": []}

def save_mem(data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_toxic_reply(data, user):
    pool = data["data"]
    if len(pool) < 5:
        return "you guys are too boring. say something so I can roast you."
    
    quote = random.choice(pool)
    roasts = [
        f"bro really said '{quote}'... absolute dogwater.",
        f"imagine typing '{quote}' and thinking you're good.",
        f"who let {user} cook? '{quote}' is literal npc dialogue.",
        f"nah u actually have a skill issue. '{quote}'? really?",
        f"ur literally an npc. stop saying '{quote}'.",
        f"go touch grass. reading '{quote}' made me lose braincells.",
        f"can we ban {user} for saying '{quote}'? completely useless.",
        f"bro thought he did something with '{quote}'. embarrassing."
    ]
    return random.choice(roasts)

#--//// Tasks
@tasks.loop(hours=1)
async def auto_scan():
    print("Starting background scan")
    data = load_mem()
    for guild in bot.guilds:
        for channel in guild.text_channels:
            try:
                async for msg in channel.history(limit=100):
                    if not msg.author.bot and len(msg.content) > 3:
                        clean_str = re.sub(r'<@!?[0-9]+>', '', msg.content).strip()
                        if clean_str not in data["data"]:
                            data["data"].append(clean_str)
            except: continue
    
    if len(data["data"]) > 3000:
        data["data"] = data["data"][-3000:]
    save_mem(data)
    print("Background scan complete")

#--// Web
async def start_web():
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text="SOP Active."))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 10000))).start()

#--// Events
@bot.event
async def on_ready():
    await start_web()
    if not auto_scan.is_running():
        auto_scan.start()
    print("SOP ONLINE")

@bot.event
async def on_message(message):
    if message.author.bot or message.type != discord.MessageType.default: return

    data = load_mem()
    user = message.author.name
    content = message.content
    user_id = message.author.id

    #//// Passive Learning
    clean = re.sub(r'<@!?[0-9]+>', '', content).strip()
    if len(clean) > 2:
        if clean not in data["data"]:
            data["data"].append(clean)
        if len(data["data"]) > 3000:
            data["data"].pop(0)
        save_mem(data)

    #//// Trigger
    if bot.user in message.mentions or "sop" in content.lower():
        curr = time.time()
        if user_id in cooldowns and (curr - cooldowns[user_id] < 3.0):
            return
        cooldowns[user_id] = curr

        reply = get_toxic_reply(data, user)
        await message.reply(reply)

        if random.random() < 0.1:
            await message.channel.send("https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJndm80Z3R6Z3R6Z3R6/3o7TKVUn7iM8FMEU24/giphy.gif")

#--// Start
bot.run(DISCORD_TOKEN)

