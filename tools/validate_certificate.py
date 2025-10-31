#!/usr/bin/env python3
"""Certificate Validation CLI Tool.

Validates certificate text alignment against reference template and expected positions.
Generates a visual overlay showing alignment status.

Usage:
    python tools/validate_certificate.py <generated_cert.png> [template.png] [--tolerance 3]
"""
import sys
import os
import json
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.certificate_validator import validate


def main():
    """Main entry point for certificate validation."""
    parser = argparse.ArgumentParser(
        description='Validate certificate text alignment',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/validate_certificate.py generated_certificates/cert.png
  python tools/validate_certificate.py cert.png templates/goonj_certificate.png --tolerance 5
        """
    )
    
    parser.add_argument(
        'generated',
        help='Path to generated certificate image'
    )
    parser.add_argument(
        'template',
        nargs='?',
        default=None,
        help='Path to reference template image (optional)'
    )
    parser.add_argument(
        '--tolerance',
        type=int,
        default=3,
        help='Maximum allowed pixel offset (default: 3)'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON'
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if not os.path.exists(args.generated):
        print(f"Error: Generated certificate not found: {args.generated}", file=sys.stderr)
        return 1
    
    if args.template and not os.path.exists(args.template):
        print(f"Error: Template not found: {args.template}", file=sys.stderr)
        return 1
    
    try:
        # Run validation
        result = validate(
            generated_path=args.generated,
            template_ref_path=args.template,
            tolerance_px=args.tolerance
        )
        
        # Output results
        if args.json:
            # JSON output
            output = {
                'pass': result['pass'],
                'tolerance_px': result['tolerance_px'],
                'overlay_path': result['overlay_path'],
                'details': result['details']
            }
            print(json.dumps(output, indent=2))
        else:
            # Human-readable output
            print("\n" + "="*70)
            print("CERTIFICATE ALIGNMENT VALIDATION REPORT")
            print("="*70)
            print(f"\nGenerated Certificate: {args.generated}")
            print(f"Tolerance: {args.tolerance} pixels")
            print(f"Status: {'✅ PASS' if result['pass'] else '❌ FAIL'}")
            print(f"\nOverlay Image: {result['overlay_path']}")
            
            print("\n" + "-"*70)
            print("Field-by-Field Analysis:")
            print("-"*70)
            
            for field_name, data in result['details'].items():
                status = "✅ OK" if data['ok'] else "❌ FAIL"
                print(f"\n{field_name.upper()}:")
                print(f"  Generated Position: {data['gen_px']}")
                print(f"  Reference Position: {data['ref_px']}")
                print(f"  Offset: dx={data['dx']:+d}px, dy={data['dy']:+d}px")
                print(f"  Distance: {data['distance']:.2f}px")
                print(f"  Status: {status}")
            
            print("\n" + "="*70)
            
            if result['pass']:
                print("✅ All fields are within tolerance")
            else:
                print("❌ Some fields exceed tolerance")
                print("\nTo fix alignment issues:")
                print("  1. Review the overlay image: " + result['overlay_path'])
                print("  2. Run calibration: python tools/calibrate_and_patch.py")
                print("  3. Re-validate after calibration")
            
            print("="*70 + "\n")
        
        # Exit with appropriate code
        return 0 if result['pass'] else 1
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception(f"Error during validation: {e}")
        print(f"Error during validation: {e}", file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
