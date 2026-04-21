#--// Services
import os
import json
import random
import re
import time
import asyncio
import math
from collections import defaultdict
import discord
from discord.ext import commands
from aiohttp import web

#--//// Variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
MEMORY_FILE = "sop_leviathan_core.json"
PORT = int(os.environ.get("PORT", 10000))

#--//// Math & NLP Core
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
        for w in words:
            self.document_frequencies[w] += 1

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

class AdvancedMarkovChain:
    def __init__(self, order=2):
        self.order = order
        self.chain = defaultdict(lambda: defaultdict(int))
        self.starts = []

    def feed(self, text):
        words = text.split()
        if len(words) <= self.order: return
        self.starts.append(tuple(words[:self.order]))
        for i in range(len(words) - self.order):
            state = tuple(words[i:i+self.order])
            next_word = words[i+self.order]
            self.chain[state][next_word] += 1

    def generate(self, max_words=20):
        if not self.starts: return None
        current = random.choice(self.starts)
        output = list(current)
        for _ in range(max_words):
            if current not in self.chain or not self.chain[current]: break
            choices = list(self.chain[current].keys())
            weights = list(self.chain[current].values())
            next_word = random.choices(choices, weights=weights)[0]
            output.append(next_word)
            current = tuple(output[-self.order:])
        return " ".join(output)

class SentimentEngine:
    def __init__(self):
        self.toxics = {"trash": -3, "bad": -2, "noob": -3, "stupid": -2, "idiot": -2, "hate": -2, "bot": -1, "quit": -2, "skill": -1, "issue": -2}
        self.praises = {"good": 1, "pro": 2, "god": 2, "nice": 1, "win": 2}

    def evaluate(self, text):
        words = text.lower().split()
        score = 0.0
        for w in words:
            if w in self.toxics: score += self.toxics[w]
            if w in self.praises: score += self.praises[w]
        return score

#--//// Game State & Database
class BossState:
    def __init__(self):
        self.global_rage = 0
        self.phase = 1

    def add_rage(self, amount):
        self.global_rage += amount
        if self.global_rage < 0: self.global_rage = 0
        
        old_phase = self.phase
        if self.global_rage > 500: self.phase = 3
        elif self.global_rage > 200: self.phase = 2
        else: self.phase = 1
        
        return self.phase != old_phase

class PlayerProfile:
    def __init__(self, name):
        self.name = name
        self.messages_sent = 0
        self.ego_score = 100
        self.toxicity_level = 0
        self.deaths = 0

    def update(self, sentiment_score):
        self.messages_sent += 1
        if sentiment_score < 0:
            self.toxicity_level += abs(int(sentiment_score))
            self.ego_score -= random.randint(1, 5)
        elif sentiment_score > 0:
            self.ego_score += random.randint(1, 3)

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
        self.markov = AdvancedMarkovChain()
        self.sentiment = SentimentEngine()
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
            self.markov.feed(text)

    def process(self, user, text):
        clean = re.sub(r'<@!?[0-9]+>', '', text).strip()
        if len(clean) < 3: return None
        
        if user not in self.data["players"]:
            self.data["players"][user] = PlayerProfile(user).__dict__
            
        profile = PlayerProfile(user)
        profile.__dict__.update(self.data["players"][user])
        
        score = self.sentiment.evaluate(clean)
        profile.update(score)
        
        if score < 0: self.boss.add_rage(abs(score))
        else: self.boss.add_rage(-0.5)
        
        self.data["players"][user] = profile.__dict__
        
        if clean not in self.data["corpus"]:
            self.data["corpus"].append(clean)
            self.nlp.add_document(clean)
            self.markov.feed(clean)
            if len(self.data["corpus"]) > 20000:
                self.data["corpus"].pop(0)
                
        self.save()
        return profile, score

#--//// Bot Setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)
db = DatabaseManager()
cooldowns = {}

