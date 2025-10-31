"""Certificate Validator - Validates certificate text alignment and positioning.

This module provides validation and visual comparison tools for certificate generation,
ensuring that text fields are positioned correctly according to template specifications.
"""
import os
import json
from PIL import Image, ImageDraw, ImageFont
import logging

logger = logging.getLogger(__name__)

# Try to import pytesseract for OCR (optional)
try:
    import pytesseract
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False
    logger.debug("pytesseract not available - OCR-based validation disabled")


def validate(generated_path, template_ref_path=None, expected_positions=None, tolerance_px=3):
    """Validate certificate text alignment against expected positions.
    
    Args:
        generated_path: Path to the generated certificate image
        template_ref_path: Path to reference template image (optional)
        expected_positions: Dict of expected field positions (optional)
                           Format: {'field_name': {'x': normalized, 'y': normalized}}
        tolerance_px: Maximum allowed pixel offset (default: 3)
    
    Returns:
        Dictionary with validation results:
        {
            'pass': bool,
            'details': {
                'field_name': {
                    'gen_px': (x, y),
                    'ref_px': (x, y),
                    'dx': int,
                    'dy': int,
                    'distance': float,
                    'ok': bool
                }
            },
            'overlay_path': str (path to comparison overlay image)
        }
    """
    if not os.path.exists(generated_path):
        raise FileNotFoundError(f"Generated certificate not found: {generated_path}")
    
    # Load generated certificate
    gen_img = Image.open(generated_path).convert('RGB')
    width, height = gen_img.size
    
    # Get expected positions
    if expected_positions is None:
        expected_positions = _load_expected_positions(template_ref_path)
    
    # If still no positions, use defaults
    if not expected_positions:
        logger.warning("No expected positions found, using default positions")
        expected_positions = {
            'name': {'x': 0.5, 'y': 0.33},
            'event': {'x': 0.5, 'y': 0.42},
            'organiser': {'x': 0.5, 'y': 0.51}
        }
    
    # Detect actual positions in generated certificate
    detected_positions = _detect_text_positions(gen_img, expected_positions)
    
    # Compare positions and compute offsets
    details = {}
    all_ok = True
    
    for field_name, expected in expected_positions.items():
        # Convert normalized to pixel coordinates
        ref_px = (int(expected['x'] * width), int(expected['y'] * height))
        
        # Get detected position (or use expected if detection failed)
        detected = detected_positions.get(field_name, expected)
        gen_px = (int(detected['x'] * width), int(detected['y'] * height))
        
        # Calculate offsets
        dx = gen_px[0] - ref_px[0]
        dy = gen_px[1] - ref_px[1]
        distance = (dx**2 + dy**2)**0.5
        
        # Check if within tolerance
        ok = abs(dx) <= tolerance_px and abs(dy) <= tolerance_px
        all_ok = all_ok and ok
        
        details[field_name] = {
            'gen_px': gen_px,
            'ref_px': ref_px,
            'dx': dx,
            'dy': dy,
            'distance': round(distance, 2),
            'ok': ok
        }
    
    # Generate overlay visualization
    overlay_path = _generate_overlay(
        gen_img, 
        details, 
        generated_path,
        tolerance_px
    )
    
    return {
        'pass': all_ok,
        'details': details,
        'overlay_path': overlay_path,
        'tolerance_px': tolerance_px
    }


def _load_expected_positions(template_ref_path=None):
    """Load expected field positions from JSON configuration.
    
    Args:
        template_ref_path: Optional path to template (used to locate offsets JSON)
    
    Returns:
        Dictionary of field positions or None if not found
    """
    # Try to find offsets JSON file
    offsets_path = None
    
    if template_ref_path:
        # Look for offsets file next to template
        template_dir = os.path.dirname(template_ref_path)
        offsets_path = os.path.join(template_dir, 'goonj_template_offsets.json')
    
    # Also try templates/ directory in current working directory
    if not offsets_path or not os.path.exists(offsets_path):
        offsets_path = 'templates/goonj_template_offsets.json'
    
    if os.path.exists(offsets_path):
        try:
            with open(offsets_path, 'r') as f:
                data = json.load(f)
                if 'fields' in data:
                    positions = {}
                    for field_name, field_data in data['fields'].items():
                        positions[field_name] = {
                            'x': field_data['x'],
                            'y': field_data['y']
                        }
                    logger.info(f"Loaded expected positions from {offsets_path}")
                    return positions
        except Exception as e:
            logger.warning(f"Could not load positions from {offsets_path}: {e}")
    
    return None


