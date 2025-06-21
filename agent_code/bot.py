import logging
from telegram import Update
from telegram.ext import Updater, CallbackContext, MessageHandler, Filters
from utils import get_embedding
import pickle
from scipy.spatial.distance import cosine
from openai import OpenAI
from config import OPEN_AI_API_KEY, TELEGRAM_BOT_TOKEN

MESSAGE_HISTORY_SIZE = 5  # Number of previous messages to consider for context
MESSAGE_HISTORY = []  # List to store the last messages and answers

# Given a query embedding, compute the text of all the documentation pages which are the most relevant to the query.
def get_top_k_similar_text(query_embedding, k=5):
    similarities = []
    for url, doc_embedding in url_to_embedding.items():
        sim = 1 - cosine(query_embedding, doc_embedding)  # cosine similarity
        similarities.append((url, sim))
    similarities.sort(key=lambda x: x[1], reverse=True)
    best_urls = list(map(lambda x : x[0], similarities[:k]))
    return "\n".join(list(map(lambda x : url_to_text[x], best_urls)))

def message_handler(update: Update, context: CallbackContext) -> None:
    current_message = update.message.text
    print(f'{update.message.from_user.first_name} wrote {current_message}')
    current_message_embedding = get_embedding(current_message)
    if current_message_embedding is None:
        update.message.reply_text('Sorry, I could not process your message.')
        return
    current_message_retrieved_content = get_top_k_similar_text(current_message_embedding)
    
    previous_messages = "\n".join(MESSAGE_HISTORY[-MESSAGE_HISTORY_SIZE:])
    if previous_messages:
        previous_messages_embedding = get_embedding(previous_messages)
        previous_messages_retrieved_content = get_top_k_similar_text(previous_messages_embedding)
    else:
        previous_messages_retrieved_content = ""

    prompt = f"""You are a helpful assistant answering based on documentation.
    Answer the question based on the relevant documentation above. If you don't know the answer, say "I don't know".
    Limit your answer to 200 words by summarizing. In case the user is vague, ask for clarification.
    Relevant documentation:
    {current_message_retrieved_content}
    {previous_messages_retrieved_content}
    Question:
    {current_message}
    Previous questions and answers:
    {previous_messages}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )
    response_message = response.choices[0].message.content.strip()
    update.message.reply_text(response_message)
    MESSAGE_HISTORY.append(f"User: {current_message}\nAssistant: {response_message}")

updater = Updater(TELEGRAM_BOT_TOKEN)
client = OpenAI(api_key=OPEN_AI_API_KEY)
logger = logging.getLogger(__name__)

with open("url_split_merges_to_embedding.pkl", "rb") as f:
    url_to_embedding = pickle.load(f)
with open("url_splits_merges_to_text.pkl", "rb") as f:
    url_to_text = pickle.load(f)
  
# Get the dispatcher to register handlers
# Then, we register each handler and the conditions the update must meet to trigger it
dispatcher = updater.dispatcher
dispatcher.add_handler(MessageHandler(~Filters.command, message_handler))

# Start the Bot
updater.start_polling()

# Run the bot until you press Ctrl-C
updater.idle()

