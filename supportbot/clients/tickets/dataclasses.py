from dataclasses import dataclass
from typing import Literal
from datetime import datetime


@dataclass
class TicketCreateMesage:
    title: str
    description: str
@dataclass
class CreateTicketRecord:
    title: str
    description: str
    status: Literal['open', 'in_progress', 'resolved']
    chat_id: str
    chat_name: str
    created_by: str
    bot_id: int | None = None

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
    bot_name: str | None = None

@dataclass
class Ticket:
    id: int
    title: str
    status: Literal['open', 'in_progress', 'resolved']
    description: str | None = None
    created_by: str | None = None
    updated_by: str | None = None
    assigned_to: str | None = None
    chat_id: int | None = None
    chat_name: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    resolved_at: datetime | None = None
    bot_id: int | None = None
