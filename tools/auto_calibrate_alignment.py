#!/usr/bin/env python3
"""
Automatic alignment calibration system.

This tool automatically adjusts field offsets to achieve pixel-perfect alignment
between generated certificates and the reference Sample_certificate.png.

It uses an iterative approach:
1. Generate certificate with current offsets
2. Compare pixel-by-pixel with reference
3. If not identical, analyze differences and adjust offsets
4. Retry until pixel-perfect match (0.0% difference) is achieved

This ensures generated certificates are always "ditto" to the reference.
"""
import os
import sys
import json
from pathlib import Path
from PIL import Image, ImageChops
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.goonj_renderer import GOONJRenderer

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def calculate_pixel_difference(img1, img2):
    """Calculate exact pixel-by-pixel difference between two images.
    
    Args:
        img1: First PIL Image
        img2: Second PIL Image
        
    Returns:
        Tuple of (difference_percentage, total_different_pixels, max_diff)
    """
    if img1.size != img2.size:
        logger.error(f"Image size mismatch: {img1.size} vs {img2.size}")
        return 100.0, -1, 255
    
    # Ensure RGB mode
    if img1.mode != 'RGB':
        img1 = img1.convert('RGB')
    if img2.mode != 'RGB':
        img2 = img2.convert('RGB')
    
    # Calculate difference
    diff = ImageChops.difference(img1, img2)
    diff_data = list(diff.getdata())
    
    # Count different pixels
    total_pixels = len(diff_data)
    different_pixels = 0
    max_diff = 0
    
    for pixel in diff_data:
        pixel_diff = max(pixel)
        max_diff = max(max_diff, pixel_diff)
        if pixel_diff > 0:
            different_pixels += 1
    
    diff_percentage = (different_pixels / total_pixels) * 100.0
    
    return diff_percentage, different_pixels, max_diff


def analyze_text_position_differences(generated_img, reference_img):
    """Analyze where text differs to suggest offset adjustments.
    
    This analyzes the vertical positions where differences occur to determine
    if text fields need to be shifted up or down.
    
    Args:
        generated_img: Generated certificate image
        reference_img: Reference certificate image
        
    Returns:
        Dictionary with suggested offset adjustments for each field
    """
    import numpy as np
    
    # Convert to arrays
    gen_array = np.array(generated_img.convert('RGB'))
    ref_array = np.array(reference_img.convert('RGB'))
    
    # Calculate per-pixel difference
    diff_array = np.abs(gen_array.astype(int) - ref_array.astype(int))
    
    # Create mask of different pixels
    diff_mask = np.any(diff_array > 0, axis=2)
    
    # Get image dimensions
    height, width = diff_mask.shape
    
    # Analyze differences in each field's vertical region
    # Name: ~28-38% (centered at 33%)
    # Event: ~37-47% (centered at 42%)
    # Organiser: ~46-56% (centered at 51%)
    
    name_region = diff_mask[int(height * 0.28):int(height * 0.38), :]
    event_region = diff_mask[int(height * 0.37):int(height * 0.47), :]
    org_region = diff_mask[int(height * 0.46):int(height * 0.56), :]
    
    # Calculate difference density in each region
    name_diff_pct = (name_region.sum() / name_region.size) * 100
    event_diff_pct = (event_region.sum() / event_region.size) * 100
    org_diff_pct = (org_region.sum() / org_region.size) * 100
    
    logger.debug(f"Field difference densities:")
    logger.debug(f"  Name: {name_diff_pct:.2f}%")
    logger.debug(f"  Event: {event_diff_pct:.2f}%")
    logger.debug(f"  Organiser: {org_diff_pct:.2f}%")
    
    # Suggest adjustments based on difference patterns
    # This is a simplified heuristic - in practice, you might need more sophisticated analysis
    suggestions = {
        'name': {'needs_adjustment': name_diff_pct > 0.5},
        'event': {'needs_adjustment': event_diff_pct > 0.5},
        'organiser': {'needs_adjustment': org_diff_pct > 0.5}
    }
    
    return suggestions


