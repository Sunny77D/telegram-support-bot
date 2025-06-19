import logging
from supportbot.clients.messages.dataclasses import MessageMetadata
from supportbot.clients.supabase.supabase_client import Supabase
from supportbot.dataclasses import Bot

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


async def handle_activate_bot_command(message: str, message_metadata: MessageMetadata, supabase_client: Supabase) -> str | None:
    try:
        # Double check if the bot is already activated for the chat
        existing_bot_chat = await supabase_client.get_row(
            table='bot_chats',
            primary_key='chat_id',
            primary_data=message_metadata.chat_id
        )
        if existing_bot_chat and existing_bot_chat.get('status') == 'active':
            return f"Bot '{existing_bot_chat.get('bot_name')}' is already activated for this chat."

        user = await supabase_client.get_row(
            table='users',
            primary_key='username',
            primary_data=message_metadata.username
        )

        if not user:
            return f"You do not have a user account. Please create one first by dming the bot directly." 

        bot_id = user.get('bot_id')

        if not bot_id:
            return f"You do not have a bot associated with your username. Please create a bot first using the =support build bot: [BOT_NAME] command \n or ask the bot owner to add you to the bot by dming the bot directly."

        bot = await supabase_client.get_row(
            table='bots',
            primary_key='id',
            primary_data=bot_id
        )
        bot_name = bot.get('bot_name')
        if bot.get('created_by') != message_metadata.username:
            return f"You do not have permission to activate the bot '{bot_name}'. Only the creator can activate it."

        bot_chat_data = {
            'bot_name': bot_name,
            'bot_id': bot.get('id'),
            'chat_id': message_metadata.chat_id,
            'chat_name': message_metadata.chat_name,
            'status': 'active',
        }
        result = await supabase_client.insert_row(table='bot_chats', dict=bot_chat_data)
        if result:
            return f"Bot '{bot_name}' has been activated for chat: {message_metadata.chat_name}!"
        else:
            return None
    except Exception as e:
        logger.error(f"An error occurred while activating the bot: {str(e)}")
        return "An error occurred while activating the bot. Please try again later."

async def handle_add_user_to_bot_command(
    message: str, 
    message_metadata: MessageMetadata, 
    supabase_client: Supabase,
    bot: Bot,
) -> str | None:
    """
    Handle the =support add user to bot: [USERNAME] command.
    This function should interact with the Supabase client to add a user to the bot.
    It will return a confirmation message upon successful addition or an error message if something goes wrong.
    """

    if bot.created_by != message_metadata.username:
        return f"You do not have permission to add users to the bot '{bot.bot_name}'. Only the creator can add users."
    
    parts = message.split(':', 1)
    if len(parts) < 2 or not parts[1].strip():
        return "Please provide a valid username after 'add user to bot:'."

    username_to_update = parts[1].strip()

    # Check if the user exists
    user_to_update = await supabase_client.get_row(
        table='users',
        primary_key='username',
        primary_data=username_to_update
    )

    if not user_to_update:
        # Add the user to the users table if they do not exist
        user_metadata = {
            'username': username_to_update,
            'first_name': None,
            'last_name': None,
            'language_code': None,
            'bot_id': bot.bot_id,  # Associate the bot with the user
        }
        result = await supabase_client.insert_row(
            table='users',
            dict=user_metadata
        )
    else:
        # Update the user's bot_id
        updated_data = {
            'bot_id': bot.bot_id,
        }
        
        result = await supabase_client.update_row(
            table='users',
            primary_key='username',
            primary_data=username_to_update,
            update_dict=updated_data
        )

    if result:
        return f"User '{username_to_update}' has been successfully added to the bot {bot.bot_name}!"
    else:
        logger.error(f"Failed to add user '{username_to_update}' to the bot.")
        return "An error occurred while adding the user to the bot. Please reach out to the team."
