from openai import OpenAI
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
