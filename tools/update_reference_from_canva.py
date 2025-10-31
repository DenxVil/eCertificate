#!/usr/bin/env python3
"""
Update reference certificate from Canva design.

This script helps you replace the current Sample_certificate.png with a new
reference image from Canva.

Usage:
    1. Download your Canva design as PNG:
       - Open: https://www.canva.com/design/DAG3WWj3eUk/yThBfXKr0YLNUBzigPzSUA/view
       - Click "Share" > "Download" > "PNG"
       - Save the downloaded file
    
    2. Run this script with the downloaded file path:
       python tools/update_reference_from_canva.py /path/to/downloaded_canva_image.png
    
    3. The script will:
       - Backup your current reference
       - Replace it with the Canva image
       - Verify dimensions and format
       - Update the system to match the new reference
"""
import sys
import os
import shutil
from pathlib import Path
from PIL import Image

def update_reference(canva_image_path):
    """Update the reference certificate with a Canva design.
    
    Args:
        canva_image_path: Path to the downloaded Canva PNG file
    """
    base_dir = Path(__file__).parent.parent
    reference_path = base_dir / 'templates' / 'Sample_certificate.png'
    backup_path = base_dir / 'templates' / 'Sample_certificate_canva_backup.png'
    
    print("=" * 70)
    print("Updating Reference Certificate from Canva Design")
    print("=" * 70)
    print()
    
    # Validate input file
    if not os.path.exists(canva_image_path):
        print(f"❌ Error: File not found: {canva_image_path}")
        return False
    
    try:
        # Load the Canva image
        print(f"Loading Canva image: {canva_image_path}")
        canva_img = Image.open(canva_image_path)
        
        print(f"  Format: {canva_img.format}")
        print(f"  Size: {canva_img.size}")
        print(f"  Mode: {canva_img.mode}")
        print()
        
        # Check dimensions
        expected_width = 2000
        expected_height = 1414
        
        if canva_img.size != (expected_width, expected_height):
            print(f"⚠️  Warning: Image dimensions are {canva_img.size}")
            print(f"   Expected: {expected_width}x{expected_height}")
            print()
            
            response = input("Do you want to resize the image? (y/n): ").lower()
            if response == 'y':
                print(f"Resizing image to {expected_width}x{expected_height}...")
                canva_img = canva_img.resize((expected_width, expected_height), Image.LANCZOS)
                print("✓ Resized")
            else:
                print("⚠️  Proceeding with original dimensions")
                print("   Note: This may cause alignment verification to fail")
        
        # Convert to RGB if needed
        if canva_img.mode != 'RGB':
            print(f"Converting from {canva_img.mode} to RGB mode...")
            canva_img = canva_img.convert('RGB')
            print("✓ Converted to RGB")
        
        print()
        
        # Backup current reference
        if reference_path.exists():
            print(f"Backing up current reference to: {backup_path}")
            shutil.copy2(reference_path, backup_path)
            print("✓ Backup created")
        
        # Save the new reference
        print(f"Saving new reference to: {reference_path}")
        canva_img.save(reference_path, 'PNG')
        print("✓ New reference saved")
        
        print()
        print("=" * 70)
        print("✅ Reference certificate updated successfully!")
        print("=" * 70)
        print()
        print("Next steps:")
        print("1. Run alignment verification to ensure the renderer matches:")
        print("   python scripts/verify_alignment.py")
        print()
        print("2. If alignment fails, you may need to adjust field positions in:")
        print("   templates/goonj_template_offsets.json")
        print()
        print("3. The auto-fix system will help regenerate the reference if needed")
        print()
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point."""
    if len(sys.argv) != 2:
        print("Usage: python tools/update_reference_from_canva.py <path_to_canva_image.png>")
        print()
        print("Instructions:")
        print("1. Open the Canva design:")
        print("   https://www.canva.com/design/DAG3WWj3eUk/yThBfXKr0YLNUBzigPzSUA/view")
        print()
        print("2. Download as PNG:")
        print("   Click 'Share' > 'Download' > Select 'PNG' > 'Download'")
        print()
        print("3. Run this script with the downloaded file:")
        print("   python tools/update_reference_from_canva.py ~/Downloads/certificate.png")
        print()
        return 1
    
    canva_image_path = sys.argv[1]
    success = update_reference(canva_image_path)
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
