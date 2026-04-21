
#--// Services
import os, json, random, re, time, asyncio, discord
from discord.ext import commands

#--//// Variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
MEMORY_FILE = "sop_final_brain.json"
cooldowns = {}
processed_msgs = []

#--// Core
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
        clean = re.sub(r'<@!?[0-9]+>', '', text).strip()
        if len(clean) < 2: return
        
        if clean not in self.memory["vocabulary"]:
            self.memory["vocabulary"].append(clean)
            
        if user not in self.memory["player_profiles"]:
            self.memory["player_profiles"][user] = {"msgs": 0}
            
        self.memory["player_profiles"][user]["msgs"] += 1
        
        if len(self.memory["vocabulary"]) > 8000:
            self.memory["vocabulary"].pop(0)
        self.save()

#--//// Logic
def is_gibberish(text):
    # Detects keyboard mashing by analyzing vowel ratio
    clean = re.sub(r'[^a-zA-Z]', '', text)
    if not clean: return False
    vowels = sum(1 for char in clean.lower() if char in 'aeiouy')
    if vowels == 0 and len(clean) > 4: return True
    if len(clean) > 15 and vowels / len(clean) < 0.15: return True
    return False

def generate_ai_thought(user, input_text, core_data):
    vocab = core_data.memory["vocabulary"]
    profiles = core_data.memory["player_profiles"]
    user_msgs = profiles.get(user, {}).get("msgs", 0)
    
    if is_gibberish(input_text):
        roasts = [
            "bro had a stroke on his keyboard.",
            "typing random letters wont hide the fact that ur bad.",
            "did u fall asleep on ur desk? wake up.",
            "english please. or are u just mashing buttons because u lost?"
        ]
        return random.choice(roasts)

    t = input_text.lower()
    if any(w in t for w in ["how are u", "u good", "ca va"]):
        return "im doing better than ur ranked stats."
    
    if any(w in t for w in ["why", "how", "what"]):
        return "google is free bro. use it."

    if len(vocab) < 10: 
        return "say something interesting for once."

    base_memory = random.choice(vocab)
    
    roasts = [
        f"bro really typed that thinking he did something.",
        f"ive seen u send {user_msgs} messages in this server and not a single one was smart.",
        f"somebody ban {user} please.",
        f"u sound like the type of guy to say '{base_memory}' unironically.",
        f"ur entire existence in this chat is a skill issue.",
        f"ratio + u have no life + touch grass.",
        f"im not reading all that but u definitely need to uninstall."
    ]
    return random.choice(roasts)

#--// Init
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)
core = SOPNeuralCore()

#--// Events
@bot.event
async def on_ready():
    print("--// SOP OMNISCIENT CORE ONLINE")

@bot.event
async def on_message(message):
    if message.author.bot or message.type != discord.MessageType.default: return

    if message.id in processed_msgs: return
    processed_msgs.append(message.id)
    if len(processed_msgs) > 100: processed_msgs.pop(0)

    user = message.author.name
    content = message.content

    if content == "!sop_consume":
        if not message.author.guild_permissions.administrator:
            await message.reply("u dont tell me what to do bro. quiet.")
            return
        
        await message.reply("reading all ur chat history rn. give me a sec.")
        count = 0
        for channel in message.guild.text_channels:
            try:
                async for msg in channel.history(limit=250):
                    if not msg.author.bot and len(msg.content) > 3:
                        core.feed(msg.author.name, msg.content)
                        count += 1
            except: continue
        await message.reply(f"done. read {count} messages. my iq dropped just looking at this server.")
        return

    if not content.startswith("!"):
        core.feed(user, content)

    if bot.user in message.mentions or "sop" in content.lower():
        clean = re.sub(r'<@!?[0-9]+>', '', content).strip()
        if not clean or clean.lower() == "sop":
            # Toxic reaction fallback without emojis
            await message.add_reaction("\u2620\ufe0f")
            return

        curr = time.time()
        if message.author.id in cooldowns and (curr - cooldowns[message.author.id] < 3.0): return
        cooldowns[message.author.id] = curr

        async with message.channel.typing():
            response = generate_ai_thought(user, clean, core)
            # Dynamic typing delay based on string length
            delay = min(3.0, max(1.0, len(response) * 0.05))
            await asyncio.sleep(delay)
            await message.reply(response.lower())

#--// Run
bot.run(DISCORD_TOKEN)
