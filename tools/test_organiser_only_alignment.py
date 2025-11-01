#!/usr/bin/env python3
"""
Test alignment for ORGANISER field only across all 13 systems.
Leaves name and event fields empty to isolate organiser field alignment.
"""

import sys
import os
sys.path.insert(0, '/home/runner/work/eCertificate/eCertificate')

from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np
import json

# Test data - only organiser field
TEST_ORGANISER = "IETE-SF"

# Load templates
TEMPLATE_PATH = "/home/runner/work/eCertificate/eCertificate/templates/goonj_certificate.png"
REFERENCE_PATH = "/home/runner/work/eCertificate/eCertificate/templates/Sample_certificate.png"
OUTPUT_DIR = "/home/runner/work/eCertificate/eCertificate/generated_certificates/organiser_only_comparison"

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

def render_certificate(system_name, organiser_config, output_path):
    """Render certificate with only organiser field"""
    template = Image.open(TEMPLATE_PATH).convert('RGB')
    width, height = template.size
    draw = ImageDraw.Draw(template)
    
    # Get font size and position
    font_size = organiser_config['font_size']
    y_ratio = organiser_config['y_ratio']
    
    try:
        font = ImageFont.truetype("/home/runner/work/eCertificate/eCertificate/fonts/AlexBrush-Regular.ttf", font_size)
    except:
        font = ImageFont.load_default()
    
    # Calculate position
    bbox = draw.textbbox((0, 0), TEST_ORGANISER, font=font)
    text_width = bbox[2] - bbox[0]
    x = (width - text_width) // 2
    y = int(height * y_ratio)
    
    # Draw organiser only
    draw.text((x, y), TEST_ORGANISER, font=font, fill=(0, 0, 0))
    
    template.save(output_path)
    return output_path

# Define all 13 systems with organiser-only configurations
systems = [
    {
        'name': 'System 1: PIL Calibrated',
        'config': {'font_size': 110, 'y_ratio': 0.72104}  # From goonj_renderer.py
    },
    {
        'name': 'System 2: PIL Original Sizes',
        'config': {'font_size': 59, 'y_ratio': 0.706}  # Original
    },
    {
        'name': 'System 3: PIL Extracted Positions',
        'config': {'font_size': 110, 'y_ratio': 0.721}  # CV extracted
    },
    {
        'name': 'System 4: PIL Subpixel',
        'config': {'font_size': 220, 'y_ratio': 0.72104}  # 2x render
    },
    {
        'name': 'System 5: OpenCV Rendering',
        'config': {'font_size': 59, 'y_ratio': 0.706}  # Similar to original
    },
    {
        'name': 'System 6: Hybrid Reference',
        'config': {'font_size': 59, 'y_ratio': 0.706}  # Will return reference
    },
    {
        'name': 'System 7: PIL Manual Kerning',
        'config': {'font_size': 110, 'y_ratio': 0.72104}
    },
    {
        'name': 'System 8: PIL Anchor Center',
        'config': {'font_size': 110, 'y_ratio': 0.72104}
    },
    {
        'name': 'System 9: PIL Optimized Median',
        'config': {'font_size': 85, 'y_ratio': 0.713}  # Median of approaches
    },
    {
        'name': 'System 10: PIL Adjusted Positions',
        'config': {'font_size': 110, 'y_ratio': 0.715}  # Slightly adjusted
    },
    {
        'name': 'System 11: PIL Larger Fonts',
        'config': {'font_size': 150, 'y_ratio': 0.72104}
    },
    {
        'name': 'System 12: PIL Alpha Composite',
        'config': {'font_size': 110, 'y_ratio': 0.72104}
    },
    {
        'name': 'System 13: PPTX Extracted',
        'config': {'font_size': 23, 'y_ratio': 0.687}  # From PowerPoint
    }
]

print("=" * 80)
print("ORGANISER FIELD ALIGNMENT TEST - ALL 13 SYSTEMS")
print("=" * 80)
print(f"Test organiser: {TEST_ORGANISER}")
print(f"Output directory: {OUTPUT_DIR}")
print()

results = []

