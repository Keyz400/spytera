from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from pyrogram.enums import ChatAction
from pyrogram.errors import UserNotParticipant, FloodWait
import httpx
import asyncio
import time
from bs4 import BeautifulSoup
from flask import Flask, request
from threading import Thread
import pymongo
from typing import Optional
from pyrogram.errors import FloodWait, RPCError
import requests
import pyfiglet
from termcolor import cprint
import sys
import os  # Added import for environment variables

# Bot details
BOT_TOKEN = '6479322823:AAFTzuzIsoYUPH8wdL6sHsePM6JQv2kTxOo'
CHANNEL_USERNAME = 'Lox_Bots'
API_HASH = '04c316c7a167cfede7256ca9c57462ab'
API_ID = 20760512
TERABOX_API = 'https://terabox-api.mrspyboy.workers.dev/'
TERABOX_API2 = 'https://terabox.spyboyxdeepak.workers.dev/?url='
DUMP_CHANNEL = -1001824360922
OWNER_ID = 1318663278

# Flask app for monitoring
flask_app = Flask(__name__)
start_time = time.time()

# MongoDB setup
mongo_client = pymongo.MongoClient('mongodb+srv://ggatg:ggatg@cluster0.lv9rt.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = mongo_client['Rishu-free-db']
users_collection = db['users']

# HTTP client setup with timeout
http_client = httpx.AsyncClient(timeout=10.0)

# Pyrogram bot client
app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# AI Chatbot functionality
def get_ai_response(query: str) -> str:
    """Fetch AI response from the API."""
    api_url = f"https://devil-web.in/api/ai.php?query={query}"
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "Sorry, I couldn't retrieve an answer.")
    except requests.exceptions.RequestException as e:
        return f"Error: Could not connect to the API. {e}"
    except ValueError:
        return "Error: Invalid response from the API."

async def typing_indicator(client, chat_id):
    """Simulate typing indicator."""
    await client.send_chat_action(chat_id, ChatAction.TYPING)
    await asyncio.sleep(1)  # Simulate typing delay

# Command handler for /ai and /ask
@app.on_message(filters.command(["ai", "ask"]))
async def ai_chatbot(client, message):
    user_id = message.from_user.id
    if not await is_user_in_channel(client, user_id):
        await send_join_prompt(client, message.chat.id)
        return

    query = " ".join(message.command[1:])  # Extract the query from the command
    if not query:
        await message.reply_text("Please provide a query after the command. Example: `/ai What is AI?`")
        return

    # Simulate typing indicator
    await typing_indicator(client, message.chat.id)

    # Fetch AI response
    ai_response = get_ai_response(query)

    # Send the response
    await message.reply_text(f"🤖 AI Response:\n\n{ai_response}")

# Rest of the existing code remains unchanged
async def is_user_in_channel(client, user_id):
    try:
        await client.get_chat_member(CHANNEL_USERNAME, user_id)
        return True
    except UserNotParticipant:
        return False
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await is_user_in_channel(client, user_id)

async def send_join_prompt(client, chat_id):
    join_button = InlineKeyboardButton("Join Channel", url=f"https://t.me/{CHANNEL_USERNAME}")
    blume_button = InlineKeyboardButton('♡ Follow ♡', url='https://insta.oia.bio/21j2s')
    markup = InlineKeyboardMarkup([[join_button, blume_button]])
    try:
        await client.send_message(chat_id, "You need to join our channel to use this bot. ♡♡♡", reply_markup=markup)
    except FloodWait as e:
        await asyncio.sleep(e.value)
        await send_join_prompt(client, chat_id)

@app.on_message(filters.command("start"))
async def start_message(client, message):
    user_id = message.from_user.id
    if users_collection.count_documents({'user_id': user_id}) == 0:
        users_collection.insert_one({'user_id': user_id})
    await message.reply_text("♡ Hello! Send me a TeraBox URL to Get Started. ♡")

@app.on_message(filters.command("all") & filters.user(OWNER_ID))
async def broadcast_message(client, message):
    if len(message.command) < 2:
        await message.reply_text("Please provide a message to broadcast. Usage: /all <message>")
        return

    broadcast_text = " ".join(message.command[1:])
    users = users_collection.find({})

    success_count = 0
    fail_count = 0

    for user in users:
        try:
            await client.send_message(user["user_id"], broadcast_text)
            success_count += 1
        except Exception as e:
            print(f"Error sending to {user['user_id']}: {str(e)}")
            fail_count += 1
        await asyncio.sleep(0.1)  # Add slight delay to prevent flooding

    await message.reply_text(f"Broadcast completed!\nSuccess: {success_count}\nFailed: {fail_count}")

