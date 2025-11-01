#!/usr/bin/env python3
"""
Iterative Alignment Calibration Tool

This tool iteratively adjusts field positions to achieve pixel-perfect alignment
between generated certificates and the reference Sample_certificate.png.

Strategy:
1. Generate certificate with current offsets
2. Compare with reference to measure misalignment
3. Adjust offsets based on measured difference
4. Repeat until perfect alignment (or max iterations reached)

This uses up to 30 attempts as requested to find the perfect alignment.
"""
import os
import sys
import json
import copy
from pathlib import Path
from PIL import Image, ImageChops
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.goonj_renderer import GOONJRenderer
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def calculate_pixel_difference(img1, img2):
    """Calculate exact pixel difference."""
    if img1.size != img2.size:
        return 100.0, -1, 255
    
    if img1.mode != 'RGB':
        img1 = img1.convert('RGB')
    if img2.mode != 'RGB':
        img2 = img2.convert('RGB')
    
    diff = ImageChops.difference(img1, img2)
    diff_data = list(diff.getdata())
    
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


def analyze_text_misalignment(generated_img, reference_img, current_offsets, img_height):
    """Analyze where text differs to suggest offset adjustments."""
    gen_array = np.array(generated_img.convert('RGB'))
    ref_array = np.array(reference_img.convert('RGB'))
    
    # Calculate per-pixel difference
    diff_array = np.abs(gen_array.astype(int) - ref_array.astype(int))
    diff_mask = np.any(diff_array > 5, axis=2)  # Threshold for "different"
    
    height, width = diff_mask.shape
    
    # For each field, find where differences are concentrated
    adjustments = {}
    
    for field in ['name', 'event', 'organiser']:
        current_y = current_offsets['fields'][field]['y']
        current_y_px = int(current_y * img_height)
        
        # Look at a band around the current position
        band_height = 100
        start_y = max(0, current_y_px - band_height)
        end_y = min(height, current_y_px + band_height)
        
        band_diff = diff_mask[start_y:end_y, :]
        
        if band_diff.any():
            # Find center of mass of differences in this band
            y_coords, x_coords = np.where(band_diff)
            
            if len(y_coords) > 0:
                diff_center_y = np.mean(y_coords) + start_y
                diff_center_x = np.mean(x_coords)
                
                # Calculate adjustment needed
                y_adjustment = (diff_center_y - current_y_px) / img_height
                
                # Limit adjustment to prevent overcorrection
                y_adjustment = np.clip(y_adjustment, -0.02, 0.02)
                
                adjustments[field] = {
                    'y_adjustment': y_adjustment,
                    'diff_pixels': len(y_coords)
                }
    
    return adjustments


