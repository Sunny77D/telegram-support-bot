# flake8: noqa
import logging
from dataclasses import asdict

from telegram import Update
from telegram.ext import ContextTypes

from supportbot.clients.messages.dataclasses import Message, MessageMetadata
from supportbot.clients.supabase.supabase_client import Supabase
from supportbot.handlers.bot_handlers import (handle_activate_bot_command,
                                              handle_add_user_to_bot_command,
                                              handle_build_bot_command)
from supportbot.handlers.helper import (get_bot_for_chat, get_bot_for_user,
                                        get_user)
from supportbot.handlers.ticket_handlers import (handle_ticket_create_command,
                                                 handle_ticket_update_command)
from agent_utils import send_message
import json
from message_history_utils import get_message_history
from supportbot.clients.crawl.dataclasses import ChunkAndEmbedding

supabase_client = Supabase()
logger = logging.getLogger(__name__)


# TODO: Create a response + structure to get a user started
# V2: They should be able to create teams and assign tickets to teams + as well as members.
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Process incoming messages and generate charts based on user commands.
    """
    message_text = update.message.text.strip()
    username = update.effective_sender.username
    chat_id = update.effective_chat.id
    chat_name = update.effective_chat.title if update.effective_chat.title else update.effective_chat.username
    update_id = update.update_id
    message = update.message.text

    if not message:
        logger.warning("Received an empty message, skipping processing.")
        return

    if not username:
        logger.warning("Received a message without a username, skipping processing.")
        await update.message.reply_text(
            "Error: You must have a username to use this bot. Please set a username in your Telegram settings.",
            parse_mode="Markdown"
        )
        return

    user = await get_user(update.effective_user, supabase_client)

    if not user.bot_id and 'build' not in message.strip():
        await update.message.reply_text(
            f" Please Create a Bot \n"
            f" Use the following command to create a bot: \n"
            f" =support build bot: [BOT_NAME]\n\n"
            f"Note: You can only have one bot attached per account\n"
            f"If you would like to be added to a support bot team\n"
            f"please reach out to the Support Bot Team or the creator of the bot you would like to join.",
            parse_mode="Markdown"
        )
        return

    bot = await get_bot_for_user(username, supabase_client)

    if not message.strip().startswith('=support'):
        message = Message(
            message=message_text,
            chat_id=chat_id,
            chat_name=chat_name,
            username=username,
            update_id=update_id,
            bot_id=bot.bot_id
        )
        message_insert_response = await supabase_client.insert_row(
            table='messages',
            dict=asdict(message)
        )
        logger.info(f"Message doesn't start with =support, inserting into messages table: {message_insert_response}")
        return

    support_prefix = message.strip()[0:9]
    stripped_message = message.strip()[9:]
    command = stripped_message.split(" ")[0].lower()
    full_command_text = support_prefix + command
    message_metadata = MessageMetadata(username=username, chat_id=chat_id, chat_name=chat_name, update_id=update_id)
    try:
        match command:
            case "create":
                response = await handle_ticket_create_command(stripped_message, message_metadata, bot)
                if not response:
                    await update.message.reply_text(
                        f"Error: No Reponse\n\n"
                        f"Internal Error please reach out to the team"
                    )
                else:
                    await update.message.reply_text(response, parse_mode="Markdown")
            case "update":
                response = await handle_ticket_update_command(stripped_message, message_metadata, bot)
                await update.message.reply_text(response, parse_mode="Markdown")
            case "build":
                if bot:
                    await update.message.reply_text(
                        f" You already have a bot created: {bot.bot_name}\n"
                        f" If you would like to create a new bot please delete the old one first.\n"
                        f" Note: You can only have one bot attached per account\n",
                        parse_mode="Markdown"
                    )
                    return
                bot_built = await handle_build_bot_command(stripped_message, message_metadata, supabase_client)
                if not bot_built:
                    await update.message.reply_text(
                        f"Error: No Reponse\n\n"
                        f"Internal Error please reach out to the team"
                    )
                await update.message.reply_text(
                    f" {bot_built} \n\n"
                    f" You can now add the bot to a group chat and start using it.\n"
                    f" Use the following command to add more user to the bot: \n"
                    f" =support add user: [username] to bot: [BOT_NAME]\n"
                    f" Note: You can only have one bot attached per account\n",
                    parse_mode="Markdown"
                )
            case "add":
                response = await handle_add_user_to_bot_command(stripped_message, message_metadata, supabase_client, bot)
                if not response:
                    await update.message.reply_text(
                        f"Error: No Reponse\n\n"
                        f"Internal Error please reach out to the team",
                        parse_mode="Markdown"
                    )
                await update.message.reply_text(response, parse_mode="Markdown")
            case "question":
                crawls_chunks_text_and_embedding = context.bot_data.get("crawls_chunks_text_and_embedding")
                message_chunks_text_and_embedding = context.bot_data.get("message_chunks_text_and_embedding")
                message_history = context.bot_data.get("message_history")
                response = await handle_question_command(stripped_message, crawls_chunks_text_and_embedding, message_chunks_text_and_embedding, message_history)
                if not response:
                    await update.message.reply_text(
                        f"Error: No Reponse\n\n"
                        f"Internal Error please reach out to the team"
                    )
                else:
                    await update.message.reply_text(response, parse_mode="Markdown")
            case "fetch_my_messages":
                message_history_list = await get_message_history()
                for message_history in message_history_list:
                    message_history_data = {
                        'chat_id': message_history.chat_id,
                        'chat_name': message_history.chat_name,
                        'owner_username': message_metadata.username,
                        'bot_id': bot.bot_id,
                        'chat_history': json.dumps(message_history.chat_history),
                        'chat_member_ids': json.dumps(message_history.chat_member_ids),
                    }
                    result = await supabase_client.insert_row(table='message_history', dict=message_history_data)
                    if result is None:
                        await update.message.reply_text(
                            "Could not upload message history for chat " + message_metadata.chat_name,
                        )
                await update.message.reply_text(
                    "Message history has been successfully uploaded for all the chats you are a member of.\n"
                    "The bot now has access to more knowledge based on your previous chats when users ask questions!\n"
                )
            case _:
                await update.message.reply_text(
                    f" Command is not recognize \n\n"
                    f" The previous command was {full_command_text}\n"
                    f" Please only give one of the following commands:\n\n"
                    f"  1. =support create Title: [title] Description: [description]"
                    f"  2. =support update [ticket_id] in progress|done",
                    f"  3. =support build bot: [BOT_NAME]\n"
                    f"  4. =support add user: [username] to bot: [BOT_NAME]\n"
                    f"  5. =support question: [your question]\n"
                    f"  6. =support fetch_my_messages\n"
                    f"Note: You can only have one bot attached per account\n",
                    parse_mode="Markdown"
                )
                return
    except Exception as e:
        await update.message.reply_text(
            f"Error: {str(e)}\n\n"
            f"Internal Error please reach out to the team"
        )
        return
    return


# Handles messages in group chats where the bot is added
# This is to handle the group chat messages and commands.
# It will handle the commands that start with =support and will process the messages accordingly.
async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Process incoming messages and generate charts based on user commands.
    """
    message_text = update.message.text.strip()
    username = update.effective_sender.username
    chat_id = update.effective_chat.id
    chat_name =  update.effective_chat.title if update.effective_chat.title else update.effective_chat.username
    update_id = update.update_id
    message = update.message.text

    if not message:
        logger.warning("Received an empty message, skipping processing.")
        return

    # Get the bot for the chat
    bot = await get_bot_for_chat(chat_id, supabase_client)
    if not message.strip().startswith('=support'):
        if bot:
            message = Message(
                message=message_text,
                chat_id=chat_id,
                chat_name=chat_name,
                username=username,
                update_id=update_id,
                bot_id=bot.bot_id
            )
            message_insert_response = await supabase_client.insert_row(
                table='messages',
                dict=asdict(message)
            )
            logger.info(f"Message doesn't start with =support, inserting into messages table: {message_insert_response}")
        else:
            logger.info(f"Message doesn't start with =support and no bot is active in the chat, so no action taken.")
        return


    support_prefix = message.strip()[0:9]
    stripped_message = message.strip()[9:]
    command = stripped_message.split(" ")[0].lower()
    full_command_text = support_prefix + command
    message_metadata = MessageMetadata(username=username, chat_id=chat_id, chat_name=chat_name, update_id=update_id)

    if not bot and command != 'activate':
        await update.message.reply_text(
            f" Please Activate the Bot for this chat with the following command \n"
            f" Use the following command to activate the bot: \n"
            f" =support activate\n",
            parse_mode="Markdown"
        )
        return

    try:
        # It should only have a few commands that it can handle.
        # 1. Create a ticket
        # 2. Update a ticket
        # 3. Activate a bot in the group chat
        match command:
            case "create":
                response = await handle_ticket_create_command(stripped_message, message_metadata, bot)
                if not response:
                    await update.message.reply_text(
                        f"Error: No Reponse\n\n"
                        f"Internal Error please reach out to the team"
                    )
                else:
                    await update.message.reply_text(response, parse_mode="Markdown")
            case "update":
                response = await handle_ticket_update_command(stripped_message, message_metadata, bot)
                await update.message.reply_text(response, parse_mode="Markdown")
            # You can only activate a bot in the group chat if you are the owner of the bot.
            case "activate":
                response = await handle_activate_bot_command(stripped_message, message_metadata, supabase_client)
                await update.message.reply_text(response, parse_mode="Markdown")
            case _:
                await update.message.reply_text(
                    f" Command is not recognize \n\n"
                    f" The previous command was {full_command_text}\n"
                    f" Please only give one of the following commands:\n\n"
                    f"  1. =support create ticket Title: [title] Description: [description]"
                    f"  2. =support update ticket [ticket_id] in progress|resolved\n",
                    f"  3. =support activate\n"
                    f"Note: You can only have one bot attached per account\n",
                    parse_mode="Markdown"
                )
    except Exception as e:
        await update.message.reply_text(
            f"Error: {str(e)}\n\n"
            f"Internal Error please reach out to the team"
        )
        return
    return


