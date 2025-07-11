import asyncio
import json
from supabase import create_client, Client
from config import SUPABASE_KEY, SUPABASE_URL
from agent_code.chunk_utils import split_text_by_num_tokens

class MessageChunkifier:
    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
        self.supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    async def write_chunks(self):
        response = (
            self.supabase_client.table("message_history")
            .select("*")
            .execute()
        )
        message_history_chunks = []

        for message_history in response.data:
            chat_history = message_history.get('chat_history')
            if chat_history is None:
                pass
            chat_history = json.loads(chat_history)
            chat_history_str = "\n\n".join(chat_history)
            chat_history_chunks = split_text_by_num_tokens(chat_history_str)
            for i, chunk in enumerate(chat_history_chunks):
                message_history_chunks.append({
                    'message_history_id': message_history.get('id'),
                    'chat_member_ids': message_history.get('chat_member_ids'),
                    'chunk': chunk,
                    'chunk_number': i,
                })
        response = (
            self.supabase_client.table("message_history_chunks")
            .insert(message_history_chunks)
            .execute()
        )
        print(f"Inserted {len(message_history_chunks)} chunks")

async def main():
    chunkifier = MessageChunkifier()
    await chunkifier.write_chunks()

if __name__ == "__main__":
    asyncio.run(main())
