"""Application configuration."""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Base configuration."""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # MongoDB
    MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017/ecertificate')
    
    # Mail
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')
    
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    
    # Upload
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB
    ALLOWED_EXTENSIONS = set(os.getenv('ALLOWED_EXTENSIONS', 'png,jpg,jpeg,svg').split(','))
    
    # Certificate generation
    OUTPUT_FOLDER = os.getenv('OUTPUT_FOLDER', 'generated_certificates')
    
    # Alignment verification settings
    ENABLE_ALIGNMENT_CHECK = os.getenv('ENABLE_ALIGNMENT_CHECK', 'True').lower() == 'true'
    ALIGNMENT_TOLERANCE_PX = float(os.getenv('ALIGNMENT_TOLERANCE_PX', '0.01'))
    ALIGNMENT_MAX_ATTEMPTS = int(os.getenv('ALIGNMENT_MAX_ATTEMPTS', '150'))
    
    # Field position verification settings
    FIELD_POSITION_TOLERANCE_PX = int(os.getenv('FIELD_POSITION_TOLERANCE_PX', '2'))
    
    # Validation settings (dev mode only)
    DEBUG_VALIDATE = os.getenv('DEBUG_VALIDATE', 'True').lower() == 'true'
    VALIDATE_TOLERANCE_PX = int(os.getenv('VALIDATE_TOLERANCE_PX', 3))


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
