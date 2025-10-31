"""Email utility for sending certificates."""
from flask_mail import Mail, Message
from flask import current_app
import os
import logging
import time

mail = Mail()
logger = logging.getLogger(__name__)


def send_certificate_email(recipient_email, recipient_name, event_name, certificate_path, retries=None):
    """Send certificate via email with retries.

    Returns True if sent, False otherwise. Retries a configured number of times on transient errors.
    
    Args:
        recipient_email: Email address of recipient
        recipient_name: Name of recipient
        event_name: Name of the event
        certificate_path: Path to certificate file
        retries: Number of retry attempts (defaults to EMAIL_MAX_RETRIES from config, or 3)
    """
    # Get retry count from config if not specified
    if retries is None:
        retries = current_app.config.get('EMAIL_MAX_RETRIES', 3)
    
    subject = f"Certificate of Participation - {event_name}"

    body = f"""
Dear {recipient_name},

Congratulations! We are pleased to present you with your Certificate of Participation for {event_name}.

Please find your certificate attached to this email.

Thank you for your participation!

Best regards,
AMA Certificate Generator Team
    """

    for attempt in range(1, retries + 1):
        try:
            msg = Message(
                subject=subject,
                recipients=[recipient_email],
                body=body
            )
            
            # Set sender if configured
            if current_app.config.get('MAIL_DEFAULT_SENDER'):
                msg.sender = current_app.config['MAIL_DEFAULT_SENDER']

            # Attach certificate
            if os.path.exists(certificate_path):
                with open(certificate_path, 'rb') as cert_file:
                    msg.attach(
                        filename=os.path.basename(certificate_path),
                        content_type='image/png',
                        data=cert_file.read()
                    )

            mail.send(msg)
            logger.info(f"Certificate email sent successfully to {recipient_email}")
            return True

        except Exception as e:
            # Log error and retry for transient issues
            logger.warning(f"Attempt {attempt}/{retries} - Error sending email to {recipient_email}: {str(e)}")
            if attempt < retries:
                # exponential backoff
                time.sleep(2 ** attempt)
            else:
                logger.error(f"Failed to send certificate email to {recipient_email} after {retries} attempts")
                return False


def send_bulk_notification(admin_email, job_id, total_sent, total_failed):
    """Send bulk job completion notification.
    
    Args:
        admin_email: Email address of the admin
        job_id: ID of the completed job
        total_sent: Number of certificates sent successfully
        total_failed: Number of failed sends
    """
    try:
        subject = f"Certificate Generation Job #{job_id} Completed"
        
        body = f"""
Certificate generation job #{job_id} has been completed.

Summary:
- Total certificates sent: {total_sent}
- Total failed: {total_failed}

Best regards,
AMA Certificate Generator System
        """
        
        msg = Message(
            subject=subject,
            recipients=[admin_email],
            body=body
        )
        
        # Set sender if configured
        if current_app.config.get('MAIL_DEFAULT_SENDER'):
            msg.sender = current_app.config['MAIL_DEFAULT_SENDER']
        
        mail.send(msg)
        logger.info(f"Bulk notification email sent successfully to {admin_email}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending notification email to {admin_email}: {str(e)}")
        return False
