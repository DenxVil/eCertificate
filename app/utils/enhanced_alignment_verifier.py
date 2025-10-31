"""
Enhanced alignment verification with all advanced features.

This module integrates:
- Position caching
- Progressive refinement
- Statistics tracking
- Original iterative verification

For backward compatibility and gradual rollout.
"""
import os
import logging
from typing import Dict, Any, Optional, Callable

from .iterative_alignment_verifier import (
    extract_field_positions,
    calculate_position_difference,
    verify_alignment_with_retries as _original_verify
)
from .position_cache import get_position_cache
from .progressive_refiner import ProgressiveRefiner, apply_progressive_refinement
from .alignment_stats import get_alignment_stats

logger = logging.getLogger(__name__)


def verify_alignment_enhanced(
    generated_cert_path: str,
    reference_cert_path: str,
    participant_data: Dict[str, str],
    tolerance_px: float = 0.02,
    max_attempts: int = 30,
    regenerate_func: Optional[Callable] = None,
    progress_callback: Optional[Callable] = None,
    enable_cache: bool = True,
    enable_progressive: bool = True,
    enable_stats: bool = True
) -> Dict[str, Any]:
    """
    Enhanced alignment verification with caching, progressive refinement, and statistics.
    
    Args:
        generated_cert_path: Path to generated certificate
        reference_cert_path: Path to reference sample certificate
        participant_data: Dictionary with name, event, organiser fields
        tolerance_px: Maximum allowed difference in pixels (default: 0.02)
        max_attempts: Maximum number of verification attempts (default: 30)
        regenerate_func: Optional function to regenerate certificate on failure
        progress_callback: Optional callback for progress updates
        enable_cache: Enable position caching (default: True)
        enable_progressive: Enable progressive refinement (default: True)
        enable_stats: Enable statistics tracking (default: True)
        
    Returns:
        Dictionary with verification results (same as original + enhancement info)
    """
    # Initialize enhancement modules
    cache = get_position_cache() if enable_cache else None
    refiner = ProgressiveRefiner(tolerance_px) if enable_progressive else None
    stats_tracker = get_alignment_stats() if enable_stats else None
    
    # Check cache first
    if cache:
        cached_data = cache.get(participant_data)
        if cached_data:
            logger.info("Using cached position data - skipping alignment verification")
            # Still verify to ensure cache is valid
            generated_positions = extract_field_positions(generated_cert_path)
            reference_positions = extract_field_positions(reference_cert_path)
            diff_result = calculate_position_difference(generated_positions, reference_positions)
            
            if diff_result['max_difference_px'] <= tolerance_px:
                logger.info("✅ Cache hit resulted in perfect alignment!")
                
                result = {
                    'passed': True,
                    'attempts': 1,
                    'max_difference_px': diff_result['max_difference_px'],
                    'fields': diff_result['fields'],
                    'message': f"CACHED: Perfect alignment from cache (diff={diff_result['max_difference_px']:.4f}px)",
                    'used_cache': True
                }
                
                if stats_tracker:
                    stats_tracker.record_verification(
                        passed=True,
                        attempts=1,
                        max_difference_px=diff_result['max_difference_px'],
                        field_differences=diff_result['fields'],
                        tolerance_px=tolerance_px,
                        participant_data=participant_data
                    )
                
                return result
            else:
                logger.warning("Cache data did not produce valid alignment - proceeding with verification")
    
    # Use progressive refinement or fall back to original
    if enable_progressive and refiner and regenerate_func:
        logger.info("Using progressive refinement for alignment verification")
        result = _verify_with_progressive_refinement(
            generated_cert_path=generated_cert_path,
            reference_cert_path=reference_cert_path,
            tolerance_px=tolerance_px,
            max_attempts=max_attempts,
            regenerate_func=regenerate_func,
            progress_callback=progress_callback,
            refiner=refiner
        )
        result['used_progressive'] = True
    else:
        # Fall back to original verification
        logger.info("Using standard iterative alignment verification")
        result = _original_verify(
            generated_cert_path=generated_cert_path,
            reference_cert_path=reference_cert_path,
            tolerance_px=tolerance_px,
            max_attempts=max_attempts,
            regenerate_func=regenerate_func,
            progress_callback=progress_callback
        )
        result['used_progressive'] = False
    
    # Cache successful alignment
    if cache and result['passed']:
        cache_data = {
            'max_difference_px': result['max_difference_px'],
            'attempts': result['attempts'],
            'fields': result['fields']
        }
        cache.set(participant_data, cache_data)
        logger.info("Cached successful alignment data")
    
    # Record statistics
    if stats_tracker:
        stats_tracker.record_verification(
            passed=result['passed'],
            attempts=result['attempts'],
            max_difference_px=result.get('max_difference_px', float('inf')),
            field_differences=result.get('fields', {}),
            tolerance_px=tolerance_px,
            participant_data=participant_data
        )
    
    return result


