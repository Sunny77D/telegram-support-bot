from openai import OpenAI
from scipy.spatial.distance import cosine
from config import OPEN_AI_API_KEY

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

def send_message(message, url_to_embedding, url_to_text, message_history, message_history_size=5):
    message_embedding = get_embedding(message)
    if message_embedding is None:
        raise ValueError("Could not get embedding for the message.")
    retrived_content = get_top_k_similar_text(message_embedding, url_to_embedding, url_to_text)
    previous_messages = "\n".join(message_history[-message_history_size:])
    if previous_messages:
        previous_messages_embedding = get_embedding(previous_messages)
        previous_messages_retrieved_content = get_top_k_similar_text(previous_messages_embedding, url_to_embedding, url_to_text)
    else:
        previous_messages_retrieved_content = ""
    
    prompt = f"""You are a helpful assistant answering based on documentation.
    Answer the question based on the relevant documentation above. If you don't know the answer, say "I don't know".
    Limit your answer to 200 words by summarizing. In case the user is vague, ask for clarification.
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
def get_top_k_similar_text(query_embedding, url_to_embedding, url_to_text, k=5):
    similarities = []
    for url, doc_embedding in url_to_embedding.items():
        sim = 1 - cosine(query_embedding, doc_embedding)  # cosine similarity
        similarities.append((url, sim))
    similarities.sort(key=lambda x: x[1], reverse=True)
    best_urls = list(map(lambda x : x[0], similarities[:k]))
    return "\n".join(list(map(lambda x : url_to_text[x], best_urls)))