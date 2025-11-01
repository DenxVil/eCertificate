#!/usr/bin/env python3
"""
Test alignment with PPTX-extracted positions

Uses the exact positions extracted from PowerPoint files.
"""
import os
import sys
from pathlib import Path
import json
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import cv2

sys.path.insert(0, str(Path(__file__).parent.parent))

def test_pptx_alignment():
    """Test alignment using PPTX-extracted positions."""
    base_dir = Path(__file__).parent.parent
    
    # Load PPTX-extracted positions
    pptx_offsets_path = base_dir / 'templates' / 'pptx_extracted_offsets.json'
    with open(pptx_offsets_path, 'r') as f:
        pptx_config = json.load(f)
    
    # Load reference and template
    reference_path = base_dir / 'templates' / 'Sample_certificate.png'
    template_path = base_dir / 'templates' / 'template_extracted_from_sample.png'
    font_path = base_dir / 'templates' / 'ARIALBD.TTF'
    
    reference = Image.open(reference_path).convert('RGB')
    template = Image.open(template_path).convert('RGB')
    width, height = template.size
    
    # Sample text
    sample_text = {
        'name': 'SAMPLE NAME',
        'event': 'SAMPLE EVENT',
        'organiser': 'SAMPLE ORG'
    }
    
    print("=" * 80)
    print("TESTING ALIGNMENT WITH PPTX-EXTRACTED POSITIONS")
    print("=" * 80)
    print()
    print(f"Reference: {reference_path}")
    print(f"Template: {template_path}")
    print(f"Image size: {width} x {height} px")
    print()
    
    # PowerPoint slide dimensions
    ppt_width = pptx_config['slide_dimensions']['width_pt']
    ppt_height = pptx_config['slide_dimensions']['height_pt']
    print(f"PowerPoint slide: {ppt_width} x {ppt_height} pt")
    print(f"Aspect ratio - PPT: {ppt_width/ppt_height:.4f}, PNG: {width/height:.4f}")
    print()
    
    # Generate certificate with PPTX positions
    print("Rendering with PPTX-extracted positions...")
    cert = template.copy()
    draw = ImageDraw.Draw(cert)
    
    for field_name in ['name', 'event', 'organiser']:
        field = pptx_config['fields'][field_name]
        text = sample_text[field_name]
        
        # Use PPTX positions directly
        x = field['x'] * width
        y = field['y'] * height
        font_size = field['font_size']
        
        print(f"\n{field_name.upper()}:")
        print(f"  Position: ({field['x']:.6f}, {field['y']:.6f})")
        print(f"  Pixel position: ({x:.1f}, {y:.1f})")
        print(f"  Font size: {font_size}pt")
        
        # Render text
        font = ImageFont.truetype(str(font_path), font_size)
        
        # Center text
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x_pos = x - text_width / 2
        y_pos = y - text_height / 2
        
        draw.text((x_pos, y_pos), text, fill=(0, 0, 0), font=font)
    
    # Save result
    output_dir = base_dir / 'generated_certificates'
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / 'pptx_aligned_certificate.png'
    cert.save(output_path)
    print(f"\n✅ Generated: {output_path}")
    
    # Calculate difference
    print("\nCalculating difference from reference...")
    gen_arr = np.array(cert)
    ref_arr = np.array(reference)
    
    diff = np.abs(gen_arr.astype(int) - ref_arr.astype(int))
    diff_mask = np.any(diff > 5, axis=2)
    
    total_pixels = diff_mask.size
    different_pixels = np.sum(diff_mask)
    diff_percentage = (different_pixels / total_pixels) * 100.0
    
    print(f"  Difference: {diff_percentage:.4f}%")
    print(f"  Different pixels: {different_pixels:,} / {total_pixels:,}")
    
    if diff_percentage < 1.0:
        print(f"\n  ✅ EXCELLENT - Less than 1% difference!")
    elif diff_percentage < 10.0:
        print(f"\n  ✓ GOOD - Less than 10% difference")
    elif diff_percentage < 20.0:
        print(f"\n  ⚠️  MODERATE - 10-20% difference")
    else:
        print(f"\n  ❌ SIGNIFICANT - Over 20% difference")
    
    print("\n" + "=" * 80)
    print("PPTX ALIGNMENT TEST COMPLETE")
    print("=" * 80)
    print("\nThe PPTX-extracted positions use font size 23pt")
    print("(vs previous calibrations of 70pt, 250pt, 489pt)")
    print("\nThis represents the EXACT layout from the PowerPoint file.")
    
    return diff_percentage


if __name__ == '__main__':
    diff = test_pptx_alignment()
    sys.exit(0 if diff < 20.0 else 1)
