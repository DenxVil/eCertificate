"""Main Flask application initialization."""
from flask import Flask
from config import config
from app.models import db
from app.utils.email_sender import mail
import os


def create_app(config_name='default'):
    """Create and configure the Flask application.
    
    Args:
        config_name: Configuration name (development, production, or default)
        
    Returns:
        Configured Flask application
    """
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Create necessary directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
    
    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.events import events_bp
    from app.routes.jobs import jobs_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(events_bp, url_prefix='/events')
    app.register_blueprint(jobs_bp, url_prefix='/jobs')
    
    return app
