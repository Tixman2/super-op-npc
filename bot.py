#--// Services
import os, json, random, re, time, asyncio, discord
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
        except: return {"data": [], "nemesis": "", "stats": {}}
    return {"data": [], "nemesis": "", "stats": {}}

def save_mem(data):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def gen_markov(data_list):
    #//// Creates fake sentences using server vocabulary
    if len(data_list) < 10: return None
    words = []
    for sentence in data_list[-200:]:
        words.extend(sentence.split())
    if len(words) < 5: return None
    
    start_word = random.choice(words)
    res = [start_word]
    for _ in range(random.randint(3, 8)):
        try:
            idx = words.index(res[-1])
            if idx + 1 < len(words):
                res.append(words[idx + 1])
            else:
                res.append(random.choice(words))
        except:
            res.append(random.choice(words))
    return " ".join(res)

def get_smart_reply(data, user, content):
    low_content = content.lower()
    
    #//// Contextual analysis
    if "?" in low_content:
        return f"why u asking me '{content}'? figure it out urself."
    if "sorry" in low_content or "my bad" in low_content:
        return "apology rejected. uninstall the game."
    if "lol" in low_content or "lmao" in low_content:
        return "nothing is funny here. ur stats are a joke tho."
        
    generated = gen_markov(data["data"])
    pool = data["data"]
    quote = random.choice(pool) if pool else "trash"
    
    roasts = [
        f"bro really thinks he is him. u literally said '{quote}'.",
        f"ur brain works like this: '{generated}'. absolute bot.",
        f"i analyzed ur chat history. u talk like '{generated}'. pathetic.",
        f"can everyone report {user} for saying '{quote}'?",
        f"skill issue. go back to the tutorial.",
        f"stop typing. every time u speak u sound like '{generated}'."
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

    #//// Stats & Nemesis tracker
    if user not in data["stats"]: data["stats"][user] = 0
    data["stats"][user] += 1
    
    nemesis = max(data["stats"], key=data["stats"].get)
    data["nemesis"] = nemesis

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

        async with message.channel.typing():
            await asyncio.sleep(random.uniform(1.5, 3.0))
            
            reply = get_smart_reply(data, user, content)
            if user == data["nemesis"] and random.random() < 0.3:
                reply = f"oh look, it's my biggest fan {user}. " + reply

            await message.reply(reply)

            if random.random() < 0.05:
                await message.channel.send("https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJndm80Z3R6Z3R6Z3R6/3o7TKVUn7iM8FMEU24/giphy.gif")

#--// Start
bot.run(DISCORD_TOKEN)

