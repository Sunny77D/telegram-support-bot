import logging
from telegram import Update
from telegram.ext import Updater, CallbackContext, MessageHandler, Filters
from .. import agent_utils
from .. import config

MESSAGE_HISTORY_SIZE = 5  # Number of previous messages to consider for context
MESSAGE_HISTORY = []  # List to store the last messages and answers

def message_handler(update: Update, context: CallbackContext) -> None:
    current_message = update.message.text
    print(f'{update.message.from_user.first_name} wrote {current_message}')
    chunks_text_and_embedding = agent_utils.get_chunks_text_and_embedding()
    response_message = agent_utils.send_message(current_message, chunks_text_and_embedding, MESSAGE_HISTORY, MESSAGE_HISTORY_SIZE)
    update.message.reply_text(response_message)
    MESSAGE_HISTORY.append(f"User: {current_message}\nAssistant: {response_message}")

updater = Updater(config.TELEGRAM_BOT_TOKEN)
logger = logging.getLogger(__name__)

  
# Get the dispatcher to register handlers
# Then, we register each handler and the conditions the update must meet to trigger it
dispatcher = updater.dispatcher
dispatcher.add_handler(MessageHandler(~Filters.command, message_handler))

# Start the Bot
updater.start_polling()

# Run the bot until you press Ctrl-C
updater.idle()

