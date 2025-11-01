#!/usr/bin/env python3
"""
ReportLab-based Certificate Renderer

Uses ReportLab's professional text rendering instead of PIL.
ReportLab has better typography and may match Canva's output more closely.
"""
import os
import sys
from pathlib import Path
from PIL import Image
import io

from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter

sys.path.insert(0, str(Path(__file__).parent.parent))

def test_reportlab_rendering():
    """Test if ReportLab produces better rendering."""
    base_dir = Path(__file__).parent.parent
    template_path = base_dir / 'templates' / 'template_extracted_from_sample.png'
    font_path = base_dir / 'templates' / 'ARIALBD.TTF'
    reference_path = base_dir / 'templates' / 'Sample_certificate.png'
    
    # Load template to get dimensions
    template_img = Image.open(template_path)
    width_px, height_px = template_img.size
    
    # Convert to points (PDF uses points: 1 point = 1/72 inch)
    width_pt = width_px * 72.0 / 96.0  # Assuming 96 DPI
    height_pt = height_px * 72.0 / 96.0
    
    print(f"Template: {width_px} x {height_px} px")
    print(f"PDF size: {width_pt:.1f} x {height_pt:.1f} pt")
    
    # Create PDF in memory
    pdf_buffer = io.BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=(width_pt, height_pt))
    
    # Register font
    pdfmetrics.registerFont(TTFont('ArialBold', str(font_path)))
    
    # Draw template as background
    c.drawImage(str(template_path), 0, 0, width=width_pt, height=height_pt)
    
    # Test text rendering
    # NAME field
    c.setFont('ArialBold', 489)  # Large font as detected
    c.setFillColorRGB(0, 0, 0)
    text = "SAMPLE NAME"
    text_width = c.stringWidth(text, 'ArialBold', 489)
    x = (width_pt - text_width) / 2
    y = height_pt * 0.722  # From top (PDF coordinates are bottom-up)
    c.drawString(x, y, text)
    
    c.save()
    
    # Convert PDF to PNG
    print("\nNote: ReportLab creates PDFs. Would need pdf2image to convert to PNG for comparison.")
    print("However, this approach has limitations:")
    print("1. ReportLab is designed for PDFs, not pixel-perfect raster images")
    print("2. PDF text rendering still won't match Canva's rasterization")
    print("3. Conversion back to PNG adds another layer of transformation")
    
    return False

if __name__ == '__main__':
    test_reportlab_rendering()
