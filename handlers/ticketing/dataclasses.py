from dataclasses import dataclass
from typing import Literal
from datetime import datetime


@dataclass
class TicketCreateMesage:
    title: str
    description: str
    action: str = 'create'

@dataclass
class TicketResponse:
    status: Literal['success', 'failed']
    response: str

@dataclass
class CreateTicketRecord:
    title: str
    description: str
    status: Literal['open', 'in_progress', 'done']
    chat_id: str
    chat_name: str
    created_by: str
    created_at: str = datetime.utcnow().isoformat()
    updated_at: str = datetime.utcnow().isoformat()

@dataclass    
class CreateTicketResponse:
    ticket_id: int
    title: str
    description: str
    status: Literal['open', 'in_progress', 'done']
    chat_id: str
    chat_name: str
    created_by: str
    created_at: str = datetime.utcnow().isoformat()
