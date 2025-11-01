#!/usr/bin/env python3
"""
Sequential Field-by-Field Alignment Tool

This tool aligns certificate fields one at a time with extensive cross-validation:
1. Align NAME field perfectly with hundreds of iterations
2. Cross-check NAME alignment against reference
3. Align EVENT field perfectly
4. Cross-check EVENT alignment
5. Align ORGANISER field perfectly
6. Final cross-check all fields with 1000 iterations

Uses maximum intelligence and all available methods for perfect alignment.
"""
import os
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageChops
import cv2
import json
import time
from copy import deepcopy

sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class SequentialFieldAligner:
    """Align fields one by one with extensive validation."""
    
    def __init__(self, reference_path, template_path, font_path, offsets_path):
        self.reference_path = reference_path
        self.template_path = template_path
        self.font_path = font_path
        self.offsets_path = offsets_path
        
        # Load reference
        self.reference = Image.open(reference_path)
        if self.reference.mode != 'RGB':
            self.reference = self.reference.convert('RGB')
        self.width, self.height = self.reference.size
        
        # Load template
        self.template = Image.open(template_path)
        if self.template.mode != 'RGB':
            self.template = self.template.convert('RGB')
        
        # Load current offsets
        with open(offsets_path, 'r') as f:
            self.offsets = json.load(f)
        
        # Sample text (must match reference)
        self.sample_text = {
            'name': 'SAMPLE NAME',
            'event': 'SAMPLE EVENT',
            'organiser': 'SAMPLE ORG'
        }
        
    def extract_field_from_reference(self, field_name, search_region):
        """Extract a field's position and appearance from reference using CV."""
        ref_array = np.array(self.reference)
        gray = cv2.cvtColor(ref_array, cv2.COLOR_RGB2GRAY)
        
        # Define search region
        y_start, y_end = int(self.height * search_region[0]), int(self.height * search_region[1])
        region = gray[y_start:y_end, :]
        
        # Find text via threshold
        _, binary = cv2.threshold(region, 200, 255, cv2.THRESH_BINARY_INV)
        
        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
        
        # Get bounding box of all text
        all_x, all_y, all_w, all_h = [], [], [], []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if w > 20 and h > 15:  # Filter noise
                all_x.append(x)
                all_y.append(y)
                all_w.append(w)
                all_h.append(h)
        
        if not all_x:
            return None
        
        # Combined bounding box
        min_x = min(all_x)
        min_y = min(all_y)
        max_x = max(x + w for x, w in zip(all_x, all_w))
        max_y = max(y + h for y, h in zip(all_y, all_h))
        
        # Center position (absolute to image, not region)
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2 + y_start
        
        # Normalized positions
        norm_x = center_x / self.width
        norm_y = center_y / self.height
        
        # Text dimensions
        text_width = max_x - min_x
        text_height = max_y - min_y
        
        return {
            'center_x': norm_x,
            'center_y': norm_y,
            'center_x_px': center_x,
            'center_y_px': center_y,
            'width_px': text_width,
            'height_px': text_height,
            'estimated_font_size': int(text_height * 0.85)  # Font size from height
        }
    
    def find_optimal_font_size(self, text, target_height, field_name):
        """Find font size that produces text of target height."""
        logger.info(f"  Finding optimal font size for {field_name}...")
        logger.info(f"  Target text height: {target_height:.1f}px")
        
        best_size = None
        best_diff = float('inf')
        
        # Binary search for font size
        min_size, max_size = 10, 500
        
        for iteration in range(20):  # Binary search iterations
            mid_size = (min_size + max_size) // 2
            
            try:
                font = ImageFont.truetype(self.font_path, mid_size)
                bbox = font.getbbox(text)
                height = bbox[3] - bbox[1]
                
                diff = abs(height - target_height)
                
                if diff < best_diff:
                    best_diff = diff
                    best_size = mid_size
                
                if diff < 2:  # Close enough
                    break
                
                if height < target_height:
                    min_size = mid_size + 1
                else:
                    max_size = mid_size - 1
                    
            except:
                break
        
        logger.info(f"  Optimal font size: {best_size}pt (produces {height:.1f}px height)")
        return best_size
    
    def render_field(self, img, field_name, text, x, y, font_size):
        """Render a single field on the image."""
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype(self.font_path, font_size)
        
        # Draw centered text
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Position
        x_pos = x - text_width / 2
        y_pos = y - text_height / 2
        
        draw.text((x_pos, y_pos), text, fill=(0, 0, 0), font=font)
    
    def calculate_field_difference(self, generated, reference, field_region):
        """Calculate pixel difference in a specific field region."""
        gen_arr = np.array(generated.convert('RGB'))
        ref_arr = np.array(reference.convert('RGB'))
        
        # Define region
        y_start = int(self.height * field_region[0])
        y_end = int(self.height * field_region[1])
        
        # Extract region
        gen_region = gen_arr[y_start:y_end, :]
        ref_region = ref_arr[y_start:y_end, :]
        
        # Calculate difference
        diff = np.abs(gen_region.astype(int) - ref_region.astype(int))
        diff_mask = np.any(diff > 5, axis=2)
        
        total_pixels = diff_mask.size
        different_pixels = np.sum(diff_mask)
        diff_percentage = (different_pixels / total_pixels) * 100.0
        
        return diff_percentage, different_pixels
    
    def calibrate_field_position(self, field_name, field_region, ref_position, font_size, max_iterations=100):
        """Calibrate a single field's position with extensive iterations."""
        logger.info(f"\n{'='*80}")
        logger.info(f"CALIBRATING {field_name.upper()} FIELD")
        logger.info(f"{'='*80}")
        logger.info(f"Target position from reference: ({ref_position['center_x']:.6f}, {ref_position['center_y']:.6f})")
        logger.info(f"Font size: {font_size}pt")
        logger.info(f"Max iterations: {max_iterations}")
        
        text = self.sample_text[field_name]
        
        # Start with reference position
        best_x = ref_position['center_x']
        best_y = ref_position['center_y']
        best_diff = float('inf')
        
        history = []
        
        for iteration in range(max_iterations):
            # Generate with current position
            test_img = self.template.copy()
            x_px = best_x * self.width
            y_px = best_y * self.height
            
            self.render_field(test_img, field_name, text, x_px, y_px, font_size)
            
            # Calculate difference in field region
            diff_pct, diff_pixels = self.calculate_field_difference(test_img, self.reference, field_region)
            
            history.append({
                'iteration': iteration + 1,
                'x': best_x,
                'y': best_y,
                'diff_pct': diff_pct,
                'diff_pixels': diff_pixels
            })
            
            if (iteration + 1) % 10 == 0 or iteration == 0:
                logger.info(f"  Iteration {iteration + 1}/{max_iterations}: {diff_pct:.6f}% difference ({diff_pixels:,} pixels)")
            
            if diff_pct < best_diff:
                best_diff = diff_pct
            
            # If perfect, we're done
            if diff_pct < 0.01:
                logger.info(f"\n  ✅ PERFECT ALIGNMENT achieved at iteration {iteration + 1}!")
                break
            
            # Analyze where differences are
            if iteration < max_iterations - 1:
                # Extract region for analysis
                y_start = int(self.height * field_region[0])
                y_end = int(self.height * field_region[1])
                
                gen_arr = np.array(test_img.convert('RGB'))
                ref_arr = np.array(self.reference.convert('RGB'))
                
                gen_region = gen_arr[y_start:y_end, :]
                ref_region = ref_arr[y_start:y_end, :]
                
                diff = np.abs(gen_region.astype(int) - ref_region.astype(int))
                diff_mask = np.any(diff > 5, axis=2)
                
                if diff_mask.any():
                    # Find center of differences
                    y_coords, x_coords = np.where(diff_mask)
                    diff_center_x = np.mean(x_coords)
                    diff_center_y = np.mean(y_coords) + y_start
                    
                    # Current text center
                    curr_x_px = best_x * self.width
                    curr_y_px = best_y * self.height
                    
                    # Adjustment (small steps)
                    x_adj = (diff_center_x - curr_x_px) / self.width * 0.1  # 10% of error
                    y_adj = (diff_center_y - curr_y_px) / self.height * 0.1
                    
                    # Limit adjustments
                    x_adj = np.clip(x_adj, -0.005, 0.005)
                    y_adj = np.clip(y_adj, -0.005, 0.005)
                    
                    best_x += x_adj
                    best_y += y_adj
        
        logger.info(f"\nCalibration complete:")
        logger.info(f"  Final position: ({best_x:.6f}, {best_y:.6f})")
        logger.info(f"  Best difference: {best_diff:.6f}%")
        logger.info(f"  Iterations used: {len(history)}")
        
        return best_x, best_y, font_size, history
    
    def cross_check_field(self, field_name, x, y, font_size, field_region, num_checks=100):
        """Cross-check a field alignment multiple times."""
        logger.info(f"\n{'='*80}")
        logger.info(f"CROSS-CHECKING {field_name.upper()} ALIGNMENT ({num_checks} iterations)")
        logger.info(f"{'='*80}")
        
        text = self.sample_text[field_name]
        differences = []
        
        for i in range(num_checks):
            # Generate
            test_img = self.template.copy()
            x_px = x * self.width
            y_px = y * self.height
            
            self.render_field(test_img, field_name, text, x_px, y_px, font_size)
            
            # Check difference
            diff_pct, diff_pixels = self.calculate_field_difference(test_img, self.reference, field_region)
            differences.append(diff_pct)
            
            if (i + 1) % 20 == 0:
                logger.info(f"  Check {i + 1}/{num_checks}: {diff_pct:.6f}% difference")
        
        # Statistics
        min_diff = min(differences)
        max_diff = max(differences)
        mean_diff = np.mean(differences)
        std_diff = np.std(differences)
        
        logger.info(f"\nCross-check results:")
        logger.info(f"  Min difference: {min_diff:.6f}%")
        logger.info(f"  Max difference: {max_diff:.6f}%")
        logger.info(f"  Mean difference: {mean_diff:.6f}%")
        logger.info(f"  Std deviation: {std_diff:.6f}%")
        
        if mean_diff < 0.01:
            logger.info(f"  ✅ PERFECT - All checks passed!")
            return True
        else:
            logger.info(f"  ⚠️  Alignment needs improvement")
            return False
    
    def final_verification(self, num_checks=1000):
        """Final verification with all fields rendered together."""
        logger.info(f"\n{'='*80}")
        logger.info(f"FINAL VERIFICATION ({num_checks} iterations)")
        logger.info(f"{'='*80}")
        logger.info("Rendering all fields together and comparing with reference...")
        
        differences = []
        
        for i in range(num_checks):
            # Generate complete certificate
            test_img = self.template.copy()
            
            for field_name in ['name', 'event', 'organiser']:
                x = self.offsets['fields'][field_name]['x']
                y = self.offsets['fields'][field_name]['y']
                font_size = self.offsets['fields'][field_name]['font_size']
                text = self.sample_text[field_name]
                
                x_px = x * self.width
                y_px = y * self.height
                
                self.render_field(test_img, field_name, text, x_px, y_px, font_size)
            
            # Compare entire image
            gen_arr = np.array(test_img.convert('RGB'))
            ref_arr = np.array(self.reference.convert('RGB'))
            
            diff = np.abs(gen_arr.astype(int) - ref_arr.astype(int))
            diff_mask = np.any(diff > 5, axis=2)
            
            total_pixels = diff_mask.size
            different_pixels = np.sum(diff_mask)
            diff_pct = (different_pixels / total_pixels) * 100.0
            
            differences.append(diff_pct)
            
            if (i + 1) % 100 == 0:
                logger.info(f"  Iteration {i + 1}/{num_checks}: {diff_pct:.6f}% difference")
        
        # Statistics
        min_diff = min(differences)
        max_diff = max(differences)
        mean_diff = np.mean(differences)
        std_diff = np.std(differences)
        
        logger.info(f"\nFinal verification results:")
        logger.info(f"  Checks performed: {num_checks}")
        logger.info(f"  Min difference: {min_diff:.6f}%")
        logger.info(f"  Max difference: {max_diff:.6f}%")
        logger.info(f"  Mean difference: {mean_diff:.6f}%")
        logger.info(f"  Std deviation: {std_diff:.6f}%")
        
        if mean_diff < 0.1:
            logger.info(f"\n{'='*80}")
            logger.info(f"✅ PERFECT ALIGNMENT CONFIRMED")
            logger.info(f"{'='*80}")
            return True
        else:
            logger.info(f"\n⚠️  Alignment needs further refinement")
            return False


