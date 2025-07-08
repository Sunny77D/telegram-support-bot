import os
from telethon import TelegramClient
from supportbot.clients.messages.dataclasses import MessageHistory

async def get_message_history() -> list[MessageHistory]:
    api_id = int(os.getenv('TELEGRAM_API_ID'))
    api_hash = os.getenv('TELEGRAM_API_HASH')

    async with TelegramClient('session_name', api_id, api_hash) as client:
        message_history = []
        async for dialog in client.iter_dialogs():
            if dialog.is_group or dialog.is_channel:
                messages = []
                members = set()
                chat = await client.get_entity(dialog.id)
                async for message in client.iter_messages(chat):
                    if message.sender_id is not None:
                        members.add(message.sender_id)
                    if message.text:
                        messages.append(message.text)
                message_history.append(MessageHistory(
                    chat_id=chat.id,
                    chat_name=chat.title,
                    chat_history=messages,
                    chat_member_ids=list(members)
                ))
                
    return message_history
