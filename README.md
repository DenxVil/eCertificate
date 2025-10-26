# 🎓 Denx Certificate Generator

A powerful web application for generating and distributing digital certificates with email delivery and Telegram bot integration.

## Features

- ✅ **Custom Certificate Templates**: Upload your own certificate designs (PNG, JPG, SVG)
- ✅ **Event Management**: Create and manage multiple events with different templates
- ✅ **Bulk Processing**: Upload participant lists via CSV or Excel files
- ✅ **Automated Generation**: Certificates are generated automatically with participant names
- ✅ **Email Delivery**: Certificates are sent directly to participants via email
- ✅ **Telegram Bot**: Control the system through an integrated Telegram bot
- ✅ **Job Tracking**: Monitor certificate generation jobs in real-time
- ✅ **Web Interface**: User-friendly web interface for all operations

## Technology Stack

- **Backend**: Flask (Python 3.8+)
- **Database**: SQLAlchemy with SQLite
- **Certificate Generation**: Pillow (PIL)
- **Email**: Flask-Mail (SMTP)
- **Bot**: python-telegram-bot
- **Data Processing**: Pandas, openpyxl

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- A Gmail account (for sending emails) or another SMTP server
- A Telegram bot token (optional, for Telegram integration)

### Step 1: Clone the Repository

```bash
git clone https://github.com/DenxVil/eCertificate.git
cd eCertificate
```

### Step 2: Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Create a `.env` file in the root directory:

```bash
cp .env.sample .env
```

Edit the `.env` file with your settings:

```env
# Flask Configuration
SECRET_KEY=your-secret-key-here-change-in-production
FLASK_ENV=development

# Database
DATABASE_URL=sqlite:///certificates.db

# Mail Configuration (Gmail example)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com

# Telegram Bot Configuration (Optional)
TELEGRAM_BOT_TOKEN=your-telegram-bot-token-here

# Upload Configuration
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216
ALLOWED_EXTENSIONS=png,jpg,jpeg,svg

# Certificate Generation
OUTPUT_FOLDER=generated_certificates
```

### Step 5: Set Up Gmail App Password (for Email)

1. Go to your Google Account settings
2. Enable 2-Factor Authentication
3. Go to Security > App Passwords
4. Generate a new app password for "Mail"
5. Use this password in your `.env` file as `MAIL_PASSWORD`

### Step 6: Set Up Telegram Bot (Optional)

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` command
3. Follow the instructions to create your bot
4. Copy the bot token
5. Add the token to your `.env` file as `TELEGRAM_BOT_TOKEN`

## Running the Application

### Start the Web Application

```bash
python app.py
```

The web interface will be available at `http://localhost:5000`

### Start the Telegram Bot (Optional)

In a separate terminal:

```bash
python bot.py
```

## Usage

### Web Interface

1. **Create an Event**
   - Navigate to "Events" → "Create New Event"
   - Enter event name and description
   - Upload a certificate template (PNG, JPG, or SVG)
   - Click "Create Event"

2. **Generate Certificates**
   - Navigate to "Jobs" → "Create New Job"
   - Select an event
   - Add participants:
     - Single entry: Enter name and email
     - Bulk upload: Upload CSV/Excel file
   - Click "Create Job"

3. **Track Progress**
   - View job status in the "Jobs" list
   - Click on a job to see detailed progress
   - Monitor certificate generation and email delivery

### CSV File Format

Your CSV file should contain two columns: `name` and `email`

Example:

```csv
name,email
John Doe,john@example.com
Jane Smith,jane@example.com
Alice Johnson,alice@example.com
```

### Telegram Bot Commands

- `/start` - Get welcome message and instructions
- `/events` - List all available events
- `/newjob` - Start a new certificate generation job
- `/status <job_id>` - Check the status of a job
- `/help` - Show help information

### Using the Telegram Bot

1. Open Telegram and search for your bot
2. Send `/start` to begin
3. Send `/newjob` to create a new job
4. Select an event by sending its ID
5. Upload a CSV file with participant data
6. Receive job confirmation with job ID
7. Use `/status <job_id>` to check progress

## Project Structure

```
eCertificate/
├── app/
│   ├── __init__.py          # Flask app initialization
│   ├── models/              # Database models
│   │   └── __init__.py
│   ├── routes/              # Route handlers
│   │   ├── main.py
│   │   ├── events.py
│   │   └── jobs.py
│   ├── utils/               # Utility functions
│   │   ├── __init__.py
│   │   ├── certificate_generator.py
│   │   └── email_sender.py
│   ├── templates/           # HTML templates
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── about.html
│   │   ├── events/
│   │   └── jobs/
│   └── static/              # Static files (CSS, JS, images)
├── bot.py                   # Telegram bot
├── app.py                   # Main application entry point
├── config.py                # Configuration
├── requirements.txt         # Python dependencies
├── .env.sample             # Sample environment variables
├── .gitignore              # Git ignore file
└── README.md               # This file
```

## Customization

### Certificate Template

The certificate template should be an image file (PNG, JPG, or SVG) with space for:
- Participant name (centered)
- Event name
- Date

The default positions are:
- Name: Center of the image, 50px above middle
- Event: Center of the image, 50px below middle
- Date: Center of the image, 150px from bottom

You can customize these positions by modifying the `CertificateGenerator` class in `app/utils/certificate_generator.py`.

### Email Template

Email templates can be customized in `app/utils/email_sender.py`. Modify the `send_certificate_email` function to change the email content.

## Troubleshooting

### Database Issues

If you encounter database errors, try deleting the database file and restarting:

```bash
rm certificates.db
python app.py
```

### Email Not Sending

- Verify SMTP credentials in `.env`
- Check if "Less secure app access" is enabled (for Gmail)
- Use an app password instead of your regular password
- Check firewall settings for SMTP port (587)

### Telegram Bot Not Responding

- Verify the bot token in `.env`
- Ensure `bot.py` is running
- Check bot permissions in Telegram
- Look for errors in the bot terminal

### Certificate Generation Issues

- Ensure the template file exists and is accessible
- Check file permissions on upload and output folders
- Verify PIL/Pillow is properly installed
- Check available fonts on your system

## API Endpoints

The application provides REST API endpoints:

### Events
- `GET /events/api` - List all events
- `GET /events/api/<event_id>` - Get event details

### Jobs
- `GET /jobs/api` - List all jobs
- `GET /jobs/api/<job_id>` - Get job status

## Security Considerations

- **IMPORTANT**: Set `FLASK_ENV=production` and `FLASK_DEBUG=False` in your `.env` file when deploying to production
- Change the `SECRET_KEY` in production to a strong random value
- Use HTTPS in production
- Keep your `.env` file secure and never commit it
- Use app passwords for email services
- Regularly update dependencies
- Implement rate limiting for production use
- Add authentication for the web interface in production
- Never run Flask with debug mode enabled in production environments

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is open source and available under the MIT License.

## Credits

This project combines the best features from several certificate generation projects:
- [Certificate-Generator-MLSA](https://github.com/Sabyasachi-Seal/Certificate-Generator-MLSA)
- [hudas-certificate-generator](https://github.com/haliknihudas666/hudas-certificate-generator)
- [Flask-Generate-Certificate](https://github.com/vigneshshettyin/Flask-Generate-Certificate)
- [CertificateGenerator](https://github.com/tusharnankani/CertificateGenerator)

## Support

For issues, questions, or suggestions, please open an issue on GitHub.

---

Made with ❤️ by DenxVil