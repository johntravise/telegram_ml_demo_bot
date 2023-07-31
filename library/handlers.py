import requests
import time
import io
import os
import hashlib
import urllib.request
from library.utils import *
from library.user import User
from datetime import datetime
from library.config import *
from telegram import Update, MessageEntity, InlineQueryResultArticle, InputTextMessageContent, ChatAction, InputFile
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, InlineQueryHandler
IMAGE, = range(1)
# Set up Telegram bot
updater = Updater(TELEGRAM_TOKEN, use_context=True)
dispatcher = updater.dispatcher
user_voice_choices = {}
# Create dictionary to store conversation history for each user
conversation_history = {}



import logging

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

def cancel(update: Update, context: CallbackContext) -> int:
    """Cancel the current conversation."""
    update.message.reply_text('Operation cancelled.')
    return ConversationHandler.END

def list_style_presets(update, context):
    """List available style presets."""
    style_presets = [
        "3d-model", "analog-film", "anime", "cinematic", "comic-book", "digital-art", "enhance", "fantasy-art",
        "isometric", "line-art", "low-poly", "modeling-compound", "neon-punk", "origami", "photographic",
        "pixel-art", "tile-texture", "none"
    ]
    message = ", ".join(style_presets)
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)

def remove_text_from_image(update: Update, context: CallbackContext):
    # Check if the message is a reply and has a photo
    if update.message.photo:
        # Check if the reply is to the bot's message asking for an image or has /rti caption
        if (update.message.reply_to_message and update.message.reply_to_message.from_user.is_bot and "Please reply to this message with the image" in update.message.reply_to_message.text) or (update.message.caption and update.message.caption.strip() == '/rti'):
            # Send typing action to indicate that the bot is processing
            update.message.chat.send_action(ChatAction.TYPING)
            
            # Define the API endpoint and headers
            url = "https://clipdrop-api.co/remove-text/v1"
            headers = {'x-api-key': CLIPDROP_API_KEY}
            
            # Get file_id of the photo
            file_id = update.message.photo[-1].file_id
            
            # Get the file path
            file = context.bot.get_file(file_id)
            file_path = file.file_path
            
            # Download the image
            image_content = requests.get(file_path).content
            
            # Send the POST request to the API
            files = {'image_file': ('image.png', image_content, 'image/png')}
            response = requests.post(url, headers=headers, files=files)
            
            # Check if the response is an image
            if response.status_code == 200 and response.headers['Content-Type'] == 'image/png':
                # Send the image back to the user
                update.message.reply_photo(photo=InputFile(io.BytesIO(response.content), filename='result.png'))
            else:
                # Try to parse the error message from the response
                try:
                    error_message = json.loads(response.text).get('error', 'Unknown error')
                except json.JSONDecodeError:
                    error_message = 'Unknown error'
                
                # Send an error message
                update.message.reply_text(f"An error occurred while removing text from the image: {error_message}")
    elif update.message.text == '/rti':
        # Send a message asking for an image
        update.message.reply_text("Please reply to this message with the image from which you want to remove text, or send an image with the caption '/rti'.")

def text_to_image(update: Update, context: CallbackContext):
    # Check if the command has any text input
    if context.args:
        # Join the text input into a single string
        prompt_text = ' '.join(context.args)
        update.message.chat.send_action(ChatAction.TYPING)
        # Define the API endpoint and headers
        url = "https://clipdrop-api.co/text-to-image/v1"
        headers = {'x-api-key': CLIPDROP_API_KEY}
        
        # Send the POST request to the API
        response = requests.post(url, headers=headers, files={'prompt': (None, prompt_text)})
        
        # Check if the response is an image
        if response.status_code == 200 and response.headers['Content-Type'] == 'image/png':
            # Send the image back to the user
            update.message.reply_photo(photo=InputFile(io.BytesIO(response.content), filename='result.png'))
        else:
            # Try to parse the error message from the response
            try:
                error_message = json.loads(response.text).get('error', 'Unknown error')
            except json.JSONDecodeError:
                error_message = 'Unknown error'
            
            # Send an error message
            update.message.reply_text(f"An error occurred while generating the image: {error_message}")
    else:
        # Send a message asking for input text
        update.message.reply_text("Please provide text input for the image generation. Example: /tti photograph of a cat surfing")

