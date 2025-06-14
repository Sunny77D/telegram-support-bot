from dataclasses import dataclass
from typing import Literal
from datetime import datetime


@dataclass
class TicketCreateMesage:
    title: str
    description: str

@dataclass
class TicketResponse:
    response: str

@dataclass
class CreateTicketRecord:
    title: str
    description: str
    status: Literal['open', 'in_progress', 'resolved']
    chat_id: str
    chat_name: str
    created_by: str

@dataclass    
class CreateTicketResponse:
    ticket_id: int
    title: str
    description: str
    status: Literal['open', 'in_progress', 'resolved']
    chat_id: str
    chat_name: str
    created_by: str
    created_at: str = datetime.utcnow().isoformat()
