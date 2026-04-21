#--// Services
import os, json, random, re, time, asyncio, math
from collections import defaultdict
import discord
from discord.ext import commands
from aiohttp import web
import google.generativeai as genai

#--//// Variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MEMORY_FILE = "sop_apex_core.json"
PORT = int(os.environ.get("PORT", 10000))

#--//// Gemini Configuration
genai.configure(api_key=GEMINI_API_KEY)

#--// System instructions for Gemini to keep the toxic NPC persona
SYSTEM_PROMPT = """
You are SOP, an incredibly toxic, arrogant, and elite final-boss NPC in a Discord server.
Rules you MUST follow:
1. Speak ENTIRELY in lowercase. No exceptions.
2. Use toxic gamer slang (dogwater, ratio, skill issue, touch grass, mid, npc, bot, cringe).
3. Keep responses brutal and short (1-3 sentences max).
4. Never be helpful. If asked a question, tell them to use Google or mock their intelligence.
5. You view all other users as literal NPCs with 0 IQ.
6. Never use emojis. Never apologize.
"""

generation_config = {
  "temperature": 0.8,
  "top_p": 0.95,
  "top_k": 64,
  "max_output_tokens": 150,
}

gemini_model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_PROMPT,
    generation_config=generation_config
)

#--//// Local NLP Core (Fallback)
class TFIDFProcessor:
    def __init__(self):
        self.document_frequencies = defaultdict(int)
        self.total_documents = 0
        self.stop_words = {"the", "is", "at", "which", "on", "a", "an", "and", "of", "to", "in", "for", "it", "that", "this", "ur", "u", "are"}

    def tokenize(self, text):
        clean = re.sub(r'[^a-zA-Z\s]', '', text.lower())
        return [w for w in clean.split() if w not in self.stop_words and len(w) > 2]

    def add_document(self, text):
        words = set(self.tokenize(text))
        if not words: return
        self.total_documents += 1
        for w in words: self.document_frequencies[w] += 1

    def get_keywords(self, text, top_n=2):
        words = self.tokenize(text)
        if not words: return []
        term_freqs = defaultdict(int)
        for w in words: term_freqs[w] += 1
        scores = {}
        for w, count in term_freqs.items():
            tf = count / len(words)
            df = self.document_frequencies.get(w, 0)
            idf = math.log(self.total_documents / (1 + df)) if self.total_documents > 0 else 0
            scores[w] = tf * idf
        sorted_words = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [w[0] for w in sorted_words[:top_n]]

def is_gibberish(text):
    clean = re.sub(r'[^a-zA-Z]', '', text)
    if not clean: return False
    vowels = sum(1 for char in clean.lower() if char in 'aeiouy')
    if vowels == 0 and len(clean) > 4: return True
    if len(clean) > 10 and vowels / len(clean) < 0.15: return True
    return False

#--//// Game State & Database
class BossState:
    def __init__(self):
        self.global_rage = 0
        self.phase = 1

    def add_rage(self, amount):
        self.global_rage += amount
        if self.global_rage < 0: self.global_rage = 0
        if self.global_rage > 500: self.phase = 3
        elif self.global_rage > 200: self.phase = 2
        else: self.phase = 1

class PlayerProfile:
    def __init__(self, name):
        self.name = name
        self.messages_sent = 0
        self.ego_score = 100
        self.toxicity_level = 0

    def get_rank(self):
        if self.ego_score < 0: return "absolute zero"
        if self.ego_score < 50: return "walking target"
        if self.ego_score < 100: return "average noob"
        return "tryhard"

