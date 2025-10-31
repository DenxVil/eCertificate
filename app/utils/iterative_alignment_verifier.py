"""
Iterative alignment verification system for certificate generation.

This module implements a retry-based approach to ensure generated certificates
match the reference sample_certificate.png with sub-pixel precision (<=0.02px difference).
"""
import os
import logging
from PIL import Image
import numpy as np
from typing import Dict, Any, Optional, Tuple
import time

logger = logging.getLogger(__name__)


def extract_field_positions(img_path: str) -> Dict[str, Dict[str, float]]:
    """
    Extract precise field positions from a certificate image.
    
    Args:
        img_path: Path to certificate image
        
    Returns:
        Dictionary with field positions and their coordinates
    """
    img = Image.open(img_path).convert('L')
    arr = np.array(img)
    height, width = arr.shape
    
    # Define search windows for the three main fields
    windows = [
        (int(height * 0.20), int(height * 0.40), "name"),
        (int(height * 0.40), int(height * 0.58), "event"),
        (int(height * 0.55), int(height * 0.70), "organiser")
    ]
    
    threshold = 200
    min_dark_pixels = 100
    
    results = {}
    
    for y_start, y_end, field_name in windows:
        slice_arr = arr[y_start:y_end, :]
        dark_pixels_per_row = np.sum(slice_arr < threshold, axis=1)
        
        # Find rows with significant text
        text_rows = np.where(dark_pixels_per_row > min_dark_pixels)[0]
        
        if len(text_rows) > 0:
            text_start = y_start + text_rows[0]
            text_end = y_start + text_rows[-1]
            text_center = (text_start + text_end) / 2  # Sub-pixel precision
            
            # Calculate horizontal center
            text_region = arr[text_start:text_end+1, :]
            dark_pixels_per_col = np.sum(text_region < threshold, axis=0)
            text_cols = np.where(dark_pixels_per_col > 10)[0]
            
            if len(text_cols) > 0:
                text_left = text_cols[0]
                text_right = text_cols[-1]
                text_center_x = (text_left + text_right) / 2
            else:
                text_center_x = width / 2
            
            results[field_name] = {
                'y_center': text_center,
                'x_center': text_center_x,
                'y_start': text_start,
                'y_end': text_end,
                'normalized_y': text_center / height,
                'normalized_x': text_center_x / width
            }
            logger.debug(f"Field '{field_name}' detected at y={text_center:.2f}, x={text_center_x:.2f}")
        else:
            logger.warning(f"Field '{field_name}' NOT detected in search window y={y_start}-{y_end}")
    
    # Log summary of detected fields
    detected_fields = list(results.keys())
    missing_fields = [f for f in ['name', 'event', 'organiser'] if f not in detected_fields]
    
    if missing_fields:
        logger.error(f"Missing fields in {img_path}: {', '.join(missing_fields)}")
    
    return results


def calculate_position_difference(
    generated_positions: Dict[str, Dict[str, float]],
    reference_positions: Dict[str, Dict[str, float]]
) -> Dict[str, Any]:
    """
    Calculate the maximum position difference between generated and reference.
    
    Args:
        generated_positions: Field positions from generated certificate
        reference_positions: Field positions from reference certificate
        
    Returns:
        Dictionary with difference metrics including errors for missing fields
    """
    differences = {}
    max_diff = 0.0
    missing_fields = []
    
    # Check all three required fields
    for field_name in ['name', 'event', 'organiser']:
        gen_field = generated_positions.get(field_name)
        ref_field = reference_positions.get(field_name)
        
        # Check if field is missing in either certificate
        if gen_field is None or ref_field is None:
            missing_fields.append(field_name)
            differences[field_name] = {
                'error': 'Field not detected',
                'detected_in_generated': gen_field is not None,
                'detected_in_reference': ref_field is not None
            }
            # Treat missing field as maximum error
            max_diff = float('inf')
            continue
        
        # Calculate position differences for detected fields
        y_diff = abs(gen_field['y_center'] - ref_field['y_center'])
        x_diff = abs(gen_field['x_center'] - ref_field['x_center'])
        
        differences[field_name] = {
            'y_diff': y_diff,
            'x_diff': x_diff,
            'y_center_gen': gen_field['y_center'],
            'y_center_ref': ref_field['y_center'],
            'x_center_gen': gen_field['x_center'],
            'x_center_ref': ref_field['x_center']
        }
        
        # Track maximum difference
        max_diff = max(max_diff, y_diff, x_diff)
    
    result = {
        'fields': differences,
        'max_difference_px': max_diff
    }
    
    # Add warning about missing fields
    if missing_fields:
        result['missing_fields'] = missing_fields
        result['error'] = f"Missing fields: {', '.join(missing_fields)}"
    
    return result


