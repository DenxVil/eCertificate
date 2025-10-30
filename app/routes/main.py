"""Main routes for the application."""
from flask import Blueprint, render_template, jsonify, redirect, url_for
import os

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Home page with Smart Certificate Generator."""
    return render_template('index.html')


@main_bp.route('/smart-certificate/')
def smart_certificate_redirect():
    """Redirect old smart-certificate route to main page."""
    return redirect(url_for('main.index'))


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
