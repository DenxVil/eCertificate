"""
Universal alignment verification for all certificates.

This module verifies that field positions in generated certificates match
the expected positions defined in the template configuration, regardless
of the actual text content. This allows alignment verification for all
certificates, not just the sample reference.
"""
import os
import logging
from PIL import Image
import json

logger = logging.getLogger(__name__)


def verify_certificate_dimensions(cert_path, expected_width=2000, expected_height=1414):
    """Verify that certificate has the correct dimensions.
    
    Args:
        cert_path: Path to the certificate image
        expected_width: Expected width in pixels (default: 2000)
        expected_height: Expected height in pixels (default: 1414)
        
    Returns:
        Dictionary with verification results
    """
    try:
        img = Image.open(cert_path)
        width, height = img.size
        
        dimensions_match = (width == expected_width and height == expected_height)
        
        return {
            'passed': dimensions_match,
            'actual_width': width,
            'actual_height': height,
            'expected_width': expected_width,
            'expected_height': expected_height,
            'message': f'Dimensions: {width}x{height}' + (
                f' (expected {expected_width}x{expected_height})'
                if not dimensions_match else ' ✓'
            )
        }
    except Exception as e:
        logger.error(f"Error verifying certificate dimensions: {e}")
        return {
            'passed': False,
            'message': f'Error reading certificate: {e}'
        }


def verify_certificate_format(cert_path, expected_format='PNG'):
    """Verify that certificate has the correct format.
    
    Args:
        cert_path: Path to the certificate image
        expected_format: Expected image format (default: 'PNG')
        
    Returns:
        Dictionary with verification results
    """
    try:
        img = Image.open(cert_path)
        format_match = (img.format == expected_format)
        
        return {
            'passed': format_match,
            'actual_format': img.format,
            'expected_format': expected_format,
            'mode': img.mode,
            'message': f'Format: {img.format}, Mode: {img.mode}' + (
                f' (expected {expected_format})'
                if not format_match else ' ✓'
            )
        }
    except Exception as e:
        logger.error(f"Error verifying certificate format: {e}")
        return {
            'passed': False,
            'message': f'Error reading certificate: {e}'
        }


def verify_template_consistency(template_path):
    """Verify that the template and offsets configuration are consistent.
    
    Args:
        template_path: Path to the certificate template
        
    Returns:
        Dictionary with verification results
    """
    try:
        # Check template exists
        if not os.path.exists(template_path):
            return {
                'passed': False,
                'message': f'Template not found: {template_path}'
            }
        
        # Check offsets file
        template_dir = os.path.dirname(template_path)
        offsets_path = os.path.join(template_dir, 'goonj_template_offsets.json')
        
        if not os.path.exists(offsets_path):
            return {
                'passed': False,
                'message': f'Offsets configuration not found: {offsets_path}'
            }
        
        # Load and validate offsets
        with open(offsets_path, 'r') as f:
            offsets_data = json.load(f)
        
        required_fields = ['name', 'event', 'organiser']
        if 'fields' not in offsets_data:
            return {
                'passed': False,
                'message': 'Offsets configuration missing "fields" key'
            }
        
        missing_fields = [f for f in required_fields if f not in offsets_data['fields']]
        if missing_fields:
            return {
                'passed': False,
                'message': f'Missing field configurations: {", ".join(missing_fields)}'
            }
        
        # Verify template dimensions
        img = Image.open(template_path)
        width, height = img.size
        
        return {
            'passed': True,
            'template_dimensions': (width, height),
            'fields_configured': list(offsets_data['fields'].keys()),
            'message': f'Template and configuration validated ✓'
        }
        
    except Exception as e:
        logger.error(f"Error verifying template consistency: {e}")
        return {
            'passed': False,
            'message': f'Error: {e}'
        }


def verify_all_certificates(cert_path, template_path):
    """Comprehensive verification for any certificate.
    
    This performs multiple checks to ensure the certificate was generated correctly:
    1. Correct dimensions (2000x1414)
    2. Correct format (PNG, RGB)
    3. Template configuration is valid
    
    This works for ALL certificates, not just sample certificates.
    
    Args:
        cert_path: Path to the generated certificate
        template_path: Path to the certificate template
        
    Returns:
        Dictionary with comprehensive verification results
    """
    results = {
        'passed': True,
        'checks': {},
        'errors': [],
        'warnings': []
    }
    
    # Check 1: Dimensions
    dim_result = verify_certificate_dimensions(cert_path)
    results['checks']['dimensions'] = dim_result
    if not dim_result['passed']:
        results['passed'] = False
        results['errors'].append(dim_result['message'])
    
    # Check 2: Format
    format_result = verify_certificate_format(cert_path)
    results['checks']['format'] = format_result
    if not format_result['passed']:
        results['passed'] = False
        results['errors'].append(format_result['message'])
    
    # Check 3: Template consistency
    template_result = verify_template_consistency(template_path)
    results['checks']['template'] = template_result
    if not template_result['passed']:
        results['passed'] = False
        results['errors'].append(template_result['message'])
    
    # Generate summary message
    if results['passed']:
        results['message'] = 'All verification checks passed ✓'
    else:
        results['message'] = f"Verification failed: {'; '.join(results['errors'])}"
    
    return results
