"""MongoDB-based models for the certificate generator application."""
from datetime import datetime
from app import mongo
from bson.objectid import ObjectId
import logging
import os

logger = logging.getLogger(__name__)


def _check_db_connection():
    """Check if MongoDB is available."""
    try:
        if mongo.db is None:
            raise RuntimeError("MongoDB is not initialized")
        return True
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        raise RuntimeError("Database is not available. Please check your MongoDB connection.")


def ensure_indexes():
    """Create database indexes for better query performance.
    
    This should be called once during application initialization.
    """
    try:
        _check_db_connection()
        
        # Events collection indexes
        mongo.db.events.create_index([("created_at", -1)])
        mongo.db.events.create_index([("name", 1)])
        
        # Jobs collection indexes
        mongo.db.jobs.create_index([("event_id", 1)])
        mongo.db.jobs.create_index([("status", 1)])
        mongo.db.jobs.create_index([("created_at", -1)])
        mongo.db.jobs.create_index([("telegram_chat_id", 1)], sparse=True)
        
        # Participants collection indexes
        mongo.db.participants.create_index([("job_id", 1)])
        mongo.db.participants.create_index([("email", 1)])
        
        # Scans collection with TTL index (expires after 1 hour)
        mongo.db.scans.create_index([("created_at", 1)], expireAfterSeconds=3600)
        
        logger.info("Database indexes created successfully")
    except Exception as e:
        logger.warning(f"Failed to create indexes (this may be normal if they already exist): {e}")


class Event:
    """Event model for managing different events."""
    
    @staticmethod
    def find_all(sort_by='created_at', descending=True):
        """Find all events with optional sorting.
        
        Args:
            sort_by: Field to sort by (default: 'created_at')
            descending: Sort in descending order (default: True)
        
        Returns:
            List of event documents
        """
        _check_db_connection()
        sort_direction = -1 if descending else 1
        return list(mongo.db.events.find().sort(sort_by, sort_direction))

    @staticmethod
    def find_by_id(event_id):
        _check_db_connection()
        return mongo.db.events.find_one({"_id": ObjectId(event_id)})

    @staticmethod
    def create(name, description, template_path):
        _check_db_connection()
        event_data = {
            "name": name,
            "description": description,
            "template_path": template_path,
            "created_at": datetime.utcnow()
        }
        return mongo.db.events.insert_one(event_data).inserted_id

    @staticmethod
    def update(event_id, name, description, template_path):
        _check_db_connection()
        mongo.db.events.update_one(
            {"_id": ObjectId(event_id)},
            {"$set": {
                "name": name,
                "description": description,
                "template_path": template_path
            }}
        )

    @staticmethod
    def delete(event_id):
        _check_db_connection()
        # Get event for template file cleanup
        event = mongo.db.events.find_one({"_id": ObjectId(event_id)})
        if not event:
            return
        
        # Delete template file if exists
        if event.get('template_path') and os.path.exists(event['template_path']):
            try:
                os.remove(event['template_path'])
            except OSError as e:
                logger.warning(f"Failed to delete template file {event['template_path']}: {e}")
        
        # Get all job IDs for this event
        job_ids = [job['_id'] for job in mongo.db.jobs.find({"event_id": ObjectId(event_id)}, {"_id": 1})]
        
        # Bulk delete participants for all jobs
        if job_ids:
            mongo.db.participants.delete_many({"job_id": {"$in": job_ids}})
        
        # Bulk delete all jobs for this event
        mongo.db.jobs.delete_many({"event_id": ObjectId(event_id)})
        
        # Delete the event itself
        mongo.db.events.delete_one({"_id": ObjectId(event_id)})


class Job:
    """Job model for tracking certificate generation jobs."""

    @staticmethod
    def find_by_id(job_id):
        _check_db_connection()
        return mongo.db.jobs.find_one({"_id": ObjectId(job_id)})

    @staticmethod
    def create(event_id, telegram_chat_id=None):
        _check_db_connection()
        job_data = {
            "event_id": ObjectId(event_id),
            "status": "pending",
            "total_certificates": 0,
            "generated_certificates": 0,
            "created_at": datetime.utcnow(),
            "completed_at": None,
            "telegram_chat_id": telegram_chat_id,
            "error_message": None
        }
        return mongo.db.jobs.insert_one(job_data).inserted_id

    @staticmethod
    def update_status(job_id, status, error_message=None):
        _check_db_connection()
        update = {"status": status}
        if error_message:
            update["error_message"] = error_message
        if status in ["completed", "failed"]:
            update["completed_at"] = datetime.utcnow()
        mongo.db.jobs.update_one({"_id": ObjectId(job_id)}, {"$set": update})

    @staticmethod
    def increment_generated(job_id):
        _check_db_connection()
        mongo.db.jobs.update_one({"_id": ObjectId(job_id)}, {"$inc": {"generated_certificates": 1}})

    @staticmethod
    def set_total(job_id, total):
        _check_db_connection()
        mongo.db.jobs.update_one({"_id": ObjectId(job_id)}, {"$set": {"total_certificates": total}})

    @staticmethod
    def delete(job_id):
        _check_db_connection()
        Participant.delete_by_job(job_id)
        mongo.db.jobs.delete_one({"_id": ObjectId(job_id)})


class Participant:
    """Participant model for storing participant information."""

    @staticmethod
    def find_by_job(job_id):
        _check_db_connection()
        return list(mongo.db.participants.find({"job_id": ObjectId(job_id)}))

    @staticmethod
    def create_many(participants_data):
        _check_db_connection()
        mongo.db.participants.insert_many(participants_data)

    @staticmethod
    def update_certificate(participant_id, certificate_path, email_sent):
        _check_db_connection()
        mongo.db.participants.update_one(
            {"_id": ObjectId(participant_id)},
            {"$set": {
                "certificate_path": certificate_path,
                "email_sent": email_sent
            }}
        )

    @staticmethod
    def delete_by_job(job_id):
        _check_db_connection()
        mongo.db.participants.delete_many({"job_id": ObjectId(job_id)})


class Scan:
    """Scan model for storing temporary template scan data."""

    @staticmethod
    def create(session_id, analysis_data, template_path):
        """Store scan analysis data.
        
        Args:
            session_id: Unique session identifier
            analysis_data: Serialized analysis data
            template_path: Path to the scanned template
            
        Returns:
            Inserted document ID
        """
        _check_db_connection()
        scan_data = {
            "session_id": session_id,
            "analysis_data": analysis_data,
            "template_path": template_path,
            "created_at": datetime.utcnow()
        }
        return mongo.db.scans.insert_one(scan_data).inserted_id

    @staticmethod
    def find_by_session(session_id):
        """Retrieve scan data by session ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Scan document or None
        """
        _check_db_connection()
        return mongo.db.scans.find_one({"session_id": session_id})

    @staticmethod
    def find_by_template_path(template_path):
        """Retrieve scan data by template path.
        
        Args:
            template_path: Path to template
            
        Returns:
            Scan document or None
        """
        _check_db_connection()
        return mongo.db.scans.find_one({"template_path": template_path})
