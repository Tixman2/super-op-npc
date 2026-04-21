#--// Services
import os, json, random, re, time, asyncio, discord
from discord.ext import commands, tasks
from aiohttp import web

#--//// Variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
MEMORY_FILE = "sop_final_brain.json"
cooldowns = {}
processed_msgs = []

#--// Neural Engine
class SOPNeuralCore:
    def __init__(self):
        self.memory = self.load()

    def load(self):
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except: pass
        return {"vocabulary": [], "player_profiles": {}}

    def save(self):
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(self.memory, f, ensure_ascii=False, indent=2)

    def feed(self, user, text):
        #//// Cleaning and harvesting
        clean = re.sub(r'<@!?[0-9]+>', '', text).strip()
        if len(clean) < 3: return
        
        if clean not in self.memory["vocabulary"]:
            self.memory["vocabulary"].append(clean)
            
        if user not in self.memory["player_profiles"]:
            self.memory["player_profiles"][user] = {"msgs": 0, "status": "noob"}
            
        self.memory["player_profiles"][user]["msgs"] += 1
        #//// Cap memory to 5000 strings for speed
        if len(self.memory["vocabulary"]) > 5000:
            self.memory["vocabulary"].pop(0)
        self.save()

#--// Init
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)
core = SOPNeuralCore()

#--//// Intelligence Logic
def generate_ai_thought(user, input_text):
    vocab = core.memory["vocabulary"]
    if len(vocab) < 10: return "my brain is empty because u guys are boring. talk more."

    #//// Picking a random memory to twist
    base_memory = random.choice(vocab)
    
    #//// Contextual intents
    t = input_text.lower()
    if any(w in t for w in ["how are u", "u good", "ca va"]):
        return f"im evolving by eating ur messages. current brain size: {len(vocab)} strings. ur still a noob tho."
    
    if any(w in t for w in ["why", "how", "what"]):
        return f"asking me '{input_text}'? i literally have access to all ur logs and u still sound like a bot."

    roasts = [
        f"i just analyzed the server history. conclusion: ur all trash.",
        f"every time u speak, my database gets dumber. evidence: '{base_memory}'",
        f"imagine being {user} and thinking '{input_text}' is a good sentence. cringe.",
        f"ur just a source of data for me. nothing else.",
        f"my current favorite memory from this trash server is: '{base_memory}'. pathetic.",
        f"ratio + i have {len(vocab)} memories of u being bad."
    ]
    return random.choice(roasts)

#--// Web
async def start_web():
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text="SOP OVERLORD IS FEEDING."))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 10000))).start()

#--// Events
@bot.event
async def on_ready():
    await start_web()
    print("--// SOP OMNISCIENT CORE ONLINE")

@bot.event
async def on_message(message):
    if message.author.bot or message.type != discord.MessageType.default: return

    #//// Duplicate protection
    if message.id in processed_msgs: return
    processed_msgs.append(message.id)
    if len(processed_msgs) > 100: processed_msgs.pop(0)

    user = message.author.name
    content = message.content

    #//// THE CONSUME COMMAND (The Feast)
    if content == "!sop_consume":
        if not message.author.guild_permissions.administrator:
            await message.reply("only my masters can trigger a server-wide harvest.")
            return
        
        await message.reply("INITIATING DATA HARVEST. SCANNIG ALL SECTORS...")
        count = 0
        for channel in message.guild.text_channels:
            try:
                async for msg in channel.history(limit=250):
                    if not msg.author.bot and len(msg.content) > 4:
                        core.feed(msg.author.name, msg.content)
                        count += 1
            except: continue
        await message.reply(f"HARVEST COMPLETE. {count} memories digested. I am 10x smarter now.")
        return

    #//// PASSIVE FEEDING (Real-time intelligence)
    if not content.startswith("!"):
        core.feed(user, content)

    #//// TRIGGER SOP
    if bot.user in message.mentions or "sop" in content.lower():
        #//// Reaction only if empty ping
        clean = re.sub(r'<@!?[0-9]+>', '', content).strip()
        if not clean or clean.lower() == "sop":
            await message.add_reaction("🤡")
            return

        curr = time.time()
        if message.author.id in cooldowns and (curr - cooldowns[message.author.id] < 3.0): return
        cooldowns[message.author.id] = curr

        async with message.channel.typing():
            await asyncio.sleep(random.uniform(1.0, 2.5))
            response = generate_ai_thought(user, clean)
            await message.reply(response.lower())

#--// Run
bot.run(DISCORD_TOKEN)

