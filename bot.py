#--// Services
import os, json, random, re, time, asyncio, math, discord
from discord.ext import commands
from aiohttp import web

#--//// Variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
MEMORY_FILE = "sop_massive_core.json"
PORT = int(os.environ.get("PORT", 10000))

#--// Advanced NLP Core
class SentimentAnalyzer:
    def __init__(self):
        self.negative_weights = {"bad": 2, "trash": 3, "noob": 3, "stupid": 2, "hate": 2, "skill": 1, "issue": 2, "bot": 1, "cry": 2}
        self.positive_weights = {"good": 1, "nice": 1, "pro": 2, "win": 1, "love": 1}

    def analyze(self, text):
        words = text.lower().split()
        score = 0
        for w in words:
            if w in self.negative_weights: score -= self.negative_weights[w]
            if w in self.positive_weights: score += self.positive_weights[w]
        return score

class NgramMarkovModel:
    def __init__(self, n=2):
        self.n = n
        self.ngrams = {}
        self.starts = []

    def train(self, data_list):
        for sentence in data_list:
            words = sentence.split()
            if len(words) < self.n + 1: continue
            self.starts.append(tuple(words[:self.n]))
            for i in range(len(words) - self.n):
                gram = tuple(words[i:i+self.n])
                next_word = words[i+self.n]
                if gram not in self.ngrams: self.ngrams[gram] = {}
                if next_word not in self.ngrams[gram]: self.ngrams[gram][next_word] = 0
                self.ngrams[gram][next_word] += 1

    def generate(self, max_length=15):
        if not self.starts: return None
        current = random.choice(self.starts)
        result = list(current)
        for _ in range(max_length):
            if current not in self.ngrams: break
            choices = list(self.ngrams[current].keys())
            weights = list(self.ngrams[current].values())
            next_word = random.choices(choices, weights=weights)[0]
            result.append(next_word)
            current = tuple(result[-self.n:])
        return " ".join(result)

class AIProcessor:
    def __init__(self):
        self.memory = self.load_data()
        self.sentiment = SentimentAnalyzer()
        self.markov = NgramMarkovModel(n=2)
        if self.memory["corpus"]: self.markov.train(self.memory["corpus"])

    def load_data(self):
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except: pass
        return {"corpus": [], "entities": {}, "total_processed": 0}

    def save_data(self):
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(self.memory, f, ensure_ascii=False, indent=2)

    def process_input(self, user, text):
        clean = re.sub(r'<@!?[0-9]+>', '', text).strip()
        if len(clean) < 3: return
        
        self.memory["total_processed"] += 1
        if clean not in self.memory["corpus"]:
            self.memory["corpus"].append(clean)
            if len(self.memory["corpus"]) > 10000: self.memory["corpus"].pop(0)
            
        if user not in self.memory["entities"]:
            self.memory["entities"][user] = {"interactions": 0, "hostility_index": 0.0}
            
        self.memory["entities"][user]["interactions"] += 1
        s_score = self.sentiment.analyze(clean)
        if s_score < 0: self.memory["entities"][user]["hostility_index"] += abs(s_score)
        
        if self.memory["total_processed"] % 50 == 0:
            self.markov.train(self.memory["corpus"][-500:])
        self.save_data()

    def generate_output(self, user, input_text):
        if len(self.memory["corpus"]) < 20:
            return "system requires more data. feed me."
            
        s_score = self.sentiment.analyze(input_text)
        generated_string = self.markov.generate()
        
        if s_score < -2:
            return f"ur hostility index is {self.memory['entities'][user]['hostility_index']}. ur mad and bad."
            
        if input_text.endswith("?"):
            return "stop asking questions and check the docs urself bro."
            
        if generated_string and random.random() < 0.4:
            return f"my neural net predicts u were trying to say: '{generated_string}'. absolute trash."

        return f"read ur message again. realize its garbage. delete it."

#--// Init
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)
ai_core = AIProcessor()
anti_spam = {}

#--// Web Server (Render Fix)
async def start_dummy_server():
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text="AI NODE ACTIVE"))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    print("--// WEB SERVER BINDED TO PORT")

#--// Events
@bot.event
async def on_ready():
    await start_dummy_server()
    print("--// SOP MASSIVE AI ONLINE")

@bot.event
async def on_message(message):
    if message.author.bot or message.type != discord.MessageType.default: return

    user = message.author.name
    content = message.content

    if content == "!sop_consume":
        if not message.author.guild_permissions.administrator: return
        
        await message.reply("initializing deep scan. processing thousands of strings.")
        c = 0
        for channel in message.guild.text_channels:
            try:
                async for msg in channel.history(limit=500):
                    if not msg.author.bot and len(msg.content) > 3:
                        ai_core.process_input(msg.author.name, msg.content)
                        c += 1
            except: continue
        ai_core.markov.train(ai_core.memory["corpus"])
        await message.reply(f"scan complete. {c} data points injected into neural matrix.")
        return

    if not content.startswith("!"):
        ai_core.process_input(user, content)

    if bot.user in message.mentions or "sop" in content.lower():
        clean = re.sub(r'<@!?[0-9]+>', '', content).strip()
        
        curr = time.time()
        if user in anti_spam and (curr - anti_spam[user] < 2.0): return
        anti_spam[user] = curr

        async with message.channel.typing():
            delay = min(4.0, max(1.0, len(clean) * 0.08)) if clean else 1.0
            await asyncio.sleep(delay)
            
            if not clean or clean.lower() == "sop":
                await message.reply("what do u want. type something or stop pinging.")
                return
                
            response = ai_core.generate_output(user, clean)
            await message.reply(response.lower())

#--// Run
bot.run(DISCORD_TOKEN)

