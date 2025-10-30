#!/usr/bin/env python
"""
Smart Certificate Scanner & Aligner - Test & Demo Script

This script demonstrates the certificate scanner and aligner functionality.
Run this to see how certificates are scanned, templates are created, 
and aligned certificates are generated.
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from app.utils.certificate_scanner import (
    CertificateScanner,
    SmartCertificateAligner,
    TemplateCreator,
)


def demo_create_sample_certificate():
    """Create a sample certificate for testing."""
    from PIL import Image, ImageDraw, ImageFont
    
    print("\n" + "="*60)
    print("DEMO 0: Creating Sample Certificate for Testing")
    print("="*60)
    
    # Create a sample certificate image
    width, height = 1100, 850
    image = Image.new('RGB', (width, height), color=(240, 245, 250))
    draw = ImageDraw.Draw(image)
    
    # Try to use a nice font, fallback to default
    try:
        title_font = ImageFont.truetype("arial.ttf", 60)
        text_font = ImageFont.truetype("arial.ttf", 40)
        small_font = ImageFont.truetype("arial.ttf", 24)
    except:
        title_font = text_font = small_font = ImageFont.load_default()
    
    # Draw certificate content
    draw.text((width//2, 100), "Certificate of Achievement", 
              font=title_font, fill=(26, 84, 144), anchor="mm")
    
    draw.text((width//2, 250), "This is to certify that", 
              font=small_font, fill=(80, 80, 80), anchor="mm")
    
    draw.text((width//2, 350), "[PARTICIPANT NAME]", 
              font=text_font, fill=(26, 84, 144), anchor="mm")
    
    draw.text((width//2, 450), "has successfully completed", 
              font=small_font, fill=(80, 80, 80), anchor="mm")
    
    draw.text((width//2, 550), "[EVENT NAME]", 
              font=text_font, fill=(26, 84, 144), anchor="mm")
    
    draw.text((width//2, 700), "Date: [DATE]", 
              font=small_font, fill=(120, 120, 120), anchor="mm")
    
    # Save sample certificate
    os.makedirs('test_samples', exist_ok=True)
    sample_path = 'test_samples/sample_certificate.png'
    image.save(sample_path)
    
    print(f"✓ Created sample certificate: {sample_path}")
    print(f"  Size: {width}x{height} pixels")
    print(f"  Fields: Participant Name, Event Name, Date")
    
    return sample_path


def demo_scan_certificate(cert_path):
    """Demo: Scan a certificate template."""
    print("\n" + "="*60)
    print("DEMO 1: Scanning Certificate Template")
    print("="*60)
    
    scanner = CertificateScanner(dpi=300, ocr_lang='eng')
    
    print(f"Scanning: {cert_path}")
    analysis = scanner.scan_certificate(cert_path)
    
    print(f"\n✓ Scan completed successfully!")
    print(f"  Template size: {analysis.width}x{analysis.height} pixels")
    print(f"  Detected fields: {len(analysis.detected_fields)}")
    print(f"  Overall confidence: {analysis.confidence_score:.1%}")
    print(f"  Background color: {analysis.background_color}")
    
    print(f"\nDetected Fields:")
    for i, field in enumerate(analysis.detected_fields, 1):
        print(f"\n  Field {i}:")
        print(f"    Text: '{field.text}'")
        print(f"    Position: ({field.x:.2%}, {field.y:.2%})")
        print(f"    Size: {field.font_size}pt")
        print(f"    Color: {field.color}")
        print(f"    Alignment: {field.alignment}")
        print(f"    Type: {field.field_type}")
        print(f"    Confidence: {field.confidence:.0%}")
    
    return analysis


def demo_create_template(analysis):
    """Demo: Create template from scan."""
    print("\n" + "="*60)
    print("DEMO 2: Creating Template from Scan")
    print("="*60)
    
    creator = TemplateCreator()
    template = creator.create_template_from_scan(
        analysis,
        template_name="Scanned Certificate Template"
    )
    
    print(f"\n✓ Template created successfully!")
    print(f"  Name: {template['name']}")
    print(f"  Size: {template['width']:.1f}\" x {template['height']:.1f}\"")
    print(f"  Elements: {len(template['elements'])}")
    print(f"  Detection confidence: {template['detection_confidence']:.0%}")
    
    # Save template
    template_path = 'test_samples/scanned_template.json'
    creator.save_template_to_file(template, template_path)
    print(f"  Saved to: {template_path}")
    
    print(f"\nTemplate elements:")
    for i, elem in enumerate(template['elements'], 1):
        print(f"  {i}. {elem.get('text', 'N/A')}")
        print(f"     Position: ({elem['x']:.2f}, {elem['y']:.2f})")
        print(f"     Size: {elem['font_size']}pt")
    
    return template


def demo_generate_aligned_certificate(cert_path, analysis):
    """Demo: Generate aligned certificate."""
    print("\n" + "="*60)
    print("DEMO 3: Generating Aligned Certificate")
    print("="*60)
    
    aligner = SmartCertificateAligner(analysis)
    
    # Define field values
    user_fields = {
        'PARTICIPANT NAME': 'Alice Johnson',
        'EVENT NAME': 'Advanced Python Workshop 2025',
        'DATE': datetime.now().strftime("%B %d, %Y"),
    }
    
    print(f"User fields:")
    for key, value in user_fields.items():
        print(f"  {key}: {value}")
    
    # Map fields
    print(f"\nMapping fields to template...")
    mapping = aligner.map_fields(user_fields)
    
    print(f"Field mapping:")
    for detected, replacement in mapping.items():
        print(f"  '{detected}' → '{replacement}'")
    
    # Generate certificate
    output_path = 'generated_certificates/aligned_test_certificate.png'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    print(f"\nGenerating aligned certificate...")
    result_path = aligner.generate_aligned_certificate(
        template_image_path=cert_path,
        fields_data=user_fields,
        output_path=output_path
    )
    
    print(f"✓ Generated: {result_path}")
    
    return result_path


def demo_batch_generation(cert_path, analysis):
    """Demo: Batch generate aligned certificates."""
    print("\n" + "="*60)
    print("DEMO 4: Batch Generating Aligned Certificates")
    print("="*60)
    
    aligner = SmartCertificateAligner(analysis)
    
    # Sample batch of participants
    participants = [
        {'PARTICIPANT NAME': 'Bob Smith', 'EVENT NAME': 'Python Workshop', 'DATE': '2025-10-29'},
        {'PARTICIPANT NAME': 'Carol Davis', 'EVENT NAME': 'Python Workshop', 'DATE': '2025-10-29'},
        {'PARTICIPANT NAME': 'David Wilson', 'EVENT NAME': 'Python Workshop', 'DATE': '2025-10-29'},
    ]
    
    print(f"Generating {len(participants)} certificates...\n")
    
    os.makedirs('generated_certificates', exist_ok=True)
    
    for i, participant in enumerate(participants, 1):
        name = participant['PARTICIPANT NAME'].replace(' ', '_')
        output_path = f'generated_certificates/batch_{i:02d}_{name}.png'
        
        result = aligner.generate_aligned_certificate(
            template_image_path=cert_path,
            fields_data=participant,
            output_path=output_path
        )
        
        print(f"  {i}. ✓ {os.path.basename(result)}")
    
    print(f"\n✓ Batch generation complete!")


def main():
    """Run all demos."""
    print("\n" + "="*60)
    print("SMART CERTIFICATE SCANNER & ALIGNER - DEMO")
    print("="*60)
    print("This demonstrates intelligent certificate scanning,")
    print("template creation, and aligned certificate generation.")
    
    try:
        # Create sample certificate
        sample_cert = demo_create_sample_certificate()
        
        # Scan certificate
        analysis = demo_scan_certificate(sample_cert)
        
        # Create template
        template = demo_create_template(analysis)
        
        # Generate aligned certificate
        aligned_cert = demo_generate_aligned_certificate(sample_cert, analysis)
        
        # Batch generation
        demo_batch_generation(sample_cert, analysis)
        
        # Summary
        print("\n" + "="*60)
        print("✓ ALL DEMOS COMPLETED SUCCESSFULLY!")
        print("="*60)
        print("\nGenerated files:")
        print(f"  - Sample certificate: test_samples/sample_certificate.png")
        print(f"  - Template config: test_samples/scanned_template.json")
        print(f"  - Aligned certificates: generated_certificates/")
        print("\nKey files created:")
        print(f"  - Single aligned: generated_certificates/aligned_test_certificate.png")
        print(f"  - Batch (3 certs): generated_certificates/batch_*.png")
        print("\nNext steps:")
        print("  1. Review the generated certificates")
        print("  2. Edit test_samples/scanned_template.json to fine-tune")
        print("  3. Use the template in your application")
        print("  4. Integrate with CertificateGenerator for PDF output")
        print("\n" + "="*60)
        
    except Exception as e:
        print(f"\n✗ Error during demo: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
