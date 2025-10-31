#!/usr/bin/env python3
"""
Visual Alignment Diagnostic Tool

Creates side-by-side and overlay comparisons of generated vs reference certificates
to visually diagnose alignment issues.
"""
import os
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageChops
import cv2

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.goonj_renderer import GOONJRenderer

def create_visual_comparison(reference_path, generated_path, output_dir):
    """Create visual comparison images."""
    ref_img = Image.open(reference_path).convert('RGB')
    gen_img = Image.open(generated_path).convert('RGB')
    
    width, height = ref_img.size
    
    # 1. Side-by-side comparison
    sidebyside = Image.new('RGB', (width * 2 + 20, height), (255, 255, 255))
    sidebyside.paste(ref_img, (0, 0))
    sidebyside.paste(gen_img, (width + 20, 0))
    
    draw = ImageDraw.Draw(sidebyside)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
    except:
        font = ImageFont.load_default()
    
    draw.text((width // 2 - 100, 20), "REFERENCE", fill=(255, 0, 0), font=font)
    draw.text((width + width // 2 - 100, 20), "GENERATED", fill=(0, 0, 255), font=font)
    
    sidebyside_path = output_dir / 'comparison_sidebyside.png'
    sidebyside.save(sidebyside_path)
    print(f"✓ Saved side-by-side comparison: {sidebyside_path}")
    
    # 2. Difference map (heatmap)
    diff = ImageChops.difference(ref_img, gen_img)
    diff_array = np.array(diff)
    diff_gray = np.max(diff_array, axis=2)  # Max across RGB channels
    
    # Create heatmap
    diff_heatmap = cv2.applyColorMap(diff_gray, cv2.COLORMAP_JET)
    diff_heatmap_path = output_dir / 'comparison_heatmap.png'
    cv2.imwrite(str(diff_heatmap_path), diff_heatmap)
    print(f"✓ Saved difference heatmap: {diff_heatmap_path}")
    
    # 3. Overlay with transparency
    overlay = Image.blend(ref_img, gen_img, alpha=0.5)
    overlay_path = output_dir / 'comparison_overlay.png'
    overlay.save(overlay_path)
    print(f"✓ Saved overlay comparison: {overlay_path}")
    
    # 4. Red/Green comparison (reference=red, generated=green, overlap=yellow)
    ref_array = np.array(ref_img)
    gen_array = np.array(gen_img)
    
    redgreen = np.zeros_like(ref_array)
    redgreen[:, :, 0] = 255 - ref_array[:, :, 0]  # Red channel from reference
    redgreen[:, :, 1] = 255 - gen_array[:, :, 1]  # Green channel from generated
    
    redgreen_img = Image.fromarray(redgreen)
    redgreen_path = output_dir / 'comparison_redgreen.png'
    redgreen_img.save(redgreen_path)
    print(f"✓ Saved red/green comparison: {redgreen_path}")
    
    # 5. Text regions highlighted
    highlighted_ref = ref_img.copy()
    highlighted_gen = gen_img.copy()
    
    draw_ref = ImageDraw.Draw(highlighted_ref)
    draw_gen = ImageDraw.Draw(highlighted_gen)
    
    # Load offsets
    import json
    offsets_path = Path(__file__).parent.parent / 'templates' / 'goonj_template_offsets.json'
    with open(offsets_path) as f:
        offsets = json.load(f)
    
    colors = {'name': (255, 0, 0), 'event': (0, 255, 0), 'organiser': (0, 0, 255)}
    
    for field in ['name', 'event', 'organiser']:
        if field in offsets['fields']:
            x = offsets['fields'][field]['x'] * width
            y = offsets['fields'][field]['y'] * height
            
            # Draw crosshair
            size = 50
            draw_ref.line([(x - size, y), (x + size, y)], fill=colors[field], width=3)
            draw_ref.line([(x, y - size), (x, y + size)], fill=colors[field], width=3)
            draw_gen.line([(x - size, y), (x + size, y)], fill=colors[field], width=3)
            draw_gen.line([(x, y - size), (x, y + size)], fill=colors[field], width=3)
            
            # Draw text
            draw_ref.text((x + 60, y - 15), field.upper(), fill=colors[field], font=font)
            draw_gen.text((x + 60, y - 15), field.upper(), fill=colors[field], font=font)
    
    highlighted_path = output_dir / 'comparison_highlighted.png'
    highlighted_combined = Image.new('RGB', (width * 2 + 20, height), (255, 255, 255))
    highlighted_combined.paste(highlighted_ref, (0, 0))
    highlighted_combined.paste(highlighted_gen, (width + 20, 0))
    highlighted_combined.save(highlighted_path)
    print(f"✓ Saved highlighted comparison: {highlighted_path}")
    
    return {
        'sidebyside': sidebyside_path,
        'heatmap': diff_heatmap_path,
        'overlay': overlay_path,
        'redgreen': redgreen_path,
        'highlighted': highlighted_path
    }


def main():
    """Main function."""
    base_dir = Path(__file__).parent.parent
    template_path = base_dir / 'templates' / 'goonj_certificate.png'
    reference_path = base_dir / 'templates' / 'Sample_certificate.png'
    output_dir = base_dir / 'generated_certificates'
    
    print("=" * 80)
    print("VISUAL ALIGNMENT DIAGNOSTIC")
    print("=" * 80)
    print()
    
    # Generate sample certificate
    print("Generating sample certificate...")
    sample_data = {
        'name': 'SAMPLE NAME',
        'event': 'SAMPLE EVENT',
        'organiser': 'SAMPLE ORG'
    }
    
    renderer = GOONJRenderer(str(template_path), str(output_dir))
    cert_path = renderer.render(sample_data, output_format='png')
    print(f"✓ Generated: {cert_path}")
    print()
    
    # Create comparisons
    print("Creating visual comparisons...")
    comparisons = create_visual_comparison(reference_path, cert_path, output_dir)
    
    print()
    print("=" * 80)
    print("DIAGNOSTIC COMPLETE")
    print("=" * 80)
    print()
    print("Visual comparison files created:")
    for name, path in comparisons.items():
        print(f"  {name}: {path}")
    print()
    print("Review these files to diagnose alignment issues visually.")
    print()


if __name__ == '__main__':
    main()
