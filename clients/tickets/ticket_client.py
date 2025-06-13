import logging
import re
from typing import Dict, Optional
from clients.messages.dataclasses import MessageMetadata
from clients.supabase.supabase_client import Supabase
from clients.tickets.dataclasses import CreateTicketRecord, CreateTicketResponse, TicketCreateMesage

logger = logging.getLogger(__name__)
supabase_client = Supabase()

class TicketParser:
    """Parse ticket creation and update commands."""
    
    @staticmethod
    def parse_ticket_create_command(message: str) -> Optional[TicketCreateMesage]:
        pattern = r'create\s+ticket\s+Title:\s*(.+?)\s+Description:\s*(.+)'
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return TicketCreateMesage(title=match.group(1), description=match.group(2))
        return None
    
    @staticmethod
    def parse_status_update_command(message: str) -> Optional[Dict]:
            
        command_text = message[8:].strip()  # Remove '=support'

        # Pattern: =support mark TICKET_ID (in progress|done)
        pattern = r'mark\s+([A-Z0-9]+)\s+(in progress|done)'
        match = re.search(pattern, command_text, re.IGNORECASE)
        if match:
            return {
                'action': 'update_status',
                'ticket_id': match.group(1).upper(),
                'status': match.group(2).lower().replace(' ', '_')
            }
        
        return None

class TicketManager:
    """Manage ticket operations like creation and status updates."""
    
    def __init__(self):
        self.supabase_client = Supabase()
    
    # TODO Do the Supabase connection to add the ticket to postgres! 
    async def create_ticket(self, ticket_data: TicketCreateMesage, message_metadata: MessageMetadata) -> CreateTicketResponse:
        """Create a new support ticket."""
        try:
            ticket_record = CreateTicketRecord(
                title=ticket_data.title,
                description=ticket_data.description,
                status="open",
                created_by=message_metadata.username,
                chat_id=message_metadata.chat_id,
                chat_name=message_metadata.chat_name,
            )
            response = await self.supabase_client.create_ticket(ticket_record)
            return CreateTicketResponse(
                ticket_id = response.ticket_id,
                title = response.title, 
                description = response.description,
                status = response.status,
                chat_id = message_metadata.chat_id,
                chat_name = message_metadata.chat_name,
                created_at=response.created_at,
                created_by=message_metadata.username 
            )
            
        except Exception as e:
            logger.error(f"Error creating ticket: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    # TODO: Implement this function
    async def update_ticket_status(self, ticket_id: str, new_status: str, username: str) -> Dict:
        pass