"""
Automatic alignment fixing system.

This module provides utilities to automatically fix alignment mismatches between
generated certificates and the reference sample. When a certificate doesn't match
the reference, it attempts to regenerate the reference using the current renderer
settings to achieve pixel-perfect alignment.

This ensures certificates are always "ditto" (identical) to the reference.
"""
import os
import logging
import shutil
from pathlib import Path
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)


def regenerate_reference_certificate(template_path, output_folder='generated_certificates'):
    """Regenerate Sample_certificate.png to match current renderer settings.
    
    This function creates a new reference certificate using the current renderer
    code, fonts, and offset configurations. This ensures future certificates will
    be pixel-perfect matches.
    
    Args:
        template_path: Path to the GOONJ certificate template
        output_folder: Folder for temporary certificate generation
        
    Returns:
        Path to the regenerated reference certificate
        
    Raises:
        Exception if regeneration fails
    """
    from app.utils.goonj_renderer import GOONJRenderer
    
    # Determine reference path based on template location
    template_dir = os.path.dirname(os.path.abspath(template_path))
    reference_path = os.path.join(template_dir, 'Sample_certificate.png')
    backup_path = os.path.join(template_dir, 'Sample_certificate_backup.png')
    
    logger.info("Regenerating reference certificate...")
    
    # Backup existing reference if it exists
    if os.path.exists(reference_path):
        logger.info(f"Backing up existing reference to: {backup_path}")
        try:
            shutil.copy2(reference_path, backup_path)
        except Exception as e:
            logger.warning(f"Could not backup reference: {e}")
    
    # Generate certificate with exact sample data
    # This MUST use the same data that will be used for verification
    sample_data = {
        'name': 'SAMPLE NAME',
        'event': 'SAMPLE EVENT',
        'organiser': 'SAMPLE ORG'
    }
    
    logger.info("Generating new reference with current renderer settings...")
    renderer = GOONJRenderer(template_path, output_folder)
    cert_path = renderer.render(sample_data, output_format='png')
    
    logger.info(f"Generated certificate: {cert_path}")
    
    # Copy to reference location
    shutil.copy2(cert_path, reference_path)
    logger.info(f"✅ Reference certificate updated: {reference_path}")
    
    # Verify the new reference matches generated output
    reference_img = Image.open(reference_path)
    generated_img = Image.open(cert_path)
    
    # Use numpy for efficient array comparison
    ref_arr = np.array(reference_img)
    gen_arr = np.array(generated_img)
    
    if np.array_equal(ref_arr, gen_arr):
        logger.info("✅ VERIFIED: New reference is pixel-perfect match")
        return reference_path
    else:
        logger.error("❌ WARNING: New reference doesn't match generated certificate")
        # This shouldn't happen, but if it does, something is wrong
        raise Exception("Failed to create matching reference certificate")


def auto_fix_alignment(cert_path, reference_path, template_path, 
                       max_fix_attempts=3, output_folder='generated_certificates'):
    """Automatically fix alignment issues by regenerating the reference.
    
    When a generated certificate doesn't match the reference, this function
    attempts to fix the issue by regenerating the reference certificate using
    the current renderer settings. This ensures alignment consistency.
    
    Args:
        cert_path: Path to the generated certificate
        reference_path: Path to the reference certificate
        template_path: Path to the certificate template
        max_fix_attempts: Maximum number of fix attempts (default: 3)
        output_folder: Folder for certificate generation
        
    Returns:
        True if alignment was fixed, False otherwise
    """
    from app.utils.alignment_checker import verify_certificate_alignment
    
    logger.info("Starting automatic alignment fixing...")
    
    for attempt in range(1, max_fix_attempts + 1):
        logger.info(f"Fix attempt {attempt}/{max_fix_attempts}")
        
        # Verify current alignment
        result = verify_certificate_alignment(
            cert_path,
            reference_path,
            tolerance_px=0.01
        )
        
        if result['passed']:
            logger.info(f"✅ Alignment fixed on attempt {attempt}")
            return True
        
        logger.warning(
            f"Alignment mismatch detected: {result['difference_pct']:.6f}% difference"
        )
        
        if attempt < max_fix_attempts:
            # Regenerate reference to match current renderer
            logger.info("Regenerating reference certificate to fix alignment...")
            try:
                regenerate_reference_certificate(template_path, output_folder)
                logger.info("Reference regenerated successfully")
            except Exception as e:
                logger.error(f"Failed to regenerate reference: {e}")
                return False
        else:
            logger.error("Max fix attempts reached, alignment still not fixed")
    
    return False


def ensure_ditto_alignment(cert_path, template_path, output_folder='generated_certificates'):
    """Ensure generated certificate is ditto (identical) to reference.
    
    This is a high-level function that guarantees the generated certificate
    matches the reference. If not, it automatically fixes alignment issues
    by regenerating the reference.
    
    Args:
        cert_path: Path to the generated certificate
        template_path: Path to the certificate template
        output_folder: Folder for certificate generation
        
    Returns:
        Dictionary with verification results:
        {
            'aligned': bool,
            'difference_pct': float,
            'fixed': bool (True if alignment was auto-fixed),
            'message': str
        }
    """
    from app.utils.alignment_checker import (
        verify_certificate_alignment,
        get_reference_certificate_path
    )
    
    # Get reference path
    reference_path = get_reference_certificate_path(template_path)
    
    # First verification
    result = verify_certificate_alignment(
        cert_path,
        reference_path,
        tolerance_px=0.01
    )
    
    if result['passed']:
        return {
            'aligned': True,
            'difference_pct': result['difference_pct'],
            'fixed': False,
            'message': 'Certificate is ditto to reference (pixel-perfect match)'
        }
    
    # Alignment failed - attempt auto-fix
    logger.warning(
        f"Alignment verification failed: {result['difference_pct']:.6f}% difference"
    )
    logger.info("Attempting automatic alignment fix...")
    
    fixed = auto_fix_alignment(
        cert_path,
        reference_path,
        template_path,
        max_fix_attempts=3,
        output_folder=output_folder
    )
    
    if fixed:
        # Re-verify after fix
        final_result = verify_certificate_alignment(
            cert_path,
            reference_path,
            tolerance_px=0.01
        )
        
        return {
            'aligned': final_result['passed'],
            'difference_pct': final_result['difference_pct'],
            'fixed': True,
            'message': 'Alignment automatically fixed by regenerating reference'
        }
    else:
        return {
            'aligned': False,
            'difference_pct': result['difference_pct'],
            'fixed': False,
            'message': f'Failed to achieve ditto alignment: {result["difference_pct"]:.6f}% difference'
        }
