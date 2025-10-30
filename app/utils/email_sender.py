"""Email utility for sending certificates."""
from flask_mail import Mail, Message
import os

mail = Mail()


def send_certificate_email(recipient_email, recipient_name, event_name, certificate_path, retries=3):
    """Send certificate via email with retries.

    Returns True if sent, False otherwise. Retries a few times on transient errors.
    """
    import time
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

            # Attach certificate
            if os.path.exists(certificate_path):
                with open(certificate_path, 'rb') as cert_file:
                    msg.attach(
                        filename=os.path.basename(certificate_path),
                        content_type='image/png',
                        data=cert_file.read()
                    )

            mail.send(msg)
            return True

        except Exception as e:
            # Print error and retry for transient issues
            print(f"Attempt {attempt} - Error sending email to {recipient_email}: {str(e)}")
            if attempt < retries:
                # exponential backoff
                time.sleep(2 ** attempt)
            else:
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
        
        mail.send(msg)
        return True
        
    except Exception as e:
        print(f"Error sending notification email: {str(e)}")
        return False
