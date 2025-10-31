"""
Field position verification for certificates.

This module verifies that text fields in generated certificates are positioned
at the same Y-coordinates as in the reference sample_certificate.png, ensuring
consistent vertical alignment across all certificates.
"""
import os
import logging
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)

# Constants for text detection
TEXT_THRESHOLD = 200  # Pixel brightness threshold for detecting text (0-255)
MIN_TEXT_PIXELS = 50  # Minimum number of dark pixels per row to consider it text


def find_text_field_positions(img_path, height=1414):
    """
    Find the Y-coordinates of the three main text fields in a certificate.
    
    Args:
        img_path: Path to certificate image
        height: Expected image height (default: 1414)
        
    Returns:
        Dictionary with field positions:
        {
            'name': {'y_center': int, 'y_start': int, 'y_end': int},
            'event': {'y_center': int, 'y_start': int, 'y_end': int},
            'organiser': {'y_center': int, 'y_start': int, 'y_end': int}
        }
    """
    img = Image.open(img_path).convert('L')  # Convert to grayscale
    arr = np.array(img)
    img_height, img_width = arr.shape
    
    # Define search windows for each field based on expected positions
    # Name: around 28.4% of height (y=401px for 1414px height)
    # Event: around 49.6% of height (y=701px for 1414px height)
    # Organiser: around 60.3% of height (y=852px for 1414px height)
    windows = [
        (int(img_height * 0.20), int(img_height * 0.35), "name"),      # 283-495
        (int(img_height * 0.43), int(img_height * 0.55), "event"),     # 608-778
        (int(img_height * 0.55), int(img_height * 0.67), "organiser")  # 778-947
    ]
    
    results = {}
    
    for y_start, y_end, field_name in windows:
        # Get a horizontal slice of the image
        slice_arr = arr[y_start:y_end, :]
        
        # Count dark pixels (text) in each row
        # Text pixels are typically darker than background
        dark_pixels_per_row = np.sum(slice_arr < TEXT_THRESHOLD, axis=1)
        
        # Find rows with significant text content
        text_rows = np.where(dark_pixels_per_row > MIN_TEXT_PIXELS)[0]
        
        if len(text_rows) > 0:
            text_start = y_start + text_rows[0]
            text_end = y_start + text_rows[-1]
            text_center = (text_start + text_end) // 2
            
            results[field_name] = {
                'y_center': text_center,
                'y_start': text_start,
                'y_end': text_end,
                'height': text_end - text_start
            }
        else:
            # No text found in this window
            logger.warning(f"No text found for field '{field_name}' in window {y_start}-{y_end}")
            results[field_name] = None
    
    return results


def verify_field_positions(generated_path, reference_path, tolerance_px=2):
    """
    Verify that field positions in generated certificate match the reference.
    
    This checks that the Y-coordinates of text fields (name, event, organiser)
    are within the specified tolerance of the reference sample_certificate.png.
    
    Args:
        generated_path: Path to generated certificate
        reference_path: Path to reference sample (sample_certificate.png)
        tolerance_px: Maximum allowed Y-coordinate difference in pixels (default: 2)
        
    Returns:
        Dictionary with verification results:
        {
            'passed': bool,
            'fields': {
                'name': {'offset': int, 'passed': bool},
                'event': {'offset': int, 'passed': bool},
                'organiser': {'offset': int, 'passed': bool}
            },
            'max_offset': int,
            'message': str
        }
    """
    # Validate inputs
    if not os.path.exists(generated_path):
        raise FileNotFoundError(f"Generated certificate not found: {generated_path}")
    
    if not os.path.exists(reference_path):
        raise FileNotFoundError(f"Reference certificate not found: {reference_path}")
    
    # Find field positions in both certificates
    generated_fields = find_text_field_positions(generated_path)
    reference_fields = find_text_field_positions(reference_path)
    
    # Compare positions
    field_results = {}
    offsets = []
    all_passed = True
    
    for field_name in ['name', 'event', 'organiser']:
        gen_field = generated_fields.get(field_name)
        ref_field = reference_fields.get(field_name)
        
        if gen_field is None or ref_field is None:
            field_results[field_name] = {
                'offset': None,
                'passed': False,
                'error': 'Field not detected'
            }
            all_passed = False
            continue
        
        # Calculate Y-coordinate offset
        offset = gen_field['y_center'] - ref_field['y_center']
        offsets.append(abs(offset))
        passed = abs(offset) <= tolerance_px
        
        field_results[field_name] = {
            'offset': offset,
            'generated_y': gen_field['y_center'],
            'reference_y': ref_field['y_center'],
            'passed': passed
        }
        
        if not passed:
            all_passed = False
    
    # Calculate maximum offset
    max_offset = max(offsets) if offsets else None
    
    # Generate message
    if all_passed:
        if max_offset == 0:
            message = "PERFECT: All fields positioned exactly at reference coordinates (0px offset)"
        else:
            message = f"PASSED: All fields within {tolerance_px}px tolerance (max offset: {max_offset}px)"
    else:
        failed_fields = [name for name, result in field_results.items() if not result['passed']]
        message = f"FAILED: Fields outside tolerance: {', '.join(failed_fields)} (max offset: {max_offset}px, tolerance: {tolerance_px}px)"
    
    return {
        'passed': all_passed,
        'fields': field_results,
        'max_offset': max_offset,
        'tolerance_px': tolerance_px,
        'message': message
    }
