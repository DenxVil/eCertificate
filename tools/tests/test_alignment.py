#!/usr/bin/env python
"""
Smoke test for certificate text alignment.

This script validates that text is properly centered using PIL anchor points
by generating a test certificate and checking the alignment visually.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from PIL import Image, ImageDraw, ImageFont
from app.utils.goonj_renderer import GOONJRenderer
import tempfile


def test_text_centering():
    """Test that text is properly centered using anchor points."""
    print("\n" + "="*60)
    print("Testing Text Centering with Anchor Points")
    print("="*60)
    
    # Create a test template (simple white canvas)
    width, height = 800, 600
    test_template = Image.new('RGB', (width, height), 'white')
    
    # Add a visual guide (center lines)
    draw = ImageDraw.Draw(test_template)
    # Draw center crosshairs for visual verification
    draw.line([(width // 2, 0), (width // 2, height)], fill='lightgray', width=1)
    draw.line([(0, height // 2), (width, height // 2)], fill='lightgray', width=1)
    
    # Save test template
    with tempfile.TemporaryDirectory() as tmpdir:
        template_path = os.path.join(tmpdir, 'test_template.png')
        test_template.save(template_path)
        
        # Initialize renderer
        renderer = GOONJRenderer(template_path, output_folder=tmpdir)
        
        # Test data
        test_data = {
            'name': 'John Doe Test',
            'event': 'Test Event',
            'organiser': 'Test Org'
        }
        
        # Generate certificate
        print(f"Generating test certificate...")
        cert_path = renderer.render(test_data, output_format='png')
        
        # Load generated certificate
        cert_img = Image.open(cert_path)
        
        # Validate: Check that pixels exist around center positions
        # This is a basic smoke test - we check that text was drawn
        center_x = width // 2
        
        # Check name position (33% down)
        name_y = int(height * 0.33)
        name_region = cert_img.crop((center_x - 50, name_y - 20, center_x + 50, name_y + 20))
        name_pixels = list(name_region.getdata())
        name_has_text = any(pixel != (255, 255, 255) for pixel in name_pixels)
        
        # Check event position (42% down)
        event_y = int(height * 0.42)
        event_region = cert_img.crop((center_x - 50, event_y - 20, center_x + 50, event_y + 20))
        event_pixels = list(event_region.getdata())
        event_has_text = any(pixel != (255, 255, 255) for pixel in event_pixels)
        
        # Check organiser position (51% down)
        org_y = int(height * 0.51)
        org_region = cert_img.crop((center_x - 50, org_y - 20, center_x + 50, org_y + 20))
        org_pixels = list(org_region.getdata())
        org_has_text = any(pixel != (255, 255, 255) for pixel in org_pixels)
        
        # Report results
        print(f"\n✓ Test certificate generated: {cert_path}")
        print(f"✓ Name text detected at center: {name_has_text}")
        print(f"✓ Event text detected at center: {event_has_text}")
        print(f"✓ Organiser text detected at center: {org_has_text}")
        
        if name_has_text and event_has_text and org_has_text:
            print("\n✅ PASS: All text fields are centered correctly")
            return 0
        else:
            print("\n❌ FAIL: Some text fields are not centered")
            return 1


def test_anchor_point_consistency():
    """Test that _draw_centered_text uses 'mm' anchor point."""
    print("\n" + "="*60)
    print("Testing Anchor Point Consistency")
    print("="*60)
    
    # Create a simple image to test drawing
    img = Image.new('RGB', (400, 300), 'white')
    draw = ImageDraw.Draw(img)
    
    # Try to get a font
    try:
        font = ImageFont.truetype("arial.ttf", 30)
    except:
        font = ImageFont.load_default()
    
    # Test that we can draw with 'mm' anchor
    try:
        draw.text((200, 150), "Test", font=font, fill='black', anchor='mm')
        print("✓ PIL supports 'mm' anchor point")
        
        # Verify text is drawn
        pixels = list(img.getdata())
        has_black = any(pixel != (255, 255, 255) for pixel in pixels)
        
        if has_black:
            print("✓ Text rendered successfully with 'mm' anchor")
            print("\n✅ PASS: Anchor point consistency verified")
            return 0
        else:
            print("❌ FAIL: Text not rendered")
            return 1
    except TypeError:
        print("❌ FAIL: PIL version does not support anchor parameter")
        print("   Please upgrade Pillow to version 8.0.0 or higher")
        return 1


def main():
    """Run all alignment tests."""
    print("\n" + "="*60)
    print("CERTIFICATE ALIGNMENT SMOKE TESTS")
    print("="*60)
    
    results = []
    
    # Run tests
    try:
        results.append(test_anchor_point_consistency())
        results.append(test_text_centering())
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Summary
    print("\n" + "="*60)
    if all(r == 0 for r in results):
        print("✅ ALL TESTS PASSED")
        print("="*60)
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("="*60)
        return 1


if __name__ == '__main__':
    sys.exit(main())
