#!/usr/bin/env python3
"""Certificate Calibration Tool.

Generates a test certificate, validates alignment, computes baseline adjustments,
and updates the offsets JSON file with measured positions.

Usage:
    python tools/calibrate_and_patch.py [--tolerance 3]
"""
import sys
import os
import json
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.goonj_renderer import GOONJRenderer
from app.utils.certificate_validator import validate


def main():
    """Main entry point for certificate calibration."""
    parser = argparse.ArgumentParser(
        description='Calibrate certificate alignment and update offsets',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--tolerance',
        type=int,
        default=3,
        help='Target tolerance in pixels (default: 3)'
    )
    parser.add_argument(
        '--template',
        default='templates/goonj_certificate.png',
        help='Path to certificate template (default: templates/goonj_certificate.png)'
    )
    parser.add_argument(
        '--output-dir',
        default='generated_certificates',
        help='Output directory for test certificate (default: generated_certificates)'
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("CERTIFICATE ALIGNMENT CALIBRATION")
    print("="*70)
    
    # Check if template exists
    if not os.path.exists(args.template):
        print(f"\n❌ Error: Template not found: {args.template}", file=sys.stderr)
        return 1
    
    print(f"\nTemplate: {args.template}")
    print(f"Tolerance: {args.tolerance} pixels")
    
    try:
        # Step 1: Generate a test certificate
        print("\n" + "-"*70)
        print("Step 1: Generating test certificate...")
        print("-"*70)
        
        renderer = GOONJRenderer(args.template, output_folder=args.output_dir)
        
        # Sample test data
        test_data = {
            'name': 'CALIBRATION TEST SAMPLE',
            'event': 'ALIGNMENT CALIBRATION EVENT',
            'organiser': 'SYSTEM CALIBRATION TEAM'
        }
        
        cert_path = renderer.render(test_data, output_format='png')
        print(f"✅ Test certificate generated: {cert_path}")
        
        # Step 2: Run validation
        print("\n" + "-"*70)
        print("Step 2: Validating alignment...")
        print("-"*70)
        
        result = validate(
            generated_path=cert_path,
            template_ref_path=args.template,
            tolerance_px=args.tolerance
        )
        
        print(f"\nValidation Status: {'✅ PASS' if result['pass'] else '⚠️  NEEDS ADJUSTMENT'}")
        print(f"Overlay saved: {result['overlay_path']}")
        
        # Display offsets
        print("\nDetected Offsets:")
        for field_name, data in result['details'].items():
            print(f"  {field_name}: dx={data['dx']:+d}px, dy={data['dy']:+d}px (distance: {data['distance']:.2f}px)")
        
        # Step 3: Compute adjustments and update JSON
        print("\n" + "-"*70)
        print("Step 3: Computing baseline adjustments...")
        print("-"*70)
        
        # Load current offsets
        offsets_path = os.path.join(os.path.dirname(args.template), 'goonj_template_offsets.json')
        
        if os.path.exists(offsets_path):
            with open(offsets_path, 'r') as f:
                offsets_data = json.load(f)
        else:
            # Create new offsets structure
            offsets_data = {
                'version': '1.0',
                'template': os.path.basename(args.template),
                'description': 'Calibrated field positions for GOONJ certificate template',
                'fields': {},
                'tolerance_px': args.tolerance
            }
        
        # Load template to get dimensions
        from PIL import Image
        template_img = Image.open(args.template)
        width, height = template_img.size
        
        # Update offsets based on validation results
        adjustments_made = False
        for field_name, data in result['details'].items():
            if not data['ok']:
                # Compute new normalized position
                # We want to adjust the reference position to match where the text actually appeared
                gen_x_norm = data['gen_px'][0] / width
                gen_y_norm = data['gen_px'][1] / height
                
                # Calculate baseline offset needed
                baseline_offset = -data['dy']  # Negative because we need to move up if text is too low
                
                if field_name not in offsets_data['fields']:
                    offsets_data['fields'][field_name] = {}
                
                # Store the detected position and computed offset
                offsets_data['fields'][field_name]['x'] = round(gen_x_norm, 4)
                offsets_data['fields'][field_name]['y'] = round(gen_y_norm, 4)
                offsets_data['fields'][field_name]['baseline_offset'] = baseline_offset
                offsets_data['fields'][field_name]['description'] = f"{field_name.capitalize()} field - calibrated"
                
                adjustments_made = True
                print(f"  {field_name}: adjusted y={gen_y_norm:.4f}, baseline_offset={baseline_offset}px")
            else:
                # Field is OK, preserve existing values or set defaults
                if field_name not in offsets_data['fields']:
                    ref_x_norm = data['ref_px'][0] / width
                    ref_y_norm = data['ref_px'][1] / height
                    offsets_data['fields'][field_name] = {
                        'x': round(ref_x_norm, 4),
                        'y': round(ref_y_norm, 4),
                        'baseline_offset': 0,
                        'description': f"{field_name.capitalize()} field - default"
                    }
                print(f"  {field_name}: no adjustment needed (within tolerance)")
        
        # Step 4: Save updated offsets
        print("\n" + "-"*70)
        print("Step 4: Updating offsets file...")
        print("-"*70)
        
        with open(offsets_path, 'w') as f:
            json.dump(offsets_data, f, indent=2)
        
        print(f"✅ Offsets saved to: {offsets_path}")
        
        # Summary
        print("\n" + "="*70)
        print("CALIBRATION COMPLETE")
        print("="*70)
        
        if adjustments_made:
            print("\n⚠️  Adjustments were made to the offsets file.")
            print("\nNext steps:")
            print("  1. Review the validation overlay: " + result['overlay_path'])
            print("  2. Generate a new test certificate to verify adjustments:")
            print("     python -c \"from app.utils.goonj_renderer import GOONJRenderer; r = GOONJRenderer('templates/goonj_certificate.png'); print(r.render({'name': 'Test User', 'event': 'Test Event', 'organiser': 'Test Org'}))\"")
            print("  3. Re-run validation:")
            print(f"     python tools/validate_certificate.py <new_cert.png> --tolerance {args.tolerance}")
        else:
            print("\n✅ All fields are already within tolerance. No adjustments needed.")
        
        print("="*70 + "\n")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error during calibration: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 2


if __name__ == '__main__':
    sys.exit(main())
