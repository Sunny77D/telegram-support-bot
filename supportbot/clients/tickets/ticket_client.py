import logging
import re
from typing import Dict, Optional
from supportbot.clients.tickets.dataclasses import TicketCreateMesage

logger = logging.getLogger(__name__)
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
        # Example message: "update ticket_id: ABC123 status: resolved"
        pattern = r'update\s+ticket_id:\s([A-Z0-9]+)\s+status:\s(in progress|resolved)'
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return {
                'ticket_id': match.group(1).upper(),
                'status': match.group(2).lower().replace(' ', '_')
            }
        return None