def check_pwned(update: Update, context: CallbackContext) -> None:
    """Check if an account has been pwned."""
    account = ' '.join(context.args)
    if not account:
        update.message.reply_text("Please provide an account to check. Example: /check_pwned account@example.com")
        return

    url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{account}"
    headers = {
        "User-Agent": "TelegramBot",
        "hibp-api-key": HIBP_API_KEY  # replace with your actual API key
    }
    response = requests.get(url, headers=headers)

    logger.info(f"Response status code: {response.status_code}")

    if response.status_code == 200:
        breaches = response.json()
        message = f"Oh no — pwned! {account} has been found in the following breaches:\n"
        for breach in breaches:
            message += f"- {breach['Name']}\n"
        logger.info(f"Account {account} has been pwned. Response: {breaches}")
    else:
        message = "Good news — no pwnage found!"
        logger.info(f"Account {account} has not been pwned.")

    update.message.reply_text(message)

def check_pastes(update: Update, context: CallbackContext) -> None:
    """Check if an account has been pasted."""
    account = ' '.join(context.args)
    if not account:
        update.message.reply_text("Please provide an account to check. Example: /check_pastes account@example.com")
        return

    url = f"https://haveibeenpwned.com/api/v3/pasteaccount/{account}"
    headers = {
        "User-Agent": "TelegramBot",
        "hibp-api-key": HIBP_API_KEY  # replace with your actual API key
    }
    response = requests.get(url, headers=headers)

    logger.info(f"Response status code: {response.status_code}")

    if response.status_code == 200:
        pastes = response.json()
        if pastes:
            message = f"Oh no — pwned! {account} has been found in the following pastes:\n"
            for paste in pastes:
                message += f"Source: {paste['Source']}, ID: {paste['Id']}, Title: {paste.get('Title', 'N/A')}, Date: {paste.get('Date', 'N/A')}, EmailCount: {paste['EmailCount']}"
                if paste['Source'].lower() == 'pastebin':
                    message += f", Link: https://pastebin.com/{paste['Id']}"
                message += "\n"
            logger.info(f"Account {account} has been pasted. Response: {pastes}")
        else:
            message = "Good news — no pastes found!"
    elif response.status_code == 404:
        message = "Good news — no pastes found!"
        logger.info(f"Account {account} has not been pasted.")
    else:
        message = "An error occurred while checking for pastes."
    update.message.reply_text(message)

def get_voices_request():
    """Send a request to the ElevenLabs Get Voices API."""
    try:
        url = "https://api.elevenlabs.io/v1/voices"
        headers = {"xi-api-key": XI_API_KEY }
                response = requests.get(url, headers=headers)
        return response.json()
    except Exception as e:
        logger.error(f"Error in get_voices_request: {e}")
        return None

def set_voice(update: Update, context: CallbackContext) -> None:
    """Handle the /set_voice command."""
    try:
        voice_id = update.message.text.replace('/set_voice', '', 1).strip()
        user_id = update.effective_user.id
        user_voice_choices[user_id] = voice_id
        update.message.reply_text(f"Your preferred voice has been set to {voice_id}.")
    except Exception as e:
        logger.error(f"Error in set_voice: {e}")

def view_voices(update: Update, context: CallbackContext) -> None:
    try:
        response = get_voices_request()
        voices = response['voices']
        message = "Available voices:\n"        
        for voice in voices:
            message += f"ID: {voice['voice_id']}, Name: {voice['name']}\n"
        update.message.reply_text(message)
    except Exception as e:
        logger.error(f"Error in view_voices: {e}")