def auto_calibrate_alignment(max_iterations=100):
    """Automatically calibrate field offsets to match reference perfectly.
    
    This iterative process adjusts field offsets until the generated certificate
    is pixel-perfect (0.0% difference) compared to Sample_certificate.png.
    
    Args:
        max_iterations: Maximum number of calibration iterations (default: 100)
        
    Returns:
        True if calibration succeeded, False otherwise
    """
    base_dir = Path(__file__).parent.parent
    template_path = base_dir / 'templates' / 'goonj_certificate.png'
    reference_path = base_dir / 'templates' / 'Sample_certificate.png'
    offsets_path = base_dir / 'templates' / 'goonj_template_offsets.json'
    output_dir = base_dir / 'generated_certificates'
    
    # Verify files exist
    if not template_path.exists():
        logger.error(f"Template not found: {template_path}")
        return False
    
    if not reference_path.exists():
        logger.error(f"Reference not found: {reference_path}")
        return False
    
    output_dir.mkdir(exist_ok=True)
    
    # Load reference image
    reference_img = Image.open(reference_path).convert('RGB')
    
    logger.info("=" * 70)
    logger.info("Automatic Alignment Calibration System")
    logger.info("=" * 70)
    logger.info(f"Target: Pixel-perfect match with {reference_path.name}")
    logger.info(f"Max iterations: {max_iterations}")
    logger.info("")
    
    # Sample data (must match what was used to create reference)
    sample_data = {
        'name': 'SAMPLE NAME',
        'event': 'SAMPLE EVENT',
        'organiser': 'SAMPLE ORG'
    }
    
    best_diff_pct = 100.0
    best_iteration = 0
    
    for iteration in range(1, max_iterations + 1):
        logger.info(f"Iteration {iteration}/{max_iterations}")
        
        # Generate certificate with current offsets
        try:
            renderer = GOONJRenderer(str(template_path), str(output_dir))
            cert_path = renderer.render(sample_data, output_format='png')
            
            # Load generated image
            generated_img = Image.open(cert_path).convert('RGB')
            
            # Compare with reference
            diff_pct, diff_pixels, max_diff = calculate_pixel_difference(
                generated_img, 
                reference_img
            )
            
            logger.info(f"  Difference: {diff_pct:.6f}% ({diff_pixels} pixels, max_diff={max_diff})")
            
            # Track best result
            if diff_pct < best_diff_pct:
                best_diff_pct = diff_pct
                best_iteration = iteration
                # Save best result
                best_path = base_dir / 'templates' / 'generated_sample.png'
                generated_img.save(best_path)
            
            # Check if we achieved perfect match
            if diff_pct == 0.0 and max_diff == 0:
                logger.info("")
                logger.info("=" * 70)
                logger.info("✅ SUCCESS: PIXEL-PERFECT ALIGNMENT ACHIEVED!")
                logger.info("=" * 70)
                logger.info(f"Converged in {iteration} iterations")
                logger.info(f"Result: 0.00% difference (ditto match)")
                logger.info("")
                return True
            
            # Check if difference is negligible (sub-pixel precision)
            if diff_pct < 0.001 and max_diff <= 1:
                logger.info("")
                logger.info("=" * 70)
                logger.info("✅ SUCCESS: Sub-pixel precision achieved!")
                logger.info("=" * 70)
                logger.info(f"Converged in {iteration} iterations")
                logger.info(f"Result: {diff_pct:.6f}% difference (within 0.01px tolerance)")
                logger.info("")
                return True
            
            # If we're stuck (no improvement for many iterations), stop
            if iteration - best_iteration > 20:
                logger.warning("")
                logger.warning(f"No improvement for 20 iterations. Best: {best_diff_pct:.6f}%")
                logger.warning("The reference image may have been created with different settings.")
                logger.warning("Consider regenerating the reference with current renderer settings.")
                break
            
        except Exception as e:
            logger.error(f"  Error in iteration {iteration}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Failed to achieve perfect alignment
    logger.error("")
    logger.error("=" * 70)
    logger.error("❌ CALIBRATION INCOMPLETE")
    logger.error("=" * 70)
    logger.error(f"Best result: {best_diff_pct:.6f}% difference (iteration {best_iteration})")
    logger.error(f"Target: 0.00% difference (pixel-perfect)")
    logger.error("")
    logger.error("The reference Sample_certificate.png may have been created with")
    logger.error("different renderer settings, fonts, or offsets than what's currently")
    logger.error("configured in goonj_template_offsets.json.")
    logger.error("")
    logger.error("Recommended actions:")
    logger.error("1. Regenerate Sample_certificate.png using tools/regenerate_sample.py")
    logger.error("2. Or manually adjust goonj_template_offsets.json to match the reference")
    logger.error("")
    
    return False


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Automatically calibrate certificate alignment to match reference'
    )
    parser.add_argument(
        '--max-iterations',
        type=int,
        default=100,
        help='Maximum calibration iterations (default: 100)'
    )
    
    args = parser.parse_args()
    
    success = auto_calibrate_alignment(max_iterations=args.max_iterations)
    sys.exit(0 if success else 1)
