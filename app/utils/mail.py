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
        # Validate certificate path exists and is a file (security check)
        cert_path_abs = os.path.abspath(certificate_path)
        if not os.path.exists(cert_path_abs) or not os.path.isfile(cert_path_abs):
            logger.error(f"Certificate file not found or not a file: {cert_path_abs}")
            return False
        
        # Additional security: ensure it's within the expected output folder
        output_folder = current_app.config.get('OUTPUT_FOLDER', 'generated_certificates')
        output_folder_abs = os.path.abspath(output_folder)
        if not cert_path_abs.startswith(output_folder_abs):
            logger.error(f"Certificate path {cert_path_abs} is outside output folder {output_folder_abs}")
            return False
        
        msg = Message(
            subject=subject,
            recipients=[recipient_email],
            body=body
        )
        
        # Attach certificate
        with open(cert_path_abs, 'rb') as cert_file:
            msg.attach(
                filename=os.path.basename(cert_path_abs),
                content_type='image/png',
                data=cert_file.read()
            )
        
        mail.send(msg)
        logger.info(f"Certificate email sent successfully to {recipient_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send certificate email to {recipient_email}: {str(e)}")
        return False