def verify_alignment_with_retries(
    generated_cert_path: str,
    reference_cert_path: str,
    tolerance_px: float = 0.02,
    max_attempts: int = 30,
    regenerate_func: Optional[callable] = None,
    progress_callback: Optional[callable] = None
) -> Dict[str, Any]:
    """
    Verify certificate alignment with retry logic.
    
    This function attempts to verify alignment up to max_attempts times,
    optionally regenerating the certificate if alignment fails.
    If max attempts is reached without passing, it returns the certificate
    with the best (closest) alignment.
    
    Args:
        generated_cert_path: Path to generated certificate
        reference_cert_path: Path to reference sample certificate
        tolerance_px: Maximum allowed difference in pixels (default: 0.02)
        max_attempts: Maximum number of verification attempts (default: 30)
        regenerate_func: Optional function to regenerate certificate on failure
        progress_callback: Optional callback for progress updates (receives attempt number)
        
    Returns:
        Dictionary with verification results:
        {
            'passed': bool,
            'attempts': int,
            'max_difference_px': float,
            'fields': dict,
            'message': str,
            'best_attempt': dict (if max attempts reached without passing)
        }
    """
    if not os.path.exists(reference_cert_path):
        raise FileNotFoundError(f"Reference certificate not found: {reference_cert_path}")
    
    # Extract reference positions once
    logger.info(f"Extracting reference positions from {reference_cert_path}")
    reference_positions = extract_field_positions(reference_cert_path)
    
    # Track all attempts to find the best one
    all_attempts = []
    best_attempt = None
    
    for attempt in range(1, max_attempts + 1):
        try:
            # Notify progress
            if progress_callback:
                progress_callback(attempt, max_attempts)
            
            logger.info(f"Alignment verification attempt {attempt}/{max_attempts}")
            
            # Check if generated certificate exists
            if not os.path.exists(generated_cert_path):
                logger.warning(f"Generated certificate not found: {generated_cert_path}")
                if regenerate_func and attempt < max_attempts:
                    logger.info("Regenerating certificate...")
                    regenerate_func()
                    continue
                else:
                    return {
                        'passed': False,
                        'attempts': attempt,
                        'max_difference_px': float('inf'),
                        'fields': {},
                        'message': f'Certificate file not found after {attempt} attempts'
                    }
            
            # Extract generated positions
            generated_positions = extract_field_positions(generated_cert_path)
            
            # Calculate differences
            diff_result = calculate_position_difference(generated_positions, reference_positions)
            max_diff = diff_result['max_difference_px']
            
            # Log individual field differences for debugging
            if 'missing_fields' in diff_result:
                logger.error(f"Attempt {attempt}: {diff_result['error']}")
            
            # Log each field's alignment
            for field_name in ['name', 'event', 'organiser']:
                if field_name in diff_result['fields']:
                    field_diff = diff_result['fields'][field_name]
                    if 'error' in field_diff:
                        logger.warning(f"  {field_name}: {field_diff['error']}")
                    else:
                        logger.info(
                            f"  {field_name}: y_diff={field_diff['y_diff']:.2f}px, "
                            f"x_diff={field_diff['x_diff']:.2f}px"
                        )
            
            logger.info(f"Attempt {attempt}: Max difference = {max_diff:.4f} px (tolerance: {tolerance_px} px)")
            
            # Store this attempt's result
            attempt_result = {
                'attempt_number': attempt,
                'max_difference_px': max_diff,
                'fields': diff_result['fields'],
                'cert_path': generated_cert_path
            }
            all_attempts.append(attempt_result)
            
            # Track the best attempt so far
            if best_attempt is None or max_diff < best_attempt['max_difference_px']:
                best_attempt = attempt_result
            
            # Check if within tolerance
            if max_diff <= tolerance_px:
                message = f"PASSED: Alignment verified on attempt {attempt}/{max_attempts}. Max difference: {max_diff:.4f} px (<= {tolerance_px} px)"
                logger.info(f"✅ {message}")
                
                return {
                    'passed': True,
                    'attempts': attempt,
                    'max_difference_px': max_diff,
                    'fields': diff_result['fields'],
                    'message': message,
                    'tolerance_px': tolerance_px,
                    'all_attempts': all_attempts
                }
            else:
                logger.warning(f"Attempt {attempt} failed: {max_diff:.4f} px > {tolerance_px} px")
                
                # If we have a regenerate function and haven't exhausted attempts, try again
                if regenerate_func and attempt < max_attempts:
                    logger.info("Regenerating certificate for next attempt...")
                    # Small delay to avoid issues
                    time.sleep(0.1)
                    regenerate_func()
                else:
                    # Last attempt or no regenerate function
                    if attempt == max_attempts:
                        # Return the best attempt instead of failing completely
                        message = f"MAX ATTEMPTS REACHED: Using best alignment from {best_attempt['attempt_number']} attempts. Max difference: {best_attempt['max_difference_px']:.4f} px (tolerance: {tolerance_px} px)"
                        logger.warning(f"⚠️ {message}")
                        
                        return {
                            'passed': False,
                            'attempts': attempt,
                            'max_difference_px': best_attempt['max_difference_px'],
                            'fields': best_attempt['fields'],
                            'message': message,
                            'tolerance_px': tolerance_px,
                            'best_attempt': best_attempt,
                            'all_attempts': all_attempts,
                            'used_best_available': True
                        }
        
        except Exception as e:
            logger.exception(f"Error during alignment verification attempt {attempt}: {e}")
            if attempt == max_attempts:
                return {
                    'passed': False,
                    'attempts': attempt,
                    'max_difference_px': float('inf'),
                    'fields': {},
                    'message': f'Verification error on attempt {attempt}'
                }
            # Continue to next attempt
            continue
    
    # Should not reach here, but return failure just in case
    return {
        'passed': False,
        'attempts': max_attempts,
        'max_difference_px': float('inf'),
        'fields': {},
        'message': 'Verification failed: Unknown error'
    }
