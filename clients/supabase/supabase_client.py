from supabase import create_client, Client
import json
from clients.supabase.dataclasses import SupabaseTicketResponse

from config import SUPABASE_KEY, SUPABASE_URL
from clients.tickets.dataclasses import CreateTicketRecord


class Supabase:
    def __init__(self):
        self.supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    async def insert_message(self, chat_id, username, message, update_id):
        try: 
            response = (
                self.supabase_client.table("messages")
                .insert({"chat_id": chat_id, "username": username,  "message": message, "update_id": update_id})
                .execute()
            )
            return json.loads(response.json())

        except Exception as exception:
            raise exception

    async def create_ticket(self, ticket_record: CreateTicketRecord):
        try:
            response = (
                self.supabase_client.table("tickets")
                    .insert(
                        {
                            "chat_id": ticket_record.chat_id,
                            "chat_name": ticket_record.chat_name,
                            "title": ticket_record.title,
                            "description": ticket_record.description,
                            "status": ticket_record.status,
                            "created_by": ticket_record.created_by,
                        }
                    )
                    .execute()
            )
            response_json = json.loads(response.json())
            data_response = response_json['data'][0]
            return SupabaseTicketResponse(
                ticket_id = data_response["id"],
                title = data_response["title"],
                description = data_response["description"],
                status = data_response["status"],
                created_by = data_response["created_by"],
                updated_at = data_response["updated_at"],
                created_at = data_response["created_at"]
            )
        except Exception as exception:
            raise exception
