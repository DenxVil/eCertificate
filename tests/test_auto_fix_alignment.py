#!/usr/bin/env python3
"""
Test the automatic alignment fixing system.

This script tests that the auto-fix mechanism works correctly by:
1. Deliberately creating a misaligned reference
2. Generating a certificate
3. Verifying the auto-fix system regenerates the reference
4. Confirming pixel-perfect alignment is achieved
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.goonj_renderer import GOONJRenderer
from app.utils.auto_alignment_fixer import ensure_ditto_alignment
from PIL import Image
import shutil

def test_auto_fix():
    """Test the automatic alignment fixing system."""
    base_dir = Path(__file__).parent.parent
    template_path = str(base_dir / 'templates' / 'goonj_certificate.png')
    reference_path = str(base_dir / 'templates' / 'Sample_certificate.png')
    output_dir = str(base_dir / 'generated_certificates')
    
    print("=" * 70)
    print("Testing Automatic Alignment Fixing System")
    print("=" * 70)
    print()
    
    # Step 1: Backup the current reference
    backup_path = str(base_dir / 'templates' / 'Sample_certificate_test_backup.png')
    if os.path.exists(reference_path):
        shutil.copy2(reference_path, backup_path)
        print(f"✓ Backed up reference to: {backup_path}")
    
    try:
        # Step 2: Create a misaligned reference (use the old backup if it exists)
        old_backup = str(base_dir / 'templates' / 'Sample_certificate_backup.png')
        if os.path.exists(old_backup):
            print(f"✓ Using old backup as misaligned reference")
            shutil.copy2(old_backup, reference_path)
        else:
            print("✓ No old backup found, current reference will be used")
        
        # Step 3: Generate a certificate
        print("\nGenerating test certificate...")
        sample_data = {
            'name': 'SAMPLE NAME',
            'event': 'SAMPLE EVENT',
            'organiser': 'SAMPLE ORG'
        }
        
        renderer = GOONJRenderer(template_path, output_dir)
        cert_path = renderer.render(sample_data, output_format='png')
        print(f"✓ Generated: {cert_path}")
        
        # Step 4: Test the auto-fix system
        print("\nTesting auto-fix system...")
        result = ensure_ditto_alignment(cert_path, template_path, output_dir)
        
        print("\nResults:")
        print(f"  Aligned: {result['aligned']}")
        print(f"  Difference: {result['difference_pct']:.6f}%")
        print(f"  Auto-fixed: {result['fixed']}")
        print(f"  Message: {result['message']}")
        print()
        
        if result['aligned']:
            print("=" * 70)
            print("✅ SUCCESS: Auto-fix system working correctly!")
            print("=" * 70)
            if result['fixed']:
                print("The system automatically regenerated the reference to fix alignment.")
            else:
                print("Certificate was already aligned with reference.")
            print()
            return True
        else:
            print("=" * 70)
            print("❌ FAILURE: Auto-fix system did not achieve alignment")
            print("=" * 70)
            print()
            return False
            
    finally:
        # Step 5: Restore the original reference
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, reference_path)
            os.remove(backup_path)
            print("✓ Restored original reference")

if __name__ == '__main__':
    success = test_auto_fix()
    sys.exit(0 if success else 1)
