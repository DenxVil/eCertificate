"""Job management routes."""
from flask import Blueprint, render_template, request, jsonify, current_app, redirect, url_for, flash
from app.models.sqlite_models import db, Event, Job, Participant
from app.utils import parse_csv_file, parse_excel_file, save_uploaded_file
from app.utils.certificate_generator import CertificateGenerator
from app.utils.email_sender import send_certificate_email
from datetime import datetime
import os
import threading
import json
import logging
import io
import csv

jobs_bp = Blueprint('jobs', __name__)
logger = logging.getLogger(__name__)


def parse_participants_from_file(file_storage):
    """Parse participants from uploaded CSV file."""
    try:
        # TextIOWrapper handles streaming file storage
        stream = io.TextIOWrapper(file_storage.stream, encoding="utf-8")
    except Exception:
        # Fallback for cases where .stream is not available
        stream = io.StringIO(file_storage.read().decode("utf-8"))
    reader = csv.DictReader(stream)
    participants = []
    for row in reader:
        # normalize and trim values
        cleaned = {k: (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
        # skip empty rows
        if any((v for v in cleaned.values() if v not in (None, ""))):
            participants.append(cleaned)
    return participants


def parse_participants_from_text(csv_text):
    """Parse participants from CSV text."""
    stream = io.StringIO(csv_text)
    reader = csv.DictReader(stream)
    participants = []
    for row in reader:
        cleaned = {k: (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
        if any((v for v in cleaned.values() if v not in (None, ""))):
            participants.append(cleaned)
    return participants


def process_job(app, job_id, customization_json=None):
    """Process a certificate generation job in background."""
    with app.app_context():
        try:
            job = Job.find_by_id(job_id)
            if not job:
                logger.error(f"Job {job_id} not found")
                return
        except Exception as e:
            logger.error(f"Error retrieving job {job_id}: {e}")
            return

        import traceback as _tb
        try:
            Job.update_status(job_id, 'processing')
            
            event = Event.find_by_id(job.event_id)
            if not event:
                raise ValueError("Event not found")
            
            participants = Participant.find_by_job(job_id)
            
            tpl = event.template_path
            if not tpl:
                raise ValueError("Event template not found")

            upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
            if os.path.isabs(tpl):
                template_full_path = tpl
            elif tpl.startswith(upload_folder + os.sep) or tpl.startswith(upload_folder + '/'):
                template_full_path = tpl
            else:
                template_full_path = os.path.join(app.config['UPLOAD_FOLDER'], tpl)

            if not os.path.exists(template_full_path):
                raise ValueError(f"Event template file not found at path: {template_full_path}")
                
            generator = CertificateGenerator(
                template_path=template_full_path,
                output_folder=current_app.config['OUTPUT_FOLDER']
            )
            
            customization = json.loads(customization_json) if customization_json else None

            for participant in participants:
                try:
                    if customization:
                        fields = []
                        for field in customization:
                            text = field['text']
                            if text == 'participant_name':
                                text = participant.name
                            elif text == 'event_name':
                                text = event.name
                            elif text == 'date':
                                text = datetime.now().strftime("%B %d, %Y")
                            fields.append({**field, 'text': text})
                        cert_path = generator.generate(fields)
                    else:
                        cert_path = generator.generate_certificate(
                            participant_name=participant.name,
                            event_name=event.name
                        )
                    
                    cert_filename = os.path.basename(cert_path)
                    
                    email_sent = send_certificate_email(
                        recipient_email=participant.email,
                        recipient_name=participant.name,
                        event_name=event.name,
                        certificate_path=cert_path
                    )
                    
                    Participant.update_certificate(participant.id, cert_filename, email_sent)
                    Job.increment_generated(job_id)
                    
                except Exception as e:
                    tb = _tb.format_exc()
                    logger.error(f"Error processing participant {participant.name}: {str(e)}\n{tb}")
            
            Job.update_status(job_id, 'completed')

        except Exception as e:
            tb = _tb.format_exc()
            Job.update_status(job_id, 'failed', error_message=f"{str(e)}\n{tb}")
            logger.error(f"Job {job_id} failed: {str(e)}\n{tb}")


@jobs_bp.route('/')
def list_jobs():
    """List all jobs with pagination."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Limit per_page to prevent abuse
    per_page = min(per_page, 100)
    
    jobs_pagination = Job.query.order_by(Job.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    jobs_list = jobs_pagination.items
    for job in jobs_list:
        event = Event.find_by_id(job.event_id)
        job.event_name = event.name if event else 'Unknown Event'
    
    return render_template('jobs/list.html', 
                         jobs=jobs_list,
                         pagination=jobs_pagination)


@jobs_bp.route('/create', methods=['GET', 'POST'])
def create_job():
    """Create a new certificate generation job."""
    if request.method == 'POST':
        # Log diagnostic information
        logger.debug("Create job: content-type=%s, form_keys=%s, files=%s",
                     request.content_type, list(request.form.keys()), list(request.files.keys()))
        
        event_id = request.form.get('event_id')
        participants_data = None

        # 1) Try file upload (multipart/form-data) - check both 'participants' and 'participant_file'
        file_storage = request.files.get('participants') or request.files.get('participant_file')
        if file_storage and getattr(file_storage, 'filename', ''):
            try:
                # Handle CSV files with new robust parser
                if file_storage.filename.endswith('.csv'):
                    participants_data = parse_participants_from_file(file_storage)
                # Handle Excel files with existing parser
                elif file_storage.filename.endswith(('.xls', '.xlsx')):
                    participants_data = parse_excel_file(file_storage)
                else:
                    flash('Invalid file type. Please upload CSV or Excel.', 'error')
                    return redirect(request.url)
            except Exception as e:
                logger.exception('Failed to parse participants file: %s', e)
                flash('Failed to parse participants file', 'error')
                return redirect(request.url)

        # 2) Try CSV text from form field 'participants'
        if not participants_data and 'participants' in request.form:
            csv_text = request.form.get('participants', '')
            if csv_text.strip():
                try:
                    participants_data = parse_participants_from_text(csv_text)
                except Exception as e:
                    logger.exception('Failed to parse participants form text: %s', e)
                    flash('Failed to parse participants text', 'error')
                    return redirect(request.url)

        # 3) Try JSON body with {'participants': [...] }
        if not participants_data and request.is_json:
            body = request.get_json(silent=True) or {}
            if isinstance(body, dict) and 'participants' in body and body['participants']:
                participants_data = body['participants']
                # Extract event_id from JSON if not in form
                if not event_id and 'event_id' in body:
                    event_id = body['event_id']

        # 4) Check if we have participants data
        if not participants_data:
            # For API requests, return JSON error
            if request.is_json or request.accept_mimetypes.best == 'application/json':
                return jsonify({
                    'error': "No participant data provided. Provide multipart/form-data with field 'participants' (CSV file),\n"
                             "or a form field 'participants' containing CSV text, or a JSON body {\"participants\": [...] }."
                }), 400
            # For web forms, flash message and redirect
            flash('No participant data provided.', 'error')
            return redirect(request.url)
        
        # Check event_id
        if not event_id:
            if request.is_json or request.accept_mimetypes.best == 'application/json':
                return jsonify({'error': 'Please provide an event_id.'}), 400
            flash('Please select an event.', 'error')
            return redirect(url_for('jobs.create_job'))

        try:
            if not participants_data:
                if request.is_json or request.accept_mimetypes.best == 'application/json':
                    return jsonify({'error': 'No participants found in the data.'}), 400
                flash('No participants found in the file.', 'error')
                return redirect(request.url)

            job_id = Job.create(event_id)
            
            participants_to_insert = [
                {"job_id": job_id, "name": p.get('name', ''), "email": p.get('email', '')}
                for p in participants_data
            ]
            if participants_to_insert:
                Participant.create_many(participants_to_insert)
            
            Job.set_total(job_id, len(participants_to_insert))

            customization_json = request.form.get('customization_json')

            thread = threading.Thread(
                target=process_job,
                args=(current_app._get_current_object(), job_id, customization_json)
            )
            thread.daemon = True
            thread.start()

            # Return appropriate response based on request type
            if request.is_json or request.accept_mimetypes.best == 'application/json':
                return jsonify({'status': 'ok', 'job_id': str(job_id), 'participants_count': len(participants_to_insert)}), 201
            
            flash('Job created successfully! Certificates are being generated.', 'success')
            return redirect(url_for('jobs.view_job', job_id=job_id))

        except Exception as e:
            logger.exception('Error creating job: %s', e)
            if request.is_json or request.accept_mimetypes.best == 'application/json':
                return jsonify({'error': f'Error creating job: {str(e)}'}), 500
            flash(f'Error processing file: {e}', 'error')
            return redirect(request.url)

    events = Event.find_all()
    return render_template('jobs/create.html', events=events)


@jobs_bp.route('/<job_id>')
def view_job(job_id):
    """View job details and participants."""
    job = Job.find_by_id(job_id)
    if not job:
        flash('Job not found.', 'error')
        return redirect(url_for('jobs.list_jobs'))
        
    event = Event.find_by_id(job.event_id)
    participants = Participant.find_by_job(job_id)
    
    job.event_name = event.name if event else 'Unknown'
    
    return render_template('jobs/view.html', job=job, participants=participants)


@jobs_bp.route('/<job_id>/status')
def job_status(job_id):
    """Return job status as JSON."""
    job = Job.find_by_id(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify({
        'status': job.status,
        'total': job.total_certificates,
        'generated': job.generated_certificates,
        'error': job.error_message
    })


@jobs_bp.route('/<job_id>/reprocess', methods=['POST'])
def reprocess_job(job_id):
    """Reprocess a failed or completed job."""
    job = Job.find_by_id(job_id)
    if not job:
        flash('Job not found.', 'error')
        return redirect(url_for('jobs.list_jobs'))

    Job.update_status(job_id, 'pending')
    
    thread = threading.Thread(
        target=process_job,
        args=(current_app._get_current_object(), job_id, None)
    )
    thread.daemon = True
    thread.start()

    flash(f'Job {job_id} has been queued for reprocessing.', 'info')
    return redirect(url_for('jobs.view_job', job_id=job_id))
