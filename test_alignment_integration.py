#!/usr/bin/env python3
"""
Manual test script for alignment verification in certificate generation.

This script tests the complete workflow:
1. Generate a certificate
2. Verify alignment
3. Simulate email sending with alignment check
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.utils.goonj_renderer import GOONJRenderer
from app.utils.alignment_checker import (
    verify_certificate_alignment,
    get_reference_certificate_path,
    verify_with_retry
)
import tempfile

def test_certificate_generation_with_verification():
    """Test certificate generation with alignment verification."""
    print("=" * 70)
    print("TESTING CERTIFICATE GENERATION WITH ALIGNMENT VERIFICATION")
    print("=" * 70)
    print()
    
    # Paths
    template_path = 'templates/goonj_certificate.png'
    
    if not os.path.exists(template_path):
        print(f"❌ ERROR: Template not found at {template_path}")
        return 1
    
    # Get reference path
    try:
        reference_path = get_reference_certificate_path(template_path)
        print(f"✓ Template: {template_path}")
        print(f"✓ Reference: {reference_path}")
        print()
    except FileNotFoundError as e:
        print(f"❌ ERROR: {e}")
        return 1
    
    # Test with temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"Output directory: {tmpdir}")
        print()
        
        # Initialize renderer
        renderer = GOONJRenderer(template_path, output_folder=tmpdir)
        
        # Test Case 1: Sample data (should pass perfectly)
        print("-" * 70)
        print("TEST CASE 1: Sample Data (Expected: PERFECT MATCH)")
        print("-" * 70)
        
        sample_data = {
            'name': 'SAMPLE NAME',
            'event': 'SAMPLE EVENT',
            'organiser': 'SAMPLE ORG'
        }
        
        print(f"Generating certificate for: {sample_data['name']}")
        cert_path = renderer.render(sample_data, output_format='png')
        print(f"✓ Generated: {cert_path}")
        print()
        
        # Verify alignment
        print("Verifying alignment...")
        result = verify_certificate_alignment(
            cert_path,
            reference_path,
            tolerance_px=0.01
        )
        
        print(f"Result: {'✅ PASSED' if result['passed'] else '❌ FAILED'}")
        print(f"  Difference: {result['difference_pct']:.6f}%")
        print(f"  Max pixel diff: {result['max_pixel_diff']}/255")
        print(f"  Message: {result['message']}")
        print()
        
        # Test Case 2: Different data (should still pass with exact alignment)
        print("-" * 70)
        print("TEST CASE 2: Different Data (Expected: PERFECT MATCH)")
        print("-" * 70)
        
        test_data = {
            'name': 'John Doe Test User',
            'event': 'Test Event 2025',
            'organiser': 'Test Organization'
        }
        
        print(f"Generating certificate for: {test_data['name']}")
        cert_path2 = renderer.render(test_data, output_format='png')
        print(f"✓ Generated: {cert_path2}")
        print()
        
        # This will likely fail alignment because it has different text
        # But we're testing that the verification logic works
        print("Verifying alignment (this is expected to fail - different text)...")
        result2 = verify_certificate_alignment(
            cert_path2,
            reference_path,
            tolerance_px=0.01
        )
        
        print(f"Result: {'✅ PASSED' if result2['passed'] else '❌ FAILED (Expected)'}")
        print(f"  Difference: {result2['difference_pct']:.6f}%")
        print(f"  Max pixel diff: {result2['max_pixel_diff']}/255")
        print(f"  Message: {result2['message']}")
        print()
        
        # Test Case 3: Retry logic
        print("-" * 70)
        print("TEST CASE 3: Retry Logic with Sample Data")
        print("-" * 70)
        
        print(f"Generating certificate for: {sample_data['name']}")
        cert_path3 = renderer.render(sample_data, output_format='png')
        print(f"✓ Generated: {cert_path3}")
        print()
        
        print("Testing retry logic (should succeed on first attempt)...")
        result3 = verify_with_retry(
            cert_path3,
            reference_path,
            max_attempts=150,
            tolerance_px=0.01
        )
        
        print(f"Result: {'✅ PASSED' if result3['passed'] else '❌ FAILED'}")
        print(f"  Attempts: {result3['attempts']}")
        print(f"  Difference: {result3['difference_pct']:.6f}%")
        print(f"  Message: {result3['message']}")
        print()
    
    print("=" * 70)
    print("TESTING COMPLETED")
    print("=" * 70)
    
    # Return success if at least sample data test passed
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    sys.exit(test_certificate_generation_with_verification())
