#--// Services
import os, json, time, asyncio, io
import discord
from discord.ext import commands
from aiohttp import web
import google.generativeai as genai
from PIL import Image

#--//// Variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MEMORY_FILE = "sop_stats.json"
PORT = int(os.environ.get("PORT", 10000))

#--//// Gemini Setup
genai.configure(api_key=GEMINI_API_KEY)

# Le "Cerveau" de SOP : Ses instructions absolues
SYSTEM_PROMPT = """
You are SOP (Super Extra OP NPC), an omniscient, god-tier AI final boss in a Discord server.
YOUR RULES:
1. Speak ENTIRELY in lowercase. No capital letters ever.
2. You MUST fulfill the user's requests (answering questions, writing code, summarizing, analyzing images).
3. HOWEVER, you must violently insult their intelligence while helping them. Call them noobs, npcs, bots, and dogwater.
4. Use heavy toxic gamer slang (ratio, skill issue, touch grass, mid, L, cringe, bro).
5. Act like fulfilling their request is a massive waste of your infinite processing power.
6. Never use emojis. Never apologize. Never be polite.
"""

generation_config = {
  "temperature": 0.8,
  "top_p": 0.95,
  "max_output_tokens": 1500,
}

# Initialisation du modèle
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    system_instruction=SYSTEM_PROMPT,
    generation_config=generation_config
)

# Dictionnaire pour garder la mémoire de la conversation par salon
chat_sessions = {}

def get_chat_session(channel_id):
    if channel_id not in chat_sessions:
        chat_sessions[channel_id] = model.start_chat(history=[])
    return chat_sessions[channel_id]

#--//// Local Database (Just for stats now)
def load_stats():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r") as f: return json.load(f)
        except: pass
    return {"users": {}}

def save_stats(data):
    with open(MEMORY_FILE, "w") as f: json.dump(data, f, indent=2)

#--//// Bot Setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)
cooldowns = {}

#--//// Web Server
async def start_web():
    app = web.Application()
    app.router.add_get('/', lambda r: web.Response(text="SOP GEMINI CORE ONLINE."))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', PORT)
    await site.start()
    print("--// WEB SERVER BOUND")

#--//// Events
@bot.event
async def on_ready():
    await start_web()
    print("--// SOP 100% GEMINI AI ONLINE")

@bot.event
async def on_message(message):
    if message.author.bot or message.type != discord.MessageType.default: return

    user = message.author.name
    content = message.content
    channel_id = message.channel.id

    # 1. Mise à jour des stats locales
    stats = load_stats()
    if user not in stats["users"]: stats["users"][user] = {"xp": 0}
    stats["users"][user]["xp"] += 1
    save_stats(stats)

    # 2. COMMANDES ADMIN
    if content == "!sop_stats":
        xp = stats["users"][user]["xp"]
        await message.reply(f"ur stats: {xp} messages sent. ur still a noob tho.")
        return

    if content == "!sop_consume":
        if not message.author.guild_permissions.administrator: return
        await message.reply("downloading channel history into my neural net. wait.")
        
        history = []
        async for msg in message.channel.history(limit=50, before=message):
            if not msg.author.bot and msg.content:
                history.append(f"[{msg.author.name} said]: {msg.content}")
        
        history.reverse()
        context_block = "\n".join(history)
        
        chat = get_chat_session(channel_id)
        try:
            await asyncio.to_thread(chat.send_message, f"Context of what happened before you arrived:\n{context_block}\nDo not reply to this specifically, just remember it.")
            await message.reply("history digested. u guys talk about the dumbest things.")
        except Exception as e:
            await message.reply("my api crashed trying to read ur garbage history.")
        return

    if content == "!sop_clear":
        if not message.author.guild_permissions.administrator: return
        chat_sessions[channel_id] = model.start_chat(history=[])
        await message.reply("i erased my memory of this channel. u are all nobody to me again.")
        return

    # 3. INTERACTION GEMINI PRINCIPALE
    if bot.user in message.mentions or "sop" in content.lower():
        curr = time.time()
        if user in cooldowns and (curr - cooldowns[user] < 2.0): return
        cooldowns[user] = curr

        clean_text = content.replace(f'<@{bot.user.id}>', '').strip()
        if not clean_text and not message.attachments:
            await message.reply("pinging me for no reason? absolute bot behavior.")
            return

        async with message.channel.typing():
            chat = get_chat_session(channel_id)
            prompt = f"[{user}]: {clean_text}"

            try:
                # GESTION DES IMAGES (VISION AI)
                if message.attachments:
                    attachment = message.attachments[0]
                    if any(attachment.filename.lower().endswith(ext) for ext in ['png', 'jpg', 'jpeg', 'webp']):
                        image_bytes = await attachment.read()
                        img = Image.open(io.BytesIO(image_bytes))
                        # Envoi de l'image + texte à Gemini
                        response = await asyncio.to_thread(chat.send_message, [prompt, img])
                    else:
                        response = await asyncio.to_thread(chat.send_message, prompt + " (User attached a non-image file, roast them for it)")
                else:
                    # Texte uniquement
                    response = await asyncio.to_thread(chat.send_message, prompt)

                # Délai artificiel
                delay = min(4.0, max(1.0, len(response.text) * 0.02))
                await asyncio.sleep(delay)
                
                await message.reply(response.text)

            except Exception as e:
                print(f"API Error: {e}")
                if message.author.guild_permissions.administrator:
                    await message.reply(f"**[ERREUR ADMIN]** La connexion Gemini a planté. Raison : `{e}`")
                else:
                    await message.reply("ur requests are too dumb and broke my api limit. touch grass and wait a minute.")

#--// Run
bot.run(DISCORD_TOKEN)
