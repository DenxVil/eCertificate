"""Job management routes."""
from flask import Blueprint, render_template, request, jsonify, current_app, redirect, url_for, flash
from app.models import db, Event, Job, Participant
from app.utils import parse_csv_file, parse_excel_file, save_uploaded_file
from app.utils.certificate_generator import CertificateGenerator
from app.utils.email_sender import send_certificate_email
from datetime import datetime
import os
import threading

jobs_bp = Blueprint('jobs', __name__)


def process_job(app, job_id):
    """Process a certificate generation job in background.
    
    Args:
        app: Flask application instance
        job_id: ID of the job to process
    """
    with app.app_context():
        job = Job.query.get(job_id)
        if not job:
            return
        
        try:
            # Update job status
            job.status = 'processing'
            db.session.commit()
            
            # Get event and participants
            event = Event.query.get(job.event_id)
            participants = Participant.query.filter_by(job_id=job.id).all()
            
            if not event.template_path or not os.path.exists(event.template_path):
                raise ValueError("Event template not found")
            
            # Initialize certificate generator
            generator = CertificateGenerator(
                template_path=event.template_path,
                output_folder=current_app.config['OUTPUT_FOLDER']
            )
            
            # Generate and send certificates
            for participant in participants:
                try:
                    # Generate certificate
                    cert_path = generator.generate_certificate(
                        participant_name=participant.name,
                        event_name=event.name
                    )
                    
                    participant.certificate_path = cert_path
                    
                    # Send email
                    email_sent = send_certificate_email(
                        recipient_email=participant.email,
                        recipient_name=participant.name,
                        event_name=event.name,
                        certificate_path=cert_path
                    )
                    
                    participant.email_sent = email_sent
                    job.generated_certificates += 1
                    db.session.commit()
                    
                except Exception as e:
                    print(f"Error processing participant {participant.name}: {str(e)}")
            
            # Update job status
            job.status = 'completed'
            job.completed_at = datetime.utcnow()
            db.session.commit()
            
        except Exception as e:
            job.status = 'failed'
            job.error_message = str(e)
            db.session.commit()


@jobs_bp.route('/')
def list_jobs():
    """List all jobs."""
    jobs = Job.query.order_by(Job.created_at.desc()).all()
    return render_template('jobs/list.html', jobs=jobs)


@jobs_bp.route('/create', methods=['GET', 'POST'])
def create_job():
    """Create a new certificate generation job."""
    if request.method == 'POST':
        event_id = request.form.get('event_id')
        
        if not event_id:
            flash('Please select an event', 'error')
            return redirect(url_for('jobs.create_job'))
        
        event = Event.query.get(event_id)
        if not event:
            flash('Event not found', 'error')
            return redirect(url_for('jobs.create_job'))
        
        # Create job
        job = Job(event_id=event_id)
        db.session.add(job)
        db.session.commit()
        
        # Handle participant data
        participants = []
        
        # Single participant entry
        if request.form.get('single_name') and request.form.get('single_email'):
            participants.append({
                'name': request.form.get('single_name'),
                'email': request.form.get('single_email')
            })
        
        # Bulk upload
        if 'participants_file' in request.files:
            file = request.files['participants_file']
            if file and file.filename:
                filepath = save_uploaded_file(file, current_app.config['UPLOAD_FOLDER'])
                
                try:
                    if file.filename.endswith('.csv'):
                        participants.extend(parse_csv_file(filepath))
                    elif file.filename.endswith(('.xlsx', '.xls')):
                        participants.extend(parse_excel_file(filepath))
                    
                    # Clean up uploaded file
                    os.remove(filepath)
                    
                except Exception as e:
                    flash(f'Error parsing file: {str(e)}', 'error')
                    db.session.delete(job)
                    db.session.commit()
                    return redirect(url_for('jobs.create_job'))
        
        if not participants:
            flash('Please provide at least one participant', 'error')
            db.session.delete(job)
            db.session.commit()
            return redirect(url_for('jobs.create_job'))
        
        # Add participants to job
        for p_data in participants:
            participant = Participant(
                job_id=job.id,
                name=p_data['name'],
                email=p_data['email']
            )
            db.session.add(participant)
        
        job.total_certificates = len(participants)
        db.session.commit()
        
        # Start background processing
        thread = threading.Thread(
            target=process_job,
            args=(current_app._get_current_object(), job.id)
        )
        thread.daemon = True
        thread.start()
        
        flash(f'Job created successfully! Processing {len(participants)} certificates.', 'success')
        return redirect(url_for('jobs.view_job', job_id=job.id))
    
    # GET request - show form
    events = Event.query.all()
    return render_template('jobs/create.html', events=events)


@jobs_bp.route('/<int:job_id>')
def view_job(job_id):
    """View job details."""
    job = Job.query.get_or_404(job_id)
    participants = Participant.query.filter_by(job_id=job.id).all()
    return render_template('jobs/view.html', job=job, participants=participants)


# API endpoints
@jobs_bp.route('/api/<int:job_id>', methods=['GET'])
def api_get_job(job_id):
    """API endpoint to get job status."""
    job = Job.query.get_or_404(job_id)
    return jsonify(job.to_dict())


@jobs_bp.route('/api', methods=['GET'])
def api_list_jobs():
    """API endpoint to list all jobs."""
    jobs = Job.query.all()
    return jsonify([job.to_dict() for job in jobs])
