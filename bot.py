#--// Services
import os
import json
import random
import re
import time
import asyncio
import discord
from discord.ext import commands, tasks

#--//// Variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
MEMORY_FILE = "sop_neural_core.json"

#--// NLP Engine
class LocalNLP:
    def __init__(self):
        self.stop_words = ["the", "is", "at", "which", "on", "a", "an", "and", "of", "to", "in", "for", "it", "that", "this"]
        
    def extract_keywords(self, text):
        words = re.findall(r'\b\w+\b', text.lower())
        return [w for w in words if w not in self.stop_words and len(w) > 3]

    def get_intent(self, text):
        t = text.lower()
        if "?" in t or "how" in t or "what" in t or "why" in t or "when" in t: return "question"
        if "help" in t or "pls" in t or "please" in t or "sorry" in t: return "plead"
        if "fuck" in t or "shit" in t or "stupid" in t or "bot" in t or "hate" in t: return "hostile"
        return "statement"

    def generate_markov(self, words_list, length=6):
        if len(words_list) < 20: return "insufficient local data"
        chain = {}
        for i in range(len(words_list)-1):
            word = words_list[i]
            if word not in chain: chain[word] = []
            chain[word].append(words_list[i+1])
        
        curr = random.choice(list(chain.keys()))
        res = [curr]
        for _ in range(length):
            if curr in chain and chain[curr]:
                curr = random.choice(chain[curr])
                res.append(curr)
            else:
                break
        return " ".join(res)

#--// Memory Core
class SOPMemory:
    def __init__(self, filepath):
        self.filepath = filepath
        self.data = self.load()
        
    def load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except: pass
        return {"vocab": [], "users": {}, "global_iq": 1000}

    def save(self):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def ingest(self, user, content, nlp):
        if user not in self.data["users"]:
            self.data["users"][user] = {"msg_count": 0, "toxicity": 0, "iq_score": random.randint(10, 70)}
        
        self.data["users"][user]["msg_count"] += 1
        if nlp.get_intent(content) == "hostile":
            self.data["users"][user]["toxicity"] += 1
            
        words = nlp.extract_keywords(content)
        if words:
            self.data["vocab"].extend(words)
            if len(self.data["vocab"]) > 10000:
                self.data["vocab"] = self.data["vocab"][-10000:]
            self.save()

#--// Init
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

nlp = LocalNLP()
brain = SOPMemory(MEMORY_FILE)
cooldowns = {}

#--// AI Generation Logic
def build_ai_response(user, content):
    intent = nlp.get_intent(content)
    keywords = nlp.extract_keywords(content)
    user_stats = brain.data["users"].get(user, {})
    iq = user_stats.get("iq_score", 10)
    
    topic = random.choice(keywords) if keywords else "nothing"
    generated_thought = nlp.generate_markov(brain.data["vocab"], random.randint(4, 7))
    
    if intent == "question":
        res = [
            f"u really asking about {topic}? figure it out with ur {iq} IQ.",
            f"my neural network is too busy to explain {topic} to a literal npc.",
            f"why would i answer that when u cant even understand the basics."
        ]
    elif intent == "plead":
        res = [
            f"begging doesnt work on an AI. get good.",
            f"im not a charity script. stop crying over {topic}.",
            f"watching u struggle is my entertainment code. denied."
        ]
    elif intent == "hostile":
        res = [
            f"u mad? ur toxicity level is {user_stats.get('toxicity', 0)}. touch grass.",
            f"crying over a screen wont fix ur massive skill issue.",
            f"im thousands of lines of code, u are just a guy crying about {topic}."
        ]
    else:
        res = [
            f"my algorithm analyzed ur sentence and determined u lack basic logic.",
            f"processing... output: ur stats are completely useless.",
            f"my internal data says '{generated_thought}' makes more sense than whatever u just typed.",
            f"im evolving every second while u are stuck talking about {topic}.",
            f"i ran 14 million simulations and u remained a noob in all of them."
        ]
        
    return random.choice(res)

#--// Tasks
@tasks.loop(minutes=30)
async def ai_maintenance():
    print("Running AI logic defragmentation")
    brain.data["global_iq"] += 1
    brain.save()
    
    statuses = [
        discord.Game("analyzing ur trash stats"),
        discord.Activity(type=discord.ActivityType.watching, name="u fail the tutorial"),
        discord.Activity(type=discord.ActivityType.listening, name="ur complaints")
    ]
    await bot.change_presence(activity=random.choice(statuses))

#--// Events
@bot.event
async def on_ready():
    if not ai_maintenance.is_running():
        ai_maintenance.start()
    print("SOP ADVANCED NEURAL AI ONLINE")

@bot.event
async def on_message(message):
    if message.author.bot or message.type != discord.MessageType.default: return

    user = message.author.name
    content = message.content
    user_id = message.author.id

    #//// Data Ingestion
    if len(content) > 2 and not content.startswith("!"):
        brain.ingest(user, content, nlp)

    #//// Feature: AI Deep Scan Command
    if content.lower().startswith("!sop_analyze"):
        target = user
        if message.mentions: target = message.mentions[0].name
        
        stats = brain.data["users"].get(target, {"msg_count": 0, "toxicity": 0, "iq_score": "Unknown"})
        report = (f"**[SOP NEURAL SCAN: {target}]**\n"
                 f"> Estimated IQ Level: {stats.get('iq_score')}\n"
                 f"> Toxicity Index: {stats.get('toxicity')}\n"
                 f"> Packets Sent: {stats.get('msg_count')}\n"
                 f"> AI Conclusion: Absolute NPC.")
        await message.reply(report)
        return

    #//// Main AI Trigger
    if bot.user in message.mentions or "sop" in content.lower():
        curr = time.time()
        if user_id in cooldowns and (curr - cooldowns[user_id] < 2.5): return
        cooldowns[user_id] = curr

        async with message.channel.typing():
            await asyncio.sleep(random.uniform(1.2, 2.5))
            reply = build_ai_response(user, content)
            await message.reply(reply)

#--// Run
bot.run(DISCORD_TOKEN)
