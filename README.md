# Telegram Machine Learning Demo Bot

This Telegram bot offers various functionalities, including text-based conversations, image processing, and text-to-speech conversion, utilizing APIs such as OpenAI's GPT-4, Stability.ai, ClipDrop AI, ElevenLabs, and Leonardo.

## Features

### Text-based Conversations
- **Claude (`/claude`)**: Generate a response using the Anthropic API (Claude), similar to GPT-4.
- **Regular Conversations**: Engage in text-based conversations with the bot, powered by OpenAI's GPT-4.

### Image Generation & Processing
- **Generate Image (`/image`)**: Generate an image based on a text prompt using Stability.ai.
- **Text to Image (`/text_to_image` or `/tti`)**: Convert text to an image using the ClipDrop API. Endpoint: `https://clipdrop-api.co/text-to-image/v1`.
- **Remove Text from Image (`/remove_text_from_image` or `/rti`)**: Remove text from an image using the ClipDrop API. Endpoint: `https://clipdrop-api.co/remove-text/v1`.
- **Transform Image (`/transform_image`)**: Transform an image using Stability.ai.
- **List Style Presets (`/list_style_presets`)**: List available style presets for image transformation using Stability.ai.
- **Set Style Preset (`/set_style_preset`)**: Set your preferred style preset for image generation using Stability.ai.
- **Leo (`/leo`)**: Generate an image using the Leonardo API based on a text prompt.

### Text-to-Speech (ElevenLabs)
- **View & Set Voices (`/view_voices` & `/set_voice`)**: View and set voices for text-to-speech using ElevenLabs.
- **Text to Speech (`/text_to_speech` or `/tts`)**: Convert text to speech using ElevenLabs.

### General Commands
- **Start (`/start`)**: Initiates the bot interaction.
- **Reset (`/reset`)**: Resets the user session.
- **Stats (`/stats`)**: Retrieves bot statistics.
- **Help (`/help`)**: Displays help information.
- **History (`/history` or `/view_history`)**: Views user interaction history.
- **Cancel (`/cancel`)**: Cancels the current action.

## Usage

Users can interact with the bot by sending specific commands. Refer to the `/help` command for detailed usage instructions.

## Installation and Setup

1. **Clone the Repository**: Clone this repository to your local machine.
2. **Install Dependencies**: Install required dependencies using `pip install -r requirements.txt`.
3. **Configure Environment Variables**: Modify config.py with yoru API keys.
4. **Run the Bot**: Execute the `main.py` script to start the bot.

## Contributing

Feel free to contribute to the project by opening issues, submitting pull requests, or suggesting new features.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
