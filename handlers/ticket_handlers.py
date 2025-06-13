from telegram import Update
from telegram.ext import ContextTypes
import logging
from clients.messages.dataclasses import MessageMetadata
from clients.tickets.dataclasses import CreateTicketResponse
from clients.tickets.ticket_client import TicketManager, TicketParser

logger = logging.getLogger(__name__)


# Status emoji mapping
STATUS_EMOJIS = {
    'open': '🔓',
    'in_progress': '⏳',
    'done': '✅'
}

def format_create_ticket_message(ticket_data: CreateTicketResponse) -> str:
    """Format ticket information for display."""
    status_emoji = STATUS_EMOJIS.get(ticket_data.status, '🔓')
    return (
        f"🎫 *Ticket Created Successfully!*\n\n"
        f"📋 *Ticket ID:* `{ticket_data.ticket_id}`\n"
        f"📝 *Title:* {ticket_data.title}\n"
        f"📄 *Description:* {ticket_data.description}\n"
        f"{status_emoji} *Status:* {ticket_data.status.replace('_', ' ').title()}\n"
        f"👤 *Created by:* @{ticket_data.created_by}\n"
        f"📅 *Created At:* {ticket_data.created_at}"
    )


# TODO Implement Update logic
def format_status_update_message(ticket_id: str, new_status: str, username: str) -> str:
    pass

async def handle_ticket_create_command(message: str, message_metadata : MessageMetadata) -> str:
    # Try to parse status update command first
    create_ticket_message = TicketParser.parse_ticket_create_command(message)
    if create_ticket_message:
        ticket_manager = TicketManager()
        result = await ticket_manager.create_ticket(
            ticket_data=create_ticket_message,
            message_metadata=message_metadata
        )
        if result:
            response = format_create_ticket_message(result)
            return response
        else:
            return None
    return None


# TODO Implement Logic
async def handle_ticket_update_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pass