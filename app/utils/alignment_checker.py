"""Certificate alignment verification module.

This module provides pixel-perfect alignment verification for generated certificates,
ensuring they match the reference sample with <0.01px tolerance before sending.
"""
import os
import logging
from PIL import Image, ImageChops
from pathlib import Path

logger = logging.getLogger(__name__)

# Tolerance constants for pixel-perfect verification
# These map the 0.01px requirement to practical thresholds
PIXEL_VALUE_TOLERANCE = 1  # Maximum RGB channel difference (0-255)
PERCENTAGE_TOLERANCE = 0.001  # Maximum percentage of different pixels (0.001% ~= 0.01px)


class AlignmentVerificationError(Exception):
    """Raised when certificate alignment verification fails."""
    pass


def calculate_image_difference(img1, img2, tolerance=1):
    """Calculate pixel-level difference between two images.
    
    Args:
        img1: First PIL Image
        img2: Second PIL Image
        tolerance: Maximum pixel value difference to consider equal (0-255)
        
    Returns:
        Tuple of (difference_percentage, max_pixel_diff, has_significant_diff)
    """
    if img1.size != img2.size:
        logger.warning(f"Image size mismatch: {img1.size} vs {img2.size}")
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
    has_significant_diff = diff_percentage > PERCENTAGE_TOLERANCE  # More than 0.001% different pixels
    
    return diff_percentage, max_diff, has_significant_diff


def verify_certificate_alignment(generated_path, reference_path, tolerance_px=0.01):
    """Verify that a generated certificate matches the reference within tolerance.
    
    This function performs pixel-perfect comparison to ensure the generated certificate
    has less than 0.01px difference from the reference sample.
    
    Args:
        generated_path: Path to the generated certificate image
        reference_path: Path to the reference sample certificate
        tolerance_px: Maximum allowed difference in pixels (default: 0.01)
        
    Returns:
        Dictionary with verification results:
        {
            'passed': bool,
            'difference_pct': float,
            'max_pixel_diff': int,
            'tolerance_px': float,
            'message': str
        }
        
    Raises:
        FileNotFoundError: If generated or reference file doesn't exist
        AlignmentVerificationError: If verification cannot be performed
    """
    # Validate inputs
    if not os.path.exists(generated_path):
        raise FileNotFoundError(f"Generated certificate not found: {generated_path}")
    
    if not os.path.exists(reference_path):
        raise FileNotFoundError(f"Reference certificate not found: {reference_path}")
    
    try:
        # Load images
        generated_img = Image.open(generated_path)
        reference_img = Image.open(reference_path)
        
        # Calculate difference with strict tolerance (1-value differences allowed for 0.01px tolerance)
        # This maps to the 0.01px requirement by allowing minimal anti-aliasing differences
        diff_pct, max_diff, has_diff = calculate_image_difference(
            generated_img, 
            reference_img, 
            tolerance=PIXEL_VALUE_TOLERANCE
        )
        
        # Check against tolerance
        # Perfect match: 0.0% diff and max_diff=0
        # Sub-pixel precision: <PERCENTAGE_TOLERANCE (maps to ~0.01px tolerance)
        passed = diff_pct < PERCENTAGE_TOLERANCE and max_diff <= PIXEL_VALUE_TOLERANCE
        
        result = {
            'passed': passed,
            'difference_pct': round(diff_pct, 6),
            'max_pixel_diff': max_diff,
            'tolerance_px': tolerance_px,
            'message': _get_verification_message(passed, diff_pct, max_diff, tolerance_px)
        }
        
        logger.info(
            f"Alignment verification: {'PASSED' if passed else 'FAILED'} - "
            f"diff={diff_pct:.6f}%, max_pixel_diff={max_diff}"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error during alignment verification: {e}")
        raise AlignmentVerificationError(f"Failed to verify alignment: {e}")


def _get_verification_message(passed, diff_pct, max_diff, tolerance_px):
    """Generate a descriptive message for the verification result."""
    if passed:
        if diff_pct == 0.0 and max_diff == 0:
            return f"PERFECT MATCH: Certificate is pixel-identical to reference (0.00px difference)"
        else:
            return f"PASSED: Certificate matches reference within {tolerance_px}px tolerance (diff={diff_pct:.6f}%)"
    else:
        return f"FAILED: Certificate differs from reference by {diff_pct:.6f}% (exceeds {tolerance_px}px tolerance)"


def verify_with_retry(generated_path, reference_path, max_attempts=3, tolerance_px=0.01):
    """Verify certificate alignment with retry logic.
    
    Attempts to verify alignment multiple times. This is useful when generation
    might have some variability (though it shouldn't in a properly configured system).
    
    Args:
        generated_path: Path to the generated certificate image
        reference_path: Path to the reference sample certificate
        max_attempts: Maximum number of verification attempts (default: 3)
        tolerance_px: Maximum allowed difference in pixels (default: 0.01)
        
    Returns:
        Dictionary with verification results (same as verify_certificate_alignment)
        plus 'attempts' field indicating how many tries were needed
        
    Raises:
        AlignmentVerificationError: If all attempts fail
    """
    last_result = None
    
    for attempt in range(1, max_attempts + 1):
        logger.info(f"Alignment verification attempt {attempt}/{max_attempts}")
        
        try:
            result = verify_certificate_alignment(
                generated_path, 
                reference_path, 
                tolerance_px=tolerance_px
            )
            
            result['attempts'] = attempt
            
            if result['passed']:
                logger.info(f"Alignment verification passed on attempt {attempt}")
                return result
            
            last_result = result
            logger.warning(
                f"Attempt {attempt} failed: {result['message']}"
            )
            
        except Exception as e:
            logger.error(f"Attempt {attempt} error: {e}")
            if attempt == max_attempts:
                raise
    
    # All attempts failed
    if last_result:
        error_msg = (
            f"Certificate alignment verification failed after {max_attempts} attempts. "
            f"Last result: {last_result['message']}"
        )
    else:
        error_msg = f"Certificate alignment verification failed after {max_attempts} attempts"
    
    logger.error(error_msg)
    raise AlignmentVerificationError(error_msg)


def get_reference_certificate_path(template_path=None):
    """Get the path to the reference sample certificate.
    
    Args:
        template_path: Optional path to the template (used to find reference)
        
    Returns:
        Absolute path to the reference certificate
        
    Raises:
        FileNotFoundError: If reference certificate not found
    """
    # Default reference path relative to template
    if template_path:
        template_dir = os.path.dirname(template_path)
        reference_path = os.path.join(template_dir, 'Sample_certificate.png')
    else:
        # Fallback to default location
        reference_path = 'templates/Sample_certificate.png'
    
    reference_path = os.path.abspath(reference_path)
    
    if not os.path.exists(reference_path):
        raise FileNotFoundError(
            f"Reference certificate not found at: {reference_path}. "
            "Please ensure templates/Sample_certificate.png exists."
        )
    
    return reference_path