def _verify_with_progressive_refinement(
    generated_cert_path: str,
    reference_cert_path: str,
    tolerance_px: float,
    max_attempts: int,
    regenerate_func: Callable,
    progress_callback: Optional[Callable],
    refiner: ProgressiveRefiner
) -> Dict[str, Any]:
    """
    Verify alignment using progressive refinement.
    
    This is an internal function that implements progressive refinement logic.
    """
    if not os.path.exists(reference_cert_path):
        raise FileNotFoundError(f"Reference certificate not found: {reference_cert_path}")
    
    # Extract reference positions once
    logger.info(f"Extracting reference positions from {reference_cert_path}")
    reference_positions = extract_field_positions(reference_cert_path)
    
    # Track all attempts
    all_attempts = []
    best_attempt = None
    
    for attempt in range(1, max_attempts + 1):
        try:
            # Notify progress
            if progress_callback:
                progress_callback(attempt, max_attempts)
            
            logger.info(f"Progressive refinement attempt {attempt}/{max_attempts}")
            
            # Check if generated certificate exists
            if not os.path.exists(generated_cert_path):
                logger.warning(f"Generated certificate not found: {generated_cert_path}")
                if attempt < max_attempts:
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
            
            # Log individual field differences
            if 'missing_fields' in diff_result:
                logger.error(f"Attempt {attempt}: {diff_result['error']}")
            
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
            
            # Store this attempt
            attempt_result = {
                'attempt_number': attempt,
                'max_difference_px': max_diff,
                'fields': diff_result['fields'],
                'cert_path': generated_cert_path
            }
            all_attempts.append(attempt_result)
            
            # Track best attempt
            if best_attempt is None or max_diff < best_attempt['max_difference_px']:
                best_attempt = attempt_result
            
            # Check if within tolerance
            if max_diff <= tolerance_px:
                message = f"PASSED: Progressive refinement converged on attempt {attempt}/{max_attempts}. Max difference: {max_diff:.4f} px"
                logger.info(f"✅ {message}")
                
                return {
                    'passed': True,
                    'attempts': attempt,
                    'max_difference_px': max_diff,
                    'fields': diff_result['fields'],
                    'message': message,
                    'tolerance_px': tolerance_px,
                    'all_attempts': all_attempts,
                    'refiner_stats': refiner.get_stats()
                }
            
            # Check if we should abort due to non-convergence
            if refiner.should_abort():
                message = f"Progressive refinement not converging after {attempt} attempts. Using best available."
                logger.warning(message)
                
                return {
                    'passed': False,
                    'attempts': attempt,
                    'max_difference_px': best_attempt['max_difference_px'],
                    'fields': best_attempt['fields'],
                    'message': message,
                    'tolerance_px': tolerance_px,
                    'best_attempt': best_attempt,
                    'all_attempts': all_attempts,
                    'used_best_available': True,
                    'refiner_stats': refiner.get_stats()
                }
            
            # Apply progressive refinement for next attempt
            if attempt < max_attempts:
                logger.info("Applying progressive refinement for next attempt...")
                # TODO: Integrate with renderer to apply adjustments
                # For now, just regenerate
                regenerate_func()
        
        except Exception as e:
            logger.exception(f"Error during progressive refinement attempt {attempt}: {e}")
            if attempt == max_attempts:
                return {
                    'passed': False,
                    'attempts': attempt,
                    'max_difference_px': float('inf'),
                    'fields': {},
                    'message': f'Verification error on attempt {attempt}: {e}'
                }
            continue
    
    # Max attempts reached
    if best_attempt:
        message = f"MAX ATTEMPTS REACHED: Using best alignment from {best_attempt['attempt_number']} attempts. Max difference: {best_attempt['max_difference_px']:.4f} px"
        logger.warning(f"⚠️ {message}")
        
        return {
            'passed': False,
            'attempts': max_attempts,
            'max_difference_px': best_attempt['max_difference_px'],
            'fields': best_attempt['fields'],
            'message': message,
            'tolerance_px': tolerance_px,
            'best_attempt': best_attempt,
            'all_attempts': all_attempts,
            'used_best_available': True,
            'refiner_stats': refiner.get_stats()
        }
    
    return {
        'passed': False,
        'attempts': max_attempts,
        'max_difference_px': float('inf'),
        'fields': {},
        'message': 'Verification failed: Unknown error'
    }