def _detect_text_positions(image, expected_positions):
    """Detect actual text positions in the generated certificate.
    
    Uses OCR if available, otherwise estimates based on expected positions.
    
    Args:
        image: PIL Image object of the certificate
        expected_positions: Dict of expected positions for guidance
    
    Returns:
        Dictionary of detected positions (normalized coordinates)
    """
    if not PYTESSERACT_AVAILABLE:
        # Without OCR, return expected positions as fallback
        logger.debug("OCR not available, using expected positions")
        return expected_positions
    
    # Try to use OCR to detect text positions
    try:
        width, height = image.size
        
        # Get OCR data with bounding boxes
        ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        
        detected = {}
        
        # Search for text in expected regions
        for field_name, expected in expected_positions.items():
            # Define search region around expected position
            search_y = int(expected['y'] * height)
            search_range = int(height * 0.1)  # Search within 10% of height
            
            # Find text boxes in this region
            best_match = None
            best_confidence = 0
            
            for i, conf in enumerate(ocr_data['conf']):
                if conf > 0:  # Valid detection
                    box_y = ocr_data['top'][i] + ocr_data['height'][i] // 2
                    if abs(box_y - search_y) < search_range:
                        if conf > best_confidence:
                            best_confidence = conf
                            box_x = ocr_data['left'][i] + ocr_data['width'][i] // 2
                            best_match = {
                                'x': box_x / width,
                                'y': box_y / height
                            }
            
            if best_match:
                detected[field_name] = best_match
            else:
                # Use expected position as fallback
                detected[field_name] = expected
        
        return detected
        
    except Exception as e:
        logger.warning(f"OCR detection failed: {e}, using expected positions")
        return expected_positions


def _generate_overlay(image, details, original_path, tolerance_px):
    """Generate visual overlay showing alignment validation.
    
    Args:
        image: PIL Image object
        details: Validation details dictionary
        original_path: Path to original generated certificate
        tolerance_px: Tolerance in pixels
    
    Returns:
        Path to saved overlay image
    """
    # Create overlay image
    overlay = image.copy()
    draw = ImageDraw.Draw(overlay)
    
    # Load a font for labels
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except (OSError, IOError):
        font = ImageFont.load_default()
    
    # Draw markers and comparison lines
    for field_name, data in details.items():
        gen_px = data['gen_px']
        ref_px = data['ref_px']
        ok = data['ok']
        
        # Color: green if OK, red if not
        color = (0, 255, 0) if ok else (255, 0, 0)
        
        # Draw reference position marker (circle)
        _draw_crosshair(draw, ref_px, color=(0, 0, 255), size=15)
        
        # Draw generated position marker (X)
        _draw_crosshair(draw, gen_px, color=color, size=20)
        
        # Draw connecting line
        draw.line([ref_px, gen_px], fill=color, width=2)
        
        # Draw label
        label = f"{field_name}: dx={data['dx']}px dy={data['dy']}px"
        label_pos = (gen_px[0] + 25, gen_px[1] - 10)
        draw.text(label_pos, label, fill=color, font=font)
    
    # Add legend
    legend_y = 10
    draw.text((10, legend_y), "Reference (blue +)", fill=(0, 0, 255), font=font)
    draw.text((10, legend_y + 20), "Generated (X)", fill=(255, 255, 255), font=font)
    draw.text((10, legend_y + 40), f"Tolerance: {tolerance_px}px", fill=(255, 255, 255), font=font)
    
    # Save overlay
    base_path, ext = os.path.splitext(original_path)
    overlay_path = f"{base_path}_validation_overlay{ext if ext else '.png'}"
    overlay.save(overlay_path)
    logger.info(f"Validation overlay saved to {overlay_path}")
    
    return overlay_path


def _draw_crosshair(draw, position, color, size=10):
    """Draw a crosshair marker at the given position.
    
    Args:
        draw: ImageDraw object
        position: (x, y) tuple
        color: RGB tuple
        size: Size of the crosshair in pixels
    """
    x, y = position
    half = size // 2
    
    # Draw cross
    draw.line([(x - half, y), (x + half, y)], fill=color, width=2)
    draw.line([(x, y - half), (x, y + half)], fill=color, width=2)
    
    # Draw circle outline
    draw.ellipse(
        [(x - half, y - half), (x + half, y + half)],
        outline=color,
        width=2
    )
