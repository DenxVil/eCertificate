"""GOONJ certificate generation routes."""
from flask import Blueprint, request, jsonify, send_file, current_app, render_template
from app.utils.goonj_renderer import GOONJRenderer
from app.utils.mail import send_goonj_certificate
import os
import io
import csv
import json
import logging

goonj_bp = Blueprint('goonj', __name__)
logger = logging.getLogger(__name__)


@goonj_bp.route('/', methods=['GET'])
def goonj_page():
    """Render the GOONJ UI page."""
    return render_template('goonj.html')


def parse_csv_file(file_storage):
    """Parse CSV file and return list of participant dictionaries."""
    try:
        stream = io.TextIOWrapper(file_storage.stream, encoding="utf-8")
    except Exception:
        stream = io.StringIO(file_storage.read().decode("utf-8"))
    
    reader = csv.DictReader(stream)
    participants = []
    for row in reader:
        # Normalize and trim values
        cleaned = {k.lower().strip(): (v.strip() if isinstance(v, str) else v) 
                  for k, v in row.items()}
        # Skip empty rows
        if any(v for v in cleaned.values() if v not in (None, "")):
            participants.append(cleaned)
    return participants


def parse_csv_text(csv_text):
    """Parse CSV text and return list of participant dictionaries."""
    stream = io.StringIO(csv_text)
    reader = csv.DictReader(stream)
    participants = []
    for row in reader:
        cleaned = {k.lower().strip(): (v.strip() if isinstance(v, str) else v) 
                  for k, v in row.items()}
        if any(v for v in cleaned.values() if v not in (None, "")):
            participants.append(cleaned)
    return participants


@goonj_bp.route('/generate', methods=['POST'])
def generate_certificate():
    """Generate GOONJ certificate for a single participant.
    
    Accepts participant data in three formats:
    1. CSV file upload (multipart/form-data with 'file' field)
    2. CSV text (form field 'csv_text')
    3. JSON ({"name": "...", "email": "...", "event": "...", "date": "..."})
    
    Returns:
        Generated certificate file (PNG or PDF) or JSON error
    """
    participant_data = None
    output_format = request.form.get('format', 'png').lower()
    
    # Validate format
    if output_format not in ['png', 'pdf']:
        return jsonify({
            'error': 'Invalid format. Supported formats: png, pdf'
        }), 400
    
    # 1. Try file upload (CSV)
    file_storage = request.files.get('file')
    if file_storage and getattr(file_storage, 'filename', ''):
        if not file_storage.filename.endswith('.csv'):
            return jsonify({
                'error': 'Invalid file type. Please upload a CSV file.'
            }), 400
        
        try:
            participants = parse_csv_file(file_storage)
            if not participants:
                return jsonify({
                    'error': 'No valid participant data found in CSV file.'
                }), 400
            # Use first participant for single certificate generation
            participant_data = participants[0]
        except Exception as e:
            logger.exception('Failed to parse CSV file: %s', e)
            return jsonify({
                'error': 'Failed to parse CSV file. Please ensure it has valid format with headers.'
            }), 400
    
    # 2. Try CSV text from form field
    if not participant_data and 'csv_text' in request.form:
        csv_text = request.form.get('csv_text', '')
        if csv_text.strip():
            try:
                participants = parse_csv_text(csv_text)
                if not participants:
                    return jsonify({
                        'error': 'No valid participant data found in CSV text.'
                    }), 400
                participant_data = participants[0]
            except Exception as e:
                logger.exception('Failed to parse CSV text: %s', e)
                return jsonify({
                    'error': 'Failed to parse CSV text. Please ensure it has valid CSV format.'
                }), 400
    
    # 3. Try JSON body
    if not participant_data and request.is_json:
        try:
            participant_data = request.get_json()
        except Exception as e:
            logger.exception('Failed to parse JSON: %s', e)
            return jsonify({
                'error': 'Failed to parse JSON body. Please ensure valid JSON format.'
            }), 400
    
    # 4. Try form fields for direct input
    if not participant_data:
        name = request.form.get('name')
        if name:
            participant_data = {
                'name': name,
                'email': request.form.get('email', ''),
                'event': request.form.get('event', 'GOONJ'),
                'date': request.form.get('date', ''),
            }
    
    # Validate that we have participant data
    if not participant_data:
        return jsonify({
            'error': 'No participant data provided. Please provide data via CSV file, CSV text, JSON body, or form fields (name, email, event, date).'
        }), 400
    
    # Validate required field: name
    if 'name' not in participant_data or not participant_data['name']:
        return jsonify({
            'error': 'Missing required field: name'
        }), 400
    
    try:
        # Get GOONJ template path
        template_path = os.path.join(
            current_app.root_path, 
            '..', 
            'templates', 
            'goonj_certificate.png'
        )
        template_path = os.path.abspath(template_path)
        
        if not os.path.exists(template_path):
            logger.error(f"GOONJ template not found at: {template_path}")
            return jsonify({
                'error': 'GOONJ certificate template not found. Please ensure templates/goonj_certificate.png exists.'
            }), 500
        
        # Initialize renderer
        output_folder = current_app.config.get('OUTPUT_FOLDER', 'generated_certificates')
        # Ensure output_folder is an absolute path
        if not os.path.isabs(output_folder):
            output_folder = os.path.abspath(output_folder)
        renderer = GOONJRenderer(template_path, output_folder)
        
        # Generate certificate
        cert_path = renderer.render(participant_data, output_format=output_format)
        
        # Validate the certificate path is within the output folder (security check)
        cert_path_abs = os.path.abspath(cert_path)
        output_folder_abs = os.path.abspath(output_folder)
        if not cert_path_abs.startswith(output_folder_abs):
            logger.error(f"Certificate path {cert_path_abs} is outside output folder {output_folder_abs}")
            return jsonify({
                'error': 'Certificate generation failed: invalid output path.'
            }), 500
        
        # Send email if email is present and SMTP is configured
        email_sent = False
        participant_email = participant_data.get('email')
        if participant_email:
            event_name = participant_data.get('event', 'GOONJ')
            email_sent = send_goonj_certificate(
                recipient_email=participant_email,
                recipient_name=participant_data['name'],
                certificate_path=cert_path_abs,
                event_name=event_name
            )
        
        # Return the certificate file
        mimetype = 'application/pdf' if output_format == 'pdf' else 'image/png'
        return send_file(
            cert_path_abs,
            mimetype=mimetype,
            as_attachment=True,
            download_name=os.path.basename(cert_path_abs)
        )
        
    except FileNotFoundError as e:
        logger.error(f"File not found error: {str(e)}")
        return jsonify({
            'error': 'Certificate generation failed: template or output directory not found.'
        }), 500
    except Exception as e:
        logger.exception('Error generating certificate: %s', e)
        return jsonify({
            'error': 'Error generating certificate. Please check your input data and try again.'
        }), 500


@goonj_bp.route('/status', methods=['GET'])
def status():
    """Check if GOONJ certificate generation is available."""
    template_path = os.path.join(
        current_app.root_path, 
        '..', 
        'templates', 
        'goonj_certificate.png'
    )
    template_path = os.path.abspath(template_path)
    
    smtp_configured = bool(current_app.config.get('MAIL_USERNAME'))
    
    return jsonify({
        'status': 'available',
        'template_exists': os.path.exists(template_path),
        'smtp_configured': smtp_configured,
        'supported_formats': ['png', 'pdf'],
        'endpoint': '/goonj/generate'
    })
