from openai import OpenAI
from scipy.spatial.distance import cosine
from supportbot.clients.crawl.dataclasses import ChunkAndEmbedding
from supabase import create_client
from config import SUPABASE_KEY, SUPABASE_URL, OPEN_AI_API_KEY

def get_embedding(text, model="text-embedding-3-small"):
    client = OpenAI(api_key=OPEN_AI_API_KEY)
    try:
        response = client.embeddings.create(
            input=text,
            model=model
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error embedding text: {e}")
        return None

def send_message(
        message : str, 
        crawls_chunks_text_and_embedding : list[ChunkAndEmbedding],
        message_history : list[str], 
        message_history_size : int = 5
    ) -> str:
    message_embedding = get_embedding(message)
    if message_embedding is None:
        raise ValueError("Could not get embedding for the message.")
    retrived_content = get_top_k_similar_text(message_embedding, crawls_chunks_text_and_embedding)
    previous_messages = "\n".join(message_history[-message_history_size:])
    if previous_messages:
        previous_messages_embedding = get_embedding(previous_messages)
        previous_messages_retrieved_content = get_top_k_similar_text(previous_messages_embedding, crawls_chunks_text_and_embedding)
    else:
        previous_messages_retrieved_content = ""
    
    prompt = f"""You are a helpful assistant answering based on documentation.
    Answer the question based on the relevant documentation above.
    Limit your answer to 200 words by summarizing. In case the user is vague, ask for clarification.
    If the question is not relevant to the documentation, say "I don't know".
    Relevant documentation:
    {retrived_content}
    {previous_messages_retrieved_content}
    Question:
    {message}
    Previous questions and answers:
    {previous_messages}
    """
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
    best_chunks = list(map(lambda x : x[0], similarities[:k]))
    return "\n".join(best_chunks)

def get_crawls_chunks_text_and_embedding() -> list[ChunkAndEmbedding]:
    supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    response = (
        supabase_client.table("crawled_url_chunks")
        .select("chunk, chunk_embedding")
        .not_.is_('chunk_embedding', None)
        .execute()
    )
    rows = response.data
    return map(lambda row: ChunkAndEmbedding(
        chunk=row['chunk'],
        embedding=row['chunk_embedding']
    ), rows)