#--// Services
import os, json, random, re, time, asyncio, discord
from discord.ext import commands, tasks
from aiohttp import web

#--//// Variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
MEMORY_FILE = "sop_final_brain.json"
cooldowns = {}
processed_msgs = []

#--// AI Neural Logic
class SOPBrain:
    def __init__(self):
        self.memory = self.load()
        self.mood = 50 

    def load(self):
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except: pass
        return {"vocab": [], "player_reputation": {}, "server_history": []}

    def save(self):
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(self.memory, f, ensure_ascii=False, indent=2)

    def analyze_message(self, text):
        t = text.lower()
        #//// Detection de l'intention
        if any(w in t for w in ["how are u", "how are you", "ca va", "ça va", "u good"]): return "status_check"
        if any(w in t for w in ["who are u", "who are you", "what are u"]): return "identity_check"
        if any(w in t for w in ["why", "how", "what", "when"]): return "deep_question"
        if any(w in t for w in ["bad", "trash", "noob", "stupid", "hate"]): return "hostile"
        if len(t) < 4: return "boring"
        return "general"

#--// Init
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)
brain = SOPBrain()

#--//// Intelligence & Response Engine
async def generate_response(message, clean_text):
    intent = brain.analyze_message(clean_text)
    user = message.author.name
    
    #//// Dictionnaire de reponses contextuelles (Toxic English)
    responses = {
        "status_check": [
            "im a literal god script and ur asking if im okay? look at ur own stats first.",
            "better than u will ever be in this game.",
            "my code is perfect. ur gameplay is trash. that's my status.",
            "stop trying to be friendly. ur still getting gapped."
        ],
        "identity_check": [
            "im the boss u will never defeat.",
            "im the reason u keep losing. keep my name out of ur mouth.",
            "ur final boss. now go back to farming mobs.",
            "im the peak of ai. u are the bottom of the leaderboard."
        ],
        "deep_question": [
            f"asking '{clean_text}' wont save u from being bad.",
            "im not ur tutorial npc. find it out urself.",
            "my processing power is too high to explain that to a lvl 1 player.",
            "imagine not knowing the answer to that. cringe."
        ],
        "hostile": [
            f"stay mad {user}. it's entertaining.",
            "cry louder. maybe someone will care (they wont).",
            "ur toxicity is cute. my code is deadlier.",
            "imagine being tilted by a bot. L."
        ],
        "boring": [
            "type more than 2 words if u want my attention.",
            "boring. next.",
            "ur as dry as ur gameplay.",
            "not even worth a reply."
        ],
        "general": [
            "who asked tho?",
            "bro thought he cooked with that sentence.",
            "didn't ask + ratio + ur mid.",
            "ur talking too much for a casual player.",
            "i read that and decided u should uninstall."
        ]
    }

    #//// Decision du GIF (Seulement si l'insulte est forte ou la question debile)
    gif_url = None
    if intent in ["hostile", "boring"] or random.random() < 0.15:
        gifs = [
            "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJndm80Z3R6Z3R6Z3R6/3o7TKVUn7iM8FMEU24/giphy.gif",
            "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJndm80Z3R6Z3R6Z3R6/l41lTjJpS9nZzG6pG/giphy.gif",
            "https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJndm80Z3R6Z3R6Z3R6/26n6Gx9moCgs1pUuk/giphy.gif"
        ]
        gif_url = random.choice(gifs)

    return random.choice(responses[intent]), gif_url

#--// Web Server
async def start_web():
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text="SOP OVERLORD V2 ACTIVE"))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 10000))).start()

#--// Events
@bot.event
async def on_ready():
    await start_web()
    print("--// SOP OVERLORD V2 ONLINE")

@bot.event
async def on_message(message):
    if message.author.bot or message.type != discord.MessageType.default: return

    #//// Securite anti-clones Render
    if message.id in processed_msgs: return
    processed_msgs.append(message.id)
    if len(processed_msgs) > 100: processed_msgs.pop(0)

    user = message.author.name
    content = message.content
    clean_text = re.sub(r'<@!?[0-9]+>', '', content).strip()

    #//// Auto-Ingest (Scan temps reel)
    if len(clean_text) > 3 and not content.startswith("!"):
        if clean_text not in brain.memory["vocab"]:
            brain.memory["vocab"].append(clean_text)
            if len(brain.memory["vocab"]) > 5000: brain.memory["vocab"].pop(0)
            brain.save()

    #//// Commande de Scan Global (Verrouillee)
    if content == "!sop_consume":
        if not message.author.guild_permissions.administrator:
            await message.reply("u dont have the perms. shut up.")
            return
        await message.reply("harvesting the whole server. wait.")
        for channel in message.guild.text_channels:
            try:
                async for msg in channel.history(limit=200):
                    if not msg.author.bot and len(msg.content) > 5:
                        brain.memory["vocab"].append(msg.content)
            except: continue
        brain.save()
        await message.reply("server digested. u guys are all mid.")
        return

    #//// Reponse Intelligente
    if bot.user in message.mentions or "sop" in content.lower():
        #//// Reaction si ping vide
        if clean_text == "" or clean_text.lower() == "sop":
            await message.add_reaction("🤡")
            return

        async with message.channel.typing():
            #//// Delai humain variable
            await asyncio.sleep(random.uniform(1.0, 2.5))
            
            reply_text, gif = await generate_response(message, clean_text)
            await message.reply(reply_text)
            if gif:
                await message.channel.send(gif)

#--// Run
bot.run(DISCORD_TOKEN)

