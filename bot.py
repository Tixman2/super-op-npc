#--// Services
import os, json, random, re, time, asyncio, discord
from discord.ext import commands, tasks
from aiohttp import web

#--//// Variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
MEMORY_FILE = "sop_human_core.json"

#--// Engine
class ToxicHumanNLP:
    def __init__(self):
        self.stop_words = ["the", "is", "at", "which", "on", "a", "an", "and", "of", "to", "in", "for", "it", "that", "this"]
        
    def extract_keywords(self, text):
        words = re.findall(r'\b\w+\b', text.lower())
        return [w for w in words if w not in self.stop_words and len(w) > 3]

    def get_intent(self, text):
        t = text.lower()
        if "?" in t or "how" in t or "what" in t or "why" in t or "when" in t: return "question"
        if "help" in t or "pls" in t or "please" in t or "sorry" in t or "my bad" in t: return "plead"
        if "fuck" in t or "shit" in t or "stupid" in t or "hate" in t or "trash" in t: return "hostile"
        return "statement"

    def mimic_player_speech(self, words_list, length=5):
        if len(words_list) < 20: return ""
        chain = {}
        for i in range(len(words_list)-1):
            w1, w2 = words_list[i], words_list[i+1]
            if w1 not in chain: chain[w1] = []
            chain[w1].append(w2)
        
        curr = random.choice(list(chain.keys()))
        res = [curr]
        for _ in range(length):
            if curr in chain and chain[curr]:
                curr = random.choice(chain[curr])
                res.append(curr)
            else: break
        return " ".join(res)

#--// Memory
class PlayerMemory:
    def __init__(self, filepath):
        self.filepath = filepath
        self.data = self.load()
        
    def load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except: pass
        return {"vocab": [], "users": {}}

    def save(self):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def ingest(self, user, content, nlp):
        if user not in self.data["users"]:
            self.data["users"][user] = {"msg_count": 0, "deaths": 0}
        
        self.data["users"][user]["msg_count"] += 1
        words = nlp.extract_keywords(content)
        if words:
            self.data["vocab"].extend(words)
            if len(self.data["vocab"]) > 15000:
                self.data["vocab"] = self.data["vocab"][-15000:]
            self.save()

#--// Init
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

nlp = ToxicHumanNLP()
brain = PlayerMemory(MEMORY_FILE)
cooldowns = {}
processed_msgs = []

#--//// Logic
def build_human_response(user, content):
    intent = nlp.get_intent(content)
    keywords = nlp.extract_keywords(content)
    
    topic = random.choice(keywords) if keywords else ""
    player_clone = nlp.mimic_player_speech(brain.data["vocab"], random.randint(3, 6))
    
    # Human toxic slang
    if intent == "question":
        res = [
            f"why u asking me bro? google is free.",
            f"bro really asked about {topic}. literal skill issue.",
            f"figure it out urself man im not ur guide.",
            f"who cares honestly."
        ]
    elif intent == "plead":
        res = [
            f"stop crying bro it's embarrassing.",
            f"apology rejected. uninstall.",
            f"begging wont make u better at the game.",
            f"cringe. just get good."
        ]
    elif intent == "hostile":
        res = [
            f"stay mad {user}.",
            f"bro is fuming over {topic} rn 💀",
            f"cry more. ur literally dogwater.",
            f"ur mad cuz u got carried."
        ]
    else:
        res = [
            f"who asked tho?",
            f"bro thought he cooked saying that.",
            f"im not reading all that but u still suck.",
            f"literally nobody cares {user}.",
            f"u talk too much for someone with negative stats.",
            f"bro's whole personality is {topic}. L.",
            f"didn't ask + ratio + ur bad."
        ]
        
    final_reply = random.choice(res)
    
    # Sometimes it mocks how players speak on the server
    if player_clone and random.random() < 0.2:
        final_reply = f"u sound like '{player_clone}'. {final_reply}"
        
    return final_reply.lower()

#--// Web
async def start_web():
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text="SOP Human Simulation Active."))
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, '0.0.0.0', int(os.environ.get("PORT", 10000))).start()

#--// Events
@bot.event
async def on_ready():
    await start_web()
    print("SOP HUMAN NPC ONLINE")

@bot.event
async def on_message(message):
    if message.author.bot or message.type != discord.MessageType.default: return

    if message.id in processed_msgs: return
    processed_msgs.append(message.id)
    if len(processed_msgs) > 100: processed_msgs.pop(0)

    user = message.author.name
    content = message.content
    user_id = message.author.id
    clean_text = re.sub(r'<@!?[0-9]+>', '', content).strip()

    #//// COMMAND: CONSUME (Global Server Scan)
    if content == "!sop_consume":
        if not message.author.guild_permissions.administrator:
            await message.reply("u dont have admin perms bro. quiet.")
            return
        
        await message.reply("scanning the whole server rn. give me a sec.")
        scanned = 0
        for channel in message.guild.text_channels:
            try:
                async for msg in channel.history(limit=300):
                    if not msg.author.bot and len(msg.content) > 3:
                        clean_old = re.sub(r'<@!?[0-9]+>', '', msg.content).strip()
                        brain.ingest(msg.author.name, clean_old, nlp)
                        scanned += 1
            except: continue
        
        await message.reply(f"done. read {scanned} messages. u guys are all terrible.")
        return

    #//// Passive Learning
    if len(clean_text) > 2 and not content.startswith("!"):
        brain.ingest(user, clean_text, nlp)

    #//// Trigger
    if bot.user in message.mentions or "sop" in content.lower():
        if clean_text == "" or clean_text.lower() == "sop":
            await message.add_reaction("🤡")
            return

        curr = time.time()
        if user_id in cooldowns and (curr - cooldowns[user_id] < 3.0): return
        cooldowns[user_id] = curr

        async with message.channel.typing():
            await asyncio.sleep(random.uniform(1.0, 2.0))
            reply = build_human_response(user, clean_text)
            await message.reply(reply)

#--// Run
bot.run(DISCORD_TOKEN)

