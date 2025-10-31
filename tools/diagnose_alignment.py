#!/usr/bin/env python
"""
Diagnostic tool for certificate alignment verification.

This tool helps diagnose alignment issues by:
1. Extracting field positions from generated and reference certificates
2. Showing individual field differences
3. Providing visual feedback on alignment quality

Usage:
    python tools/diagnose_alignment.py <generated_cert_path> [reference_cert_path]
"""
import sys
import os

# Direct import to avoid Flask dependencies
import importlib.util

# Load the module directly from file
verifier_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'app', 'utils', 'iterative_alignment_verifier.py'
)
spec = importlib.util.spec_from_file_location("iterative_alignment_verifier", verifier_path)
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)

extract_field_positions = verifier.extract_field_positions
calculate_position_difference = verifier.calculate_position_difference

from PIL import Image
import json


def diagnose_alignment(generated_path, reference_path=None):
    """Diagnose alignment issues in a certificate."""
    
    # Use default reference if not provided
    if reference_path is None:
        reference_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'templates',
            'Sample_certificate.png'
        )
    
    print("=" * 70)
    print("CERTIFICATE ALIGNMENT DIAGNOSTIC TOOL")
    print("=" * 70)
    
    # Validate inputs
    if not os.path.exists(generated_path):
        print(f"❌ ERROR: Generated certificate not found: {generated_path}")
        return 1
    
    if not os.path.exists(reference_path):
        print(f"❌ ERROR: Reference certificate not found: {reference_path}")
        return 1
    
    # Load images
    gen_img = Image.open(generated_path)
    ref_img = Image.open(reference_path)
    
    print(f"\n📄 Generated Certificate: {generated_path}")
    print(f"   Size: {gen_img.size}, Mode: {gen_img.mode}")
    
    print(f"\n📄 Reference Certificate: {reference_path}")
    print(f"   Size: {ref_img.size}, Mode: {ref_img.mode}")
    
    # Extract positions
    print("\n" + "=" * 70)
    print("EXTRACTING FIELD POSITIONS")
    print("=" * 70)
    
    print("\n🔍 Scanning generated certificate...")
    gen_positions = extract_field_positions(generated_path)
    
    print("\n🔍 Scanning reference certificate...")
    ref_positions = extract_field_positions(reference_path)
    
    # Display detected fields
    print("\n" + "=" * 70)
    print("DETECTED FIELDS")
    print("=" * 70)
    
    print("\n📊 Generated Certificate Fields:")
    for field_name in ['name', 'event', 'organiser']:
        if field_name in gen_positions:
            pos = gen_positions[field_name]
            print(f"  ✅ {field_name:10s}: y={pos['y_center']:7.2f}px, x={pos['x_center']:7.2f}px "
                  f"(y={pos['y_start']}-{pos['y_end']})")
        else:
            print(f"  ❌ {field_name:10s}: NOT DETECTED")
    
    print("\n📊 Reference Certificate Fields:")
    for field_name in ['name', 'event', 'organiser']:
        if field_name in ref_positions:
            pos = ref_positions[field_name]
            print(f"  ✅ {field_name:10s}: y={pos['y_center']:7.2f}px, x={pos['x_center']:7.2f}px "
                  f"(y={pos['y_start']}-{pos['y_end']})")
        else:
            print(f"  ❌ {field_name:10s}: NOT DETECTED")
    
    # Calculate differences
    print("\n" + "=" * 70)
    print("ALIGNMENT ANALYSIS")
    print("=" * 70)
    
    diff_result = calculate_position_difference(gen_positions, ref_positions)
    max_diff = diff_result['max_difference_px']
    
    # Check for missing fields
    if 'missing_fields' in diff_result:
        print(f"\n❌ CRITICAL: Missing fields: {', '.join(diff_result['missing_fields'])}")
        print(f"   {diff_result['error']}")
    
    # Show individual field differences
    print("\n📏 Individual Field Differences:")
    for field_name in ['name', 'event', 'organiser']:
        if field_name in diff_result['fields']:
            field_diff = diff_result['fields'][field_name]
            
            if 'error' in field_diff:
                print(f"\n  ❌ {field_name.upper()}:")
                print(f"     Error: {field_diff['error']}")
                print(f"     Detected in generated: {field_diff.get('detected_in_generated', False)}")
                print(f"     Detected in reference: {field_diff.get('detected_in_reference', False)}")
            else:
                y_diff = field_diff['y_diff']
                x_diff = field_diff['x_diff']
                
                # Determine status
                if y_diff <= 0.02 and x_diff <= 0.02:
                    status = "✅ PERFECT"
                elif y_diff <= 2.0 and x_diff <= 2.0:
                    status = "✓ GOOD"
                elif y_diff <= 10.0 and x_diff <= 10.0:
                    status = "⚠️  WARNING"
                else:
                    status = "❌ FAILED"
                
                print(f"\n  {status} {field_name.upper()}:")
                print(f"     Y difference: {y_diff:7.2f} px  (gen={field_diff['y_center_gen']:7.2f}, ref={field_diff['y_center_ref']:7.2f})")
                print(f"     X difference: {x_diff:7.2f} px  (gen={field_diff['x_center_gen']:7.2f}, ref={field_diff['x_center_ref']:7.2f})")
    
    # Overall verdict
    print("\n" + "=" * 70)
    print("OVERALL VERDICT")
    print("=" * 70)
    
    if max_diff == float('inf'):
        print("\n❌ ALIGNMENT FAILED: One or more fields not detected")
        verdict = "FAILED"
    elif max_diff <= 0.02:
        print(f"\n✅ PERFECT ALIGNMENT: Max difference = {max_diff:.4f} px (≤ 0.02 px)")
        verdict = "PERFECT"
    elif max_diff <= 2.0:
        print(f"\n✓ GOOD ALIGNMENT: Max difference = {max_diff:.2f} px (≤ 2.0 px)")
        verdict = "GOOD"
    elif max_diff <= 10.0:
        print(f"\n⚠️  WARNING: Max difference = {max_diff:.2f} px (> 2.0 px)")
        print("   Certificate may have noticeable alignment issues")
        verdict = "WARNING"
    else:
        print(f"\n❌ POOR ALIGNMENT: Max difference = {max_diff:.2f} px (> 10.0 px)")
        print("   Certificate has significant alignment issues")
        verdict = "POOR"
    
    print("\n" + "=" * 70)
    
    # Return appropriate exit code
    return 0 if verdict in ["PERFECT", "GOOD"] else 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/diagnose_alignment.py <generated_cert_path> [reference_cert_path]")
        print("\nExample:")
        print("  python tools/diagnose_alignment.py generated_certificates/cert_123.png")
        print("  python tools/diagnose_alignment.py my_cert.png templates/Sample_certificate.png")
        sys.exit(1)
    
    generated_path = sys.argv[1]
    reference_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    exit_code = diagnose_alignment(generated_path, reference_path)
    sys.exit(exit_code)
