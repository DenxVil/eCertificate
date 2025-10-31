"""Shared text alignment helper for certificate generation.

This module provides robust text alignment utilities that use PIL anchor points
when available and fall back to metrics-based placement for precise vertical alignment.
"""
from PIL import ImageFont
import logging

logger = logging.getLogger(__name__)


def draw_text_centered(draw, position, text, font, fill, align="center", baseline_offset=0):
    """Draw text centered at the given position with optional baseline adjustment.
    
    Uses PIL anchor points ('mm', 'rm', 'lm') for precise alignment when supported.
    Falls back to robust metrics-based placement using font.getmetrics() and 
    draw.textbbox when anchor is unavailable.
    
    Args:
        draw: PIL ImageDraw object
        position: (x, y) tuple for text position
        text: Text string to render
        font: PIL ImageFont object
        fill: Text color (RGB tuple or color name)
        align: Alignment mode - "center", "right", or "left" (default: "center")
        baseline_offset: Vertical offset in pixels to adjust baseline (default: 0)
    
    Returns:
        Final drawn position (x, y) tuple
    """
    x, y = position
    
    # Apply baseline offset
    y_adjusted = y + baseline_offset
    
    # Map alignment to PIL anchor points
    anchor_map = {
        "center": "mm",  # middle-middle
        "right": "rm",   # right-middle
        "left": "lm"     # left-middle
    }
    anchor = anchor_map.get(align, "mm")
    
    try:
        # Try using PIL anchor points (available in Pillow 8.0.0+)
        draw.text((x, y_adjusted), text, font=font, fill=fill, anchor=anchor)
        return (x, y_adjusted)
    except TypeError:
        # Fallback: anchor parameter not supported
        logger.debug("PIL anchor not supported, using metrics-based fallback")
        return _draw_text_centered_fallback(draw, (x, y_adjusted), text, font, fill, align)


def _draw_text_centered_fallback(draw, position, text, font, fill, align="center"):
    """Fallback method for text centering using textbbox and font metrics.
    
    This method computes precise text dimensions and positions text manually
    when PIL anchor points are not available.
    
    Args:
        draw: PIL ImageDraw object
        position: (x, y) tuple for text position
        text: Text string to render
        font: PIL ImageFont object
        fill: Text color
        align: Alignment mode - "center", "right", or "left"
    
    Returns:
        Final drawn position (x, y) tuple
    """
    x, y = position
    
    # Get text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    # Get font metrics for better vertical alignment
    try:
        ascent, descent = font.getmetrics()
        # Calculate vertical center based on ascent/descent
        vertical_center = (ascent - descent) // 2
    except (AttributeError, TypeError):
        # If getmetrics not available, use text_height
        vertical_center = text_height // 2
    
    # Calculate horizontal position based on alignment
    if align == "center":
        x_draw = x - text_width // 2
    elif align == "right":
        x_draw = x - text_width
    else:  # left
        x_draw = x
    
    # Calculate vertical position (centered on y)
    y_draw = y - vertical_center
    
    # Draw the text
    draw.text((x_draw, y_draw), text, font=font, fill=fill)
    
    return (x_draw, y_draw)


def get_font(font_path, size):
    """Load a TrueType font with fallback to default font.
    
    Args:
        font_path: Path to TrueType font file or None for default
        size: Font size in points
    
    Returns:
        PIL ImageFont object
    """
    if font_path:
        try:
            return ImageFont.truetype(font_path, size)
        except (OSError, IOError) as e:
            logger.warning(f"Could not load font {font_path}: {e}, using default")
    
    # Fallback to default font
    try:
        return ImageFont.load_default()
    except Exception as e:
        logger.error(f"Could not load default font: {e}")
        raise
