"""Main application entry point."""
from app import create_app
import os

app = create_app(os.getenv('FLASK_ENV', 'development'))

if __name__ == '__main__':
    # Debug mode is controlled by the Flask configuration
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