def iterative_calibration(max_attempts=30):
    """Perform iterative calibration with up to max_attempts."""
    logger.info("=" * 80)
    logger.info("ITERATIVE ALIGNMENT CALIBRATION")
    logger.info("=" * 80)
    logger.info(f"\nMax attempts: {max_attempts}")
    logger.info("Target: 0.00% pixel difference (perfect alignment)")
    logger.info("")
    
    # Setup paths
    base_dir = Path(__file__).parent.parent
    template_path = base_dir / 'templates' / 'goonj_certificate.png'
    reference_path = base_dir / 'templates' / 'Sample_certificate.png'
    offsets_path = base_dir / 'templates' / 'goonj_template_offsets.json'
    output_dir = base_dir / 'generated_certificates'
    
    # Load current offsets
    with open(offsets_path, 'r') as f:
        offsets = json.load(f)
    
    logger.info(f"Starting offsets:")
    for field in ['name', 'event', 'organiser']:
        logger.info(f"  {field}: x={offsets['fields'][field]['x']:.6f}, y={offsets['fields'][field]['y']:.6f}")
    logger.info("")
    
    # Load reference
    reference_img = Image.open(reference_path).convert('RGB')
    img_width, img_height = reference_img.size
    
    # Sample data (must match what's in the reference!)
    sample_data = {
        'name': 'SAMPLE NAME',
        'event': 'SAMPLE EVENT',
        'organiser': 'SAMPLE ORG'
    }
    
    best_diff = float('inf')
    best_offsets = copy.deepcopy(offsets)
    history = []
    
    for attempt in range(1, max_attempts + 1):
        logger.info(f"\n{'=' * 80}")
        logger.info(f"ATTEMPT {attempt}/{max_attempts}")
        logger.info(f"{'=' * 80}")
        
        # Save current offsets to file
        with open(offsets_path, 'w') as f:
            json.dump(offsets, f, indent=2)
        
        # Generate certificate
        renderer = GOONJRenderer(str(template_path), str(output_dir))
        cert_path = renderer.render(sample_data, output_format='png')
        cert_img = Image.open(cert_path).convert('RGB')
        
        # Compare
        diff_pct, diff_pixels, max_diff = calculate_pixel_difference(cert_img, reference_img)
        
        logger.info(f"\nResults:")
        logger.info(f"  Difference: {diff_pct:.6f}%")
        logger.info(f"  Different pixels: {diff_pixels:,}")
        logger.info(f"  Max pixel diff: {max_diff}/255")
        
        # Record history
        history.append({
            'attempt': attempt,
            'diff_pct': diff_pct,
            'diff_pixels': diff_pixels,
            'max_diff': max_diff,
            'offsets': copy.deepcopy(offsets['fields'])
        })
        
        # Check if perfect
        if diff_pct == 0.0 and max_diff == 0:
            logger.info(f"\n{'=' * 80}")
            logger.info(f"✅ PERFECT ALIGNMENT ACHIEVED!")
            logger.info(f"{'=' * 80}")
            logger.info(f"\nAchieved in {attempt} attempt(s)")
            logger.info(f"Final offsets:")
            for field in ['name', 'event', 'organiser']:
                logger.info(f"  {field}: x={offsets['fields'][field]['x']:.6f}, y={offsets['fields'][field]['y']:.6f}")
            
            # Save best offsets
            with open(offsets_path, 'w') as f:
                json.dump(offsets, f, indent=2)
            
            return 0, history
        
        # Track best result
        if diff_pct < best_diff:
            best_diff = diff_pct
            best_offsets = copy.deepcopy(offsets)
            logger.info(f"  ★ New best result!")
        
        # If not perfect and not last attempt, calculate adjustments
        if attempt < max_attempts:
            logger.info(f"\nAnalyzing misalignment...")
            adjustments = analyze_text_misalignment(cert_img, reference_img, offsets, img_height)
            
            if adjustments:
                logger.info(f"Applying adjustments:")
                for field, adj in adjustments.items():
                    old_y = offsets['fields'][field]['y']
                    new_y = old_y + adj['y_adjustment']
                    offsets['fields'][field]['y'] = new_y
                    logger.info(f"  {field}: y {old_y:.6f} → {new_y:.6f} (Δ {adj['y_adjustment']:+.6f})")
            else:
                logger.info("No clear adjustments found, trying small random perturbations...")
                # Small random adjustments to escape local minimum
                for field in ['name', 'event', 'organiser']:
                    perturbation = (np.random.random() - 0.5) * 0.01  # ±0.005
                    offsets['fields'][field]['y'] += perturbation
    
    # Max attempts reached
    logger.info(f"\n{'=' * 80}")
    logger.info(f"⚠️  MAX ATTEMPTS REACHED ({max_attempts})")
    logger.info(f"{'=' * 80}")
    logger.info(f"\nBest result: {best_diff:.6f}% difference")
    logger.info(f"Best offsets:")
    for field in ['name', 'event', 'organiser']:
        logger.info(f"  {field}: x={best_offsets['fields'][field]['x']:.6f}, y={best_offsets['fields'][field]['y']:.6f}")
    
    # Save best offsets
    with open(offsets_path, 'w') as f:
        json.dump(best_offsets, f, indent=2)
    
    logger.info(f"\nSaved best offsets to: {offsets_path}")
    
    return 1, history


def main():
    """Main function."""
    max_attempts = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    exit_code, history = iterative_calibration(max_attempts)
    
    # Print summary
    logger.info(f"\n{'=' * 80}")
    logger.info("CALIBRATION SUMMARY")
    logger.info(f"{'=' * 80}")
    logger.info(f"\nTotal attempts: {len(history)}")
    logger.info(f"Best result: {min(h['diff_pct'] for h in history):.6f}%")
    logger.info(f"\nProgress:")
    for h in history[:10]:  # Show first 10
        logger.info(f"  Attempt {h['attempt']}: {h['diff_pct']:.6f}%")
    if len(history) > 10:
        logger.info(f"  ...")
        for h in history[-3:]:  # Show last 3
            logger.info(f"  Attempt {h['attempt']}: {h['diff_pct']:.6f}%")
    
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
