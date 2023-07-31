from PIL import Image
import base64
import csv
import openai
import requests
import os
import base64
from datetime import datetime
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater, CallbackContext, ConversationHandler
from telegram import Update, ChatAction
from library.config import OPENAI_API_KEY, LOGGER, STABILITY_API_KEY, CLAUDE_API_KEY
openai.api_key = OPENAI_API_KEY
STYLE_PRESETS = ["3d-model", "analog-film", "anime", "cinematic", "comic-book", "digital-art", "enhance", "fantasy-art", "isometric", "line-art", "low-poly", "modeling-compound", "neon-punk", "origami", "photographic", "pixel-art", "tile-texture"]
DEFAULT_STYLE_PRESET = "cinematic"
style_presets = {
    "3d-model": "3d-model",
    "analog-film": "analog-film",
    "anime": "anime",
    "cinematic": "cinematic",
    "comic-book": "comic-book",
    "digital-art": "digital-art",
    "enhance": "enhance",
    "fantasy-art": "fantasy-art",
    "isometric": "isometric",
    "line-art": "line-art",
    "low-poly": "low-poly",
    "modeling-compound": "modeling-compound",
    "neon-punk": "neon-punk",
    "origami": "origami",
    "photographic": "photographic",
    "pixel-art": "pixel-art",
    "tile-texture": "tile-texture",
    "none":"none"
}

USER_STYLE_PRESETS = {}

def add_user_to_csv(user_id: int, user_username: str) -> None:
    """Add a new user to the CSV file if they are not already in it."""
    with open('user_data.csv', 'r') as f:
        reader = csv.reader(f)
        users = list(reader)

    if [str(user_id), user_username] not in users:
        users.append([str(user_id), user_username])
        with open('user_data.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(users)

def remove_mention(text: str, mention: str) -> str:
    """Remove the bot's mention from the text."""
    return text.replace(mention, "", 1).strip()

def chatgpt_request(prompt: str, history: list, assistant_role: str) -> str:
    """Use the OpenAI API to generate a response to the user message."""
    LOGGER.debug(f"Sending prompt to OpenAI API: {prompt}")
    message_list = [{'role': 'system', 'content': assistant_role}]
    message_list.extend([
        {'role': 'user', 'content': user_msg} if i % 2 == 0 else {'role': 'assistant', 'content': user_msg}
        for i, user_msg in enumerate(history[-3:])
    ])

    response = openai.ChatCompletion.create(
        model="gpt-4-0613",
        messages=message_list,
        max_tokens=4000,
        temperature=0.7,
    )

    response_text = response.choices[0].message.content.strip()
    return response_text

def claude_request(prompt: str) -> str:
    """Send a request to the Anthropic API and return the response."""
    url = "https://api.anthropic.com/v1/complete"
    headers = {
        "x-api-key": CLAUDE_API_KEY,
        "Content-Type": "application/json"
    }
    body = {
        "prompt": "\n\nHuman: " + prompt + "\n\nAssistant: ",
        "model": "claude-2",
        "max_tokens_to_sample": 300,
        "stop_sequences": ["\n\nHuman:"]
    }

    response = requests.post(url, headers=headers, json=body)
    response_json = response.json()

    if 'error' in response_json:
        LOGGER.warning(f"Error: {response_json['error']['message']}")
        return

    generated_text = response_json.get('completion')
    if generated_text is None:
        LOGGER.warning(f"Unexpected API response: {response_json}")
    return generated_text

def set_style_preset(update: Update, context: CallbackContext) -> None:
    """Set the style preset for the user."""
    user_id = update.message.from_user.id
    style_preset = ' '.join(context.args)
    if style_preset not in STYLE_PRESETS:
        update.message.reply_text(f"Invalid style preset. Please choose from the following: {', '.join(STYLE_PRESETS)}")
    else:
        USER_STYLE_PRESETS[user_id] = style_preset
        update.message.reply_text(f"Style preset set to {style_preset}.")

def generate_image(prompt: str, user_id: int, n: int = 1, size: str = '1024x1024', response_format: str = 'url'):
    """Generate an image using the Stability.ai API."""

    engine_id = "stable-diffusion-xl-1024-v1-0"  # Replace with your chosen engine ID
    url = f"https://api.stability.ai/v1/generation/{engine_id}/text-to-image"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {STABILITY_API_KEY}"
    }
    data = {
        "text_prompts": [
            {
                "text": prompt
            }
        ],
        "cfg_scale": 7.0,
        "clip_guidance_preset": "FAST_BLUE",
        "samples": 1,
        "steps": 50,
        "style_preset": get_style_preset(user_id),  # Use the style_preset for the user
        "width": 1024,
        "height": 1024
    }

    # LOGGER.info(f"URL: {url}")  # Log the URL
    # LOGGER.info(f"Headers: {headers}")  # Log the headers
    # LOGGER.info(f"Data: {data}")  # Log the data
    response = requests.post(url, headers=headers, json=data)
    # response_content = response.content

    # LOGGER.info(f"/n/nResponse: {response.content}/n/n")
    try:
        response_json = response.json()
    except ValueError:
        LOGGER.error("No JSON object could be decoded from the response.")
        return None

    if 'error' in response_json:
        LOGGER.warning(f"Error: {response_json['error']['message']}")
        return None

    # Save the image
    image_filenames = []
    for i, image in enumerate(response_json["artifacts"]):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"./images/v1_txt2img_{timestamp}_{i}.png"
        with open(filename, "wb") as f:
            f.write(base64.b64decode(image["base64"]))
        image_filenames.append(filename)

    return image_filenames

