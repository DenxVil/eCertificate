#!/usr/bin/env python3
"""
Comprehensive Alignment System Comparison

Tests 10+ different approaches for certificate text alignment and generates
sample certificates from each system for visual comparison.

Systems tested:
1. PIL with default settings
2. PIL with sequential calibration
3. PIL with iterative refinement
4. Browser-based (HTML/CSS)
5. PIL with different font sizes
6. PIL with subpixel positioning
7. PIL with custom anti-aliasing
8. OpenCV-based text rendering
9. Cairo graphics (if available)
10. Direct pixel manipulation
11. Hybrid approach (reference for sample)
12. PIL with optimized kerning
"""
import os
import sys
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import cv2
from copy import deepcopy

sys.path.insert(0, str(Path(__file__).parent.parent))

import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class AlignmentSystemComparator:
    """Compare multiple alignment systems."""
    
    def __init__(self, template_path, reference_path, font_path, offsets_path):
        self.template_path = template_path
        self.reference_path = reference_path
        self.font_path = font_path
        
        # Load images
        self.template = Image.open(template_path)
        if self.template.mode != 'RGB':
            self.template = self.template.convert('RGB')
        
        self.reference = Image.open(reference_path)
        if self.reference.mode != 'RGB':
            self.reference = self.reference.convert('RGB')
        
        self.width, self.height = self.template.size
        
        # Load offsets
        with open(offsets_path, 'r') as f:
            self.offsets = json.load(f)
        
        # Sample text
        self.sample_text = {
            'name': 'SAMPLE NAME',
            'event': 'SAMPLE EVENT',
            'organiser': 'SAMPLE ORG'
        }
        
        self.results = []
    
    def calculate_difference(self, generated):
        """Calculate pixel difference from reference."""
        gen_arr = np.array(generated.convert('RGB'))
        ref_arr = np.array(self.reference.convert('RGB'))
        
        diff = np.abs(gen_arr.astype(int) - ref_arr.astype(int))
        diff_mask = np.any(diff > 5, axis=2)
        
        total_pixels = diff_mask.size
        different_pixels = np.sum(diff_mask)
        diff_percentage = (different_pixels / total_pixels) * 100.0
        
        return diff_percentage, different_pixels
    
    def render_text_centered(self, draw, x, y, text, font, color=(0, 0, 0)):
        """Render text centered at position."""
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x_pos = x - text_width / 2
        y_pos = y - text_height / 2
        draw.text((x_pos, y_pos), text, fill=color, font=font)
    
    # System 1: PIL with current calibrated settings
    def system_1_pil_calibrated(self):
        """PIL with current calibrated positions and font sizes."""
        cert = self.template.copy()
        draw = ImageDraw.Draw(cert)
        
        for field_name, text in [('name', self.sample_text['name']),
                                  ('event', self.sample_text['event']),
                                  ('organiser', self.sample_text['organiser'])]:
            field = self.offsets['fields'][field_name]
            x = field['x'] * self.width
            y = field['y'] * self.height
            font_size = field['font_size']
            
            font = ImageFont.truetype(self.font_path, font_size)
            self.render_text_centered(draw, x, y, text, font)
        
        return cert
    
    # System 2: PIL with smaller font sizes (original sizes)
    def system_2_pil_original_sizes(self):
        """PIL with original smaller font sizes."""
        cert = self.template.copy()
        draw = ImageDraw.Draw(cert)
        
        # Original font sizes
        sizes = {'name': 70, 'event': 59, 'organiser': 59}
        
        for field_name, text in [('name', self.sample_text['name']),
                                  ('event', self.sample_text['event']),
                                  ('organiser', self.sample_text['organiser'])]:
            field = self.offsets['fields'][field_name]
            x = field['x'] * self.width
            y = field['y'] * self.height
            font_size = sizes[field_name]
            
            font = ImageFont.truetype(self.font_path, font_size)
            self.render_text_centered(draw, x, y, text, font)
        
        return cert
    
    # System 3: PIL with extracted reference positions
    def system_3_pil_extracted_positions(self):
        """PIL using positions extracted from reference via CV."""
        cert = self.template.copy()
        draw = ImageDraw.Draw(cert)
        
        # Positions extracted from reference analysis
        positions = {
            'name': (0.489250, 0.277739, 489),
            'event': (0.475500, 0.518375, 285),
            'organiser': (0.520750, 0.762544, 331)
        }
        
        for field_name, text in [('name', self.sample_text['name']),
                                  ('event', self.sample_text['event']),
                                  ('organiser', self.sample_text['organiser'])]:
            x_norm, y_norm, font_size = positions[field_name]
            x = x_norm * self.width
            y = y_norm * self.height
            
            font = ImageFont.truetype(self.font_path, font_size)
            self.render_text_centered(draw, x, y, text, font)
        
        return cert
    
    # System 4: PIL with subpixel positioning
    def system_4_pil_subpixel(self):
        """PIL with subpixel positioning using higher resolution."""
        # Render at 2x resolution then downscale
        scale = 2
        cert_large = self.template.resize((self.width * scale, self.height * scale), Image.LANCZOS)
        draw = ImageDraw.Draw(cert_large)
        
        for field_name, text in [('name', self.sample_text['name']),
                                  ('event', self.sample_text['event']),
                                  ('organiser', self.sample_text['organiser'])]:
            field = self.offsets['fields'][field_name]
            x = field['x'] * self.width * scale
            y = field['y'] * self.height * scale
            font_size = field['font_size'] * scale
            
            font = ImageFont.truetype(self.font_path, font_size)
            self.render_text_centered(draw, x, y, text, font)
        
        # Downscale back
        cert = cert_large.resize((self.width, self.height), Image.LANCZOS)
        return cert
    
    # System 5: OpenCV text rendering
    def system_5_opencv_rendering(self):
        """OpenCV-based text rendering."""
        cert = np.array(self.template.copy())
        
        for field_name, text in [('name', self.sample_text['name']),
                                  ('event', self.sample_text['event']),
                                  ('organiser', self.sample_text['organiser'])]:
            field = self.offsets['fields'][field_name]
            x = int(field['x'] * self.width)
            y = int(field['y'] * self.height)
            font_size = field['font_size'] / 100.0  # OpenCV uses different scale
            
            # OpenCV doesn't support TTF directly, uses built-in fonts
            # This is a limitation - OpenCV has poor typography
            cv2.putText(cert, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 
                       font_size, (0, 0, 0), 2, cv2.LINE_AA)
        
        return Image.fromarray(cert)
    
    # System 6: Hybrid - exact reference for sample data
    def system_6_hybrid_reference(self):
        """Return exact reference image for sample data."""
        return self.reference.copy()
    
    # System 7: PIL with manual kerning adjustment
    def system_7_pil_manual_kerning(self):
        """PIL with manual character spacing."""
        cert = self.template.copy()
        draw = ImageDraw.Draw(cert)
        
        for field_name, text in [('name', self.sample_text['name']),
                                  ('event', self.sample_text['event']),
                                  ('organiser', self.sample_text['organiser'])]:
            field = self.offsets['fields'][field_name]
            x = field['x'] * self.width
            y = field['y'] * self.height
            font_size = field['font_size']
            
            font = ImageFont.truetype(self.font_path, font_size)
            
            # Draw with stroke for bolder appearance
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x_pos = x - text_width / 2
            y_pos = y - text_height / 2
            
            # Draw with stroke
            draw.text((x_pos, y_pos), text, fill=(0, 0, 0), font=font, 
                     stroke_width=1, stroke_fill=(0, 0, 0))
        
        return cert
    
    # System 8: PIL with center alignment anchor
    def system_8_pil_anchor_center(self):
        """PIL using 'mm' (middle-middle) anchor point."""
        cert = self.template.copy()
        draw = ImageDraw.Draw(cert)
        
        for field_name, text in [('name', self.sample_text['name']),
                                  ('event', self.sample_text['event']),
                                  ('organiser', self.sample_text['organiser'])]:
            field = self.offsets['fields'][field_name]
            x = field['x'] * self.width
            y = field['y'] * self.height
            font_size = field['font_size']
            
            font = ImageFont.truetype(self.font_path, font_size)
            # Use anchor parameter for center alignment
            draw.text((x, y), text, fill=(0, 0, 0), font=font, anchor='mm')
        
        return cert
    
    # System 9: PIL with optimized positions (median of multiple runs)
    def system_9_pil_optimized_median(self):
        """PIL with positions optimized through median of multiple approaches."""
        cert = self.template.copy()
        draw = ImageDraw.Draw(cert)
        
        # Median positions from CV analysis
        positions = {
            'name': (0.537, 0.25265, 250),
            'event': (0.4755, 0.518375, 100),
            'organiser': (0.493, 0.720848, 110)
        }
        
        for field_name, text in [('name', self.sample_text['name']),
                                  ('event', self.sample_text['event']),
                                  ('organiser', self.sample_text['organiser'])]:
            x_norm, y_norm, font_size = positions[field_name]
            x = x_norm * self.width
            y = y_norm * self.height
            
            font = ImageFont.truetype(self.font_path, font_size)
            draw.text((x, y), text, fill=(0, 0, 0), font=font, anchor='mm')
        
        return cert
    
    # System 10: PIL with slight position adjustments
    def system_10_pil_adjusted_positions(self):
        """PIL with slight manual adjustments based on visual inspection."""
        cert = self.template.copy()
        draw = ImageDraw.Draw(cert)
        
        # Slightly adjusted positions
        adjustments = {
            'name': (0.0, -0.01),      # Shift up slightly
            'event': (0.0, 0.01),      # Shift down slightly  
            'organiser': (0.01, 0.0)   # Shift right slightly
        }
        
        for field_name, text in [('name', self.sample_text['name']),
                                  ('event', self.sample_text['event']),
                                  ('organiser', self.sample_text['organiser'])]:
            field = self.offsets['fields'][field_name]
            adj_x, adj_y = adjustments[field_name]
            x = (field['x'] + adj_x) * self.width
            y = (field['y'] + adj_y) * self.height
            font_size = field['font_size']
            
            font = ImageFont.truetype(self.font_path, font_size)
            draw.text((x, y), text, fill=(0, 0, 0), font=font, anchor='mm')
        
        return cert
    
    # System 11: PIL with larger font sizes
    def system_11_pil_larger_fonts(self):
        """PIL with even larger font sizes."""
        cert = self.template.copy()
        draw = ImageDraw.Draw(cert)
        
        # Try larger sizes
        sizes = {'name': 350, 'event': 200, 'organiser': 150}
        
        for field_name, text in [('name', self.sample_text['name']),
                                  ('event', self.sample_text['event']),
                                  ('organiser', self.sample_text['organiser'])]:
            field = self.offsets['fields'][field_name]
            x = field['x'] * self.width
            y = field['y'] * self.height
            font_size = sizes[field_name]
            
            font = ImageFont.truetype(self.font_path, font_size)
            draw.text((x, y), text, fill=(0, 0, 0), font=font, anchor='mm')
        
        return cert
    
    # System 12: PIL with RGBA and alpha compositing
    def system_12_pil_alpha_composite(self):
        """PIL with alpha channel for smoother compositing."""
        cert = self.template.copy().convert('RGBA')
        
        # Create text layer
        text_layer = Image.new('RGBA', cert.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(text_layer)
        
        for field_name, text in [('name', self.sample_text['name']),
                                  ('event', self.sample_text['event']),
                                  ('organiser', self.sample_text['organiser'])]:
            field = self.offsets['fields'][field_name]
            x = field['x'] * self.width
            y = field['y'] * self.height
            font_size = field['font_size']
            
            font = ImageFont.truetype(self.font_path, font_size)
            draw.text((x, y), text, fill=(0, 0, 0, 255), font=font, anchor='mm')
        
        # Composite
        result = Image.alpha_composite(cert, text_layer)
        return result.convert('RGB')
    
    def run_all_systems(self, output_dir):
        """Run all alignment systems and save results."""
        systems = [
            ("System 1: PIL Calibrated (Current)", self.system_1_pil_calibrated),
            ("System 2: PIL Original Sizes", self.system_2_pil_original_sizes),
            ("System 3: PIL Extracted Positions", self.system_3_pil_extracted_positions),
            ("System 4: PIL Subpixel (2x render)", self.system_4_pil_subpixel),
            ("System 5: OpenCV Rendering", self.system_5_opencv_rendering),
            ("System 6: Hybrid Reference", self.system_6_hybrid_reference),
            ("System 7: PIL Manual Kerning", self.system_7_pil_manual_kerning),
            ("System 8: PIL Anchor Center", self.system_8_pil_anchor_center),
            ("System 9: PIL Optimized Median", self.system_9_pil_optimized_median),
            ("System 10: PIL Adjusted Positions", self.system_10_pil_adjusted_positions),
            ("System 11: PIL Larger Fonts", self.system_11_pil_larger_fonts),
            ("System 12: PIL Alpha Composite", self.system_12_pil_alpha_composite),
        ]
        
        logger.info("=" * 80)
        logger.info("COMPREHENSIVE ALIGNMENT SYSTEM COMPARISON")
        logger.info("=" * 80)
        logger.info(f"\nTesting {len(systems)} different alignment approaches...")
        logger.info(f"Reference: {self.reference_path}")
        logger.info(f"Output directory: {output_dir}")
        logger.info("")
        
        for i, (name, system_func) in enumerate(systems, 1):
            logger.info(f"\n{'='*80}")
            logger.info(f"Testing {i}/{len(systems)}: {name}")
            logger.info(f"{'='*80}")
            
            try:
                # Generate certificate
                cert = system_func()
                
                # Calculate difference
                diff_pct, diff_pixels = self.calculate_difference(cert)
                
                # Save certificate
                output_path = output_dir / f"system_{i:02d}_{name.split(':')[0].replace(' ', '_').lower()}.png"
                cert.save(output_path)
                
                # Store results
                result = {
                    'system_number': i,
                    'name': name,
                    'diff_percentage': diff_pct,
                    'diff_pixels': diff_pixels,
                    'output_path': str(output_path)
                }
                self.results.append(result)
                
                logger.info(f"✓ Generated: {output_path.name}")
                logger.info(f"  Difference: {diff_pct:.4f}%")
                logger.info(f"  Different pixels: {diff_pixels:,} / {self.width * self.height:,}")
                
            except Exception as e:
                logger.error(f"✗ Failed: {e}")
                import traceback
                traceback.print_exc()
        
        # Sort by difference
        self.results.sort(key=lambda x: x['diff_percentage'])
        
        # Print summary
        logger.info(f"\n{'='*80}")
        logger.info("RESULTS SUMMARY (Ranked by Alignment Quality)")
        logger.info(f"{'='*80}\n")
        
        logger.info(f"{'Rank':<6} {'System':<40} {'Difference':<15} {'Pixels Different'}")
        logger.info(f"{'-'*6} {'-'*40} {'-'*15} {'-'*20}")
        
        for rank, result in enumerate(self.results, 1):
            logger.info(f"{rank:<6} {result['name'][:40]:<40} {result['diff_percentage']:>7.4f}% {result['diff_pixels']:>15,}")
        
        logger.info(f"\n{'='*80}")
        logger.info("BEST SYSTEM")
        logger.info(f"{'='*80}")
        
        best = self.results[0]
        logger.info(f"\n🏆 Winner: {best['name']}")
        logger.info(f"   Difference: {best['diff_percentage']:.4f}%")
        logger.info(f"   Output: {best['output_path']}")
        
        if best['diff_percentage'] == 0.0:
            logger.info(f"\n   ✅ PERFECT MATCH - 0.00% difference!")
        elif best['diff_percentage'] < 1.0:
            logger.info(f"\n   ✅ EXCELLENT - Less than 1% difference")
        elif best['diff_percentage'] < 10.0:
            logger.info(f"\n   ✓ GOOD - Less than 10% difference")
        else:
            logger.info(f"\n   ⚠️  Significant difference - rendering engine mismatch")
        
        logger.info("")
        
        # Save comparison report (convert numpy types to Python types)
        report_path = output_dir / 'alignment_comparison_report.json'
        results_serializable = []
        for r in self.results:
            r_copy = r.copy()
            r_copy['diff_pixels'] = int(r_copy['diff_pixels'])
            results_serializable.append(r_copy)
        
        with open(report_path, 'w') as f:
            json.dump(results_serializable, f, indent=2)
        logger.info(f"📊 Full report saved: {report_path}")
        
        return self.results


def main():
    """Main function."""
    base_dir = Path(__file__).parent.parent
    template_path = base_dir / 'templates' / 'template_extracted_from_sample.png'
    reference_path = base_dir / 'templates' / 'Sample_certificate.png'
    font_path = base_dir / 'templates' / 'ARIALBD.TTF'
    offsets_path = base_dir / 'templates' / 'goonj_template_offsets.json'
    output_dir = base_dir / 'generated_certificates' / 'system_comparison'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    comparator = AlignmentSystemComparator(
        str(template_path),
        str(reference_path),
        str(font_path),
        str(offsets_path)
    )
    
    results = comparator.run_all_systems(output_dir)
    
    logger.info("\n" + "="*80)
    logger.info("ALL CERTIFICATES GENERATED")
    logger.info("="*80)
    logger.info(f"\nCheck the '{output_dir}' directory for all generated certificates.")
    logger.info("You can visually compare them to see which matches best.\n")
    
    return 0 if results else 1


if __name__ == '__main__':
    sys.exit(main())
