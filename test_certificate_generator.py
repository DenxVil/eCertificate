#!/usr/bin/env python
"""
Demo script for Certificate Generator v2.0

This script demonstrates all features of the new professional certificate generator.
Run this to generate sample certificates in multiple formats with various features.
"""

import sys
import os
from datetime import datetime

# Add app to path
sys.path.insert(0, os.path.dirname(__file__))

from app.utils.certificate_generator_v2 import (
    CertificateGenerator,
    CertificateFormat,
)


def demo_basic_pdf():
    """Demo: Generate basic PDF certificate."""
    print("\n" + "="*60)
    print("DEMO 1: Basic PDF Generation")
    print("="*60)
    
    # Create default template
    template = CertificateGenerator.create_default_template()
    
    # Initialize generator
    generator = CertificateGenerator(
        template,
        output_folder='generated_certificates',
        default_format=CertificateFormat.PDF
    )
    
    # Generate certificate
    fields = {
        'participant_name': 'Alice Johnson',
        'event_name': 'Professional Python Masterclass 2025',
        'date': datetime.now().strftime("%B %d, %Y"),
    }
    
    pdf_path = generator.generate_pdf(fields)
    print(f"✓ Generated: {pdf_path}")
    return pdf_path


def demo_png_backward_compat():
    """Demo: Generate PNG (backward compatible)."""
    print("\n" + "="*60)
    print("DEMO 2: PNG Generation (Backward Compatible)")
    print("="*60)
    
    template = CertificateGenerator.create_default_template()
    generator = CertificateGenerator(
        template,
        output_folder='generated_certificates',
        default_format=CertificateFormat.PNG
    )
    
    fields = {
        'participant_name': 'Bob Smith',
        'event_name': 'Advanced AI Workshop',
        'date': datetime.now().strftime("%B %d, %Y"),
    }
    
    png_path = generator.generate_png(fields)
    print(f"✓ Generated: {png_path}")
    return png_path


def demo_both_formats():
    """Demo: Generate both PDF and PNG."""
    print("\n" + "="*60)
    print("DEMO 3: Dual Format Generation (PDF + PNG)")
    print("="*60)
    
    template = CertificateGenerator.create_default_template()
    generator = CertificateGenerator(
        template,
        output_folder='generated_certificates',
        default_format=CertificateFormat.BOTH
    )
    
    fields = {
        'participant_name': 'Charlie Brown',
        'event_name': 'Machine Learning Fundamentals',
        'date': datetime.now().strftime("%B %d, %Y"),
    }
    
    pdf_path, png_path = generator.generate(fields)
    print(f"✓ Generated PDF: {pdf_path}")
    print(f"✓ Generated PNG: {png_path}")
    return (pdf_path, png_path)


def demo_with_qr_code():
    """Demo: Generate PDF with QR code."""
    print("\n" + "="*60)
    print("DEMO 4: PDF with QR Code Verification")
    print("="*60)
    
    template = CertificateGenerator.create_default_template()
    generator = CertificateGenerator(
        template,
        output_folder='generated_certificates',
        default_format=CertificateFormat.PDF
    )
    
    fields = {
        'participant_name': 'Diana Prince',
        'event_name': 'Cybersecurity Essentials',
        'date': datetime.now().strftime("%B %d, %Y"),
    }
    
    pdf_path = generator.generate_pdf(
        fields,
        include_qr_code=True,
        qr_data="https://verify.certificates.example.com/verify?cert=CERT_001"
    )
    print(f"✓ Generated with QR code: {pdf_path}")
    print(f"  QR Data: https://verify.certificates.example.com/verify?cert=CERT_001")
    return pdf_path


