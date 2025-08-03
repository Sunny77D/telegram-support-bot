import json
import logging
import re
from typing import Dict, Optional

from supabase import Client, create_client

from config import SUPABASE_KEY, SUPABASE_URL
from supportbot.clients.tickets.dataclasses import Ticket, TicketCreateMesage

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

class TicketClient:
    """Client for handling ticket operations."""
    def __init__(self):
        self.supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    async def get_open_tickets_for_bot(self, bot_id: str) -> list[Ticket]:
        """Get open tickets for a specific bot."""
        try:
            # Fetch tickets with status 'open' or 'in_progress'
            response = (
                self.supabase_client.table("tickets")
                .select("*")
                .eq("bot_id", int(bot_id))
                .eq("status", "open")
                .execute()
            )
            response_json = json.loads(response.json())
            if response_json['data']:
                return [Ticket(**item) for item in response_json['data']]
            else:
                return None
        except Exception as e:
            logger.error(f"Error fetching open tickets for bot: {str(e)}")
            raise e

    async def get_in_progress_tickets_for_bot(self, bot_id: str) -> list[Ticket]:
        """Get in-progress tickets for a specific bot."""
        try:
            response = (
                self.supabase_client.table("tickets")
                .select("*")
                .eq("bot_id", int(bot_id))
                .eq("status", "in_progress")
                .order("created_at", desc=True)
                .execute()
            )
            response_json = json.loads(response.json())
            if response_json['data']:
                return [Ticket(**item) for item in response_json['data']]
            else:
                return None
        except Exception as e:
            logger.error(f"Error fetching in-progress tickets for bot: {str(e)}")
            raise e

    async def get_closed_tickets_for_bot(self, bot_id: str, limit: int = 10) -> list[Ticket]:
        """Get closed tickets for a specific bot."""
        try:
            response = (
                self.supabase_client.table("tickets")
                .select("*")
                .eq("bot_id", int(bot_id))
                .eq("status", "resolved")
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            response_json = json.loads(response.json())
            if response_json['data']:
                return [Ticket(**item) for item in response_json['data']]
            else:
                return None
        except Exception as e:
            logger.error(f"Error fetching closed tickets for bot: {str(e)}")
            raise e
