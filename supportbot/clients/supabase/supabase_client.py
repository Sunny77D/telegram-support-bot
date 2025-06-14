import logging
from supabase import create_client, Client
import json
from config import SUPABASE_KEY, SUPABASE_URL

logger = logging.getLogger(__name__)
class Supabase:
    def __init__(self):
        self.supabase_client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    """
        Generic Insert Function for inserting a row into a Supabase table.
        Args:
            table (str): The name of the table to insert into.
            dict (dict): A dictionary containing the data to insert.
        Returns:
            dict: The inserted row data as a dictionary.
    """
    async def insert_row(self, table, dict: dict) -> dict:
        try: 
            response = (
                self.supabase_client.table(table)
                .insert(dict)
                .execute()
            )
            response_json = json.loads(response.json())
            data_response = response_json['data'][0]
            return data_response
        except Exception as e:
            raise e

    """
        Generic Update Function for updating a row in a Supabase table.
        Args:
            primary_key (str): The primary key of the row to update.
            primary_data (str): The value of the primary key to match.
            table (str): The name of the table to update.
            update_dict (dict): A dictionary containing the data to update.
        Returns:
            dict: The updated row data as a dictionary.
    """
    async def update_row(self, primary_key, primary_data, table, update_dict: dict) -> dict:
        try:
            response = (
                self.supabase_client.table(table)
                .update(update_dict)
                .eq(primary_key, primary_data)
                .execute()
            )
            response_json = json.loads(response.json())
            data_response = response_json['data'][0]
            return data_response
        except Exception as exception:
            logger.error(f"Error updating {primary_key}: {str(exception)}")
            raise exception
