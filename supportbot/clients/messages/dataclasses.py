from dataclasses import dataclass

@dataclass
class MessageMetadata:
    username: str
    chat_id: str
    update_id: str
    chat_name: str
    
@dataclass
class Message:
    message: str
    chat_id: str
    chat_name: str
    username: str
    update_id: str
    bot_id: int | None = None


@dataclass
class MessageHistory:
    chat_id: str
    chat_name: str
    chat_history: list[str]
    chat_member_ids: list[int]
