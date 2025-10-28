"""MongoDB-based models for the certificate generator application."""
from datetime import datetime
from app import mongo
from bson.objectid import ObjectId

class Event:
    """Event model for managing different events."""
    
    @staticmethod
    def find_all():
        return list(mongo.db.events.find())

    @staticmethod
    def find_by_id(event_id):
        return mongo.db.events.find_one({"_id": ObjectId(event_id)})

    @staticmethod
    def create(name, description, template_path):
        event_data = {
            "name": name,
            "description": description,
            "template_path": template_path,
            "created_at": datetime.utcnow()
        }
        return mongo.db.events.insert_one(event_data).inserted_id

    @staticmethod
    def update(event_id, name, description, template_path):
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
        # Also delete associated jobs and participants
        jobs = list(mongo.db.jobs.find({"event_id": ObjectId(event_id)}))
        for job in jobs:
            Job.delete(job["_id"])
        mongo.db.events.delete_one({"_id": ObjectId(event_id)})


class Job:
    """Job model for tracking certificate generation jobs."""

    @staticmethod
    def find_by_id(job_id):
        return mongo.db.jobs.find_one({"_id": ObjectId(job_id)})

    @staticmethod
    def create(event_id, telegram_chat_id=None):
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
        update = {"status": status}
        if error_message:
            update["error_message"] = error_message
        if status in ["completed", "failed"]:
            update["completed_at"] = datetime.utcnow()
        mongo.db.jobs.update_one({"_id": ObjectId(job_id)}, {"$set": update})

    @staticmethod
    def increment_generated(job_id):
        mongo.db.jobs.update_one({"_id": ObjectId(job_id)}, {"$inc": {"generated_certificates": 1}})

    @staticmethod
    def set_total(job_id, total):
        mongo.db.jobs.update_one({"_id": ObjectId(job_id)}, {"$set": {"total_certificates": total}})

    @staticmethod
    def delete(job_id):
        Participant.delete_by_job(job_id)
        mongo.db.jobs.delete_one({"_id": ObjectId(job_id)})


class Participant:
    """Participant model for storing participant information."""

    @staticmethod
    def find_by_job(job_id):
        return list(mongo.db.participants.find({"job_id": ObjectId(job_id)}))

    @staticmethod
    def create_many(participants_data):
        mongo.db.participants.insert_many(participants_data)

    @staticmethod
    def update_certificate(participant_id, certificate_path, email_sent):
        mongo.db.participants.update_one(
            {"_id": ObjectId(participant_id)},
            {"$set": {
                "certificate_path": certificate_path,
                "email_sent": email_sent
            }}
        )

    @staticmethod
    def delete_by_job(job_id):
        mongo.db.participants.delete_many({"job_id": ObjectId(job_id)})
