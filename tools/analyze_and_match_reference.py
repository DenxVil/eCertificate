#!/usr/bin/env python3
"""
Analyze Reference Certificate and Match Font Parameters

This tool analyzes the Sample_certificate.png to determine:
1. Exact text content
2. Font sizes used
3. Text positions  
4. Rendering parameters

Then creates a matching configuration.
"""
import os
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import cv2
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

def analyze_text_regions(img_path):
    """Analyze text regions in the reference certificate."""
    img = Image.open(img_path).convert('RGB')
    img_array = np.array(img)
    height, width = img_array.shape[:2]
    
    # Convert to grayscale
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    
    # Threshold to find text
    _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
    
    # Find contours
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Filter and group contours by vertical bands
    bands = {
        'name': (int(height * 0.15), int(height * 0.40)),
        'event': (int(height * 0.40), int(height * 0.65)),
        'organiser': (int(height * 0.65), int(height * 0.85))
    }
    
    text_info = {}
    
    for field, (y_min, y_max) in bands.items():
        # Find contours in this band
        band_contours = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            center_y = y + h / 2
            if y_min <= center_y <= y_max and w > 20 and h > 15:
                band_contours.append((x, y, w, h))
        
        if band_contours:
            # Get bounding box of all contours in this field
            min_x = min(c[0] for c in band_contours)
            min_y = min(c[1] for c in band_contours)
            max_x = max(c[0] + c[2] for c in band_contours)
            max_y = max(c[1] + c[3] for c in band_contours)
            
            text_width = max_x - min_x
            text_height = max_y - min_y
            center_x = (min_x + max_x) / 2
            center_y = (min_y + max_y) / 2
            
            text_info[field] = {
                'bbox': (min_x, min_y, max_x, max_y),
                'width_px': text_width,
                'height_px': text_height,
                'center_x': center_x / width,
                'center_y': center_y / height,
                'center_x_px': center_x,
                'center_y_px': center_y,
                'estimated_font_size': int(text_height * 0.8)  # Approx font size from text height
            }
    
    return text_info, width, height


def estimate_font_sizes_by_matching(template_path, font_path, expected_texts):
    """Estimate font sizes by rendering and matching."""
    # Load template
    template = Image.open(template_path)
    width, height = template.size
    
    font_sizes = {}
    
    # Known text that should be in the reference
    test_texts = {
        'name': 'SAMPLE NAME',
        'event': 'SAMPLE EVENT',
        'organiser': 'SAMPLE ORG'
    }
    
    # For each field, try different font sizes and measure text
    for field in ['name', 'event', 'organiser']:
        text = test_texts[field]
        
        # Try a range of font sizes
        best_size = None
        target_height = expected_texts[field]['height_px'] if field in expected_texts else 100
        
        for size in range(30, 200, 5):
            try:
                font = ImageFont.truetype(font_path, size)
                bbox = font.getbbox(text)
                text_height = bbox[3] - bbox[1]
                
                # Check if this matches our target
                if abs(text_height - target_height) < 10:
                    best_size = size
                    break
            except:
                continue
        
        if not best_size:
            # Fallback: estimate from target height
            best_size = int(target_height * 1.2)
        
        font_sizes[field] = best_size
    
    return font_sizes


def main():
    """Main function."""
    base_dir = Path(__file__).parent.parent
    reference_path = base_dir / 'templates' / 'Sample_certificate.png'
    font_path = base_dir / 'templates' / 'ARIALBD.TTF'
    
    print("=" * 80)
    print("REFERENCE CERTIFICATE ANALYSIS")
    print("=" * 80)
    print()
    
    # Analyze reference
    print(f"Analyzing: {reference_path}")
    text_info, width, height = analyze_text_regions(reference_path)
    
    print(f"\nImage dimensions: {width} x {height}")
    print("\nText regions found:")
    print()
    
    for field, info in text_info.items():
        print(f"{field.upper()}:")
        print(f"  Bounding box: {info['bbox']}")
        print(f"  Size: {info['width_px']:.0f} x {info['height_px']:.0f} px")
        print(f"  Center: ({info['center_x_px']:.1f}, {info['center_y_px']:.1f})")
        print(f"  Normalized: ({info['center_x']:.6f}, {info['center_y']:.6f})")
        print(f"  Estimated font size: {info['estimated_font_size']}pt")
        print()
    
    # Estimate font sizes
    print("Estimating font sizes by matching...")
    font_sizes = estimate_font_sizes_by_matching(
        base_dir / 'templates' / 'template_extracted_from_sample.png',
        font_path,
        text_info
    )
    
    print("\nRecommended font sizes:")
    for field, size in font_sizes.items():
        print(f"  {field}: {size}pt")
    
    # Create updated configuration
    config = {
        'version': '5.0',
        'extraction_date': '2025-10-31',
        'analysis_method': 'contour_detection_and_matching',
        'reference_image': str(reference_path),
        'dimensions': {'width': width, 'height': height},
        'fields': {}
    }
    
    for field in ['name', 'event', 'organiser']:
        if field in text_info:
            config['fields'][field] = {
                'x': text_info[field]['center_x'],
                'y': text_info[field]['center_y'],
                'font_size': font_sizes.get(field, text_info[field]['estimated_font_size']),
                'font_size_normalized': font_sizes.get(field, text_info[field]['estimated_font_size']) / height,
                'baseline_offset': 0,
                'text_height_px': text_info[field]['height_px'],
                'text_width_px': text_info[field]['width_px']
            }
    
    # Save configuration
    output_path = base_dir / 'templates' / 'analyzed_reference_config.json'
    with open(output_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\n✓ Configuration saved to: {output_path}")
    print()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
