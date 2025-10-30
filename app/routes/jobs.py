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

jobs_bp = Blueprint('jobs', __name__)
logger = logging.getLogger(__name__)


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
                    print(f"Error processing participant {participant.name}: {str(e)}\n{tb}")
            
            Job.update_status(job_id, 'completed')

        except Exception as e:
            tb = _tb.format_exc()
            Job.update_status(job_id, 'failed', error_message=f"{str(e)}\n{tb}")
            print(f"Job {job_id} failed: {str(e)}\n{tb}")


@jobs_bp.route('/')
def list_jobs():
    """List all jobs."""
    jobs_list = Job.query.order_by(Job.created_at.desc()).all()
    for job in jobs_list:
        event = Event.find_by_id(job.event_id)
        job.event_name = event.name if event else 'Unknown Event'
    return render_template('jobs/list.html', jobs=jobs_list)


@jobs_bp.route('/create', methods=['GET', 'POST'])
def create_job():
    """Create a new certificate generation job."""
    if request.method == 'POST':
        event_id = request.form.get('event_id')
        if not event_id:
            flash('Please select an event.', 'error')
            return redirect(url_for('jobs.create_job'))

        if 'participant_file' not in request.files:
            flash('No participant file provided.', 'error')
            return redirect(request.url)
            
        file = request.files['participant_file']
        if file.filename == '':
            flash('No selected file.', 'error')
            return redirect(request.url)

        try:
            if file.filename.endswith('.csv'):
                participants_data = parse_csv_file(file)
            elif file.filename.endswith(('.xls', '.xlsx')):
                participants_data = parse_excel_file(file)
            else:
                flash('Invalid file type. Please upload CSV or Excel.', 'error')
                return redirect(request.url)

            if not participants_data:
                flash('No participants found in the file.', 'error')
                return redirect(request.url)

            job_id = Job.create(event_id)
            
            participants_to_insert = [
                {"job_id": job_id, "name": p['name'], "email": p['email']}
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

            flash('Job created successfully! Certificates are being generated.', 'success')
            return redirect(url_for('jobs.view_job', job_id=job_id))

        except Exception as e:
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
