"""
Integration guide for the new Certificate Generator v2.0

This document explains how to use the new professional certificate generator
and how it maintains backward compatibility with existing code.
"""

# =============================================================================
# BASIC USAGE
# =============================================================================

from app.utils.certificate_generator_v2 import (
    CertificateGenerator,
    CertificateTemplate,
    TextElement,
    CertificateFormat,
    TextAlignment,
)

# Option 1: Use built-in default template
template = CertificateGenerator.create_default_template()
generator = CertificateGenerator(
    template,
    output_folder='generated_certificates',
    default_format=CertificateFormat.PDF
)

# Generate a single certificate
fields = {
    'participant_name': 'John Doe',
    'event_name': 'Python Summit 2025',
    'date': '2025-10-29',
}
pdf_path = generator.generate(fields)
print(f"Certificate generated: {pdf_path}")

# =============================================================================
# USING JSON TEMPLATE
# =============================================================================

# Load from template file
generator = CertificateGenerator(
    'templates/certificate_template_professional.json',
    output_folder='generated_certificates',
    default_format=CertificateFormat.PDF
)

cert_path = generator.generate(fields)

# =============================================================================
# GENERATING BOTH PDF AND PNG
# =============================================================================

generator = CertificateGenerator(
    template,
    default_format=CertificateFormat.BOTH
)

pdf_path, png_path = generator.generate(fields)
print(f"PDF: {pdf_path}")
print(f"PNG: {png_path}")

# =============================================================================
# BATCH PROCESSING WITH PROGRESS TRACKING
# =============================================================================

def progress_callback(current, total):
    percent = (current / total) * 100
    print(f"Generated {current}/{total} certificates ({percent:.1f}%)")

participants = [
    {'participant_name': 'Alice', 'event_name': 'AI Workshop', 'date': '2025-10-29'},
    {'participant_name': 'Bob', 'event_name': 'AI Workshop', 'date': '2025-10-29'},
    {'participant_name': 'Charlie', 'event_name': 'AI Workshop', 'date': '2025-10-29'},
]

paths = generator.batch_generate(
    participants,
    on_progress=progress_callback,
    include_qr_codes=True
)

# =============================================================================
# ADDING QR CODE TO CERTIFICATES
# =============================================================================

# Generate PDF with verification QR code
pdf_path = generator.generate_pdf(
    fields=fields,
    include_qr_code=True,
    qr_data="https://verify.example.com/cert/12345"
)

# =============================================================================
# CREATING CUSTOM TEMPLATE PROGRAMMATICALLY
# =============================================================================

from datetime import datetime

custom_template = CertificateTemplate(
    name="Custom Event Certificate",
    description="Certificate for special events",
    width=11.0,
    height=8.5,
    elements=[
        TextElement(
            text="🎓 Certificate of Completion",
            x=5.5,
            y=1.0,
            font_size=48,
            bold=True,
            color="#007ACC",
            alignment=TextAlignment.CENTER
        ),
        TextElement(
            text="This certificate is awarded to",
            x=5.5,
            y=2.5,
            font_size=18,
            alignment=TextAlignment.CENTER
        ),
        TextElement(
            text="{{participant_name}}",
            x=5.5,
            y=3.3,
            font_size=40,
            bold=True,
            color="#007ACC",
            alignment=TextAlignment.CENTER
        ),
        TextElement(
            text="for completing",
            x=5.5,
            y=4.2,
            font_size=16,
            alignment=TextAlignment.CENTER
        ),
        TextElement(
            text="{{event_name}}",
            x=5.5,
            y=4.8,
            font_size=32,
            bold=True,
            alignment=TextAlignment.CENTER
        ),
        TextElement(
            text="Date: {{date}}",
            x=1.0,
            y=7.0,
            font_size=12,
            alignment=TextAlignment.LEFT
        ),
    ]
)

generator = CertificateGenerator(custom_template)
cert_path = generator.generate(fields)

# Save the template for reuse
generator.save_template('custom_template.json')

# =============================================================================
# BACKWARD COMPATIBILITY - USING LEGACY IMAGE TEMPLATE
# =============================================================================

from app.utils.certificate_generator_v2 import CertificateGeneratorCompat

# This still works with old image-based templates
legacy_gen = CertificateGeneratorCompat(
    template_path='path/to/certificate_template.png',
    output_folder='generated_certificates'
)

# Generates PNG (backward compatible)
png_path = legacy_gen.generate_certificate(
    participant_name='John Doe',
    event_name='Python Summit 2025'
)

# =============================================================================
# INTEGRATION WITH MONGODB/JOBS
# =============================================================================

# In jobs.py:
from app.utils.certificate_generator_v2 import CertificateGenerator, CertificateFormat

def process_job(app, job_id, customization_json=None):
    """Process a certificate generation job in background."""
    with app.app_context():
        job = Job.find_by_id(job_id)
        event = Event.find_by_id(job['event_id'])
        participants = Participant.find_by_job(job_id)
        
        # Load template
        template_path = event.get('template_path', 'templates/certificate_template_professional.json')
        
        generator = CertificateGenerator(
            template_path,
            output_folder=app.config['OUTPUT_FOLDER'],
            default_format=CertificateFormat.PDF  # Or PNG or BOTH
        )
        
        # Generate certificates in batch
        def progress(current, total):
            Job.update_progress(job_id, current, total)
        
        participant_data = [
            {
                'participant_name': p['name'],
                'event_name': event['name'],
                'date': datetime.now().strftime("%B %d, %Y"),
                'certificate_id': str(p['_id']),
            }
            for p in participants
        ]
        
        try:
            cert_paths = generator.batch_generate(
                participant_data,
                on_progress=progress,
                include_qr_codes=True,
            )
            
            Job.update_status(job_id, 'completed')
        except Exception as e:
            Job.update_status(job_id, 'failed', error_message=str(e))

# =============================================================================
# OUTPUT FORMATS SUPPORTED
# =============================================================================

# PDF: High-quality, professional, includes support for QR codes and complex layouts
# PNG: Legacy support, good for web display, fast generation
# BOTH: Generate both PDF and PNG in one call

# =============================================================================
# FEATURES
# =============================================================================

# ✓ Professional PDF generation with ReportLab
# ✓ PNG output for backward compatibility
# ✓ Template system (JSON-based) for easy customization
# ✓ QR code generation and embedding
# ✓ Font support: Helvetica, Times, Courier (more fonts can be added)
# ✓ Text alignment: left, center, right
# ✓ Text styling: bold, italic, colors
# ✓ Batch processing with progress tracking
# ✓ Field variable substitution: {{participant_name}}, {{event_name}}, etc.
# ✓ Responsive sizing: works with different paper sizes
# ✓ Image overlays and backgrounds

# =============================================================================
# MIGRATION PATH
# =============================================================================

# Old code:
# generator = CertificateGenerator('path/to/template.png')
# cert_path = generator.generate_certificate('John Doe', 'Event')

# Works as-is with backward compatibility wrapper!
# Or migrate to new code:
# generator = CertificateGenerator('templates/certificate_template_professional.json')
# cert_path = generator.generate({'participant_name': 'John Doe', 'event_name': 'Event'})

print("✓ Certificate Generator v2.0 loaded and ready!")
