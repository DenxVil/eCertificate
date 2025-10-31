# Quick Start Guide

This guide will help you get started with Denx Certificate Generator in 5 minutes.

## Prerequisites

- Python 3.8+
- pip
- A Gmail account (for email functionality)

## Quick Setup

1. **Clone and   Setup**
   ```bash
   git clone https://github.com/DenxVil/eCertificate.git
   cd eCertificate
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   ```bash
   cp .env.sample .env
   ```
   
   Edit `.env` and set at minimum:
   - `SECRET_KEY` - Any random string
   - `MAIL_USERNAME` - Your Gmail address
   - `MAIL_PASSWORD` - Your Gmail app password (see below)

4. **Get Gmail App Password**
   - Go to https://myaccount.google.com/security
   - Enable 2-Step Verification
   - Go to "App passwords"
   - Generate password for "Mail"
   - Copy to `MAIL_PASSWORD` in `.env`

5. **Start the Application**
   ```bash
   python app.py
   ```
   
   Open http://localhost:5000 in your browser.

## First Certificate Generation

1. **Create an Event**
   - Click "Events" → "Create New Event"
   - Name: "Test Event"
   - Upload `sample_template.png` as template
   - Click "Create Event"

2. **Create a Job**
   - Click "Jobs" → "Create New Job"
   - Select "Test Event"
   - Upload `sample_participants.csv` (or add single participant)
   - Click "Create Job"

3. **Monitor Progress**
   - Job will process automatically
   - Check status on the job details page
   - Certificates will be emailed to participants

## Using Telegram Bot (Optional)

1. **Create Bot**
   - Open Telegram, search for @BotFather
   - Send `/newbot` and follow instructions
   - Copy the bot token

2. **Configure Bot**
   - Add token to `.env` as `TELEGRAM_BOT_TOKEN`
   - Run: `python bot.py`
   - Search for your bot in Telegram
   - Send `/start`

## Need Help?

- Check the full [README.md](README.md)
- Review configuration in `.env.sample`
- Check the troubleshooting section in README.md

## Production Deployment

For production:
1. Set `FLASK_DEBUG=False` in `.env` (or remove FLASK_ENV and set config to 'production')
2. Change `SECRET_KEY` to a strong random value
3. Use a production WSGI server (gunicorn included)
4. Set up HTTPS
5. Consider using PostgreSQL instead of SQLite
6. Add authentication for the web interface

Example production start:
```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

## Tips

- Test with `sample_template.png` and `sample_participants.csv` first
- Make sure your template has space for text
- CSV must have 'name' and 'email' columns
- Check spam folder if emails don't arrive
- Monitor the console for error messages

Enjoy using Denx Certificate Generator! 🎓
