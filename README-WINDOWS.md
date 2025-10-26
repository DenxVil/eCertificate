# 🪟 eCertificate - Windows Setup Guide

This guide provides step-by-step instructions for setting up and running the eCertificate application on Windows.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Detailed Setup](#detailed-setup)
- [Running the Application](#running-the-application)
- [Docker Setup](#docker-setup)
- [Troubleshooting](#troubleshooting)
- [Development Tips](#development-tips)

## Prerequisites

Before you begin, ensure you have the following installed on your Windows machine:

### Required
- **Python 3.8 or higher** - [Download Python](https://www.python.org/downloads/)
  - During installation, make sure to check "Add Python to PATH"
- **Git** - [Download Git for Windows](https://git-scm.com/download/win)

### Optional (for Docker)
- **Docker Desktop for Windows** - [Download Docker Desktop](https://www.docker.com/products/docker-desktop)
  - Requires Windows 10/11 Pro, Enterprise, or Education (with Hyper-V support)
  - Or Windows 10/11 Home with WSL 2

## Quick Start

The fastest way to get started on Windows:

### 1. Clone the Repository

```powershell
git clone https://github.com/DenxVil/eCertificate.git
cd eCertificate
```

### 2. Allow PowerShell Script Execution

Open PowerShell as Administrator and run:

```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Type `Y` and press Enter when prompted.

### 3. Run the Setup Script

In the eCertificate directory, run:

```powershell
.\scripts\windows\setup.ps1
```

This script will:
- Create a Python virtual environment in `.venv`
- Upgrade pip to the latest version
- Install all required dependencies from `requirements.txt`
- Create a `.env` file from `.env.example`

### 4. Configure Your Environment

Edit the `.env` file with your settings:

```powershell
notepad .env
```

**Important settings to configure:**
- `SECRET_KEY` - Change to a random secret key
- `MAIL_USERNAME` - Your email address
- `MAIL_PASSWORD` - Your email app password (see [Gmail Setup](#gmail-app-password-setup))
- `TELEGRAM_BOT_TOKEN` - Your Telegram bot token (optional)

### 5. Run the Application

```powershell
.\scripts\windows\run.ps1
```

The application will start and be available at: **http://localhost:5000**

## Detailed Setup

### Setting Up Python Virtual Environment (Manual)

If you prefer to set up manually instead of using the setup script:

```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Create .env file
Copy-Item .env.example .env

# Edit .env with your configuration
notepad .env
```

### Gmail App Password Setup

To send emails via Gmail, you need to create an App Password:

1. Go to your [Google Account](https://myaccount.google.com/)
2. Select **Security** from the left menu
3. Enable **2-Step Verification** if not already enabled
4. Under "Signing in to Google," select **App Passwords**
5. Select app: **Mail**
6. Select device: **Windows Computer**
7. Click **Generate**
8. Copy the 16-character password
9. Paste this password into your `.env` file as `MAIL_PASSWORD`

**Note:** Do NOT use your regular Gmail password. Always use an App Password.

### Telegram Bot Setup (Optional)

To enable Telegram bot features:

1. Open Telegram and search for [@BotFather](https://t.me/botfather)
2. Send `/newbot` command
3. Follow the instructions to create your bot
4. Copy the bot token provided by BotFather
5. Add the token to your `.env` file as `TELEGRAM_BOT_TOKEN`

#### Webhook Setup for Local Development (ngrok)

For Telegram webhooks to work on your local Windows machine:

1. Download [ngrok](https://ngrok.com/download)
2. Extract ngrok.exe to a folder
3. Run ngrok:
   ```powershell
   .\ngrok.exe http 5000
   ```
4. Copy the HTTPS forwarding URL (e.g., `https://abc123.ngrok.io`)
5. Add to your `.env`:
   ```
   TELEGRAM_WEBHOOK_URL=https://abc123.ngrok.io
   ```

## Running the Application

### Method 1: Using PowerShell Scripts (Recommended)

#### Run with Default Settings (Flask on port 5000)

```powershell
.\scripts\windows\run.ps1
```

#### Run with Custom Port

```powershell
.\scripts\windows\run.ps1 -Port 8080
```

#### Run with Custom Entrypoint

```powershell
.\scripts\windows\run.ps1 -Entrypoint "myapp.py"
```

#### Run with FastAPI (if supported)

```powershell
.\scripts\windows\run.ps1 -Framework fastapi
```

### Method 2: Manual Run

If you prefer to run manually:

```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Run the application
python app.py
```

### Running the Telegram Bot

In a **separate PowerShell window**:

```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Run the bot
python bot.py
```

## Docker Setup

### Using Docker Run Script

The easiest way to run with Docker:

```powershell
.\scripts\windows\run-docker.ps1
```

This script will:
- Check if Docker is installed and running
- Create a Dockerfile if one doesn't exist
- Build the Docker image
- Mount necessary folders (templates, static, uploads, etc.)
- Run the container with port 5000 exposed

#### Custom Port with Docker

```powershell
.\scripts\windows\run-docker.ps1 -Port 8080
```

### Using Docker Compose

For a more advanced setup:

```powershell
docker-compose -f docker-compose.windows.yml up
```

To run in the background:

```powershell
docker-compose -f docker-compose.windows.yml up -d
```

To stop:

```powershell
docker-compose -f docker-compose.windows.yml down
```

### Building Docker Image Manually

```powershell
# Build image
docker build -t ecertificate-app .

# Run container
docker run -p 5000:5000 --env-file .env ecertificate-app
```

## Troubleshooting

### PowerShell Script Execution Error

**Problem:** `cannot be loaded because running scripts is disabled on this system`

**Solution:** Run PowerShell as Administrator and execute:
```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Python Not Found

**Problem:** `python: command not found`

**Solution:**
1. Reinstall Python from [python.org](https://www.python.org/downloads/)
2. During installation, check "Add Python to PATH"
3. Restart PowerShell after installation

### Virtual Environment Activation Issues

**Problem:** Virtual environment won't activate

**Solution:**
```powershell
# Try this alternative activation method
& .\.venv\Scripts\Activate.ps1

# Or use the Python executable directly
.\.venv\Scripts\python.exe app.py
```

### Email Not Sending

**Problem:** Emails are not being sent

**Solutions:**
1. **Verify Gmail App Password:**
   - Make sure you're using an App Password, not your regular password
   - Check that 2FA is enabled on your Google account

2. **Check Firewall:**
   - Ensure port 587 (SMTP) is not blocked by Windows Firewall
   - Temporarily disable firewall to test

3. **Verify SMTP Settings:**
   - Double-check `MAIL_SERVER`, `MAIL_PORT`, `MAIL_USE_TLS` in `.env`
   - Try using port 465 with SSL instead of 587 with TLS

4. **Test with Alternative Email:**
   - Try Outlook/Office365 instead of Gmail
   ```env
   MAIL_SERVER=smtp.office365.com
   MAIL_PORT=587
   ```

### Port Already in Use

**Problem:** `Address already in use` or port 5000 is taken

**Solution:**
```powershell
# Find process using port 5000
netstat -ano | findstr :5000

# Kill the process (replace PID with actual process ID)
taskkill /F /PID <PID>

# Or use a different port
.\scripts\windows\run.ps1 -Port 8080
```

### Missing Dependencies

**Problem:** Import errors or missing modules

**Solution:**
```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Reinstall dependencies
pip install -r requirements.txt

# Or install specific missing package
pip install package-name
```

### Docker Not Starting

**Problem:** Docker daemon not running

**Solution:**
1. Open Docker Desktop
2. Wait for Docker to fully start (whale icon in system tray should be steady)
3. Run your Docker command again

### File Path Issues

**Problem:** Application can't find files or templates

**Solution:**
- Ensure you're running commands from the project root directory
- Check that folder paths in `.env` use forward slashes or double backslashes:
  ```env
  # Good
  UPLOAD_FOLDER=uploads
  OUTPUT_FOLDER=generated_certificates
  
  # Also works
  UPLOAD_FOLDER=C:/path/to/uploads
  ```

### Database Locked Error

**Problem:** `database is locked` error with SQLite

**Solution:**
```powershell
# Stop the application
# Delete the database file
Remove-Item certificates.db

# Restart the application (database will be recreated)
.\scripts\windows\run.ps1
```

### Line Ending Issues

**Problem:** Scripts have wrong line endings (LF vs CRLF)

**Solution:**
The repository includes a `.gitattributes` file that ensures PowerShell scripts use CRLF. If you still have issues:

```powershell
# Convert line endings in Git
git config --global core.autocrlf true

# Re-clone the repository
```

## Development Tips

### Using Windows Terminal

For the best PowerShell experience, install [Windows Terminal](https://aka.ms/terminal) from the Microsoft Store.

### IDE Setup

**VS Code:**
1. Install [Python extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
2. Select the virtual environment: Ctrl+Shift+P → "Python: Select Interpreter" → `.\.venv\Scripts\python.exe`

**PyCharm:**
1. File → Settings → Project → Python Interpreter
2. Add Interpreter → Existing Environment
3. Select `.venv\Scripts\python.exe`

### Hot Reload

Flask's development server supports hot reload by default. Any changes to Python files will automatically restart the server.

### Viewing Logs

Application logs are printed to the console. To save logs to a file:

```powershell
.\scripts\windows\run.ps1 | Tee-Object -FilePath app.log
```

### Testing Locally with HTTPS (Optional)

To test with HTTPS locally:

1. Install pyOpenSSL:
   ```powershell
   .\.venv\Scripts\pip.exe install pyopenssl
   ```

2. Run with SSL:
   ```powershell
   .\.venv\Scripts\python.exe -c "from app import create_app; app = create_app(); app.run(ssl_context='adhoc', host='0.0.0.0', port=5000)"
   ```

### Backing Up Your Database

```powershell
# Create a backup
Copy-Item certificates.db certificates.backup.db

# Restore from backup
Copy-Item certificates.backup.db certificates.db
```

## Additional Resources

- [Main README](README.md) - General project documentation
- [Quick Start Guide](QUICKSTART.md) - Quick start for all platforms
- [Contributing Guide](CONTRIBUTING.md) - How to contribute to the project
- [Flask Documentation](https://flask.palletsprojects.com/) - Flask framework docs
- [Python on Windows](https://docs.python.org/3/using/windows.html) - Official Python Windows guide

## Getting Help

If you encounter issues not covered in this guide:

1. Check the [GitHub Issues](https://github.com/DenxVil/eCertificate/issues)
2. Create a new issue with:
   - Windows version
   - Python version (`python --version`)
   - Error messages
   - Steps to reproduce

---

**Happy Certificate Generating! 🎓**
