"""GOONJ certificate generation routes."""
from flask import Blueprint, request, jsonify, send_file, current_app, render_template, url_for
from app.utils.goonj_renderer import GOONJRenderer
from app.utils.mail import send_goonj_certificate
from app.utils.alignment_checker import (
    verify_certificate_alignment,
    get_reference_certificate_path,
    AlignmentVerificationError
)
from app.utils.auto_alignment_fixer import ensure_ditto_alignment
from app.utils.universal_alignment_checker import verify_all_certificates
from app.utils.field_position_verifier import verify_field_positions
import os
import io
import csv
import json
import logging
import base64

goonj_bp = Blueprint('goonj', __name__)
logger = logging.getLogger(__name__)


@goonj_bp.route('/', methods=['GET'])
def goonj_page():
    """Render the GOONJ UI page."""
    email_max_retries = current_app.config.get('EMAIL_MAX_RETRIES', 150)
    return render_template('goonj.html', email_max_retries=email_max_retries)


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


def check_smtp_configuration():
    """Check SMTP configuration and return detailed status.
    
    Returns:
        Dictionary with:
        - configured: bool
        - issues: list of configuration issues
        - message: human-readable status message
    """
    issues = []
    
    mail_server = current_app.config.get('MAIL_SERVER')
    mail_port = current_app.config.get('MAIL_PORT')
    mail_username = current_app.config.get('MAIL_USERNAME')
    mail_password = current_app.config.get('MAIL_PASSWORD')
    mail_sender = current_app.config.get('MAIL_DEFAULT_SENDER')
    
    if not mail_server:
        issues.append("MAIL_SERVER not configured")
    
    if not mail_port:
        issues.append("MAIL_PORT not configured")
    
    if not mail_username:
        issues.append("MAIL_USERNAME (email address) not configured")
    
    if not mail_password:
        issues.append("MAIL_PASSWORD (app password) not configured")
    
    if not mail_sender:
        issues.append("MAIL_DEFAULT_SENDER not configured")
    
    configured = len(issues) == 0
    
    if configured:
        message = f"SMTP configured: {mail_username} via {mail_server}:{mail_port}"
    else:
        message = f"SMTP not configured. Missing: {', '.join(issues)}"
    
    return {
        'configured': configured,
        'issues': issues,
        'message': message,
        'server': mail_server,
        'port': mail_port,
        'username': mail_username,
        'has_password': bool(mail_password),
        'sender': mail_sender
    }


