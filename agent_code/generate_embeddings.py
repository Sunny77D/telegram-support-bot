import pickle
from tqdm import tqdm
from utils import get_embedding

with open("url_splits_merges_to_text.pkl", "rb") as f:
    url_splits_merges_to_text = pickle.load(f)

url_splits_merges_to_embedding = {}

for url, text in tqdm(url_splits_merges_to_text.items()):
    if not text.strip():
        continue
    embedding = get_embedding(text)
    if embedding is not None:
        url_splits_merges_to_embedding[url] = embedding

with open("url_split_merges_to_embedding.pkl", "wb") as f:
    pickle.dump(url_splits_merges_to_embedding, f)

print("✅ Done! Saved embeddings to url_split_merges_to_embedding.pkl")
