"""Smart certificate generation routes with AI-powered field detection."""
from flask import Blueprint, render_template, request, jsonify, current_app, send_file
from app.utils.certificate_scanner import CertificateScanner, SmartCertificateAligner
from app.utils import allowed_file, save_uploaded_file
import os
import logging
from datetime import datetime

smart_cert_bp = Blueprint('smart_certificate', __name__)
logger = logging.getLogger(__name__)

# Store scanned data temporarily (in production, use Redis or database)
scanned_templates = {}


@smart_cert_bp.route('/')
def index():
    """Smart certificate generator page."""
    return render_template('smart_certificate.html')


@smart_cert_bp.route('/scan', methods=['POST'])
def scan_template():
    """Scan uploaded template and detect fields with optimized error handling."""
    try:
        # Validate request
        if 'template' not in request.files:
            return jsonify({'success': False, 'error': 'No template file provided'}), 400
        
        template_file = request.files['template']
        
        if not template_file.filename:
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        # Validate file type
        if not allowed_file(template_file.filename, current_app.config['ALLOWED_EXTENSIONS']):
            return jsonify({'success': False, 'error': 'Invalid file type. Please upload PNG, JPG, or PDF'}), 400
        
        # Validate file size (prevent excessive memory usage)
        template_file.seek(0, os.SEEK_END)
        file_size = template_file.tell()
        template_file.seek(0)
        
        max_size = current_app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)
        if file_size > max_size:
            return jsonify({'success': False, 'error': f'File too large. Maximum size: {max_size // (1024*1024)}MB'}), 400
        
        # Save uploaded file
        template_path = save_uploaded_file(template_file, current_app.config['UPLOAD_FOLDER'])
        
        # Scan the template
        scanner = CertificateScanner(dpi=300)
        analysis = scanner.scan_certificate(template_path)
        
        # Store the analysis (use session ID or database in production)
        session_id = f"scan_{datetime.now().timestamp()}"
        scanned_templates[session_id] = {
            'analysis': analysis,
            'template_path': template_path
        }
        
        # Convert detected fields to JSON-serializable format
        fields = [
            {
                'text': field.text,
                'x': field.x,
                'y': field.y,
                'width': field.width,
                'height': field.height,
                'font_size': field.font_size,
                'color': field.color,
                'alignment': field.alignment,
                'confidence': field.confidence,
                'field_type': field.field_type
            }
            for field in analysis.detected_fields
        ]
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'template_path': template_path,
            'fields': fields,
            'confidence': analysis.confidence_score,
            'width': analysis.width,
            'height': analysis.height
        })
    
    except Exception as e:
        logger.error(f"Error scanning template: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'An error occurred while scanning the template'}), 500


@smart_cert_bp.route('/generate', methods=['POST'])
def generate_certificate():
    """Generate certificate with user-provided field values."""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        template_path = data.get('template_path')
        fields = data.get('fields', {})
        
        if not template_path:
            return jsonify({'success': False, 'error': 'Template path not provided'}), 400
        
        # Find the scanned analysis
        analysis = None
        for session_data in scanned_templates.values():
            if session_data['template_path'] == template_path:
                analysis = session_data['analysis']
                break
        
        if not analysis:
            return jsonify({'success': False, 'error': 'Template analysis not found. Please rescan the template.'}), 404
        
        # Generate certificate
        aligner = SmartCertificateAligner(analysis)
        
        # Create output filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f"certificate_{timestamp}.png"
        output_path = os.path.join(current_app.config['OUTPUT_FOLDER'], output_filename)
        
        # Generate the certificate
        cert_path = aligner.generate_aligned_certificate(
            template_path,
            fields,
            output_path
        )
        
        return jsonify({
            'success': True,
            'certificate_path': cert_path,
            'message': 'Certificate generated successfully'
        })
    
    except Exception as e:
        logger.error(f"Error generating certificate: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'An error occurred while generating the certificate'}), 500


@smart_cert_bp.route('/download')
def download_certificate():
    """Download generated certificate."""
    try:
        cert_path = request.args.get('path')
        
        if not cert_path:
            return jsonify({'error': 'Certificate path not provided'}), 400
        
        # Security: Ensure the path is safe and within the output folder
        # Get absolute paths for comparison
        output_folder = os.path.abspath(current_app.config['OUTPUT_FOLDER'])
        requested_path = os.path.abspath(cert_path)
        
        # Verify the path is within the allowed output folder
        if not requested_path.startswith(output_folder):
            logger.warning(f"Attempted access to file outside output folder: {cert_path}")
            return jsonify({'error': 'Invalid file path'}), 403
        
        # Check if file exists
        if not os.path.exists(requested_path):
            return jsonify({'error': 'Certificate not found'}), 404
        
        return send_file(requested_path, as_attachment=True)
    
    except Exception as e:
        logger.error(f"Error downloading certificate: {e}", exc_info=True)
        return jsonify({'error': 'An error occurred while downloading the certificate'}), 500
