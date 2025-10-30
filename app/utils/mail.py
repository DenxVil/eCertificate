"""Mail utility for GOONJ certificates - sends certificates via SMTP."""
from flask import current_app
from flask_mail import Message
from app.utils.email_sender import mail
import os
import logging

logger = logging.getLogger(__name__)


def send_goonj_certificate(recipient_email, recipient_name, certificate_path, event_name="GOONJ"):
    """Send GOONJ certificate via email.
    
    Args:
        recipient_email: Email address of the recipient
        recipient_name: Name of the recipient
        certificate_path: Path to the certificate file
        event_name: Name of the event (default: "GOONJ")
    
    Returns:
        True if email sent successfully, False otherwise
    """
    if not recipient_email:
        logger.info("No email address provided, skipping email send")
        return False
    
    # Check if SMTP is configured
    if not current_app.config.get('MAIL_USERNAME'):
        logger.warning("SMTP not configured, skipping email send")
        return False
    
    subject = f"Your GOONJ Certificate - {event_name}"
    
    body = f"""Dear {recipient_name},

Congratulations! 🎉

We are delighted to present you with your certificate of participation for {event_name}.

Your certificate is attached to this email. We appreciate your participation and hope you had a great experience!

Best regards,
AMA Certificate Team
"""
    
    try:
        msg = Message(
            subject=subject,
            recipients=[recipient_email],
            body=body
        )
        
        # Attach certificate if it exists
        if os.path.exists(certificate_path):
            with open(certificate_path, 'rb') as cert_file:
                msg.attach(
                    filename=os.path.basename(certificate_path),
                    content_type='image/png',
                    data=cert_file.read()
                )
        else:
            logger.error(f"Certificate file not found: {certificate_path}")
            return False
        
        mail.send(msg)
        logger.info(f"Certificate email sent successfully to {recipient_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send certificate email to {recipient_email}: {str(e)}")
        return False
