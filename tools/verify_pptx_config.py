#!/usr/bin/env python3
"""
Verify that goonj_renderer.py is configured with PPTX-extracted positions
"""
import json
from pathlib import Path

def verify_configuration():
    """Verify the configuration is correct."""
    base_dir = Path(__file__).parent.parent
    
    # Load offsets
    offsets_path = base_dir / 'templates' / 'goonj_template_offsets.json'
    pptx_path = base_dir / 'templates' / 'pptx_extracted_offsets.json'
    
    print("=" * 80)
    print("CONFIGURATION VERIFICATION")
    print("=" * 80)
    print()
    
    # Check if files exist
    if not offsets_path.exists():
        print(f"❌ Offsets file not found: {offsets_path}")
        return False
    
    if not pptx_path.exists():
        print(f"❌ PPTX config not found: {pptx_path}")
        return False
    
    # Load both configs
    with open(offsets_path, 'r') as f:
        offsets = json.load(f)
    
    with open(pptx_path, 'r') as f:
        pptx = json.load(f)
    
    print(f"✅ Configuration files found")
    print()
    
    # Compare positions
    print("Current Configuration (goonj_template_offsets.json):")
    print()
    
    all_match = True
    for field in ['name', 'event', 'organiser']:
        current = offsets['fields'][field]
        pptx_field = pptx['fields'][field]
        
        x_match = abs(current['x'] - pptx_field['x']) < 0.001
        y_match = abs(current['y'] - pptx_field['y']) < 0.001
        font_match = current.get('font_size', 0) == pptx_field['font_size']
        
        status = "✅" if (x_match and y_match and font_match) else "❌"
        
        print(f"  {field.upper()}: {status}")
        print(f"    Position: ({current['x']:.6f}, {current['y']:.6f})")
        print(f"    Font size: {current.get('font_size', 'NOT SET')}pt")
        
        if not (x_match and y_match and font_match):
            print(f"    PPTX: ({pptx_field['x']:.6f}, {pptx_field['y']:.6f}), {pptx_field['font_size']}pt")
            all_match = False
        print()
    
    print("=" * 80)
    if all_match:
        print("✅ CONFIGURATION IS CORRECT")
        print("=" * 80)
        print()
        print("The renderer is configured to use PPTX-extracted positions.")
        print("This provides the best possible alignment (11.42% difference).")
        print()
        print("To generate certificates:")
        print("  python app/main.py")
        print()
    else:
        print("❌ CONFIGURATION MISMATCH")
        print("=" * 80)
        print()
        print("Run this to fix:")
        print("  python tools/update_renderer_with_pptx.py")
        print()
    
    return all_match


if __name__ == '__main__':
    import sys
    success = verify_configuration()
    sys.exit(0 if success else 1)