def get_style_preset(user_id: int) -> str:
    """Get the style preset for the user."""
    return USER_STYLE_PRESETS.get(user_id, DEFAULT_STYLE_PRESET)

def transform_image(update: Update, context: CallbackContext) -> bool:

    """Transform an image using the Stability.ai API."""
    LOGGER.info(f"Type of context.bot.send_chat_action: {type(context.bot.send_chat_action)}")
    LOGGER.info(f"Type of context.bot.send_photo: {type(context.bot.send_photo)}")
    LOGGER.info(f"Type of context.bot.send_message: {type(context.bot.send_message)}")
    user_id = update.effective_user.id
    LOGGER.info("Sending chat action...")
    context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.UPLOAD_PHOTO)
    LOGGER.info("Chat Action sent.")    
    # Check if the message contains any photo
    if update.message.photo:
        # Get the photo file from the message
        photo_file = update.message.photo[-1].get_file()
        # Download the photo and save it locally
        photo_file.download('input_image.jpg')
        image_path = 'input_image.jpg'
    else:
        update.message.reply_text("Please send an image.")
        return False

    # Get the text prompt from the caption of the image
    text_prompt = update.message.caption
    if not text_prompt:
        update.message.reply_text("Please provide a text prompt as the caption of the image.")
        return False

    image_response = stability_transform(image_path, text_prompt, user_id, context)

    if image_response is not None:
    # Iterate through all the image file paths
        for image_filepath in image_response:
            # Send the image file to the user
            with open(image_filepath, 'rb') as img:
                LOGGER.info(f"Sending image: {image_filepath}")
                context.bot.send_photo(chat_id=update.effective_chat.id, photo=img)
                LOGGER.info(f"Image sent: {image_filepath}")
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I couldn't transform the image. Please try again.")
    return ConversationHandler.END

def resize_image(input_image_path, output_image_path, size):
    original_image = Image.open(input_image_path)
    width, height = original_image.size
    # check if the image needs to be resized
    if width > size[0] or height > size[1]:
        ratio = min(size[0]/width, size[1]/height)
        new_size = tuple([int(x*ratio) for x in original_image.size])
        resized_img = original_image.resize(new_size, Image.ANTIALIAS)
        resized_img.save(output_image_path)
    else:
        original_image.save(output_image_path)

def stability_transform(image_path: str, text_prompt: str, user_id: int, context: CallbackContext) -> list:
    """Transform an image using the Stability.ai API."""
    engine_id = "stable-diffusion-xl-beta-v2-2-2"  # Replace with your chosen engine ID
    url = f"https://api.stability.ai/v1/generation/{engine_id}/image-to-image"
    headers = {
        "Authorization": f"Bearer {STABILITY_API_KEY}"
    }
    context.bot.send_message(chat_id=user_id, text="Processing your request. This may take a few moments...")

    context.bot.send_chat_action(chat_id=user_id, action=ChatAction.TYPING)

    resized_image_path = "resized_" + image_path
    resize_image(image_path, resized_image_path, (512, 896))

    # Prepare the multipart/form-data request
    multipart_form_data = {
        "init_image": (resized_image_path, open(resized_image_path, "rb")),
        "text_prompts[0][text]": (None, text_prompt),
        "cfg_scale": (None, '7.0'),
     }

    LOGGER.info(f"URL: {url}")  # Log the URL
    LOGGER.info(f"Headers: {headers}")  # Log the headers
    try:
        response = requests.post(url, headers=headers, files=multipart_form_data)
    except Exception as e:
        LOGGER.error(f"An error occurred while making the API request: {e}")
        return ConversationHandler.END
    LOGGER.info(f"Response: {response}")

    LOGGER.info(f"Response status code: {response.status_code}")
    if response.status_code == 500:
        LOGGER.error("Received a 500 error from the API")
        return None

    try:
        response_json = response.json()
    except ValueError:
        LOGGER.error("No JSON object could be decoded from the response.")
        return ConversationHandler.END

    if 'error' in response_json:
        LOGGER.warning(f"Error: {response_json['error']['message']}")
        return None

    # Save the image
    image_filenames = []
    for i, image in enumerate(response_json["artifacts"]):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"./images/v1_img2img_{timestamp}_{i}.png"
        with open(filename, "wb") as f:
            f.write(base64.b64decode(image["base64"]))
        image_filenames.append(filename)
    LOGGER.info(f"Type of image_filenames: {type(image_filenames)}")
    LOGGER.info(f"Value of image_filenames: {image_filenames}")
    LOGGER.info("Stability_Transform Function completed")    
    return image_filenames
