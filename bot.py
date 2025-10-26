"""Telegram bot for certificate generation."""
import os
import sys
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from dotenv import load_dotenv
import asyncio

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models import db, Event, Job, Participant
from app.utils import parse_csv_file
from app.routes.jobs import process_job
import tempfile

# Load environment variables
load_dotenv()

# Conversation states
SELECTING_EVENT, UPLOADING_CSV = range(2)

# Flask app instance
flask_app = create_app()


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command."""
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


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command."""
    help_message = """
📚 *Help - How to Use the Bot* 📚

*Creating a New Job:*
1. Use /newjob command
2. Select an event from the list
3. Upload a CSV file with participant data

*CSV File Format:*
Your CSV file should have two columns:
- name: Participant's name
- email: Participant's email address

Example:
```
name,email
John Doe,john@example.com
Jane Smith,jane@example.com
```

*Checking Job Status:*
Use /status <job_id> to check the progress of your certificate generation job.

For more information, visit our documentation.
    """
    await update.message.reply_text(help_message, parse_mode='Markdown')


async def events_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /events command - list all events."""
    with flask_app.app_context():
        events = Event.query.all()
        
        if not events:
            await update.message.reply_text("No events available. Please create an event first.")
            return
        
        message = "*Available Events:*\n\n"
        for event in events:
            message += f"*{event.id}.* {event.name}\n"
            if event.description:
                message += f"   _{event.description}_\n"
            message += "\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')


async def newjob_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /newjob command - start new job creation."""
    with flask_app.app_context():
        events = Event.query.all()
        
        if not events:
            await update.message.reply_text(
                "No events available. Please create an event through the web interface first."
            )
            return ConversationHandler.END
        
        message = "*Select an event for certificate generation:*\n\n"
        for event in events:
            message += f"{event.id}. {event.name}\n"
        
        message += "\nReply with the event ID number:"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        return SELECTING_EVENT


async def select_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle event selection."""
    try:
        event_id = int(update.message.text.strip())
        
        with flask_app.app_context():
            event = Event.query.get(event_id)
            
            if not event:
                await update.message.reply_text(
                    "Invalid event ID. Please use /newjob to start again."
                )
                return ConversationHandler.END
            
            # Store event ID in context
            context.user_data['event_id'] = event_id
            context.user_data['event_name'] = event.name
            
            await update.message.reply_text(
                f"Selected event: *{event.name}*\n\n"
                f"Now, please upload a CSV file with participant data.\n\n"
                f"The CSV should have 'name' and 'email' columns.",
                parse_mode='Markdown'
            )
            return UPLOADING_CSV
            
    except ValueError:
        await update.message.reply_text(
            "Please send a valid event ID number."
        )
        return SELECTING_EVENT


async def receive_csv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle CSV file upload."""
    if not update.message.document:
        await update.message.reply_text(
            "Please upload a CSV file."
        )
        return UPLOADING_CSV
    
    document = update.message.document
    
    if not document.file_name.endswith('.csv'):
        await update.message.reply_text(
            "Please upload a CSV file (must have .csv extension)."
        )
        return UPLOADING_CSV
    
    try:
        # Download the file
        file = await document.get_file()
        
        # Save to temporary location
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.csv', delete=False) as tmp_file:
            await file.download_to_drive(tmp_file.name)
            tmp_path = tmp_file.name
        
        # Parse CSV
        participants = parse_csv_file(tmp_path)
        
        if not participants:
            await update.message.reply_text(
                "No valid participants found in CSV file. Please check the format."
            )
            os.unlink(tmp_path)
            return UPLOADING_CSV
        
        # Create job
        with flask_app.app_context():
            event_id = context.user_data['event_id']
            chat_id = str(update.message.chat_id)
            
            # Create job
            job = Job(
                event_id=event_id,
                telegram_chat_id=chat_id
            )
            db.session.add(job)
            db.session.commit()
            
            # Add participants
            for p_data in participants:
                participant = Participant(
                    job_id=job.id,
                    name=p_data['name'],
                    email=p_data['email']
                )
                db.session.add(participant)
            
            job.total_certificates = len(participants)
            db.session.commit()
            
            job_id = job.id
            
            # Start processing in background
            import threading
            thread = threading.Thread(
                target=process_job,
                args=(flask_app, job_id)
            )
            thread.daemon = True
            thread.start()
        
        # Clean up temporary file
        os.unlink(tmp_path)
        
        await update.message.reply_text(
            f"✅ *Job Created Successfully!*\n\n"
            f"Job ID: {job_id}\n"
            f"Event: {context.user_data['event_name']}\n"
            f"Participants: {len(participants)}\n\n"
            f"Processing has started. Use /status {job_id} to check progress.",
            parse_mode='Markdown'
        )
        
        # Clear user data
        context.user_data.clear()
        return ConversationHandler.END
        
    except Exception as e:
        await update.message.reply_text(
            f"Error processing CSV file: {str(e)}\n\n"
            f"Please make sure your CSV has 'name' and 'email' columns."
        )
        return UPLOADING_CSV


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
        await update.message.reply_text(
            "Please provide a job ID. Usage: /status <job_id>"
        )
        return
    
    try:
        job_id = int(args[0])
        
        with flask_app.app_context():
            job = Job.query.get(job_id)
            
            if not job:
                await update.message.reply_text(
                    f"Job {job_id} not found."
                )
                return
            
            event = Event.query.get(job.event_id)
            
            # Build status message
            status_emoji = {
                'pending': '⏳',
                'processing': '⚙️',
                'completed': '✅',
                'failed': '❌'
            }
            
            message = f"{status_emoji.get(job.status, '❓')} *Job Status*\n\n"
            message += f"Job ID: {job.id}\n"
            message += f"Event: {event.name}\n"
            message += f"Status: {job.status.upper()}\n"
            message += f"Progress: {job.generated_certificates}/{job.total_certificates}\n"
            
            if job.completed_at:
                message += f"Completed: {job.completed_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            if job.error_message:
                message += f"\n⚠️ Error: {job.error_message}\n"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
    except ValueError:
        await update.message.reply_text(
            "Invalid job ID. Please provide a number."
        )


def main():
    """Run the Telegram bot."""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token:
        print("Error: TELEGRAM_BOT_TOKEN not set in environment variables")
        return
    
    # Create application
    application = Application.builder().token(token).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("events", events_command))
    application.add_handler(CommandHandler("status", status_command))
    
    # Conversation handler for new job
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("newjob", newjob_command)],
        states={
            SELECTING_EVENT: [MessageHandler(filters.TEXT & ~filters.COMMAND, select_event)],
            UPLOADING_CSV: [MessageHandler(filters.Document.ALL, receive_csv)],
        },
        fallbacks=[CommandHandler("cancel", cancel_command)],
    )
    application.add_handler(conv_handler)
    
    # Start the bot
    print("Starting Telegram bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()