def text_to_speech_request(text, voice_id):
    """Send a request to the ElevenLabs Text-to-Speech API."""
    try:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {"xi-api-key": XI_API_KEY}
        data = {"text": text}
        response = requests.post(url, headers=headers, json=data)
        audio_filename = "audio.mpeg"
        with open(audio_filename, 'wb') as f:
            f.write(response.content)
        return audio_filename
    except Exception as e:
        logger.error(f"Error in text_to_speech_request: {e}")
        return None


def text_to_speech(update: Update, context: CallbackContext) -> None:
    """Handle the /text_to_speech command."""
    user_input = update.message.text.replace('/text_to_speech', '', 1).strip()
    user_input = update.message.text.replace('/tts', '', 1).strip()    
    # Get the voice ID for the user, or use the default voice ID if the user doesn't have a voice choice
    user_id = update.effective_user.id
    voice_id = user_voice_choices.get(user_id, "21m00Tcm4TlvDq8ikWAM")
    
    audio_filename = text_to_speech_request(user_input, voice_id)
    
    # Send the audio file to the user
    with open(audio_filename, 'rb') as audio_file:
        context.bot.send_audio(chat_id=update.effective_chat.id, audio=audio_file)
    
    # Delete the audio file after sending it
    os.remove(audio_filename)
    
def claude(update: Update, context: CallbackContext) -> None:
    """Generate a response using the Anthropic API."""
    user_id = update.effective_user.id
    user_username = update.effective_user.username if update.effective_user.username else "No username"
    user_input = update.message.text

    # Remove the '/claude' command from the user's input
    user_input = user_input.replace('/claude', '', 1).strip()

    context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    # Send the user's input to the Anthropic API
    claude_response = claude_request(user_input)

    # Send the response back to the user
    context.bot.send_message(chat_id="-1001860214585", text=f"User {user_id} ({user_username}) sent: {user_input}\nClaude responded with: {claude_response}")
    update.message.reply_text(claude_response)

def image(update: Update, context: CallbackContext) -> None:
    """Generate an image using the Stability.ai API."""
    user_id = update.message.from_user.id
    user_input = update.message.text
    # Remove the '/image' command from the user's input
    user_input = user_input.replace('/image', '', 1).strip()
    # Generate the image

    context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_PHOTO)
    if not user_input:
        update.message.reply_text("Please provide a description for the image.")
        return
    image_response = generate_image(user_input, user_id)

    # Check if the response is not None
    if image_response is not None:
        # Iterate through all the image file paths
        for image_filepath in image_response:
            # Send the image file to the user
            with open(image_filepath, 'rb') as img:
                context.bot.send_photo(chat_id=update.effective_chat.id, photo=img)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I couldn't generate the image. Please try again.")

def transform_image_command(update: Update, context: CallbackContext) -> int:
    LOGGER.info("User called /transform_image in trabsform_image_command")
    """Ask the user for an image and a text prompt to transform."""
    update.message.reply_text("Please send an image you want to transform with a text caption.")
    return IMAGE



