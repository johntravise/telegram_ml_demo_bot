from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
from library.config import TELEGRAM_TOKEN
from library.handlers import start, cancel, reset_session, echo, view_voices,check_pastes, set_voice, text_to_speech, set_assistant_role, stats, help_command, view_history, list_style_presets, set_style_preset, list_models, claude, announcement, image, error, check_pwned, transform_image_command, IMAGE, text_to_image, remove_text_from_image, leo
from library.utils import transform_image
def run_bot():
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Add handlers to the bot dispatcher
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('reset', reset_session))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))
    dispatcher.add_handler(CommandHandler('tti', text_to_image, pass_args=True))
    dispatcher.add_handler(CommandHandler('set_assistant_role', set_assistant_role, pass_args=True))
    dispatcher.add_handler(CommandHandler('rti', remove_text_from_image))
    dispatcher.add_handler(MessageHandler(Filters.photo & Filters.reply, remove_text_from_image))    
    dispatcher.add_handler(CommandHandler('stats', stats))
    dispatcher.add_handler(CommandHandler('help', help_command))
    dispatcher.add_handler(CommandHandler('history', view_history))
    dispatcher.add_handler(CommandHandler('list_models', list_models))
    dispatcher.add_handler(CommandHandler('claude', claude))
    dispatcher.add_handler(CommandHandler('announcement', announcement, pass_args=True))
    dispatcher.add_handler(CommandHandler("image", image))
    dispatcher.add_handler(CommandHandler('view_voices', view_voices))
    dispatcher.add_handler(CommandHandler('set_voice', set_voice))
    dispatcher.add_handler(CommandHandler('text_to_speech', text_to_speech))
    dispatcher.add_handler(CommandHandler('tts', text_to_speech))
    dispatcher.add_handler(CommandHandler('list_style_presets', list_style_presets))
    dispatcher.add_handler(CommandHandler('set_style_preset', set_style_preset, pass_args=True))
    dispatcher.add_handler(CommandHandler("check_pwned", check_pwned))
    dispatcher.add_handler(CommandHandler("check_pastes", check_pastes))
    dispatcher.add_handler(CommandHandler('leo', leo))

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('transform_image', transform_image_command)],
        states={
            IMAGE: [MessageHandler(Filters.photo, transform_image)],
        },
         fallbacks=[CommandHandler('cancel', cancel)],
    )
    dispatcher.add_handler(conv_handler)

    dispatcher.add_error_handler(error)

    # Start the bot
    updater.start_polling()
    updater.idle()

