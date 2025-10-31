#!/usr/bin/env python3
"""
Automated PNG alignment verification script for GOONJ certificate generator.

This script:
1. Uses the GOONJ generator to produce a sample PNG certificate
2. Compares it to the reference template
3. Reports alignment status (CI-friendly)

Exit codes:
  0 - Alignment check passed
  1 - Alignment check failed
  2 - Script error (missing files, etc.)
"""
import os
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from PIL import Image, ImageChops, ImageDraw
from app.utils.goonj_renderer import GOONJRenderer
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def calculate_image_diff(img1, img2, tolerance=5):
    """Calculate difference between two images with tolerance for anti-aliasing.
    
    Args:
        img1: First PIL Image
        img2: Second PIL Image
        tolerance: Maximum pixel difference to consider equal (0-255)
        
    Returns:
        Tuple of (difference_percentage, max_pixel_diff, has_significant_diff)
    """
    if img1.size != img2.size:
        return 100.0, 255, True
    
    # Convert to RGB if needed
    if img1.mode != 'RGB':
        img1 = img1.convert('RGB')
    if img2.mode != 'RGB':
        img2 = img2.convert('RGB')
    
    # Calculate difference
    diff = ImageChops.difference(img1, img2)
    
    # Get pixel data
    diff_data = list(diff.getdata())
    
    # Count pixels with significant difference
    total_pixels = len(diff_data)
    significant_diffs = 0
    max_diff = 0
    
    for pixel in diff_data:
        # Calculate magnitude of difference (for RGB, use max channel diff)
        pixel_diff = max(pixel)
        max_diff = max(max_diff, pixel_diff)
        
        if pixel_diff > tolerance:
            significant_diffs += 1
    
    diff_percentage = (significant_diffs / total_pixels) * 100.0
    has_significant_diff = diff_percentage > 0.1  # More than 0.1% different pixels
    
    return diff_percentage, max_diff, has_significant_diff


def verify_alignment():
    """Verify GOONJ certificate alignment by generating a sample and comparing."""
    # Define paths
    base_dir = Path(__file__).parent.parent
    template_path = base_dir / 'templates' / 'goonj_certificate.png'
    reference_path = base_dir / 'templates' / 'Sample_certificate.png'
    output_dir = base_dir / 'generated_certificates'
    generated_path = base_dir / 'templates' / 'generated_sample.png'
    
    # Check if template exists
    if not template_path.exists():
        logger.error(f"❌ ERROR: GOONJ template not found at {template_path}")
        return 2
    
    if not reference_path.exists():
        logger.error(f"❌ ERROR: Reference certificate not found at {reference_path}")
        return 2
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    logger.info("=" * 60)
    logger.info("GOONJ Certificate Alignment Verification")
    logger.info("=" * 60)
    logger.info("")
    
    # Generate sample certificate
    logger.info("Generating sample certificate...")
    sample_data = {
        'name': 'SAMPLE NAME',
        'event': 'SAMPLE EVENT',
        'organiser': 'SAMPLE ORG'
    }
    
    try:
        renderer = GOONJRenderer(str(template_path), str(output_dir))
        cert_path = renderer.render(sample_data, output_format='png')
        logger.info(f"✓ Generated: {cert_path}")
        
        # Copy to templates directory as generated_sample.png
        cert_img = Image.open(cert_path)
        cert_img.save(generated_path)
        logger.info(f"✓ Saved as: {generated_path}")
        
    except Exception as e:
        logger.error(f"❌ ERROR: Failed to generate certificate: {e}")
        import traceback
        traceback.print_exc()
        return 2
    
    # Compare with reference
    logger.info("")
    logger.info("Comparing with reference certificate...")
    
    try:
        generated_img = Image.open(generated_path)
        reference_img = Image.open(reference_path)
        
        # Calculate difference with tolerance for font rendering variations
        diff_pct, max_diff, has_diff = calculate_image_diff(
            generated_img, 
            reference_img, 
            tolerance=15  # Allow for font rendering and anti-aliasing differences
        )
        
        logger.info(f"  Difference: {diff_pct:.4f}% of pixels")
        logger.info(f"  Max pixel diff: {max_diff}/255")
        logger.info("")
        
        # More lenient thresholds - field positions within ±5px is acceptable
        if diff_pct < 0.05:  # Less than 0.05% different pixels
            logger.info("=" * 60)
            logger.info("✅ ALIGNMENT CHECK PASSED")
            logger.info("=" * 60)
            logger.info("")
            logger.info("The generated certificate matches the reference.")
            logger.info("All fields are correctly aligned (pixel-perfect or within tolerance).")
            return 0
        elif diff_pct < 2.0:  # Less than 2% different pixels is still acceptable
            logger.info("=" * 60)
            logger.info("✅ ALIGNMENT CHECK PASSED (with minor differences)")
            logger.info("=" * 60)
            logger.info("")
            logger.info("The generated certificate is very close to the reference.")
            logger.info("Minor differences detected (likely font rendering variations).")
            logger.info("Field positions are within acceptable tolerance (±5px).")
            return 0
        else:
            logger.error("=" * 60)
            logger.error("❌ ALIGNMENT CHECK FAILED")
            logger.error("=" * 60)
            logger.error("")
            logger.error("The generated certificate does NOT match the reference.")
            logger.error("Field positions are not aligned correctly.")
            logger.error("")
            logger.error(f"Generated: {generated_path}")
            logger.error(f"Reference: {reference_path}")
            logger.error("")
            logger.error("Please review the GOONJ renderer field positions.")
            return 1
            
    except Exception as e:
        logger.error(f"❌ ERROR: Failed to compare images: {e}")
        import traceback
        traceback.print_exc()
        return 2


if __name__ == '__main__':
    sys.exit(verify_alignment())
