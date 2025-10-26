"""Database models for the certificate generator application."""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Event(db.Model):
    """Event model for managing different events."""
    __tablename__ = 'events'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    template_path = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    jobs = db.relationship('Job', backref='event', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Event {self.name}>'
    
    def to_dict(self):
        """Convert event to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'template_path': self.template_path,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Job(db.Model):
    """Job model for tracking certificate generation jobs."""
    __tablename__ = 'jobs'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    status = db.Column(db.String(50), default='pending')  # pending, processing, completed, failed
    total_certificates = db.Column(db.Integer, default=0)
    generated_certificates = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    telegram_chat_id = db.Column(db.String(100))
    error_message = db.Column(db.Text)
    
    # Relationships
    participants = db.relationship('Participant', backref='job', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Job {self.id} - {self.status}>'
    
    def to_dict(self):
        """Convert job to dictionary."""
        return {
            'id': self.id,
            'event_id': self.event_id,
            'status': self.status,
            'total_certificates': self.total_certificates,
            'generated_certificates': self.generated_certificates,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message
        }


class Participant(db.Model):
    """Participant model for storing participant information."""
    __tablename__ = 'participants'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    certificate_path = db.Column(db.String(500))
    email_sent = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Participant {self.name}>'
    
    def to_dict(self):
        """Convert participant to dictionary."""
        return {
            'id': self.id,
            'job_id': self.job_id,
            'name': self.name,
            'email': self.email,
            'certificate_path': self.certificate_path,
            'email_sent': self.email_sent,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
