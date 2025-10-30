"""Telegram bot for certificate generation."""
import os
import sys
import json
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from dotenv import load_dotenv
import asyncio
from datetime import datetime
from bson.objectid import ObjectId
import tempfile

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, mongo
from app.models.mongo_models import Event, Job, Participant
from app.utils import parse_csv_file
from app.routes.jobs import process_job

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Conversation states
SELECTING_EVENT, UPLOADING_CSV, CUSTOMIZING_CERTIFICATE = range(3)

# Flask app instance
flask_app = create_app()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
    try:
        welcome_message = """
🎓 *Welcome to Denx Certificate Generator Bot!* 🎓

I can help you generate and send certificates to participants.

*Available Commands:*
/start - Show this welcome message
/newjob - Start a new certificate generation job
/status <job_id> - Check the status of a job
/events - List all available events
/help - Show help information

To get started, use /newjob to create a new certificate generation job!
    """
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_message = """
📚 *Help - How to Use the Bot* 📚

*Creating a New Job:*
1. Use /newjob command
2. Select an event from the list by replying with its number.
3. Upload a CSV file with participant data.

*CSV File Format:*
Your CSV file should have two columns: 'name' and 'email'.

*Checking Job Status:*
Use /status <job_id> to check the progress of your certificate generation job.
    """
    await update.message.reply_text(help_message, parse_mode='Markdown')


async def events_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /events command - list all events."""
    try:
        with flask_app.app_context():
            events = Event.find_all()
            
            if not events:
                await update.message.reply_text("No events available. Please create an event first.")
                return
            
            message = "*Available Events:*\n\n"
            for i, event in enumerate(events):
                message += f"*{i + 1}.* {event['name']}\n"
                if event.get('description'):
                    message += f"   _{event['description']}_\n"
                message += "\n"
            
            await update.message.reply_text(message, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f"Error fetching events: {str(e)}")


async def newjob_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /newjob command - start new job creation."""
    try:
        with flask_app.app_context():
            events = Event.find_all()
            
            if not events:
                await update.message.reply_text(
                    "No events available. Please create an event through the web interface first."
                )
                return ConversationHandler.END
            
            context.user_data['events_list'] = [{'_id': str(e['_id']), 'name': e['name']} for e in events]

            message = "*Select an event for certificate generation:*\n\n"
            for i, event in enumerate(events):
                message += f"{i + 1}. {event['name']}\n"
            
            message += "\nReply with the event number:"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            return SELECTING_EVENT
    except Exception as e:
        await update.message.reply_text(f"Error starting job: {str(e)}")
        return ConversationHandler.END


async def select_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle event selection."""
    try:
        event_index = int(update.message.text.strip()) - 1
        events_list = context.user_data.get('events_list', [])
        
        if 0 <= event_index < len(events_list):
            selected_event = events_list[event_index]
            context.user_data['event_id'] = selected_event['_id']
            context.user_data['event_name'] = selected_event['name']
            
            await update.message.reply_text(
                f"Selected event: *{selected_event['name']}*\n\n"
                f"Now, please upload a CSV file with participant data.\n\n"
                f"The CSV should have 'name' and 'email' columns.",
                parse_mode='Markdown'
            )
            return UPLOADING_CSV
        else:
            await update.message.reply_text(
                "Invalid event number. Please use /newjob to start again."
            )
            return ConversationHandler.END
            
    except (ValueError, IndexError):
        await update.message.reply_text(
            "Please send a valid event number."
        )
        return SELECTING_EVENT


async def receive_csv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle CSV file upload."""
    document = update.message.document
    if not document or not document.file_name.endswith('.csv'):
        await update.message.reply_text("Please upload a valid CSV file.")
        return UPLOADING_CSV
    
    try:
        file = await document.get_file()
        
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as tmp_file:
            await file.download_to_drive(tmp_file.name)
            context.user_data['csv_path'] = tmp_file.name
        
        await update.message.reply_text(
            "CSV received. Would you like to customize the certificate layout? (yes/no)"
        )
        return CUSTOMIZING_CERTIFICATE

    except Exception as e:
        await update.message.reply_text(f"Error processing CSV file: {str(e)}")
        return UPLOADING_CSV

async def handle_customization_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle user's choice for certificate customization."""
    choice = update.message.text.lower().strip()
    if choice == 'yes':
        await update.message.reply_text(
            "Please provide the customization details in JSON format. Example:\n"
            '```json\n'
            '[\n'
            '  {"text": "participant_name", "x": 0.5, "y": 0.4, "font_size": 60, "align": "center"},\n'
            '  {"text": "event_name", "x": 0.5, "y": 0.6, "font_size": 40, "align": "center"}\n'
            ']\n'
            '```'
        )
        # Re-using the same state to wait for the JSON
        return CUSTOMIZING_CERTIFICATE 
    elif choice == 'no':
        context.user_data['customization_json'] = None
        await process_and_create_job(update, context)
        return ConversationHandler.END
    # If the message is likely JSON, process it as customization
    elif update.message.text.strip().startswith('['):
        return await receive_customization(update, context)
    else:
        await update.message.reply_text("Invalid choice. Please enter 'yes' or 'no', or provide the JSON customization.")
        return CUSTOMIZING_CERTIFICATE

