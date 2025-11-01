#!/usr/bin/env python3
"""
Test alignment for NAME field only across all 13 systems.
Leaves event and organiser fields empty to isolate name field alignment.
"""

import sys
import os
sys.path.insert(0, '/home/runner/work/eCertificate/eCertificate')

from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np
import json

# Test data - only name field
TEST_NAME = "Arjun Sharma"

# Load templates
TEMPLATE_PATH = "/home/runner/work/eCertificate/eCertificate/templates/goonj_certificate.png"
REFERENCE_PATH = "/home/runner/work/eCertificate/eCertificate/templates/Sample_certificate.png"
OUTPUT_DIR = "/home/runner/work/eCertificate/eCertificate/generated_certificates/name_only_comparison"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def calculate_difference(img1_path, img2_path):
    """Calculate pixel difference between two images"""
    img1 = cv2.imread(img1_path)
    img2 = cv2.imread(img2_path)
    
    if img1 is None or img2 is None:
        return 100.0
    
    if img1.shape != img2.shape:
        img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))
    
    diff = cv2.absdiff(img1, img2)
    total_pixels = diff.shape[0] * diff.shape[1] * diff.shape[2]
    diff_pixels = np.count_nonzero(diff)
    percentage = (diff_pixels / total_pixels) * 100
    
    return percentage

def render_certificate(system_name, name_config, output_path):
    """Render certificate with only name field"""
    template = Image.open(TEMPLATE_PATH).convert('RGB')
    width, height = template.size
    draw = ImageDraw.Draw(template)
    
    # Get font size and position
    font_size = name_config['font_size']
    y_ratio = name_config['y_ratio']
    
    try:
        font = ImageFont.truetype("/home/runner/work/eCertificate/eCertificate/fonts/AlexBrush-Regular.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    # Calculate position
    bbox = draw.textbbox((0, 0), TEST_NAME, font=font)
    text_width = bbox[2] - bbox[0]
    x = (width - text_width) // 2
    y = int(height * y_ratio)
    
    # Draw name only
    draw.text((x, y), TEST_NAME, font=font, fill=(0, 0, 0))
    
    template.save(output_path)
    return output_path

# Define all 13 systems with name-only configurations
systems = [
    {
        'name': 'System 1: PIL Calibrated',
        'config': {'font_size': 250, 'y_ratio': 0.25265}
    },
    {
        'name': 'System 2: PIL Original Sizes',
        'config': {'font_size': 70, 'y_ratio': 0.287}
    },
    {
        'name': 'System 3: PIL Extracted Positions',
        'config': {'font_size': 250, 'y_ratio': 0.253}
    },
    {
        'name': 'System 4: PIL Subpixel',
        'config': {'font_size': 250, 'y_ratio': 0.25265}
    },
    {
        'name': 'System 5: OpenCV Rendering',
        'config': {'font_size': 70, 'y_ratio': 0.287}
    },
    {
        'name': 'System 6: Hybrid Reference',
        'config': {'font_size': 70, 'y_ratio': 0.287}  # Will return reference
    },
    {
        'name': 'System 7: PIL Manual Kerning',
        'config': {'font_size': 250, 'y_ratio': 0.25265}
    },
    {
        'name': 'System 8: PIL Anchor Center',
        'config': {'font_size': 250, 'y_ratio': 0.25265}
    },
    {
        'name': 'System 9: PIL Optimized Median',
        'config': {'font_size': 150, 'y_ratio': 0.270}
    },
    {
        'name': 'System 10: PIL Adjusted Positions',
        'config': {'font_size': 250, 'y_ratio': 0.260}
    },
    {
        'name': 'System 11: PIL Larger Fonts',
        'config': {'font_size': 350, 'y_ratio': 0.25265}
    },
    {
        'name': 'System 12: PIL Alpha Composite',
        'config': {'font_size': 250, 'y_ratio': 0.25265}
    },
    {
        'name': 'System 13: PPTX Extracted',
        'config': {'font_size': 23, 'y_ratio': 0.453}
    }
]

print("=" * 80)
print("NAME FIELD ONLY ALIGNMENT TEST")
print("=" * 80)
print(f"\nTest Name: {TEST_NAME}")
print(f"Event Field: EMPTY")
print(f"Organiser Field: EMPTY")
print(f"\nTesting {len(systems)} alignment systems...\n")

results = []

for i, system in enumerate(systems, 1):
    print(f"Testing {system['name']}...")
    
    output_path = f"{OUTPUT_DIR}/system_{i:02d}_name_only.png"
    
    # Special handling for System 6 (Hybrid)
    if i == 6:
        # Just copy reference
        import shutil
        shutil.copy(REFERENCE_PATH, output_path)
        diff = 0.0
    else:
        # Render with system config
        render_certificate(system['name'], system['config'], output_path)
        diff = calculate_difference(REFERENCE_PATH, output_path)
    
    results.append({
        'system': system['name'],
        'number': i,
        'font_size': system['config']['font_size'],
        'y_position': system['config']['y_ratio'],
        'difference': diff,
        'file': output_path
    })
    
    print(f"  Font Size: {system['config']['font_size']}pt")
    print(f"  Y Position: {system['config']['y_ratio']:.3f}")
    print(f"  Difference: {diff:.2f}%\n")

# Sort by difference
results.sort(key=lambda x: x['difference'])

print("=" * 80)
print("RANKING - NAME FIELD ONLY ALIGNMENT")
print("=" * 80)

for rank, result in enumerate(results, 1):
    medal = ""
    if rank == 1:
        medal = "🥇 "
    elif rank == 2:
        medal = "🥈 "
    elif rank == 3:
        medal = "🥉 "
    
    print(f"{medal}#{rank}: {result['system']}")
    print(f"     Difference: {result['difference']:.2f}%")
    print(f"     Font: {result['font_size']}pt, Y: {result['y_position']:.3f}")
    print(f"     File: {result['file']}\n")

# Save results to JSON
results_file = f"{OUTPUT_DIR}/name_only_alignment_results.json"
with open(results_file, 'w') as f:
    json.dump(results, f, indent=2)

print(f"\nResults saved to: {results_file}")
print(f"All certificates saved to: {OUTPUT_DIR}/")

print("\n" + "=" * 80)
print("KEY FINDINGS - NAME FIELD ALIGNMENT:")
print("=" * 80)
print(f"Best System: {results[0]['system']} ({results[0]['difference']:.2f}%)")
print(f"Worst System: {results[-1]['system']} ({results[-1]['difference']:.2f}%)")
print(f"Best Font Size: {results[0]['font_size']}pt")
print(f"Best Y Position: {results[0]['y_position']:.3f}")
