"""Main routes for the application."""
from flask import Blueprint, render_template, jsonify
import os

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Home page."""
    return render_template('index.html')


@main_bp.route('/health')
def health():
    """Health check endpoint for deployment validation."""
    return jsonify({
        'status': 'healthy',
        'service': 'eCertificate',
        'version': '1.0.0'
    }), 200


@main_bp.route('/about')
def about():
    """About page."""
    return render_template('about.html')
