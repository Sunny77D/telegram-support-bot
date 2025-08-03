import json
import logging

from supabase import Client, create_client

from config import SUPABASE_KEY, SUPABASE_URL

from .dataclasses import Message

logger = logging.getLogger(__name__)
class MessageClient:
    def __init__(self):
        self.supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    async def get_chat_history(self, chat_id: str, limit: int = 5) -> list[Message] | None:
        """
        Retrieve chat history for a specific chat ID.
        Args:
            chat_id (str): The ID of the chat to retrieve history for.
            limit (int): The maximum number of messages to retrieve.
        Returns:
            list: A list of messages in the chat history.
        """
        try:
            response = (
                self.supabase_client.table("messages")
                .select("*")
                .eq("chat_id", chat_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            response_json = json.loads(response.json())
            if response_json['data']:
                # Convert the response data to Message dataclass instances
                messages = [
                    self._convert_to_message(item) for item in response_json['data']
                ]
                return messages
            else:
                return None
        except Exception as e:
            logger.error(f"Error retrieving chat history: {str(e)}")
            return None

    async def get_user_messsage_history(self, user_id: str, limit: int = 20) -> list[Message] | None:
        """
        Retrieve message history for a specific user ID.
        Args:
            user_id (str): The ID of the user to retrieve message history for.
            limit (int): The maximum number of messages to retrieve.
        Returns:
            list: A list of messages sent by the user.
        """
        try:
            response = (
                self.supabase_client.table("messages")
                .select("*")
                .eq("username", user_id)
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            response_json = json.loads(response.json())
            if response_json['data']:
                # Convert the response data to Message dataclass instances
                messages = [
                    self._convert_to_message(item) for item in response_json['data']
                ]
                return messages
            else:
                return None
        except Exception as e:
            logger.error(f"Error retrieving user message history: {str(e)}")
            return None

    """
    Private Helper Functions:
    """
    def _convert_to_message(self, data: dict) -> Message:
        """
        Convert a dictionary to a Message dataclass instance.
        Args:
            data (dict): The data to convert.
        Returns:
            Message: The converted Message instance.
        """
        return Message(
            message=data['message'],
            chat_id=data['chat_id'],
            chat_name=data['chat_name'],
            username=data['username'],
            update_id=data['update_id'],
            bot_id=data.get('bot_id'),
            created_at=data.get('created_at')
        )
