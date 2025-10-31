#!/usr/bin/env python3
"""
Comprehensive Alignment Testing System

This tool performs extensive alignment verification with:
1. 1000 iterations of alignment verification
2. Statistical analysis of alignment stability
3. Testing with various text inputs
4. Performance metrics
5. Visual comparison generation
"""
import os
import sys
import json
import time
from pathlib import Path
from datetime import datetime
import statistics

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from PIL import Image, ImageChops, ImageDraw, ImageFont
from app.utils.goonj_renderer import GOONJRenderer
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def calculate_pixel_difference(img1, img2):
    """Calculate exact pixel difference between two images."""
    if img1.size != img2.size:
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


def test_alignment_single(renderer, sample_data, reference_img):
    """Test alignment for a single certificate generation."""
    # Generate certificate in memory
    cert_image = renderer.template.copy()
    draw = ImageDraw.Draw(cert_image)
    
    # Extract and process data
    name = sample_data.get('name', 'SAMPLE NAME').upper()
    event = sample_data.get('event', 'SAMPLE EVENT').upper()
    organiser = sample_data.get('organiser', 'SAMPLE ORG').upper()
    
    # Render using the same logic as the renderer
    from app.utils.text_align import draw_text_centered, get_font
    
    # Name field
    name_font = renderer._fit_text_to_width(
        draw, name, renderer.name_bbox['base_font_size'], renderer.max_text_width
    )
    draw_text_centered(
        draw,
        (renderer.name_bbox['x'], renderer.name_bbox['y']),
        name,
        name_font,
        renderer._hex_to_rgb(renderer.name_bbox['color'])
    )
    
    # Event field
    event_font = renderer._fit_text_to_width(
        draw, event, renderer.event_bbox['base_font_size'], renderer.max_text_width
    )
    draw_text_centered(
        draw,
        (renderer.event_bbox['x'], renderer.event_bbox['y']),
        event,
        event_font,
        renderer._hex_to_rgb(renderer.event_bbox['color'])
    )
    
    # Organiser field
    org_font = renderer._fit_text_to_width(
        draw, organiser, renderer.organiser_bbox['base_font_size'], renderer.max_text_width
    )
    draw_text_centered(
        draw,
        (renderer.organiser_bbox['x'], renderer.organiser_bbox['y']),
        organiser,
        org_font,
        renderer._hex_to_rgb(renderer.organiser_bbox['color'])
    )
    
    # Compare with reference
    diff_pct, diff_pixels, max_diff = calculate_pixel_difference(cert_image, reference_img)
    
    return {
        'diff_percentage': diff_pct,
        'diff_pixels': diff_pixels,
        'max_diff': max_diff,
        'is_perfect': diff_pct == 0.0 and max_diff == 0
    }


