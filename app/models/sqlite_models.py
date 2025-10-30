"""SQLite database models using SQLAlchemy."""
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Event(db.Model):
    """Event model for managing different events."""
    __tablename__ = 'events'
    __table_args__ = (
        db.Index('idx_event_created_at', 'created_at'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    description = db.Column(db.Text)
    template_path = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to jobs
    jobs = db.relationship('Job', backref='event', lazy=True, cascade='all, delete-orphan')
    
    @staticmethod
    def find_all():
        """Get all events."""
        try:
            return Event.query.all()
        except Exception as e:
            raise RuntimeError(
                f"Database is unreachable. Check database connection. Original error: {e}"
            )
    
    @staticmethod
    def find_by_id(event_id):
        """Find event by ID."""
        return Event.query.get(event_id)
    
    @staticmethod
    def create(name, description, template_path):
        """Create a new event."""
        event = Event(
            name=name,
            description=description,
            template_path=template_path
        )
        db.session.add(event)
        db.session.commit()
        return event.id
    
    @staticmethod
    def update(event_id, name, description, template_path):
        """Update an existing event."""
        event = Event.query.get(event_id)
        if event:
            event.name = name
            event.description = description
            event.template_path = template_path
            db.session.commit()
    
    @staticmethod
    def delete(event_id):
        """Delete an event and its associated jobs."""
        event = Event.query.get(event_id)
        if event:
            db.session.delete(event)
            db.session.commit()


class Job(db.Model):
    """Job model for tracking certificate generation jobs."""
    __tablename__ = 'jobs'
    __table_args__ = (
        db.Index('idx_job_event_id', 'event_id'),
        db.Index('idx_job_status', 'status'),
        db.Index('idx_job_created_at', 'created_at'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    status = db.Column(db.String(50), default='pending', index=True)
    total_certificates = db.Column(db.Integer, default=0)
    generated_certificates = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    telegram_chat_id = db.Column(db.String(100))
    error_message = db.Column(db.Text)
    
    # Relationship to participants
    participants = db.relationship('Participant', backref='job', lazy=True, cascade='all, delete-orphan')
    
    @staticmethod
    def find_by_id(job_id):
        """Find job by ID."""
        return Job.query.get(job_id)
    
    @staticmethod
    def create(event_id, telegram_chat_id=None):
        """Create a new job."""
        job = Job(
            event_id=event_id,
            telegram_chat_id=telegram_chat_id
        )
        db.session.add(job)
        db.session.commit()
        return job.id
    
    @staticmethod
    def update_status(job_id, status, error_message=None):
        """Update job status."""
        job = Job.query.get(job_id)
        if job:
            job.status = status
            if error_message:
                job.error_message = error_message
            if status in ["completed", "failed"]:
                job.completed_at = datetime.utcnow()
            db.session.commit()
    
    @staticmethod
    def increment_generated(job_id):
        """Increment generated certificates count."""
        job = Job.query.get(job_id)
        if job:
            job.generated_certificates += 1
            db.session.commit()
    
    @staticmethod
    def set_total(job_id, total):
        """Set total certificates count."""
        job = Job.query.get(job_id)
        if job:
            job.total_certificates = total
            db.session.commit()
    
    @staticmethod
    def delete(job_id):
        """Delete a job and its participants."""
        job = Job.query.get(job_id)
        if job:
            db.session.delete(job)
            db.session.commit()


class Participant(db.Model):
    """Participant model for storing participant information."""
    __tablename__ = 'participants'
    __table_args__ = (
        db.Index('idx_participant_job_id', 'job_id'),
        db.Index('idx_participant_email', 'email'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    certificate_path = db.Column(db.String(500))
    email_sent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @staticmethod
    def find_by_job(job_id):
        """Find all participants for a job."""
        return Participant.query.filter_by(job_id=job_id).all()
    
    @staticmethod
    def create_many(participants_data):
        """Create multiple participants."""
        participants = [Participant(**data) for data in participants_data]
        db.session.add_all(participants)
        db.session.commit()
    
    @staticmethod
    def update_certificate(participant_id, certificate_path, email_sent):
        """Update participant certificate information."""
        participant = Participant.query.get(participant_id)
        if participant:
            participant.certificate_path = certificate_path
            participant.email_sent = email_sent
            db.session.commit()
    
    @staticmethod
    def delete_by_job(job_id):
        """Delete all participants for a job."""
        Participant.query.filter_by(job_id=job_id).delete()
        db.session.commit()
