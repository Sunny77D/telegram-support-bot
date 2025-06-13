from dataclasses import dataclass

@dataclass
class MessageMetadata:
    username: str
    chat_id: str
    update_id: str
    chat_name: str
    
