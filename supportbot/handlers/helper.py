from telegram import User
from supportbot.dataclasses import Bot, UserMetadata
from supportbot.clients.supabase.supabase_client import Supabase


async def get_user(user_metadata: User, supabase_client: Supabase) -> UserMetadata:
    """
    Retrieve user information from the database based on the username.
    
    Args:
        username (str): The username of the user to retrieve.
        supabase_client (Supabase): The Supabase client instance for database operations.
    
    Returns:
        dict: A dictionary containing user information if found, otherwise an empty dictionary.
    """
    if not user_metadata:
        raise ValueError("User metadata cannot be None or empty.")

    row = await supabase_client.get_row(
        table='users',
        primary_key='username',
        primary_data=user_metadata.username
    )
    if row:
        print(row)
        return UserMetadata(
            username=row['username'],
            first_name=row['first_name'],
            last_name=row['last_name'],
            language_code=row['language_code'],
            bot_id=row['bot_id'],
            user_id=row['id']
        )
    else:
        response = await supabase_client.insert_row(
            table='users',
            dict={
                'username': user_metadata.username,
                'first_name': user_metadata.first_name,
                'last_name': user_metadata.last_name,
                'language_code': user_metadata.language_code,
            }
        )
        if response:
            return UserMetadata(
                username=response['username'],
                first_name=response['first_name'],
                last_name=response['last_name'],
                language_code=response['language_code'],
                bot_id=None,
                user_id=response['id']
            )
        else:
            raise Exception("Failed to insert user metadata into the database.")


async def get_bot_for_user(username, supabase_client: Supabase) -> Bot | None:
    row = await supabase_client.get_row(
        table='users',
        primary_key='username',
        primary_data=username
    )
    bot_id = row.get('bot_id') if row else None
    if not bot_id:
        return None
    else:
        return await get_bot(bot_id, supabase_client)


async def get_bot(bot_id: int, supabase_client: Supabase) -> Bot | None:
    """
    Retrieve bot information from the database based on the bot ID.

    Args:
        bot_id (str): The ID of the bot to retrieve.
        supabase_client (Supabase): The Supabase client instance for database operations.

    Returns:
        Bot: A Bot object containing bot information if found, otherwise None.
    """
    row = await supabase_client.get_row(
        table='bots',
        primary_key='id',
        primary_data=bot_id
    )
    if row:
        return Bot(
            bot_id=row['id'],
            bot_name=row['bot_name'],
            created_by=row['created_by']
        )
    return None
