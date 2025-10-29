"""Application configuration.

This module defines configuration classes for different environments.
Environment variables are loaded from .env file.

Security Notes:
- All sensitive credentials (tokens, passwords) must be stored in environment variables
- Never commit .env files to version control
- Use strong SECRET_KEY values in production
- Enable HTTPS in production deployments
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Base configuration with common settings."""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # MongoDB - supports both local MongoDB and Azure Cosmos DB
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/ecertificate')
    
    # Mail - SMTP configuration for sending certificates
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')
    
    # Telegram - bot token for Telegram integration
    # Note: No hardcoded tokens - always use environment variables
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    
    # Upload - file upload settings
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB default
    ALLOWED_EXTENSIONS = set(os.getenv('ALLOWED_EXTENSIONS', 'png,jpg,jpeg,svg').split(','))
    
    # Certificate generation - output folder for generated certificates
    OUTPUT_FOLDER = os.getenv('OUTPUT_FOLDER', 'generated_certificates')


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
