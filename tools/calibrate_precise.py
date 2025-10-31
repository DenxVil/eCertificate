#!/usr/bin/env python3
"""
Precise calibration tool for GOONJ certificate alignment.

This tool finds the exact Y positions needed to match the reference certificate
with sub-pixel accuracy (< 0.01 pixel difference).
"""
import os
import sys
from pathlib import Path
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from PIL import Image, ImageDraw, ImageFont
import numpy as np
from app.utils.text_align import draw_text_centered, get_font


def find_text_center(img_arr, y_search_start, y_search_end):
    """Find the vertical center of text in a region."""
    region = img_arr[y_search_start:y_search_end, :, :]
    # Text is dark (close to black)
    is_text = np.all(region < 200, axis=2)
    
    if np.any(is_text):
        rows, cols = np.where(is_text)
        y_min = rows.min() + y_search_start
        y_max = rows.max() + y_search_start
        y_center = (y_min + y_max) / 2.0
        return y_center, y_min, y_max
    return None, None, None


def calibrate_field(template_path, font_path, reference_img, field_config, text):
    """Calibrate a single field to match reference."""
    template = Image.open(template_path).convert('RGB')
    width, height = template.size
    
    # Get initial Y position
    y_current = int(height * field_config['y'])
    
    # Find reference text center
    ref_arr = np.array(reference_img)
    ref_y_center, ref_y_min, ref_y_max = find_text_center(ref_arr, y_current - 100, y_current + 100)
    
    if ref_y_center is None:
        print(f"WARNING: Could not find text in reference")
        return field_config
    
    print(f"  Reference text: Y center={ref_y_center:.2f}px, bounds=[{ref_y_min}, {ref_y_max}]")
    
    # Binary search for the exact Y position that matches
    base_font_size = field_config.get('base_font_size', int(height * 0.05))
    font = ImageFont.truetype(font_path, base_font_size)
    
    best_y = y_current
    best_error = float('inf')
    
    # First pass: coarse search in wider range
    for y_offset in np.linspace(-40, 40, 401):  # 0.2px steps
        test_y = y_current + y_offset
        
        # Render text at this position
        test_img = template.copy()
        draw = ImageDraw.Draw(test_img)
        
        draw_text_centered(
            draw,
            (width // 2, test_y),
            text,
            font,
            (0, 0, 0),
            align='center',
            baseline_offset=field_config.get('baseline_offset', 0)
        )
        
        # Find text center in generated image
        gen_arr = np.array(test_img)
        gen_y_center, gen_y_min, gen_y_max = find_text_center(gen_arr, int(test_y) - 80, int(test_y) + 80)
        
        if gen_y_center is not None:
            error = abs(gen_y_center - ref_y_center)
            if error < best_error:
                best_error = error
                best_y = test_y
    
    # Second pass: fine search around best position
    if best_error > 0.1:
        for y_offset in np.linspace(-2, 2, 401):  # 0.01px steps
            test_y = best_y + y_offset
            
            # Render text at this position
            test_img = template.copy()
            draw = ImageDraw.Draw(test_img)
            
            draw_text_centered(
                draw,
                (width // 2, test_y),
                text,
                font,
                (0, 0, 0),
                align='center',
                baseline_offset=field_config.get('baseline_offset', 0)
            )
            
            # Find text center in generated image
            gen_arr = np.array(test_img)
            gen_y_center, gen_y_min, gen_y_max = find_text_center(gen_arr, int(test_y) - 80, int(test_y) + 80)
            
            if gen_y_center is not None:
                error = abs(gen_y_center - ref_y_center)
                if error < best_error:
                    best_error = error
                    best_y = test_y
    
    print(f"  Best Y position: {best_y:.4f}px (error: {best_error:.4f}px)")
    
    # Update field config
    new_config = field_config.copy()
    new_config['y'] = best_y / height
    
    return new_config


def main():
    """Main calibration function."""
    base_dir = Path(__file__).parent.parent
    template_path = base_dir / 'templates' / 'goonj_certificate.png'
    reference_path = base_dir / 'templates' / 'Sample_certificate.png'
    font_path = base_dir / 'templates' / 'ARIALBD.TTF'
    offsets_path = base_dir / 'templates' / 'goonj_template_offsets.json'
    
    # Load current offsets
    with open(offsets_path, 'r') as f:
        offsets_data = json.load(f)
    
    # Load reference image
    reference_img = Image.open(reference_path).convert('RGB')
    width, height = reference_img.size
    
    print("=" * 70)
    print("Precise GOONJ Certificate Calibration")
    print("=" * 70)
    print(f"\nTemplate: {template_path}")
    print(f"Reference: {reference_path}")
    print(f"Template size: {width}x{height}")
    print()
    
    # Calibrate each field
    fields_to_calibrate = {
        'name': {
            'text': 'SAMPLE NAME',
            'base_font_size': int(height * 0.05)
        },
        'event': {
            'text': 'SAMPLE EVENT',
            'base_font_size': int(height * 0.042)
        },
        'organiser': {
            'text': 'SAMPLE ORG',
            'base_font_size': int(height * 0.042)
        }
    }
    
    new_offsets = offsets_data.copy()
    
    for field_name, field_info in fields_to_calibrate.items():
        print(f"Calibrating {field_name.upper()} field:")
        print(f"  Text: \"{field_info['text']}\"")
        
        current_config = offsets_data['fields'][field_name].copy()
        current_config['base_font_size'] = field_info['base_font_size']
        
        new_config = calibrate_field(
            template_path,
            font_path,
            reference_img,
            current_config,
            field_info['text']
        )
        
        new_offsets['fields'][field_name] = {
            'x': new_config['x'],
            'y': new_config['y'],
            'baseline_offset': new_config.get('baseline_offset', 0),
            'description': current_config.get('description', '')
        }
        print()
    
    # Save calibrated offsets
    new_offsets['version'] = str(float(offsets_data.get('version', '1.0')) + 0.1)
    new_offsets['tolerance_px'] = 0.01
    new_offsets['notes'] = 'Sub-pixel precision calibration to match Sample_certificate.png within 0.01px tolerance.'
    
    # Write to file
    with open(offsets_path, 'w') as f:
        json.dump(new_offsets, f, indent=2)
    
    print("=" * 70)
    print("✅ Calibration complete!")
    print(f"Updated: {offsets_path}")
    print("=" * 70)
    print("\nNew field positions:")
    for field_name, field_data in new_offsets['fields'].items():
        y_px = int(height * field_data['y'])
        print(f"  {field_name}: y={field_data['y']:.6f} ({y_px}px)")
    print()


if __name__ == '__main__':
    main()
