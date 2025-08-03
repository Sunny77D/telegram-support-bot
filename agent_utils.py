import logging
import time

from openai import OpenAI
from scipy.spatial.distance import cosine
from supabase import create_client

from config import OPEN_AI_API_KEY, SUPABASE_KEY, SUPABASE_URL
from supportbot.clients.crawl.dataclasses import ChunkAndEmbedding
from supportbot.clients.messages.dataclasses import Message

logger = logging.getLogger(__name__)


def get_embedding(text, model="text-embedding-3-small"):
    client = OpenAI(api_key=OPEN_AI_API_KEY)
    try:
        response = client.embeddings.create(
            input=text,
            model=model
        )
        time.sleep(1)  # Uncomment if you need to add a delay
        return response.data[0].embedding
    except Exception as e:
        logger.error(f"Error getting embedding: {str(e)}")
        return None


async def send_message(
    message: str,
    crawls_chunks_text_and_embedding: list[ChunkAndEmbedding],
    message_chunks_text_and_embedding: list[ChunkAndEmbedding],
    message_history: list[str],
    message_history_size: int = 5,
    chat_message_history: list[Message] | None = None,
    user_message_history: list[Message] | None = None
) -> str:
    message_embedding = get_embedding(message)
    if message_embedding is None:
        raise ValueError("Could not get embedding for the message.")
    retrived_content = get_top_k_similar_text(message_embedding, crawls_chunks_text_and_embedding)
    retrived_relevant_message_chunks = get_top_k_similar_text(message_embedding, message_chunks_text_and_embedding)
    previous_messages = "\n".join(message_history[-message_history_size:])
    if previous_messages:
        previous_messages_embedding = get_embedding(previous_messages)
        previous_messages_retrieved_content = get_top_k_similar_text(previous_messages_embedding, crawls_chunks_text_and_embedding)
        previous_messages_retrieved_relevant_message_chunks = get_top_k_similar_text(previous_messages_embedding, message_chunks_text_and_embedding)
    else:
        previous_messages_retrieved_content = ""
        previous_messages_retrieved_relevant_message_chunks = ""

    prompt = f"""You are a helpful assistant answering based on documentation.
    Answer the question based on the relevant documentation and historical context below.
    Limit your answer to 200 words by summarizing. In case the user is vague, ask for clarification.
    If the question is not relevant to the documentation, say "I don't know".
    Question:
    {message}
    Previous questions and answers:
    {previous_messages}
    Relevant documentation:
    {retrived_content}
    {previous_messages_retrieved_content}
    Relevant historical context from other conversations:
    {retrived_relevant_message_chunks}
    {previous_messages_retrieved_relevant_message_chunks}
    """
    if chat_message_history:
        prompt += "\nThis the last few messages from the current chat feel free to use this to answer the question:"
        for chat_message in chat_message_history:
            prompt += f"\n{chat_message.message} (from {chat_message.chat_name}) at {chat_message.created_at if chat_message.created_at else 'unknown time'}"
    if user_message_history:
        prompt += "\nThis the last few messages from the current user across all chats asking the question ONLY use this IF it answers the question the information below is very sensitive:"
        for user_message in user_message_history:
            prompt += f"\n{user_message.message} (from {user_message.username}) at {user_message.created_at if user_message.created_at else 'unknown time'} from the chat {user_message.chat_name}"
    client = OpenAI(api_key=OPEN_AI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    )
    response_message = response.choices[0].message.content.strip()
    message_history.append(f"User: {message}\nAssistant: {response_message}")
    return response_message


# Given a query embedding, compute the text of all the documentation pages which are the most relevant to the query.
def get_top_k_similar_text(query_embedding, chunks_text_and_embedding, k=5):
    similarities = []
    for chunk in chunks_text_and_embedding:
        sim = 1 - cosine(query_embedding, chunk.embedding)  # cosine similarity
        similarities.append((chunk.chunk, sim))
    similarities.sort(key=lambda x: x[1], reverse=True)
    best_chunks = list(map(lambda x: x[0], similarities[:k]))
    return "\n".join(best_chunks)


def get_chunks_text_and_embedding(
    table_name: str,
    chunk_column_name: str = 'chunk',
    embedding_column_name: str = 'chunk_embedding'
) -> list[ChunkAndEmbedding]:
    supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    response = (
        supabase_client.table(table_name)
        .select(f"{chunk_column_name}, {embedding_column_name}")
        .not_.is_(embedding_column_name, None)
        .execute()
    )
    rows = response.data
    return list(map(lambda row: ChunkAndEmbedding(
        chunk=row[chunk_column_name],
        embedding=row[embedding_column_name]
    ), rows))
