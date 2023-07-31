import logging
import json

# config.py
# Channerl to log to
TELE_LOG_CHANNEL = ""

# Telegram Bot API Token
TELEGRAM_TOKEN = ""

# Bot Username
BOT_USERNAME = ''

# OpenAI API Key
OPENAI_API_KEY = ""

# Clipdrop
CLIPDROP_API_KEY = ""

# HIBP
HIBP_API_KEY = ""

# ElevenLabs 
XI_API_KEY = ""

# Claude API Key
CLAUDE_API_KEY = ""

#Stability.ai API Key
STABILITY_API_KEY = ""

# Leonardo API Key
LEONARDO_API_KEY = ""

# Channel Chat ID
CHANNEL_CHAT_ID = 

# Admin IDs
ADMIN_IDS = []



logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    filename='bot_logs.log',  # Add the filename parameter
    filemode='a',  # Optional: Set the file mode to 'a' for appending logs
)

LOGGER = logging.getLogger(__name__)

