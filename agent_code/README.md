Some pointers on how to refresh the RAG information:
1. If you want to crawl pages, use the `crawl.py` script (command: `python3 crawl.py`). Optionally you can change BASE_URL, URL_PREFIX and some of the current logic of how to handle recursive calls. This updates the `crawled_url_chunks` DB with the corresponding chunks.
2. Use `update_crawled_chunks_with_embeddings` script to populate the DB with embeddings.
3. Use `=support fetch_my_messages` option of the bot to fetch all your group messages and update the `message_history` table.
4. Use `chunkify_messages.py` script to chukify messages into the `message_history_chunks` table.
5. Use `update_message_chunks_with_embeddings` to update `message_history_chunks` with the corresponding embeddings.
6. Afterwards, you can just use `=support question <insert_your_question>` and the bot will automatically do RAG based on `crawled_url_chunks` and `message_history_chunks` tables.