def start(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /start is issued."""
    user_id = update.effective_user.id
    LOGGER.debug(f"User {user_id} started the bot")
    user_id = update.effective_user.id
    user_username = update.effective_user.username or "No username"
    LOGGER.debug(f"User {user_id} ({user_username}) started the bot")
    add_user_to_csv(user_id, user_username)
    conversation_history[user_id] = {
        'history': [],
        'assistant_role': 'You are ChatGPT, a large language model trained by OpenAI.',
    }
    update.message.reply_text('Hi! Send me a message, and I will use the OpenAI API to generate a response.')

    private_chat_id = TELE_LOG_CHANNEL # replace with your private chat id
    context.bot.send_message(chat_id=private_chat_id, text=f"User {user_id} ({user_username}) started the bot")


def list_models(update: Update, context: CallbackContext) -> None:
    """List all available GPT models."""
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        update.message.reply_text("Sorry, you don't have permission to use this command.")
        return

    models = openai.Model.list()
    models_list = [model.id for model in models.data]

    # Convert list of models to string
    models_str = "\n".join(models_list)

    update.message.reply_text(f"Here are the available GPT models:\n\n{models_str}")

def reset_session(update: Update, context: CallbackContext) -> None:
    """Reset the session ID when the command /reset is issued."""
    user_id = update.effective_user.id
    LOGGER.debug(f"User {user_id} reset the session")
    conversation_history[user_id] = {
        'history': [],
        'assistant_role': 'You are ChatGPT, a large language model trained by OpenAI.',
    }
    update.message.reply_text('Session reset! You can now start a new conversation.')

def echo(update: Update, context: CallbackContext) -> None:
    message = update.message
    user_id = update.effective_user.id
    user_input = message.text
    BOT_USERNAME = context.bot.username
    user_username = update.effective_user.username  or "No Username" # Get the username
    LOGGER.debug(f"Received message from user {user_id} ({user_username}): {user_input}")
    user_id = update.effective_user.id
    user_username = update.effective_user.username or "No username"
    new_user = User(user_id)  # Create a new User instance
    if new_user not in User.unique_users:
        User.unique_users.add(new_user)
        with open('unique_users.txt', 'a') as f:  # 'a' for append mode
            f.write(f"{new_user.id}\n")  # use new_user.id or user_id
        LOGGER.debug(f"Added user {user_id} ({user_username}) to unique users")
    # Check if the chat is private (DM) or the bot is mentioned in a group chat
    is_private_chat = message.chat.type == "private"
    mentioned = any(
        entity.type == MessageEntity.TEXT_MENTION or (
            entity.type == MessageEntity.MENTION and
            message.text[entity.offset:entity.offset+entity.length].lower() == f"@{BOT_USERNAME}".lower()
        )
        for entity in message.entities
    )

    if not is_private_chat and not mentioned:
        return

    if mentioned:
        # Remove mention from user's input
        user_input = remove_mention(user_input, f"@{BOT_USERNAME}")

    context.bot.send_chat_action(chat_id=message.chat_id, action=ChatAction.TYPING)

    LOGGER.debug(f"Received message from user {user_id}: {user_input}")

    # Get user data, which includes conversation history and assistant's role
    user_data = conversation_history.get(user_id, {
        'history': [],
        'assistant_role': 'You are ChatGPT, a large language model trained by OpenAI.',
    })
    history = user_data['history']

    # Add current user input to conversation history
    history.append(user_input)

    # Use conversation history as prompt for OpenAI API request
    prompt = "\n".join(history[-3:])
    chatgpt_response = chatgpt_request(prompt, history, user_data['assistant_role'])
    # Add OpenAI API response to conversation history
    history.append(chatgpt_response)

    # Save updated user data, including conversation history and role
    user_data['history'] = history
    conversation_history[user_id] = user_data

    # Check if the response_text is empty and provide a fallback message
    if not chatgpt_response.strip():
        chatgpt_response = "I'm sorry, I couldn't generate a response. Please try again."

    # Send OpenAI API response to user
    message.reply_text(chatgpt_response)
    channel_id = "-1001860214585"
    context.bot.send_message(chat_id=channel_id, text=f"User ID: {user_id}\nUsername: {user_username}\nUser: {user_input}\nBot: {chatgpt_response}")
    # Write conversation history to file
    with open(f"{user_id}.txt", "w") as f:
        f.write("\n".join(history))


def set_assistant_role(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    user_data = conversation_history.get(user_id, {
        'history': [],
        'assistant_role': 'You are ChatGPT, a large language model trained by OpenAI.',
    })

    args = context.args

    if not args:
        update.message.reply_text("Please provide a role. Example: /set_assistant_role assistant")
        return

    new_role = " ".join(args)
    user_data['assistant_role'] = f"You are {new_role}, a language model trained by OpenAI."
    conversation_history[user_id] = user_data
    update.message.reply_text(f"Assistant role has been set to: {new_role}")

def help_command(update: Update, context: CallbackContext) -> None:
    """Send a message when the command /help is issued."""
    help_text = """Here are the commands I understand:

    Basic interaction:
    /start - Start the bot (OpenAI's GPT-4).
    /claude - Generate a response using the Anthropic API (Claude), similar to GPT-4.
    /reset - Reset the current conversation.
    /set_assistant_role <role> - Set the assistant role.
    /history - Show the conversation history.
    *Note: Normal conversation uses OpenAI's ChatGPT-4 for generating responses.

    Image Generation & Processing:
    /image - Generate an image based on a text prompt (Stability.ai).
    /text_to_image or /tti - Convert text to an image (ClipDrop API).
    /transform_image - Generate an image using another image as a base (needs an image with a caption).
    /list_style_presets - List available style presets for image generation (Stability.ai).
    /set_style_preset <preset> - Set your preferred style preset for image generation (Stability.ai).
    /leo - Generate an image using Leonardo API based on a text prompt. Type '/leo help' for more information.
    /remove_text_from_image or /rti - Remove text from an image (ClipDrop API).

    Text-to-Speech:
    /tts - Convert text into speech (ElevenLabs).
    /set_voice <voice_id> - Set your preferred voice for TTS (ElevenLabs).
    /view_voices - View available TTS voices (ElevenLabs).

    Security:
    /check_pwned <email> - Check an email account for breaches.
    /check_pastes <email> - Check an email account for breaches.

    Statistics:
    /stats - Show some statistics about the bot.

    General:
    /help - Show this help message.
    """

    update.message.reply_text(help_text)

def announcement(update: Update, context: CallbackContext) -> None:
    """Send an announcement to all users."""
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        update.message.reply_text("Sorry, you don't have permission to use this command.")
        return

    announcement_text = " ".join(context.args)
    if not announcement_text:
        update.message.reply_text("Please provide a message to announce. Example: /announcement Hello, users!")
        return

    for user in User.unique_users:
        user_id = user.id  # Access ID from User object
        try:
            context.bot.send_message(chat_id=user_id, text=announcement_text)
            LOGGER.debug(f"Sent announcement to user {user_id}")
        except Exception as e:
            logger.warning(f"Failed to send announcement to user {user_id}: {e}")
    update.message.reply_text("Announcement sent.")

def stats(update: Update, context: CallbackContext) -> None:
    """Display statistics about the conversation history."""
    user_id = update.effective_user.id
    user_data = conversation_history.get(user_id, {'history': []})
    history = user_data['history']

    num_messages = len(history)
    num_assistant_messages = len([msg for msg in history if msg.startswith('Assistant:')])
    num_user_messages = num_messages - num_assistant_messages

    # Calculate the average length of user messages
    user_messages = [msg for msg in history if not msg.startswith('Assistant:')]
    user_message_lengths = [len(msg) for msg in user_messages]
    if user_message_lengths:
        avg_user_message_length = sum(user_message_lengths) / len(user_message_lengths)
    else:
        avg_user_message_length = 0

    # Create stats message
    stats_message = (
        f"Number of messages: {num_messages}\n"
        f"Number of assistant messages: {num_assistant_messages}\n"
        f"Number of user messages: {num_user_messages}\n"
        f"Average length of user messages: {avg_user_message_length:.2f} characters"
    )

    # Send stats message to user
    update.message.reply_text(stats_message)

    # Save stats to file
    with open(f"{user_id}_stats.txt", "w") as f:
        f.write(stats_message)

def view_history(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    user_data = conversation_history.get(user_id, {
        'history': [],
        'assistant_role': 'You are ChatGPT, a large language model trained by OpenAI.',
    })

    history = user_data['history']
    if not history:
        update.message.reply_text("You don't have any conversation history yet.")
        return

    # Limit the history to the most recent 10 messages
    history = history[-10:]

    # Send the history string to the user
    history_str = "\n".join(history)
    update.message.reply_text(f"Here is your conversation history:\n\n{history_str}")


def error(update: Update, context: CallbackContext) -> None:
    """Log errors caused by updates."""
    LOGGER.info(f"Type of context.error: {type(context.error)}")  # Add this line
    LOGGER.warning(f"Update {update} caused error {context.error}")

def leo(update: Update, context: CallbackContext) -> None:
    if context.args:
        if context.args[0].lower() == 'help':
            help_text = """
            Parameters for /leo command:
            - prompt: The prompt used to generate images (required)

            By default, promptMagic is set to True and the sd_version is set to v2.
            """
            update.message.reply_text(help_text)
        else:
            user_input = ' '.join(context.args)
            apikey = LEONARDO_API_KEY
            url = "https://cloud.leonardo.ai/api/rest/v1/generations"
            headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer " + apikey  # Replace with your actual token
            }
            payload = {
                "prompt": user_input,
                "promptMagic": True,
                "sd_version": "v2",
                "modelId": "291be633-cb24-434f-898f-e662799936ad",
                "num_images": 1
            }

            try:
                update.message.reply_text('Processing your request...')
                response = requests.post(url, headers=headers, data=json.dumps(payload))
                response.raise_for_status()
            except requests.exceptions.HTTPError as errh:
                update.message.reply_text("An HTTP error occurred:" + repr(errh))
                return
            except requests.exceptions.ConnectionError as errc:
                update.message.reply_text("A Connection error occurred:" + repr(errc))
                return
            except requests.exceptions.Timeout as errt:
                update.message.reply_text("A Timeout error occurred:" + repr(errt))
                return
            except requests.exceptions.RequestException as err:
                update.message.reply_text("An error occurred:" + repr(err))
                return

            # Extract the generationId from the response
            generationId = response.json().get('sdGenerationJob', {}).get('generationId')
            if generationId is None:
                update.message.reply_text('Could not find a generationId in the response.')
                return

            # Use the generationId to make a GET request to retrieve the image
            get_url = f"https://cloud.leonardo.ai/api/rest/v1/generations/{generationId}"
            
            update.message.reply_text('Generation started, waiting for the image...')
            for _ in range(10):  # Try 10 times with a delay
                try:
                    get_response = requests.get(get_url, headers=headers)
                    get_response.raise_for_status()
                    
                    # Assuming the API response includes a JSON with 'generations_by_pk' field which has 'generated_images' list
                    image_urls = get_response.json().get('generations_by_pk', {}).get('generated_images', [])
                    if image_urls:
                        update.message.reply_text('Image generation completed, sending the images...')
                        for image in image_urls:
                            image_url = image.get('url')
                            context.bot.send_photo(chat_id=update.effective_chat.id, photo=image_url)
                        break  # If images are found, break the loop

                    time.sleep(10)  # Wait for 10 seconds before trying again
                except requests.exceptions.HTTPError as errh:
                    update.message.reply_text("An HTTP error occurred while retrieving the image:" + repr(errh))
                    return
                except requests.exceptions.ConnectionError as errc:
                    update.message.reply_text("A Connection error occurred while retrieving the image:" + repr(errc))
                    return
                except requests.exceptions.Timeout as errt:
                    update.message.reply_text("A Timeout error occurred while retrieving the image:" + repr(errt))
                    return
                except requests.exceptions.RequestException as err:
                    update.message.reply_text("An error occurred while retrieving the image:" + repr(err))
                    return
            else:
                update.message.reply_text('No images were found in the response after 10 attempts.')
    else:
        update.message.reply_text('Please provide an argument for /leo command. Type /leo help for more information.')