@app.on_message(filters.command("status"))
async def status_message(client, message):
    user_count = users_collection.count_documents({})
    uptime_minutes = (time.time() - start_time) / 60
    await message.reply_text(f"💫 Bot uptime: {uptime_minutes:.2f} minutes\n👥 Total unique users: {user_count}")

@app.on_message(filters.text & ~filters.command(["start", "status", "ai", "ask"]))
async def get_video_links(client, message):
    user_id = message.from_user.id
    if not await is_user_in_channel(client, user_id):
        await send_join_prompt(client, message.chat.id)
        return
    
    video_url = message.text.strip()
    await message.reply_chat_action(ChatAction.TYPING)
    
    try:
        # Parallel execution of API calls
        thumbnail, api_response = await asyncio.gather(
            fetch_video_details(video_url),
            fetch_download_link(video_url)
        )
        
        thumbnail = thumbnail or "https://envs.sh/L75.jpg"
        download_link = api_response.get("downloadLink") if api_response else None
        filename = api_response.get("filename", "Unknown File") if api_response else "Unknown File"
        size = api_response.get("size", "Unknown Size") if api_response else "Unknown Size"

        # Shorten link if available
        shortened_link = await shorten_link(download_link) if download_link else None

        # Prepare buttons
        buttons = [
            [InlineKeyboardButton("➡️ PLAY VIDEO ▶️", web_app=WebAppInfo(url=f"{TERABOX_API}{video_url}"))],
            [InlineKeyboardButton("➡️ PLAYER NEON ▶️", web_app=WebAppInfo(url=f"{TERABOX_API2}{video_url}"))],
            [InlineKeyboardButton('🤫 PREMIUM LINKS CHANNEL 🤫', url='https://seturl.in/Study')],
            [InlineKeyboardButton("♡ Gift ♡", url="https://insta.oia.bio/21j2s")],
        ]

        if shortened_link:
            buttons.insert(2, [InlineKeyboardButton("⬇️ DOWNLOAD VIDEO (Fixed) ⬇️", url=shortened_link)])

        # Send response
        caption = f"**User:💀 {message.from_user.mention}**\n**Here's your video:**\n**Filename:** `{filename}`\n**Size:** `{size}`"
        await client.send_photo(message.chat.id, thumbnail, caption=caption, reply_markup=InlineKeyboardMarkup(buttons))

        # Log to dump channel
        dump_text = f"From {message.from_user.mention}:\nLink: {TERABOX_API}{video_url}\nFilename: `{filename}`\nSize: `{size}`"
        if shortened_link:
            dump_text += f"\nDownload: {shortened_link}"
        await client.send_photo(DUMP_CHANNEL, thumbnail, caption=dump_text)

    except Exception as e:
        await message.reply_text(f"Error processing your request: {str(e)}")

async def fetch_video_details(video_url: str) -> Optional[str]:
    try:
        async with http_client as client:
            response = await client.get(video_url)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                return soup.find("meta", property="og:image")["content"]
    except Exception:
        return None

async def fetch_download_link(video_url: str) -> Optional[dict]:
    try:
        async with http_client as client:
            response = await client.get(f"https://pika-terabox-dl.vercel.app/?url={video_url}")
            return response.json() if response.status_code == 200 else None
    except Exception:
        return None

async def shorten_link(url: str) -> Optional[str]:
    try:
        async with http_client as client:
            # First shorten with TinyURL
            tinyurl = await client.get(f"http://tinyurl.com/api-create.php?url={url}")
            if tinyurl.status_code == 200:
                short_url = tinyurl.text.strip()
                # Then shorten with v2links
                v2response = await client.get(f"https://seturl.in/api?api=435f290e284c58037d9063f35dfebbeb7877f4e2&url={short_url}&format=text")
                return v2response.text.strip() if v2response.status_code == 200 else short_url
    except Exception:
        return None

@flask_app.route('/')
def home():
    uptime_minutes = (time.time() - start_time) / 60
    user_count = users_collection.count_documents({})
    return f"Bot uptime: {uptime_minutes:.2f} minutes\nUnique users: {user_count}"

def run_flask():
    # Get port from environment variable or default to 8080
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    Thread(target=run_flask).start()
    app.run()
