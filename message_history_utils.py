import json
import os

from telethon import TelegramClient

from supportbot.clients.messages.dataclasses import (MessageHistory,
                                                     MessageMetadata)
from supportbot.clients.supabase.supabase_client import Supabase
from supportbot.dataclasses import Bot


async def get_message_history(bot: Bot, message_metadata: MessageMetadata) -> list[MessageHistory]:
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
                message_history = MessageHistory(
                    chat_id=chat.id,
                    chat_name=chat.title,
                    chat_history=messages,
                    chat_member_ids=list(members)
                )
                message_history_data = {
                    'chat_id': message_history.chat_id,
                    'chat_name': message_history.chat_name,
                    'owner_username': message_metadata.username,
                    'bot_id': bot.bot_id,
                    'chat_history': json.dumps(message_history.chat_history),
                    'chat_member_ids': json.dumps(message_history.chat_member_ids),
                }
                superbase = Supabase()
                await superbase.insert_row(table='message_history', dict=message_history_data)
                print(f"Message history for chat {chat.title} saved successfully.")

    return message_history