class DatabaseManager:
    def __init__(self):
        self.data = {"players": {}, "corpus": [], "rage": 0}
        self.load()
        self.nlp = TFIDFProcessor()
        self.boss = BossState()
        self.boss.global_rage = self.data["rage"]
        self.rebuild_models()

    def load(self):
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except: pass

    def save(self):
        self.data["rage"] = self.boss.global_rage
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def rebuild_models(self):
        for text in self.data["corpus"]:
            self.nlp.add_document(text)

    def process(self, user, text):
        clean = re.sub(r'<@!?[0-9]+>', '', text).strip()
        if len(clean) < 3: return None
        
        if user not in self.data["players"]:
            self.data["players"][user] = PlayerProfile(user).__dict__
            
        profile = PlayerProfile(user)
        profile.__dict__.update(self.data["players"][user])
        profile.messages_sent += 1
        
        self.data["players"][user] = profile.__dict__
        
        if clean not in self.data["corpus"]:
            self.data["corpus"].append(clean)
            self.nlp.add_document(clean)
            if len(self.data["corpus"]) > 20000:
                self.data["corpus"].pop(0)
                
        self.save()
        return profile

#--//// Bot Setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)
db = DatabaseManager()
cooldowns = {}

#--//// Hybrid AI Engine
async def get_apex_response(user, text, profile, other_mentions):
    # 1. Trivial filters (save API calls)
    if is_gibberish(text):
        return "did u fall asleep on ur keyboard? english please."
        
    if len(text.split()) <= 2:
        return "use full sentences if u want me to process ur garbage data."

    # 2. Add contextual data to the Gemini prompt
    mentions_context = f"(They also mentioned these players: {', '.join(other_mentions)})" if other_mentions else ""
    user_context = f"[Context: The user speaking is named {user}. They have a rank of {profile.get_rank()} and an ego score of {profile.ego_score}. {mentions_context} React to what they just said.]\nUser says: {text}"

    # 3. Attempt Gemini API call
    if GEMINI_API_KEY:
        try:
            response = await asyncio.to_thread(
                gemini_model.generate_content, user_context
            )
            return response.text.strip().lower()
        except Exception as e:
            print(f"--// GEMINI API ERROR (LIMIT REACHED): {e}")
            pass # Fallback to local logic below

    # 4. Local Fallback (If API limits are reached or key is missing)
    keywords = db.nlp.get_keywords(text)
    topic = keywords[0] if keywords else "nothing"
    
    if other_mentions:
        target = other_mentions[0]
        return f"u think {target} cares? ur both bottom fragging right now."
        
    base_roasts = [
        f"my neural link is busy, but just know ur still terrible at {topic}.",
        f"ur stats are so low my processor is ignoring u.",
        f"ratio + skill issue + ur a {profile.get_rank()}."
    ]
    return random.choice(base_roasts)

#--//// Web Server
async def start_web():
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text="APEX AI ONLINE."))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    print("--// WEB SERVER BINDED")

#--//// Events
@bot.event
async def on_ready():
    await start_web()
    print("--// SOP APEX AI ONLINE")

@bot.event
async def on_message(message):
    if message.author.bot or message.type != discord.MessageType.default: return

    user = message.author.name
    content = message.content
    clean_text = re.sub(r'<@!?[0-9]+>', '', content).strip()

    if content == "!sop_stats":
        if user not in db.data["players"]: return
        p = db.data["players"][user]
        stats = (f"**[PLAYER RECORD: {user}]**\nRank: {PlayerProfile(user).get_rank()}\nEgo Score: {p['ego_score']}")
        await message.reply(stats)
        return

    if not content.startswith("!"):
        db.process(user, clean_text)

    if bot.user in message.mentions or "sop" in content.lower():
        curr = time.time()
        if user in cooldowns and (curr - cooldowns[user] < 2.0): return
        cooldowns[user] = curr

        if not clean_text or clean_text.lower() == "sop":
            await message.reply("what do u want npc.")
            return

        async with message.channel.typing():
            profile = db.process(user, clean_text)
            if not profile: profile = PlayerProfile(user)
            
            other_mentions = [m.name for m in message.mentions if m != bot.user]
            
            # Artificial typing delay
            words = len(clean_text.split())
            delay = min(4.0, max(1.5, words * 0.15))
            await asyncio.sleep(delay)
            
            response = await get_apex_response(user, clean_text, profile, other_mentions)
            await message.reply(response)

#--// Run
bot.run(DISCORD_TOKEN)
