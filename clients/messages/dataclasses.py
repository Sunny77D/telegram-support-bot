from dataclasses import dataclass
from typing import Literal

@dataclass
class MessageMetadata:
    username: str
    chat_id: str
    update_id: str
    chat_name: str
    