for i, system in enumerate(systems, 1):
    system_num = f"system_{i:02d}"
    output_path = os.path.join(OUTPUT_DIR, f"{system_num}_organiser_only.png")
    
    # System 6 uses reference directly
    if i == 6:
        # Copy reference
        import shutil
        shutil.copy(REFERENCE_PATH, output_path)
        diff = 0.0
    else:
        render_certificate(system['name'], system['config'], output_path)
        diff = calculate_difference(REFERENCE_PATH, output_path)
    
    results.append({
        'system': system['name'],
        'number': i,
        'font_size': system['config']['font_size'],
        'y_ratio': system['config']['y_ratio'],
        'difference': diff,
        'output': output_path
    })
    
    print(f"System {i:2d}: {system['name']:<30s} | "
          f"Font: {system['config']['font_size']:3d}pt | "
          f"Y: {system['config']['y_ratio']:.3f} | "
          f"Diff: {diff:6.2f}%")

print()
print("=" * 80)
print("RESULTS SUMMARY (Sorted by difference)")
print("=" * 80)

sorted_results = sorted(results, key=lambda x: x['difference'])
for rank, result in enumerate(sorted_results, 1):
    medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "  "
    print(f"{medal} Rank {rank:2d}: System {result['number']:2d} - {result['difference']:6.2f}% - {result['system']}")

# Create visual comparison grid
print()
print("Creating visual comparison grid...")

# Load all images
images = []
labels = []
for result in sorted_results[:6]:  # Top 6 systems
    img = cv2.imread(result['output'])
    if img is not None:
        images.append(img)
        labels.append(f"S{result['number']}: {result['difference']:.2f}%")

if len(images) >= 6:
    # Create 2x3 grid
    h, w = images[0].shape[:2]
    grid = np.zeros((h * 2, w * 3, 3), dtype=np.uint8)
    
    for idx, (img, label) in enumerate(zip(images[:6], labels[:6])):
        row = idx // 3
        col = idx % 3
        
        # Add label
        img_copy = img.copy()
        cv2.putText(img_copy, label, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 
                    1.0, (255, 0, 0), 2, cv2.LINE_AA)
        
        grid[row*h:(row+1)*h, col*w:(col+1)*w] = img_copy
    
    grid_path = os.path.join(OUTPUT_DIR, "organiser_field_comparison_grid.png")
    cv2.imwrite(grid_path, grid)
    print(f"✅ Comparison grid saved: {grid_path}")

# Create heatmap for System 13 (PPTX)
print("Creating difference heatmap for System 13...")
system_13_result = [r for r in results if r['number'] == 13][0]
ref_img = cv2.imread(REFERENCE_PATH)
sys_img = cv2.imread(system_13_result['output'])

if ref_img is not None and sys_img is not None:
    diff = cv2.absdiff(ref_img, sys_img)
    diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    heatmap = cv2.applyColorMap(diff_gray, cv2.COLORMAP_JET)
    
    # Create side-by-side with heatmap
    combined = np.hstack([sys_img, heatmap])
    cv2.putText(combined, "System 13 (PPTX)", (20, 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(combined, "Difference Heatmap", (w + 20, 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2, cv2.LINE_AA)
    
    heatmap_path = os.path.join(OUTPUT_DIR, "organiser_field_heatmap_system13.png")
    cv2.imwrite(heatmap_path, combined)
    print(f"✅ Heatmap saved: {heatmap_path}")

print()
print("=" * 80)
print("KEY FINDINGS")
print("=" * 80)

# Analyze results
diffs = [r['difference'] for r in results if r['number'] != 6]  # Exclude hybrid reference
avg_diff = np.mean(diffs)
std_diff = np.std(diffs)
min_diff = min(diffs)
max_diff = max(diffs)

print(f"Average difference (excluding System 6): {avg_diff:.2f}%")
print(f"Standard deviation: {std_diff:.2f}%")
print(f"Min difference: {min_diff:.2f}%")
print(f"Max difference: {max_diff:.2f}%")
print()

# Check if similar to name field baseline
print("Compared to NAME field baseline (13.42%):")
if avg_diff < 15:
    print(f"✅ Organiser field achieves similar baseline ({avg_diff:.2f}% vs 13.42%)")
else:
    print(f"⚠️  Organiser field shows different pattern ({avg_diff:.2f}% vs 13.42%)")

print()
print("All certificates saved in:", OUTPUT_DIR)
print("=" * 80)

# Save results to JSON
results_json_path = os.path.join(OUTPUT_DIR, "organiser_field_results.json")
with open(results_json_path, 'w') as f:
    json.dump(results, f, indent=2)
print(f"Results saved to: {results_json_path}")
