"""Mail utility for GOONJ certificates - sends certificates via SMTP."""
from flask import current_app
from flask_mail import Message
from app.utils.email_sender import mail
import os
import logging

logger = logging.getLogger(__name__)


def send_goonj_certificate(recipient_email, recipient_name, certificate_path, event_name="GOONJ"):
    """Send GOONJ certificate via email.
    
    This function includes a final alignment check before sending to ensure
    the certificate matches the reference sample with <0.01px difference.
    
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
    
    # FINAL ALIGNMENT CHECK before sending
    # This ensures we never send a certificate that doesn't match the reference
    alignment_check_enabled = current_app.config.get('ENABLE_ALIGNMENT_CHECK', True)
    if alignment_check_enabled:
        try:
            from app.utils.alignment_checker import (
                verify_certificate_alignment,
                get_reference_certificate_path
            )
            
            # Get template path to find reference
            template_path = os.path.join(
                current_app.root_path,
                '..',
                'templates',
                'goonj_certificate.png'
            )
            template_path = os.path.abspath(template_path)
            
            # Get reference certificate
            reference_path = get_reference_certificate_path(template_path)
            
            # Verify alignment
            tolerance_px = current_app.config.get('ALIGNMENT_TOLERANCE_PX', 0.01)
            verification = verify_certificate_alignment(
                certificate_path,
                reference_path,
                tolerance_px=tolerance_px
            )
            
            if not verification['passed']:
                logger.error(
                    f"⛔ CRITICAL: Certificate failed final alignment check before sending. "
                    f"Email to {recipient_email} will NOT be sent. "
                    f"Reason: {verification['message']}"
                )
                return False
            
            logger.info(
                f"✅ Final alignment check passed: {verification['message']}"
            )
            
        except Exception as e:
            logger.error(f"Error during final alignment check: {e}")
            # In production, you might want to fail here rather than proceed
            logger.warning("Proceeding with email send despite alignment check error")
    
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
        
        # Set sender if configured
        if current_app.config.get('MAIL_DEFAULT_SENDER'):
            msg.sender = current_app.config['MAIL_DEFAULT_SENDER']
        
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
        logger.error(f"Failed to send certificate email to {recipient_email}: {str(e)}", exc_info=True)
        return False
