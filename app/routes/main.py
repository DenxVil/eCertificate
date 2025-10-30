"""Main routes for the application."""
from flask import Blueprint, render_template, jsonify
from app.models.sqlite_models import db
import os

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Home page."""
    return render_template('index.html')


@main_bp.route('/health')
def health():
    """Health check endpoint for deployment validation."""
    health_status = {
        'status': 'healthy',
        'service': 'eCertificate',
        'version': '1.0.0'
    }
    
    # Check database connectivity
    try:
        db.session.execute(db.text('SELECT 1'))
        health_status['database'] = 'connected'
    except Exception as e:
        health_status['database'] = 'disconnected'
        health_status['status'] = 'unhealthy'
        health_status['error'] = str(e)
        return jsonify(health_status), 503
    
    return jsonify(health_status), 200


@main_bp.route('/about')
def about():
    """About page."""
    return render_template('about.html')
