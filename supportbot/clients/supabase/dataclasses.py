from dataclasses import dataclass

@dataclass
class SupabaseTicketResponse:
    ticket_id: str
    title: str
    description: str
    status: str
    created_by: str
    updated_at: str
    created_at: str