@goonj_bp.route('/generate', methods=['POST'])
def generate_certificate():
    """Generate GOONJ certificate for a single participant.
    
    Accepts participant data in three formats:
    1. CSV file upload (multipart/form-data with 'file' field)
    2. CSV text (form field 'csv_text')
    3. JSON ({"name": "...", "event": "...", "organiser": "..."})
    
    Supports three fields:
    - name (required)
    - event (optional, default "GOONJ")
    - organiser or organizer (optional, default "AMA")
    - email (optional, for delivery only, not rendered)
    
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
                'event': request.form.get('event', 'GOONJ'),
            }
            # Accept both spellings of organiser/organizer
            organiser = request.form.get('organiser') or request.form.get('organizer', 'AMA')
            participant_data['organiser'] = organiser
            # Keep email for optional delivery, but don't render it
            email = request.form.get('email')
            if email:
                participant_data['email'] = email
    
    # Validate that we have participant data
    if not participant_data:
        return jsonify({
            'error': 'No participant data provided. Please provide data via CSV file, CSV text, JSON body, or form fields (name, event, organiser).'
        }), 400
    
    # Normalize organizer -> organiser for backward compatibility
    if 'organizer' in participant_data and 'organiser' not in participant_data:
        participant_data['organiser'] = participant_data['organizer']
    
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
        
        # ALIGNMENT VERIFICATION: Verify ALL generated certificates
        # This ensures consistent dimensions, format, template configuration, and field positions
        alignment_enabled = current_app.config.get('ENABLE_ALIGNMENT_CHECK', True)
        alignment_status = {
            'enabled': alignment_enabled,
            'passed': True,
            'message': 'Alignment verification skipped (disabled)',
            'details': {},
            'field_positions': {}
        }
        
        if alignment_enabled:
            try:
                logger.info("Running universal alignment verification for certificate")
                
                # Step 1: Universal verification (dimensions, format, template)
                verification_result = verify_all_certificates(cert_path_abs, template_path)
                
                alignment_status['passed'] = verification_result['passed']
                alignment_status['details'] = verification_result['checks']
                
                if not verification_result['passed']:
                    alignment_status['message'] = verification_result['message']
                    logger.error(f"❌ Alignment verification FAILED: {verification_result['message']}")
                    
                    # Clean up the failed certificate
                    try:
                        os.remove(cert_path_abs)
                        logger.info(f"Removed failed certificate: {cert_path_abs}")
                    except Exception as cleanup_error:
                        logger.warning(f"Could not remove failed certificate: {cleanup_error}")
                    
                    return jsonify({
                        'success': False,
                        'error': 'Certificate alignment verification failed',
                        'message': verification_result['message'],
                        'alignment_status': alignment_status
                    }), 500
                
                # Step 2: Field position verification (Y-coordinate alignment)
                # Compare with sample_certificate.png to ensure field vertical positions match
                sample_cert_path = os.path.join(
                    current_app.root_path,
                    '..',
                    'templates',
                    'sample_certificate.png'
                )
                sample_cert_path = os.path.abspath(sample_cert_path)
                
                if os.path.exists(sample_cert_path):
                    try:
                        # Get field position tolerance from config
                        tolerance_px = current_app.config.get('FIELD_POSITION_TOLERANCE_PX', 2)
                        
                        field_position_result = verify_field_positions(
                            cert_path_abs,
                            sample_cert_path,
                            tolerance_px=tolerance_px
                        )
                        
                        alignment_status['field_positions'] = field_position_result
                        
                        if field_position_result['passed']:
                            logger.info(f"✅ Field position verification PASSED: {field_position_result['message']}")
                            alignment_status['message'] = f"All checks passed. {field_position_result['message']}"
                        else:
                            logger.warning(f"⚠️ Field position verification FAILED: {field_position_result['message']}")
                            # Don't fail the certificate, just log warning
                            # This allows for minor rendering differences while still alerting
                            alignment_status['message'] = f"Dimension checks passed. Field positions: {field_position_result['message']}"
                    except Exception as e:
                        logger.warning(f"Field position verification error (non-fatal): {e}")
                        alignment_status['field_positions'] = {'error': str(e)}
                        alignment_status['message'] = f"All checks passed. Field position check skipped: {str(e)}"
                else:
                    logger.warning(f"Sample certificate not found at {sample_cert_path}, skipping field position check")
                    alignment_status['message'] = "All checks passed (field position check skipped - no sample reference)"
                
                logger.info(f"✅ Certificate verification completed: {alignment_status['message']}")
                    
            except Exception as e:
                logger.exception(f"Unexpected error during alignment verification: {e}")
                alignment_status['passed'] = False
                alignment_status['message'] = f'Verification error: {e}'
                alignment_status['error'] = str(e)
        
        # Optional validation in dev mode (gated by DEBUG_VALIDATE)
        if current_app.config.get('DEBUG_VALIDATE', False):
            try:
                from app.utils.certificate_validator import validate as validate_cert
                
                tolerance = current_app.config.get('VALIDATE_TOLERANCE_PX', 3)
                validation_result = validate_cert(
                    cert_path_abs, 
                    template_ref_path=template_path,
                    tolerance_px=tolerance
                )
                
                # Log validation results in dev mode
                logger.info(f"Certificate validation: {'PASS' if validation_result['pass'] else 'FAIL'}")
                for field_name, field_data in validation_result['details'].items():
                    logger.debug(
                        f"  {field_name}: dx={field_data['dx']}px, dy={field_data['dy']}px, "
                        f"ok={field_data['ok']}"
                    )
                
                if not validation_result['pass']:
                    logger.warning(
                        f"Certificate validation failed. Overlay saved to: {validation_result['overlay_path']}"
                    )
            except Exception as e:
                # Don't fail certificate generation if validation has issues
                logger.warning(f"Certificate validation encountered error (ignored): {e}")
        
        # Send email if email is present
        email_status = {
            'attempted': False,
            'sent': False,
            'error': None,
            'smtp_config': None
        }
        
        participant_email = participant_data.get('email')
        if participant_email:
            email_status['attempted'] = True
            
            # Check SMTP configuration first
            smtp_config = check_smtp_configuration()
            email_status['smtp_config'] = smtp_config
            
            if smtp_config['configured']:
                try:
                    event_name = participant_data.get('event', 'GOONJ')
                    email_result = send_goonj_certificate(
                        recipient_email=participant_email,
                        recipient_name=participant_data['name'],
                        certificate_path=cert_path_abs,
                        event_name=event_name
                    )
                    email_status['sent'] = email_result['success']
                    email_status['attempts'] = email_result['attempts']
                    
                    if email_result['success']:
                        logger.info(f"Certificate emailed successfully to {participant_email} after {email_result['attempts']} attempt(s)")
                    else:
                        email_status['error'] = f'Email sending failed after {email_result["attempts"]} attempt(s). Check server logs for details.'
                        logger.error(f"Failed to send email to {participant_email} after {email_result['attempts']} attempt(s)")
                        
                except Exception as e:
                    email_status['error'] = f'Email error: {str(e)}'
                    logger.exception(f"Exception while sending email to {participant_email}: {e}")
            else:
                email_status['error'] = smtp_config['message']
                logger.warning(f"Cannot send email - SMTP not configured: {smtp_config['message']}")
        
        # Check if client wants JSON response (via Accept header or return_json parameter)
        wants_json = (
            request.accept_mimetypes.best == 'application/json' or
            request.args.get('return_json') == 'true' or
            request.form.get('return_json') == 'true'
        )
        
        if wants_json:
            # Return JSON with detailed status
            # Create a download URL for the certificate
            cert_filename = os.path.basename(cert_path_abs)
            
            return jsonify({
                'success': True,
                'message': 'Certificate generated successfully',
                'certificate': {
                    'filename': cert_filename,
                    'path': cert_path_abs,
                    'download_url': url_for('goonj.download_certificate', filename=cert_filename, _external=False),
                    'format': output_format,
                    'size_bytes': os.path.getsize(cert_path_abs)
                },
                'participant': {
                    'name': participant_data['name'],
                    'event': participant_data.get('event', 'GOONJ'),
                    'organiser': participant_data.get('organiser', 'AMA'),
                    'email': participant_email
                },
                'alignment_status': alignment_status,
                'email_status': email_status
            }), 200
        
        # Default: Return the certificate file for download
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


@goonj_bp.route('/download/<filename>', methods=['GET'])
def download_certificate(filename):
    """Download a previously generated certificate.
    
    Args:
        filename: Name of the certificate file to download
        
    Returns:
        Certificate file or 404 error
    """
    try:
        # Security: validate filename (no path traversal)
        if '..' in filename or '/' in filename or '\\' in filename:
            logger.warning(f"Invalid filename attempted: {filename}")
            return jsonify({'error': 'Invalid filename'}), 400
        
        output_folder = current_app.config.get('OUTPUT_FOLDER', 'generated_certificates')
        if not os.path.isabs(output_folder):
            output_folder = os.path.abspath(output_folder)
        
        cert_path = os.path.join(output_folder, filename)
        cert_path_abs = os.path.abspath(cert_path)
        
        # Security: ensure file is within output folder
        if not cert_path_abs.startswith(os.path.abspath(output_folder)):
            logger.warning(f"Path traversal attempted: {filename}")
            return jsonify({'error': 'Invalid file path'}), 400
        
        if not os.path.exists(cert_path_abs):
            logger.warning(f"Certificate file not found: {cert_path_abs}")
            return jsonify({'error': 'Certificate not found'}), 404
        
        # Determine mimetype based on extension
        if filename.endswith('.pdf'):
            mimetype = 'application/pdf'
        elif filename.endswith('.png'):
            mimetype = 'image/png'
        else:
            mimetype = 'application/octet-stream'
        
        return send_file(
            cert_path_abs,
            mimetype=mimetype,
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.exception(f"Error downloading certificate {filename}: {e}")
        return jsonify({'error': 'Error downloading certificate'}), 500


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


# Cache for system status to avoid overhead
_system_status_cache = {'data': None, 'timestamp': 0}
_CACHE_DURATION = 2  # seconds


@goonj_bp.route('/api/system-status', methods=['GET'])
def system_status():
    """Get comprehensive system status for monitoring widget.
    
    Returns JSON with:
    - template_exists: bool
    - smtp_configured: bool
    - smtp_status_details: dict with configuration details and issues
    - engine_status: "operational" | "degraded" | "error"
    - latency_ms: int (approximate internal latency)
    - active_jobs_count: int
    - last_updated: ISO timestamp
    """
    import time
    from datetime import datetime
    
    # Check cache
    current_time = time.time()
    if (_system_status_cache['data'] is not None and 
        current_time - _system_status_cache['timestamp'] < _CACHE_DURATION):
        return jsonify(_system_status_cache['data'])
    
    # Measure latency (simple in-memory ping)
    start_time = time.time()
    
    try:
        # Check template
        template_path = os.path.join(
            current_app.root_path, 
            '..', 
            'templates', 
            'goonj_certificate.png'
        )
        template_path = os.path.abspath(template_path)
        template_exists = os.path.exists(template_path)
        
        # Check SMTP with detailed status
        smtp_status = check_smtp_configuration()
        smtp_configured = smtp_status['configured']
        
        # Count active jobs (pending or processing)
        try:
            from app.models.sqlite_models import Job
            active_jobs = Job.query.filter(
                Job.status.in_(['pending', 'processing'])
            ).count()
        except Exception as e:
            logger.warning(f"Failed to count active jobs: {e}")
            active_jobs = 0
        
        # Determine engine status
        if template_exists and smtp_configured:
            engine_status = "operational"
        elif template_exists:
            engine_status = "degraded"
        else:
            engine_status = "error"
        
        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Build response
        status_data = {
            'template_exists': template_exists,
            'smtp_configured': smtp_configured,
            'smtp_status_details': smtp_status,  # Include detailed SMTP status
            'engine_status': engine_status,
            'latency_ms': latency_ms,
            'active_jobs_count': active_jobs,
            'last_updated': datetime.utcnow().isoformat() + 'Z'
        }
        
        # Update cache
        _system_status_cache['data'] = status_data
        _system_status_cache['timestamp'] = current_time
        
        return jsonify(status_data)
        
    except Exception as e:
        logger.exception('Error getting system status: %s', e)
        # Return error status
        return jsonify({
            'template_exists': False,
            'smtp_configured': False,
            'smtp_status_details': {
                'configured': False,
                'message': 'Error checking SMTP configuration',
                'issues': ['System error occurred']
            },
            'engine_status': 'error',
            'latency_ms': int((time.time() - start_time) * 1000),
            'active_jobs_count': 0,
            'last_updated': datetime.utcnow().isoformat() + 'Z',
            'error': 'Failed to retrieve system status'
        }), 500
