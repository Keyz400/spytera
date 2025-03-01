import os
import asyncio
from urllib.parse import quote
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from playwright.sync_api import sync_playwright
import requests
from bs4 import BeautifulSoup
import pymongo
from typing import Optional

# Load environment variables
API_ID = int(os.getenv("API_ID", 20760512))
API_HASH = os.getenv("API_HASH", "04c316c7a167cfede7256ca9c57462ab")
BOT_TOKEN = os.getenv("BOT_TOKEN", "8072718373:AAHNmzjoV2qXUypXbvhccIE6bQNRmAQEn58")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "lox_bots")
DUMP_CHANNEL = int(os.getenv("DUMP_CHANNEL", -1001824360922))
OWNER_ID = int(os.getenv("OWNER_ID", 1318663278))

# MongoDB setup
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://mrdeepakushwaha:lOMs3uDmCxgNFYNP@cluster0.376zvxq.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
mongo_client = pymongo.MongoClient(MONGO_URI)
db = mongo_client['Rishu-free-db']
users_collection = db['users']

# Initialize Pyrogram client
app = Client("terabox_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def extract_terabox_m3u8(api_url):
    """Extract m3u8 URL with enhanced parameter validation."""
    direct_url = None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,  # Run in headless mode
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    '--remote-allow-origins=*'
                ]
            )
            context = browser.new_context(
                ignore_https_errors=True,
                storage_state={
                    'cookies': [
                        {'name': 'PANWEB', 'value': '1', 'domain': '.terabox.com', 'path': '/'},
                        {'name': 'ndut_fmt', 'value': 'FFFFFFFF', 'domain': '.terabox.com', 'path': '/'}
                    ]
                }
            )
            page = context.new_page()
            def handle_request(request):
                nonlocal direct_url
                raw_url = request.url
                if "extstreaming.m3u8" in raw_url:
                    direct_url = raw_url
            page.on("request", handle_request)
            page.goto(api_url, wait_until="networkidle", timeout=60000)
            browser.close()
    except Exception as e:
        print(f"Error in extract_terabox_m3u8: {e}")
    return direct_url

def ensure_valid_params(url):
    """Force-correct parameters before shortening."""
    if not url:
        return None
    corrections = [
        ('%C3%97tamp%3D', '%26timestamp%3D'),
        ('×tamp=', '&timestamp='),
        ('%26amp%3B', '%26')
    ]
    for wrong, right in corrections:
        url = url.replace(wrong, right)
    return url

def fetch_video_details(video_url: str) -> Optional[str]:
    """Fetch video thumbnail using BeautifulSoup."""
    try:
        response = requests.get(video_url, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            meta = soup.find("meta", property="og:image")
            return meta["content"] if meta and meta.has_attr("content") else "https://envs.sh/L75.jpg"
    except Exception as e:
        print(f"Error in fetch_video_details: {e}")
    return "https://envs.sh/L75.jpg"

def shorten_link(url: str) -> str:
    """Shorten URL using TinyURL."""
    try:
        tinyurl_api = f"https://tinyurl.com/api-create.php?url={quote(url, safe=':/?&=')}"
        response = requests.get(tinyurl_api, timeout=10)
        return response.text.strip() if response.status_code == 200 else url
    except Exception as e:
        print(f"Error in shorten_link: {e}")
    return url

async def is_user_in_channel(client, user_id):
    """Check if user is in required channel."""
    try:
        await client.get_chat_member(CHANNEL_USERNAME, user_id)
        return True
    except Exception as e:
        print(f"Error in is_user_in_channel: {e}")
    return False

@app.on_message(filters.command("start"))
async def start_handler(client, message):
    user_id = message.from_user.id
    if not users_collection.find_one({'user_id': user_id}):
        users_collection.insert_one({'user_id': user_id})
    await message.reply("♡ Hello! Send me a TeraBox URL to get started. ♡")

@app.on_message(filters.command("all") & filters.user(OWNER_ID))
async def broadcast_handler(client, message):
    if len(message.command) < 2:
        await message.reply_text("Usage: /all <message>")
        return

    broadcast_text = " ".join(message.command[1:])
    users = users_collection.find({})
    
    success = 0
    for user in users:
        try:
            await client.send_message(user["user_id"], broadcast_text)
            success += 1
        except Exception as e:
            print(f"Error sending message to user {user['user_id']}: {e}")
    await message.reply_text(f"Broadcast sent to {success} users")

@app.on_message(filters.command("status") & filters.user(OWNER_ID))
async def status_handler(client, message):
    user_count = users_collection.count_documents({})
    await message.reply_text(f"Total users: {user_count}")

@app.on_message(filters.text & ~filters.command(["start", "status", "all"]))
async def video_handler(client, message):
    # Channel check
    user_id = message.from_user.id
    if not await is_user_in_channel(client, user_id):
        join_button = InlineKeyboardButton("Join Channel", url=f"https://t.me/{CHANNEL_USERNAME}")
        follow_button = InlineKeyboardButton('♡ Follow ♡', url='https://insta.oia.bio/21j2s')
        await message.reply("Join our channel to use this bot:", reply_markup=InlineKeyboardMarkup([[join_button, follow_button]]))
        return

    # Process URL
    user_url = message.text.strip()
    if not user_url.startswith("http"):
        await message.reply("❌ Invalid URL format")
        return

    # Extract video data
    api_url = f"https://terabox-api.mrspyboy.workers.dev/{user_url}"
    raw_url = await asyncio.to_thread(extract_terabox_m3u8, api_url)
    
    if not raw_url:
        await message.reply("🔴 Extraction failed")
        return

    # Process URLs
    validated_url = ensure_valid_params(raw_url)
    play_url = shorten_link(validated_url)
    thumbnail = await asyncio.to_thread(fetch_video_details, user_url)

    # Create buttons
    buttons = [
        [InlineKeyboardButton("▶️ PLAY VIDEO", web_app=WebAppInfo(url=play_url))],
        [InlineKeyboardButton('🌟 PREMIUM CHANNEL', url='https://seturl.in/Study')],
        [InlineKeyboardButton("💝 SUPPORT", url="https://insta.oia.bio/21j2s")]
    ]

    # Send response
    await client.send_photo(
        chat_id=message.chat.id,
        photo=thumbnail,
        caption=f"**Hey {message.from_user.mention}!**\nYour video is ready to play:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

    # Log to dump channel
    await client.send_photo(
        chat_id=DUMP_CHANNEL,
        photo=thumbnail,
        caption=f"User: {message.from_user.mention}\nURL: {user_url}\nPlay: {play_url}"
    )

if __name__ == "__main__":
    print("Bot operational with video playback only...")
    app.run()