def run_comprehensive_test(iterations=1000):
    """Run comprehensive alignment test with multiple iterations."""
    logger.info("=" * 80)
    logger.info("COMPREHENSIVE ALIGNMENT VERIFICATION SYSTEM")
    logger.info("=" * 80)
    logger.info("")
    logger.info(f"Running {iterations} iterations of alignment verification...")
    logger.info("")
    
    # Setup paths
    base_dir = Path(__file__).parent.parent
    template_path = base_dir / 'templates' / 'goonj_certificate.png'
    reference_path = base_dir / 'templates' / 'Sample_certificate.png'
    output_dir = base_dir / 'generated_certificates'
    
    # Check files exist
    if not template_path.exists():
        logger.error(f"❌ Template not found: {template_path}")
        return 2
    if not reference_path.exists():
        logger.error(f"❌ Reference not found: {reference_path}")
        return 2
    
    # Load reference
    reference_img = Image.open(reference_path).convert('RGB')
    
    # Create renderer
    renderer = GOONJRenderer(str(template_path), str(output_dir))
    
    # Sample data (same as reference)
    sample_data = {
        'name': 'SAMPLE NAME',
        'event': 'SAMPLE EVENT',
        'organiser': 'SAMPLE ORG'
    }
    
    # Test data variations
    test_cases = [
        {'name': 'SAMPLE NAME', 'event': 'SAMPLE EVENT', 'organiser': 'SAMPLE ORG'},
        {'name': 'John Doe', 'event': 'GOONJ 2025', 'organiser': 'AMA'},
        {'name': 'A', 'event': 'X', 'organiser': 'Y'},  # Short names
        {'name': 'VERY LONG NAME WITH MANY CHARACTERS', 'event': 'EVENT', 'organiser': 'ORG'},
    ]
    
    # Statistics tracking
    results = []
    timings = []
    perfect_matches = 0
    
    # Progress tracking
    checkpoint_interval = iterations // 10 if iterations >= 10 else 1
    
    logger.info(f"Testing with sample data: {sample_data}")
    logger.info("")
    
    start_time = time.time()
    
    for i in range(iterations):
        # Show progress
        if (i + 1) % checkpoint_interval == 0 or i == 0:
            logger.info(f"Progress: {i + 1}/{iterations} iterations completed...")
        
        iter_start = time.time()
        result = test_alignment_single(renderer, sample_data, reference_img)
        iter_time = time.time() - iter_start
        
        results.append(result)
        timings.append(iter_time)
        
        if result['is_perfect']:
            perfect_matches += 1
    
    total_time = time.time() - start_time
    
    # Calculate statistics
    diff_percentages = [r['diff_percentage'] for r in results]
    max_diffs = [r['max_diff'] for r in results]
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("RESULTS SUMMARY")
    logger.info("=" * 80)
    logger.info("")
    logger.info(f"Total iterations: {iterations}")
    logger.info(f"Perfect matches: {perfect_matches}/{iterations} ({100*perfect_matches/iterations:.2f}%)")
    logger.info("")
    logger.info("Alignment Statistics:")
    logger.info(f"  Min difference: {min(diff_percentages):.6f}%")
    logger.info(f"  Max difference: {max(diff_percentages):.6f}%")
    logger.info(f"  Mean difference: {statistics.mean(diff_percentages):.6f}%")
    if len(diff_percentages) > 1:
        logger.info(f"  Std deviation: {statistics.stdev(diff_percentages):.6f}%")
    logger.info("")
    logger.info("Pixel Difference Statistics:")
    logger.info(f"  Min max_diff: {min(max_diffs)}/255")
    logger.info(f"  Max max_diff: {max(max_diffs)}/255")
    logger.info(f"  Mean max_diff: {statistics.mean(max_diffs):.2f}/255")
    logger.info("")
    logger.info("Performance Statistics:")
    logger.info(f"  Total time: {total_time:.2f}s")
    logger.info(f"  Average time per iteration: {statistics.mean(timings)*1000:.2f}ms")
    logger.info(f"  Min time: {min(timings)*1000:.2f}ms")
    logger.info(f"  Max time: {max(timings)*1000:.2f}ms")
    logger.info("")
    
    # Test with various inputs
    logger.info("=" * 80)
    logger.info("TESTING WITH VARIOUS TEXT INPUTS")
    logger.info("=" * 80)
    logger.info("")
    
    for idx, test_case in enumerate(test_cases, 1):
        logger.info(f"Test Case {idx}: {test_case}")
        
        # Generate actual certificate
        cert_path = renderer.render(test_case, output_format='png')
        cert_img = Image.open(cert_path).convert('RGB')
        
        # For reference comparison, only the sample data should match
        if test_case == sample_data:
            diff_pct, diff_pixels, max_diff = calculate_pixel_difference(cert_img, reference_img)
            logger.info(f"  vs Reference: {diff_pct:.6f}% difference, max_diff={max_diff}")
        else:
            logger.info(f"  Generated successfully: {cert_path}")
        logger.info("")
    
    # Final verdict
    logger.info("=" * 80)
    if perfect_matches == iterations and min(diff_percentages) == 0.0:
        logger.info("✅ PERFECT ALIGNMENT CONFIRMED")
        logger.info("=" * 80)
        logger.info("")
        logger.info(f"All {iterations} iterations produced PIXEL-PERFECT matches!")
        logger.info("Alignment is 100% stable and consistent.")
        logger.info("0.00px difference achieved in all tests.")
        return 0
    else:
        logger.info("⚠️  ALIGNMENT ISSUES DETECTED")
        logger.info("=" * 80)
        logger.info("")
        logger.info(f"Only {perfect_matches}/{iterations} iterations were perfect.")
        logger.info("Alignment may have instability issues.")
        return 1


if __name__ == '__main__':
    # Default to 1000 iterations, but allow override
    iterations = int(sys.argv[1]) if len(sys.argv) > 1 else 1000
    sys.exit(run_comprehensive_test(iterations))