# TODO: This is to handle the welcome message when the bot is added to a group chat.
async def welcome_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Send a welcome message when the bot is added to a group chat.
    
    Args:
        update: Telegram update
        context: CallbackContext
    """
    try:
        # Make sure we have the required attributes
        if not update or not update.message or not update.message.new_chat_members:
            return
            
        # Get information about the new member
        new_members = update.message.new_chat_members
        
        # Get our bot's user ID
        try:
            bot_id = context.bot.id
        except (AttributeError, Exception) as e:
            return
        
        # Only proceed if our bot is one of the new members
        if any(member.id == bot_id for member in new_members):
            # Get the chat name for a personalized welcome
            chat_name = update.effective_chat.title or "this group" if update.effective_chat else "this group"

            # Send a beautifully formatted welcome message
            await update.message.reply_text(
                f"🌟 *Hello {chat_name}!* 🌟\n\n"
                f"Thanks for adding me to your group! I'm your Test Support Bot Ready to answer any support Questions You Might Have!\n\n"
                
                f"📈 *What I can do for you:*\n"
                f"1. Upgrade A User\n"
                f"2. Record Tickets!\n"
                
                f"👉 *How to use me:*\n"
                f"Just type `support` followed by your asks, like:\n\n"
                
                f"👋 Get started by trying one of the examples above!\n"
                f"📖 For more details, any member can message me directly with /help",
                parse_mode="Markdown"
            )
    except Exception as e:
        pass


async def command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Redirects commands to the appropriate handlers.
    
    Args:
        update: Telegram update
        context: CallbackContext
    """
    # Extract the command
    command = update.message.text.split()[0][1:].lower()  # Remove '/' and make lowercase
    
    # Route to the appropriate handler
    if command == 'start':
        await start_command(update, context)
    elif command == 'help':
        await help_command(update, context)

# TODO: Start the command in order to create a 
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle the /start command - welcome new users.
    
    Args:
        update: Telegram update
        context: CallbackContext
    """
    await update.message.reply_text(
        "🔍 Welcome to Support Chat Bot! 📊\n\n"
        "I can track tickets for you and upgrade users.\n\n",
        parse_mode="Markdown"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = f"""
        🤖 *Artemis Chart Bot Help*

        *Basic Commands:*
        • `/help` - Show this help message

        *Support Bot Commands:*
        Format: `=support track tickets`

        *Examples:*
        • `Summary of all tickets` - Give me a summary of all the tickets
        • `Track XYZ`
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def handle_question_command(
    message: str, 
    crawls_chunks_text_and_embedding : list[ChunkAndEmbedding],
    message_chunks_text_and_embedding : list[ChunkAndEmbedding],
    message_history: list[str],
) -> str | None:
    try:
        return send_message(message, crawls_chunks_text_and_embedding, message_chunks_text_and_embedding, message_history)
    except ValueError as e:
        logger.error(f"Error in handle_question_command: {str(e)}")
        return "An error occurred while processing your question. Please try again later."
    

