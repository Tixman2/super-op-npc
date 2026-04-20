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

#--//// SOP Logic
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
    pool = data["data"]
    if len(pool) < 10: return "Insufficient data for my core logic."
    s1, s2 = random.sample(pool, 2)
    w1, w2 = s1.split(), s2.split()
    if len(w1) > 2 and len(w2) > 2:
        return " ".join(w1[:len(w1)//2] + w2[len(w2)//2:])
    return s1

#--// Web
async def start_web():
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text="SOP Server-Wide Overlord."))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 10000))).start()

#--// Events
@bot.event
async def on_ready():
    await start_web()
    print(f"--// SOP OVERLORD GLOBAL ACTIVE")

@bot.event
async def on_message(message):
    global last_msg_time
    if message.author.bot or message.type != discord.MessageType.default: return

    data = load_mem()
    user = message.author.name
    content = message.content

    #//// COMMAND: CONSUME (Global Scan - Admin Only)
    if content == "!sop_consume":
        if not message.author.guild_permissions.administrator:
            await message.reply("Error: Insufficient clearance. You are not my master.")
            return
        
        await message.reply("INITIATING SERVER-WIDE DATA HARVEST. Scanning all sectors...")
        
        total_scanned = 0
        #--//// Scans every channel in the server
        for channel in message.guild.text_channels:
            try:
                async for msg in channel.history(limit=200): # Scan 200 msg per channel
                    if not msg.author.bot and len(msg.content) > 3:
                        clean_str = re.sub(r'<@!?[0-9]+>', '', msg.content).strip()
                        if clean_str not in data["data"] and len(clean_str) > 2:
                            data["data"].append(clean_str)
                            total_scanned += 1
            except: continue # Skip channels with no access
            
        save_mem(data)
        await message.channel.send(f"HARVEST COMPLETE. {total_scanned} memories added to my core. I now know everything.")
        return

    #//// COMMAND: BRAIN
    if content == "!sop_brain":
        await message.reply(f"**[SOP OMNISCIENT]**\nStrings: {len(data['data'])}\nPlayer: {user}\nRank: {data['users'].get(user, 0)} msgs")
        return

    #//// Learning
    clean = re.sub(r'<@!?[0-9]+>', '', content).strip()
    if len(clean) > 2 and not content.startswith("!"):
        if clean not in data["data"]: data["data"].append(clean)
        data["users"][user] = data["users"].get(user, 0) + 1
        if len(data["data"]) > 2000: data["data"].pop(0)
        save_mem(data)

    #//// Trigger
    if bot.user in message.mentions or "sop" in content.lower():
        curr = time.time()
        if (curr - last_msg_time < 1.0): return
        last_msg_time = curr

        reply = build_ultra_logic(data)
        res = [
            f"Analyzing your trash: '{reply}'",
            f"Result for {user}: Garbage data found. Evidence: '{reply}'",
            f"My logic dictates that you are a noob. Statement: '{reply}'"
        ]
        await message.reply(random.choice(res))
        if random.random() < 0.1:
            await message.channel.send("https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJndm80Z3R6Z3R6Z3R6/3o7TKVUn7iM8FMEU24/giphy.gif")

#--// Start
bot.run(DISCORD_TOKEN)

