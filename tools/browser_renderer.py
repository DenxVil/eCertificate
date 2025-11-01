#!/usr/bin/env python3
"""
Browser-Based Certificate Renderer

Revolutionary approach using headless browser (Playwright) for text rendering.
This matches Canva's rendering because both use browser-based font rendering!

Advantages:
1. Uses same rendering engine as modern design tools
2. Access to web fonts and advanced typography
3. Anti-aliasing matches what users see in browsers/Canva
4. Can use HTML/CSS for precise positioning
"""
import os
import sys
from pathlib import Path
import json
import base64
from PIL import Image
import io

sys.path.insert(0, str(Path(__file__).parent.parent))

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        @font-face {{
            font-family: 'ArialBold';
            src: url('data:font/truetype;base64,{font_base64}');
        }}
        
        body {{
            margin: 0;
            padding: 0;
            width: {width}px;
            height: {height}px;
            position: relative;
            background-image: url('data:image/png;base64,{template_base64}');
            background-size: {width}px {height}px;
        }}
        
        .text-field {{
            position: absolute;
            font-family: 'ArialBold', Arial, sans-serif;
            color: #000000;
            text-align: center;
            font-weight: bold;
            transform: translateX(-50%) translateY(-50%);
            white-space: nowrap;
        }}
        
        .name {{
            left: {name_x}px;
            top: {name_y}px;
            font-size: {name_size}pt;
        }}
        
        .event {{
            left: {event_x}px;
            top: {event_y}px;
            font-size: {event_size}pt;
        }}
        
        .organiser {{
            left: {organiser_x}px;
            top: {organiser_y}px;
            font-size: {organiser_size}pt;
        }}
    </style>
</head>
<body>
    <div class="text-field name">{name_text}</div>
    <div class="text-field event">{event_text}</div>
    <div class="text-field organiser">{organiser_text}</div>
</body>
</html>
"""

def encode_file_base64(file_path):
    """Encode file as base64."""
    with open(file_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


class BrowserRenderer:
    """Render certificates using headless browser."""
    
    def __init__(self, template_path, font_path, offsets_path):
        self.template_path = template_path
        self.font_path = font_path
        
        # Load template to get size
        template = Image.open(template_path)
        self.width, self.height = template.size
        
        # Load offsets
        with open(offsets_path, 'r') as f:
            self.offsets = json.load(f)
        
        # Encode assets as base64 for data URLs
        self.font_base64 = encode_file_base64(font_path)
        self.template_base64 = encode_file_base64(template_path)
    
    def generate_html(self, name, event, organiser):
        """Generate HTML for the certificate."""
        fields = self.offsets['fields']
        
        html = HTML_TEMPLATE.format(
            font_base64=self.font_base64,
            template_base64=self.template_base64,
            width=self.width,
            height=self.height,
            name_x=fields['name']['x'] * self.width,
            name_y=fields['name']['y'] * self.height,
            name_size=fields['name']['font_size'],
            name_text=name.upper(),
            event_x=fields['event']['x'] * self.width,
            event_y=fields['event']['y'] * self.height,
            event_size=fields['event']['font_size'],
            event_text=event.upper(),
            organiser_x=fields['organiser']['x'] * self.width,
            organiser_y=fields['organiser']['y'] * self.height,
            organiser_size=fields['organiser']['font_size'],
            organiser_text=organiser.upper()
        )
        
        return html
    
    def render_with_playwright(self, name, event, organiser, output_path):
        """Render using Playwright headless browser."""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            print("❌ Playwright not installed. Install with: pip install playwright")
            print("   Then run: playwright install chromium")
            return False
        
        html = self.generate_html(name, event, organiser)
        
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport={'width': self.width, 'height': self.height})
            page.set_content(html)
            page.wait_for_timeout(1000)  # Wait for fonts to load
            page.screenshot(path=output_path, full_page=True)
            browser.close()
        
        print(f"✅ Rendered with browser: {output_path}")
        return True


def test_browser_renderer():
    """Test browser-based rendering."""
    base_dir = Path(__file__).parent.parent
    template_path = base_dir / 'templates' / 'template_extracted_from_sample.png'
    font_path = base_dir / 'templates' / 'ARIALBD.TTF'
    offsets_path = base_dir / 'templates' / 'goonj_template_offsets.json'
    output_dir = base_dir / 'generated_certificates'
    output_dir.mkdir(exist_ok=True)
    
    renderer = BrowserRenderer(
        str(template_path),
        str(font_path),
        str(offsets_path)
    )
    
    print("=" * 80)
    print("BROWSER-BASED RENDERER TEST")
    print("=" * 80)
    print()
    print("This uses Playwright (headless Chromium) for rendering.")
    print("Browser rendering matches modern design tools like Canva!")
    print()
    
    # Save HTML for inspection
    html = renderer.generate_html('SAMPLE NAME', 'SAMPLE EVENT', 'SAMPLE ORG')
    html_path = output_dir / 'certificate.html'
    with open(html_path, 'w') as f:
        f.write(html)
    print(f"📄 Generated HTML: {html_path}")
    print("   (You can open this in a browser to see the result)")
    print()
    
    # Try to render with Playwright
    output_path = str(output_dir / 'browser_rendered_sample.png')
    success = renderer.render_with_playwright('SAMPLE NAME', 'SAMPLE EVENT', 'SAMPLE ORG', output_path)
    
    if success:
        print()
        print("✅ Browser rendering successful!")
        print("This approach provides:")
        print("1. Modern font rendering (same as Canva)")
        print("2. Proper anti-aliasing")
        print("3. Professional typography")
    else:
        print()
        print("ℹ️  To use browser rendering:")
        print("   1. pip install playwright")
        print("   2. playwright install chromium")
        print("   3. Run this script again")


if __name__ == '__main__':
    test_browser_renderer()