def demo_batch_processing():
    """Demo: Batch generation with progress tracking."""
    print("\n" + "="*60)
    print("DEMO 5: Batch Processing Multiple Participants")
    print("="*60)
    
    template = CertificateGenerator.create_default_template()
    generator = CertificateGenerator(
        template,
        output_folder='generated_certificates',
        default_format=CertificateFormat.PDF
    )
    
    # Sample participants
    participants = [
        {'participant_name': 'Eve Wilson', 'event_name': 'Cloud Architecture 2025', 'date': datetime.now().strftime("%B %d, %Y")},
        {'participant_name': 'Frank Miller', 'event_name': 'Cloud Architecture 2025', 'date': datetime.now().strftime("%B %d, %Y")},
        {'participant_name': 'Grace Lee', 'event_name': 'Cloud Architecture 2025', 'date': datetime.now().strftime("%B %d, %Y")},
        {'participant_name': 'Henry Taylor', 'event_name': 'Cloud Architecture 2025', 'date': datetime.now().strftime("%B %d, %Y")},
        {'participant_name': 'Iris Martinez', 'event_name': 'Cloud Architecture 2025', 'date': datetime.now().strftime("%B %d, %Y")},
    ]
    
    def progress_callback(current, total):
        percent = (current / total) * 100
        bar_length = 30
        filled = int(bar_length * current // total)
        bar = '█' * filled + '░' * (bar_length - filled)
        print(f"  [{bar}] {current}/{total} ({percent:.1f}%)", end='\r')
    
    print(f"Generating {len(participants)} certificates...")
    paths = generator.batch_generate(
        participants,
        on_progress=progress_callback,
        include_qr_codes=False
    )
    print(f"\n✓ Generated {len(paths)} certificates successfully!")
    for i, path in enumerate(paths, 1):
        print(f"  {i}. {os.path.basename(path)}")
    return paths


def demo_custom_template():
    """Demo: Create and use a custom template."""
    print("\n" + "="*60)
    print("DEMO 6: Custom Template Creation")
    print("="*60)
    
    from app.utils.certificate_generator_v2 import (
        CertificateTemplate,
        TextElement,
        TextAlignment,
    )
    
    # Create custom template
    custom_template = CertificateTemplate(
        name="Executive Excellence Award",
        description="Premium certificate for executive achievements",
        width=11.0,
        height=8.5,
        elements=[
            TextElement(
                text="🏆 EXECUTIVE EXCELLENCE AWARD 🏆",
                x=5.5,
                y=0.8,
                font_size=40,
                bold=True,
                color="#FF6B00",
                alignment=TextAlignment.CENTER
            ),
            TextElement(
                text="PRESENTED TO",
                x=5.5,
                y=2.2,
                font_size=18,
                color="#333333",
                alignment=TextAlignment.CENTER
            ),
            TextElement(
                text="{{participant_name}}",
                x=5.5,
                y=3.0,
                font_size=44,
                bold=True,
                color="#003366",
                alignment=TextAlignment.CENTER
            ),
            TextElement(
                text="In recognition of outstanding leadership and innovation",
                x=5.5,
                y=3.9,
                font_size=14,
                color="#555555",
                alignment=TextAlignment.CENTER
            ),
            TextElement(
                text="{{event_name}}",
                x=5.5,
                y=4.6,
                font_size=28,
                bold=True,
                color="#FF6B00",
                alignment=TextAlignment.CENTER
            ),
            TextElement(
                text="Presented on {{date}}",
                x=5.5,
                y=6.2,
                font_size=12,
                color="#666666",
                alignment=TextAlignment.CENTER
            ),
        ]
    )
    
    # Generate with custom template
    generator = CertificateGenerator(
        custom_template,
        output_folder='generated_certificates'
    )
    
    fields = {
        'participant_name': 'Janet Roberts',
        'event_name': '2025 Leadership Summit',
        'date': datetime.now().strftime("%B %d, %Y"),
    }
    
    pdf_path = generator.generate_pdf(fields)
    print(f"✓ Generated custom certificate: {pdf_path}")
    
    # Save template for reuse
    template_path = 'templates/executive_award_template.json'
    os.makedirs(os.path.dirname(template_path), exist_ok=True)
    generator.save_template(template_path)
    print(f"✓ Saved template: {template_path}")
    
    return pdf_path


def main():
    """Run all demos."""
    print("\n" + "="*60)
    print("CERTIFICATE GENERATOR v2.0 - FEATURE SHOWCASE")
    print("="*60)
    print("Demonstrating all features of the new professional certificate generator")
    print(f"Output folder: generated_certificates/")
    print()
    
    try:
        # Run demos
        demo_basic_pdf()
        demo_png_backward_compat()
        demo_both_formats()
        demo_with_qr_code()
        demo_batch_processing()
        demo_custom_template()
        
        print("\n" + "="*60)
        print("✓ ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\nGenerated files are in: generated_certificates/")
        print("\nFeatures demonstrated:")
        print("  ✓ Basic PDF generation")
        print("  ✓ PNG backward compatibility")
        print("  ✓ Dual format output")
        print("  ✓ QR code embedding")
        print("  ✓ Batch processing with progress tracking")
        print("  ✓ Custom template creation")
        print("\n" + "="*60)
        
    except Exception as e:
        print(f"\n✗ Error during demo: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