async def receive_customization(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive and process certificate customization JSON."""
    try:
        # Validate JSON
        json.loads(update.message.text)
        context.user_data['customization_json'] = update.message.text
        await update.message.reply_text("Customization received. Processing job...")
        await process_and_create_job(update, context)
        return ConversationHandler.END
    except json.JSONDecodeError:
        await update.message.reply_text("Invalid JSON format. Please try again, or type 'no' to use the default layout.")
        return CUSTOMIZING_CERTIFICATE

async def process_and_create_job(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Create and process the certificate generation job."""
    tmp_path = context.user_data.get('csv_path')
    if not tmp_path:
        await update.message.reply_text("Something went wrong. Please start over with /newjob.")
        return

    try:
        participants_data = parse_csv_file(tmp_path)
        if not participants_data:
            await update.message.reply_text("No valid participants found in CSV.")
            return

        with flask_app.app_context():
            event_id = context.user_data['event_id']
            chat_id = str(update.message.chat_id)
            customization_json = context.user_data.get('customization_json')

            job_id = Job.create(event_id, telegram_chat_id=chat_id)
            
            participants_to_insert = [
                {"job_id": ObjectId(job_id), "name": p['name'], "email": p['email'], "created_at": datetime.utcnow()}
                for p in participants_data
            ]
            if participants_to_insert:
                Participant.create_many(participants_to_insert)
            
            Job.set_total(job_id, len(participants_to_insert))

            import threading
            thread = threading.Thread(
                target=process_job,
                args=(flask_app, job_id, customization_json)
            )
            thread.daemon = True
            thread.start()

        os.unlink(tmp_path)
        await update.message.reply_text(
            f"✅ *Job Created Successfully!*\n\n"
            f"Job ID: {job_id}\n"
            f"Event: {context.user_data['event_name']}\n"
            f"Participants: {len(participants_data)}\n\n"
            f"Processing has started. Use /status {job_id} to check progress.",
            parse_mode='Markdown'
        )
    except Exception as e:
        await update.message.reply_text(f"Error creating job: {str(e)}")
    finally:
        context.user_data.clear()


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /cancel command."""
    context.user_data.clear()
    await update.message.reply_text(
        "Job creation cancelled. Use /newjob to start again."
    )
    return ConversationHandler.END


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /status command."""
    args = context.args
    
    if not args:
        await update.message.reply_text("Usage: /status <job_id>")
        return
    
    try:
        job_id = args[0]
        
        with flask_app.app_context():
            job = Job.find_by_id(job_id)
            
            if not job:
                await update.message.reply_text(f"Job {job_id} not found.")
                return
            
            event = Event.find_by_id(job['event_id'])
            
            status_emoji = {'pending': '⏳', 'processing': '⚙️', 'completed': '✅', 'failed': '❌'}
            
            message = f"{status_emoji.get(job['status'], '❓')} *Job Status*\n\n"
            message += f"Job ID: {job['_id']}\n"
            message += f"Event: {event['name'] if event else 'Unknown'}\n"
            message += f"Status: {job['status'].upper()}\n"
            message += f"Progress: {job.get('generated_certificates', 0)}/{job.get('total_certificates', 0)}\n"
            
            if job.get('completed_at'):
                message += f"Completed: {job['completed_at'].strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            if job.get('error_message'):
                message += f"\n⚠️ Error: {job['error_message'].splitlines()[0]}\n" # Show first line of error
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
    except Exception as e:
        await update.message.reply_text(f"Invalid job ID or error fetching status: {e}")


async def handle_unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle any text message that's not a command."""
    try:
        response = """
👋 *Hello!* I'm the Denx Certificate Generator Bot.

I can help you generate and send certificates to participants.

*Available Commands:*
/start - Show welcome message
/newjob - Start a new certificate generation job
/status <job_id> - Check the status of a job
/events - List all available events
/help - Show detailed help information

Type a command to get started! 🚀
        """
        await update.message.reply_text(response, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error handling unknown message: {e}")
        await update.message.reply_text("Sorry, I encountered an error. Please try using one of my commands: /start, /newjob, /status, /events, /help")


def main():
    """Run the Telegram bot."""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not set in environment variables")
        return
    
    application = Application.builder().token(token).build()
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("events", events_command))
    application.add_handler(CommandHandler("status", status_command))
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("newjob", newjob_command)],
        states={
            SELECTING_EVENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_event)],
            UPLOADING_CSV: [MessageHandler(filters.Document.ALL, receive_csv)],
            CUSTOMIZING_CERTIFICATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_customization_choice)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_command)],
    )
    application.add_handler(conv_handler)
    
    # Add handler for all other text messages (not in conversation and not commands)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_unknown_message))
    
    logger.info("Starting Telegram bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
