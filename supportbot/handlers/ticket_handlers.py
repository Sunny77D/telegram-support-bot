from dataclasses import asdict
import logging
from supportbot.clients.messages.dataclasses import MessageMetadata
from supportbot.clients.supabase.supabase_client import Supabase
from supportbot.clients.tickets.dataclasses import CreateTicketRecord, CreateTicketResponse, TicketCreateMesage
from supportbot.clients.tickets.ticket_client import TicketParser

logger = logging.getLogger(__name__)


# Status emoji mapping
STATUS_EMOJIS = {
    'open': '🔓',
    'in_progress': '⏳',
    'resolved': '✅'
}

supabase_client = Supabase()

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


def format_status_update_message(ticket_id: str, new_status: str, username: str) -> str:
    """Format status update message for display."""
    status_emoji = STATUS_EMOJIS.get(new_status, '🔓')
    return (
        f"🎫 *Ticket Status Updated!*\n\n"
        f"📋 *Ticket ID:* `{ticket_id}`\n"
        f"{status_emoji} *New Status:* {new_status.replace('_', ' ').title()}\n"
        f"👤 *Updated by:* @{username}"
    )


async def handle_ticket_create_command(message: str, message_metadata : MessageMetadata) -> str:
    # Try to parse status update command first
    create_ticket_message = TicketParser.parse_ticket_create_command(message)
    if create_ticket_message:
        create_ticket_response = CreateTicketRecord(
            title=create_ticket_message.title,
            description=create_ticket_message.description,
            status='open',
            created_by=message_metadata.username,
            chat_id=message_metadata.chat_id,
            chat_name=message_metadata.chat_name
        )
        result = await supabase_client.insert_row(
            table='tickets',
            dict=asdict(create_ticket_response)
        )
        response_obj = CreateTicketResponse(
            ticket_id=result['id'],
            title=result['title'],
            description=result['description'],
            status=result['status'],
            chat_id=result['chat_id'],
            chat_name=result['chat_name'],
            created_by=result.get("created_by", 'anon'),
            created_at = result["created_at"]
        )
        if response_obj:
            response = format_create_ticket_message(response_obj)
            return response
    return None


async def handle_ticket_update_command(message: str, message_metadata: MessageMetadata) -> str:
    # Try to parse status update command first
    status_update = TicketParser.parse_status_update_command(message)
    if status_update:
        result = await supabase_client.update_row(
            primary_key='id',
            primary_data=status_update['ticket_id'],
            table='tickets',
            update_dict={'status': status_update['status']}
        )
        return format_status_update_message(
            ticket_id=result['id'],
            new_status=result['status'],
            username=message_metadata.username
        )
    return None
