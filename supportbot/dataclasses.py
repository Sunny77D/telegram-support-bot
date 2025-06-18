from dataclasses import dataclass

@dataclass
class Bot:
    bot_id: str
    bot_name: str
    created_by: str

@dataclass
class UserMetadata:
    username: str
    first_name: str
    last_name: str
    language_code: str
    bot_id: str = None
    user_id: str = None

@dataclass
class TelegramUserMetadata:
    username: str
    first_name: str
    last_name: str
    language_code: str
