from dataclasses import asdict
from telegram import Update
from telegram.ext import ContextTypes
import logging
from supportbot.clients.messages.dataclasses import MessageMetadata, Message
from supportbot.clients.supabase.supabase_client import Supabase
from supportbot.handlers.ticket_handlers import handle_ticket_create_command, handle_ticket_update_command

supabase_client = Supabase()
logger = logging.getLogger(__name__)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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

    if not message.strip().startswith('=support'):
        message = Message(
            message=message_text,
            chat_id=chat_id,
            chat_name=chat_name,
            username=username,
            update_id=update_id
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
                response = await handle_ticket_create_command(stripped_message, message_metadata)
                if not response:
                    await update.message.reply_text(
                        f"Error: No Reponse\n\n"
                        f"Internal Error please reach out to the team"
                    )
                else:
                    await update.message.reply_text(response, parse_mode="Markdown")
            case "update":
                response = await handle_ticket_update_command(stripped_message, message_metadata)
                await update.message.reply_text(response, parse_mode="Markdown")
            case _:
                await update.message.reply_text(
                    f" Command is not recognize \n\n"
                    f" The previous command was {full_command_text}\n"
                    f" Please only give one of the following commands:\n\n"
                    f"  1. =support create Title: [title] Description: [description]"
                    f"  2. =support update [ticket_id] in progress|done",
                    parse_mode="Markdown"
                )
    except Exception as e:
        await update.message.reply_text(
            f"Error: {str(e)}\n\n"
            f"Internal Error please reach out to the team"
        )


# TODO: This is to handle messages in a group chat. 
# Should have the same logic as the regular Messaging
async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    pass


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
