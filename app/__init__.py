"""Main Flask application initialization."""
from flask import Flask, jsonify
from flask_compress import Compress
from app.models.sqlite_models import db
import config as config_module
from app.utils.email_sender import mail
from app.config.db_config import get_database_uri
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask-Compress for response compression
compress = Compress()


def create_app(config_name='default'):
    """Create and configure the Flask application.
    
    Args:
        config_name: Configuration name (development, production, or default)
        
    Returns:
        Configured Flask application
    """
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config_module.config[config_name])
    
    # Use SQLite database
    app.config["SQLALCHEMY_DATABASE_URI"] = get_database_uri()
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,  # Verify connections before using
        "pool_recycle": 300,    # Recycle connections after 5 minutes
    }
    
    # Enable response compression
    app.config["COMPRESS_MIMETYPES"] = [
        'text/html', 'text/css', 'text/xml', 'application/json',
        'application/javascript'
    ]
    app.config["COMPRESS_LEVEL"] = 6
    app.config["COMPRESS_MIN_SIZE"] = 500
    compress.init_app(app)
    
    # Initialize database
    db.init_app(app)
    
    # Create tables if they don't exist
    with app.app_context():
        try:
            # Check if tables already exist to avoid unnecessary logging
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            if not existing_tables or 'events' not in existing_tables:
                # SQLAlchemy's create_all() is idempotent - only creates missing tables
                db.create_all()
                logger.info("Database tables created successfully")
            else:
                # Tables already exist, no action needed
                logger.debug("Database tables already exist, skipping creation")
        except Exception as e:
            # Log any unexpected errors but don't prevent app startup
            logger.error(f"Failed to initialize database tables: {e}")
            # Don't raise - allow app to start but it may have issues
    
    # Initialize mail
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
    from app.routes.goonj import goonj_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(goonj_bp, url_prefix='/goonj')
    
    # Add security headers
    @app.after_request
    def add_security_headers(response):
        """Add security headers to all responses."""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        return response
    
    # Global error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return jsonify({'error': 'Internal server error'}), 500
    
    @app.errorhandler(RuntimeError)
    def handle_runtime_error(err):
        """Handle RuntimeError (e.g., database unavailable) with 503."""
        logger.error(f"Runtime error: {err}")
        return (str(err), 503)
    
    logger.info(f"Flask app created successfully with config: {config_name}")
    return app
