from supabase import create_client

from agent_utils import get_embedding
from config import SUPABASE_KEY, SUPABASE_URL

CHUNK_DB = "message_history_chunks"

supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
response = (
    supabase_client.table(CHUNK_DB)
    .select("*")
    .is_('chunk_embedding', None)
    .execute()
)
rows = response.data

for row in rows:
    embedding = get_embedding(row['chunk'])
    if embedding is not None:
        update_response = (
            supabase_client.table(CHUNK_DB)
            .update({'chunk_embedding': embedding})
            .eq('id', row['id']).execute()
        )
    else:
        print(f"Failed to get embedding for chunk ID {row['id']}. Skipping update.")

print("✅ Done! Saved embeddings to the DB")
