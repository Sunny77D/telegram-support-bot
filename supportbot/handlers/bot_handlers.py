import logging
from supportbot.clients.messages.dataclasses import MessageMetadata
from supportbot.clients.supabase.supabase_client import Supabase

logger = logging.getLogger(__name__)

async def handle_build_bot_command(message: str, message_metadata: MessageMetadata, supabase_client: Supabase) -> str | None:
    """
    Handle the =support build bot: [BOT_NAME]\n
    This function should interact with the Supabase client to create a bot record in the database.
    It will return a confirmation message upon successful creation or an error message if something goes wrong.
    """
    # Extract the bot name from the message
    parts = message.split(':', 1)
    if len(parts) < 2 or not parts[1].strip():
        return "Please provide a valid bot name after 'build bot:'."

    bot_name = parts[1].strip()
    print(bot_name)

    # Create a new bot record in the database
    try:
        bot_data = {
            'bot_name': bot_name,
            'created_by': message_metadata.username,
        }
        result = await supabase_client.insert_row(table='bots', dict=bot_data)
        bot_id = result.get('id')
        # Add the bot to the user row
        updated_data = {
            'bot_id': bot_id
        }
        # It should be updated in the users table as well.
        result = await supabase_client.update_row(
            table='users',
            primary_key='username',
            primary_data=message_metadata.username,
            update_dict=updated_data
        )

        if result:
            return f"Bot '{bot_name}' has been successfully created!"
        else:
            return None
    except Exception as e:
        logger.info(f"An error occurred while creating the bot: {str(e)}")
        return None
