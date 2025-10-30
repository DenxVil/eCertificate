"""MongoDB-based models for the certificate generator application."""
from datetime import datetime
from app import mongo
from bson.objectid import ObjectId
from pymongo.errors import ServerSelectionTimeoutError, AutoReconnect
import logging

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


class Event:
    """Event model for managing different events."""
    
    @staticmethod
    def find_all():
        _check_db_connection()
        try:
            return list(mongo.db.events.find())
        except (ServerSelectionTimeoutError, AutoReconnect) as e:
            # Raise a clearer error for the caller and log the underlying exception
            raise RuntimeError(
                "Database is unreachable. Check MONGO_URI and ensure MongoDB is running. "
                f"Original error: {e}"
            )

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
        # Also delete associated jobs and participants
        jobs = list(mongo.db.jobs.find({"event_id": ObjectId(event_id)}))
        for job in jobs:
            Job.delete(job["_id"])
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