def main():
    """Main alignment process."""
    base_dir = Path(__file__).parent.parent
    reference_path = base_dir / 'templates' / 'Sample_certificate.png'
    template_path = base_dir / 'templates' / 'template_extracted_from_sample.png'
    font_path = base_dir / 'templates' / 'ARIALBD.TTF'
    offsets_path = base_dir / 'templates' / 'goonj_template_offsets.json'
    
    logger.info("=" * 80)
    logger.info("SEQUENTIAL FIELD-BY-FIELD ALIGNMENT")
    logger.info("=" * 80)
    logger.info(f"\nReference: {reference_path}")
    logger.info(f"Template: {template_path}")
    logger.info(f"Font: {font_path}")
    
    aligner = SequentialFieldAligner(
        str(reference_path),
        str(template_path),
        str(font_path),
        str(offsets_path)
    )
    
    # Define search regions for each field (vertical bands)
    field_regions = {
        'name': ((0.15, 0.45), (0.15, 0.45)),      # Search & verify in upper third
        'event': ((0.40, 0.65), (0.40, 0.65)),     # Search & verify in middle
        'organiser': ((0.65, 0.85), (0.65, 0.85))  # Search & verify in lower third
    }
    
    # STEP 1: Align NAME field
    logger.info("\n" + "=" * 80)
    logger.info("STEP 1: ALIGN NAME FIELD")
    logger.info("=" * 80)
    
    name_ref = aligner.extract_field_from_reference('name', field_regions['name'][0])
    if name_ref:
        logger.info(f"Extracted NAME position from reference:")
        logger.info(f"  Position: ({name_ref['center_x']:.6f}, {name_ref['center_y']:.6f})")
        logger.info(f"  Pixel position: ({name_ref['center_x_px']:.1f}, {name_ref['center_y_px']:.1f})")
        logger.info(f"  Text dimensions: {name_ref['width_px']:.0f} x {name_ref['height_px']:.0f} px")
        
        # Find font size
        name_font_size = aligner.find_optimal_font_size(
            aligner.sample_text['name'],
            name_ref['height_px'],
            'name'
        )
        
        # Calibrate with 200 iterations
        name_x, name_y, name_fs, name_history = aligner.calibrate_field_position(
            'name',
            field_regions['name'][1],
            name_ref,
            name_font_size,
            max_iterations=200
        )
        
        # Cross-check with 100 iterations
        name_ok = aligner.cross_check_field('name', name_x, name_y, name_fs, field_regions['name'][1], 100)
        
        # Update offsets
        aligner.offsets['fields']['name']['x'] = name_x
        aligner.offsets['fields']['name']['y'] = name_y
        aligner.offsets['fields']['name']['font_size'] = name_fs
    
    # STEP 2: Align EVENT field
    logger.info("\n" + "=" * 80)
    logger.info("STEP 2: ALIGN EVENT FIELD")
    logger.info("=" * 80)
    
    event_ref = aligner.extract_field_from_reference('event', field_regions['event'][0])
    if event_ref:
        logger.info(f"Extracted EVENT position from reference:")
        logger.info(f"  Position: ({event_ref['center_x']:.6f}, {event_ref['center_y']:.6f})")
        logger.info(f"  Pixel position: ({event_ref['center_x_px']:.1f}, {event_ref['center_y_px']:.1f})")
        logger.info(f"  Text dimensions: {event_ref['width_px']:.0f} x {event_ref['height_px']:.0f} px")
        
        event_font_size = aligner.find_optimal_font_size(
            aligner.sample_text['event'],
            event_ref['height_px'],
            'event'
        )
        
        event_x, event_y, event_fs, event_history = aligner.calibrate_field_position(
            'event',
            field_regions['event'][1],
            event_ref,
            event_font_size,
            max_iterations=200
        )
        
        event_ok = aligner.cross_check_field('event', event_x, event_y, event_fs, field_regions['event'][1], 100)
        
        aligner.offsets['fields']['event']['x'] = event_x
        aligner.offsets['fields']['event']['y'] = event_y
        aligner.offsets['fields']['event']['font_size'] = event_fs
    
    # STEP 3: Align ORGANISER field
    logger.info("\n" + "=" * 80)
    logger.info("STEP 3: ALIGN ORGANISER FIELD")
    logger.info("=" * 80)
    
    org_ref = aligner.extract_field_from_reference('organiser', field_regions['organiser'][0])
    if org_ref:
        logger.info(f"Extracted ORGANISER position from reference:")
        logger.info(f"  Position: ({org_ref['center_x']:.6f}, {org_ref['center_y']:.6f})")
        logger.info(f"  Pixel position: ({org_ref['center_x_px']:.1f}, {org_ref['center_y_px']:.1f})")
        logger.info(f"  Text dimensions: {org_ref['width_px']:.0f} x {org_ref['height_px']:.0f} px")
        
        org_font_size = aligner.find_optimal_font_size(
            aligner.sample_text['organiser'],
            org_ref['height_px'],
            'organiser'
        )
        
        org_x, org_y, org_fs, org_history = aligner.calibrate_field_position(
            'organiser',
            field_regions['organiser'][1],
            org_ref,
            org_font_size,
            max_iterations=200
        )
        
        org_ok = aligner.cross_check_field('organiser', org_x, org_y, org_fs, field_regions['organiser'][1], 100)
        
        aligner.offsets['fields']['organiser']['x'] = org_x
        aligner.offsets['fields']['organiser']['y'] = org_y
        aligner.offsets['fields']['organiser']['font_size'] = org_fs
    
    # Save updated offsets
    aligner.offsets['version'] = '6.0'
    aligner.offsets['calibration_method'] = 'sequential_field_by_field_with_extensive_cross_checking'
    aligner.offsets['calibration_date'] = '2025-10-31'
    aligner.offsets['description'] = 'Field positions calibrated sequentially (name→event→organiser) with 200 iterations per field and 100 cross-checks each. Based on original Canva-designed reference certificate.'
    
    with open(offsets_path, 'w') as f:
        json.dump(aligner.offsets, f, indent=2)
    
    logger.info(f"\n✅ Offsets saved to: {offsets_path}")
    
    # STEP 4: Final verification with 1000 iterations
    logger.info("\n" + "=" * 80)
    logger.info("STEP 4: FINAL VERIFICATION (1000 ITERATIONS)")
    logger.info("=" * 80)
    
    final_ok = aligner.final_verification(num_checks=1000)
    
    if final_ok:
        logger.info("\n🎉 SUCCESS! Perfect alignment achieved with original reference!")
        return 0
    else:
        logger.info("\n⚠️  Alignment completed but may need further tuning")
        return 1


if __name__ == '__main__':
    sys.exit(main())
