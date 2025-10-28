"""Main Flask application initialization."""
from flask import Flask, jsonify
from flask_pymongo import PyMongo
from config import config
from app.utils.email_sender import mail
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mongo = PyMongo()

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
    try:
        mongo.init_app(app)
        logger.info("MongoDB connection initialized successfully")
    except Exception as e:
        logger.warning(f"MongoDB initialization failed: {e}")
        logger.warning("App will continue without database functionality")
    
    try:
        mail.init_app(app)
        logger.info("Mail configuration initialized successfully")
    except Exception as e:
        logger.warning(f"Mail initialization failed: {e}")
        logger.warning("Email functionality may be limited")
    
    # Create necessary directories
    try:
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
        logger.info("Required directories created successfully")
    except Exception as e:
        logger.error(f"Failed to create required directories: {e}")
    
    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.events import events_bp
    from app.routes.jobs import jobs_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(events_bp, url_prefix='/events')
    app.register_blueprint(jobs_bp, url_prefix='/jobs')
    
    # Global error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({'error': 'Internal server error'}), 500
    
    logger.info(f"Flask app created successfully with config: {config_name}")
    return app
