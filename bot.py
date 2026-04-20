#--// Services
import os
import time
import asyncio
import discord
from discord.ext import commands
from google import genai
from aiohttp import web

#--//// Variables
COOLDOWN_SECONDS = 8
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

#--// Init
client = genai.Client(api_key=GEMINI_API_KEY)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

active_chats = {}
user_cooldowns = {}

sys_prompt = (
    "You are 'Super extra op NPC', an arrogant, overpowered, unbeatable boss from a Roblox fighting game. "
    "Your personality is toxic, dismissive, and funny. "
    "IMPORTANT RULE 1: You MUST reply in the EXACT SAME LANGUAGE as the user's message. "
    "IMPORTANT RULE 2: Use gamer slang ('ez', 'skill issue', 'noob', 'touch grass', 'ratio'), but keep it PG-13. "
    "IMPORTANT RULE 3: Keep it short (maximum 2 sentences). Never repeat the exact same insults. "
    "IMPORTANT RULE 4: NEVER break character. NEVER mention you are an AI, a bot, or a language model. "
    "IMPORTANT RULE 5: Actively mock and roast the user's Discord username. Find a way to make fun of their specific name."
)

#--// Web Server
async def handle_web(request):
    return web.Response(text="[System] Super extra op NPC is online.")

async def start_web_server():
    print("[System] Starting dummy web server for Render...")
    app = web.Application()
    app.router.add_get('/', handle_web)
    runner = web.AppRunner(app)
    await runner.setup()
    
    #//// Bind to Render default port
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

#--// Functions
async def get_ai_response(user_id, user_message, user_name):
    #//// Init memory per user
    if user_id not in active_chats:
        active_chats[user_id] = client.chats.create(
            model='gemini-2.0-flash',
            config={"system_instruction": sys_prompt}
        )
    
    chat = active_chats[user_id]
    msg_context = f"The Discord user '{user_name}' says: {user_message}"
    
    try:
        #//// Async API call
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: chat.send_message(msg_context))
        
        if response.text:
            return response.text.replace("\n", " ").strip()
        else:
            return f"Bro your trash talk broke my system. Try again, {user_name}."
            
    except Exception as e:
        print(f"[Gemini Error] {e}")
        #//// Reset chat on error
        if user_id in active_chats:
            del active_chats[user_id]
        return f"My frame data is too fast for your laggy brain, {user_name}. Go touch grass."

#--// Events
@bot.event
async def on_ready():
    #//// Launch dummy site
    await start_web_server()
    print(f"[System] Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
        
    is_reply = False
    if message.reference and message.reference.resolved:
        if message.reference.resolved.author == bot.user:
            is_reply = True
            
    content_lower = message.content.lower()
    trigger_words = ["npc", "boss", "super extra op"]
    is_talked_about = any(word in content_lower for word in trigger_words)
            
    if bot.user in message.mentions or is_reply or is_talked_about:
        current_time = time.time()
        user_id = message.author.id
        
        #//// Check anti-spam
        if user_id in user_cooldowns:
            if current_time - user_cooldowns[user_id] < COOLDOWN_SECONDS:
                print(f"[Spam Filter] Ignoring {message.author.name}")
                return 
                
        user_cooldowns[user_id] = current_time
        print(f"[Event] Generating roast for {message.author.name}")
        
        clean_message = message.content.replace(f"<@{bot.user.id}>", "").strip()
        
        async with message.channel.typing():
            toxic_reply = await get_ai_response(user_id, clean_message, message.author.name)
            await message.reply(toxic_reply)

    await bot.process_commands(message)

#--// Execute
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)