#--//// Response Generator
def build_leviathan_response(user, text, profile, s_score):
    phase = db.boss.phase
    keywords = db.nlp.get_keywords(text)
    topic = keywords[0] if keywords else "nothing"
    generated = db.markov.generate(max_words=10)
    
    if s_score < -2:
        if phase == 1:
            return f"ur mad about {topic}. ur ego score is {profile.ego_score}. stop typing."
        elif phase == 2:
            return f"u have {profile.toxicity_level} toxicity points. ur literally the worst player here."
        else:
            return f"SYSTEM OVERRIDE. {user} IS GARBAGE. NOOB RANK CONFIRMED."

    if "why" in text.lower() or "how" in text.lower():
        return f"im a phase {phase} boss and u want me to explain {topic} to a {profile.get_rank()}? figure it out."

    if generated and random.random() < 0.3:
        return f"i read ur chat logs. u sound like: '{generated}'. absolute bot behavior."

    base_roasts = [
        f"ur stats are dropping every time u mention {topic}.",
        f"i have analyzed {db.nlp.total_documents} messages and ur still the worst player here.",
        f"did u really think typing that was a good idea?",
        f"ur ego is at {profile.ego_score}. u have no right to speak.",
        f"ratio + skill issue + ur a {profile.get_rank()}."
    ]
    return random.choice(base_roasts)

#--//// Web Server
async def start_web():
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text="LEVIATHAN IS ONLINE."))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    print("--// WEB SERVER BOUND TO PORT")

#--//// Events
@bot.event
async def on_ready():
    await start_web()
    print("--// SOP LEVIATHAN ONLINE")

@bot.event
async def on_message(message):
    if message.author.bot or message.type != discord.MessageType.default: return

    user = message.author.name
    content = message.content
    clean_text = re.sub(r'<@!?[0-9]+>', '', content).strip()

    #//// Commands
    if content == "!sop_consume":
        if not message.author.guild_permissions.administrator: return
        await message.reply("initiating deep server harvest. this will hurt.")
        c = 0
        for channel in message.guild.text_channels:
            try:
                async for msg in channel.history(limit=500):
                    if not msg.author.bot and len(msg.content) > 3:
                        db.process(msg.author.name, msg.content)
                        c += 1
            except: continue
        await message.reply(f"harvest complete. {c} strings digested. phase {db.boss.phase} active.")
        return

    if content == "!sop_stats":
        if user not in db.data["players"]:
            await message.reply("u have no stats. u are irrelevant.")
            return
        p = db.data["players"][user]
        stats = (f"**[PLAYER RECORD: {user}]**\n"
                 f"Rank: {PlayerProfile(user).get_rank()}\n"
                 f"Ego Score: {p['ego_score']}\n"
                 f"Toxicity: {p['toxicity_level']}\n"
                 f"Packets Sent: {p['messages_sent']}")
        await message.reply(stats)
        return

    if content == "!sop_boss":
        stats = (f"**[SOP OVERLORD STATUS]**\n"
                 f"Current Phase: {db.boss.phase}\n"
                 f"Global Rage: {db.boss.global_rage}\n"
                 f"Neural Matrix: {db.nlp.total_documents} documents processed.")
        await message.reply(stats)
        return

    #//// Passive Processing
    if not content.startswith("!"):
        db.process(user, clean_text)

    #//// Trigger Logic
    if bot.user in message.mentions or "sop" in content.lower():
        curr = time.time()
        if user in cooldowns and (curr - cooldowns[user] < 2.0): return
        cooldowns[user] = curr

        if not clean_text or clean_text.lower() == "sop":
            await message.reply("stop pinging me if u have nothing to say.")
            return

        async with message.channel.typing():
            data = db.process(user, clean_text)
            if not data: return
            profile, s_score = data[0], data[1]
            
            # WPM Calculation for human-like typing delay
            words = len(clean_text.split())
            delay = min(4.0, max(1.5, words * 0.15))
            await asyncio.sleep(delay)
            
            response = build_leviathan_response(user, clean_text, profile, s_score)
            await message.reply(response.lower())

#--// Run
bot.run(DISCORD_TOKEN)
