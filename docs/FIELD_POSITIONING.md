# Certificate Field Positioning Guide

## Overview

This document explains how certificate field positions are determined and how to ensure proper alignment with your certificate templates.

## Template Analysis for IMG_0929.png

The IMG_0929.png template has specific placeholder positions for text fields. Through image analysis, we identified the following field positions:

### Field Positions (Normalized Coordinates)

| Field | Y Position (normalized) | Y Position (pixels) | Description |
|-------|------------------------|---------------------|-------------|
| NAME | 0.446 | 631px | Participant name placeholder |
| EVENT | 0.636 | 899px | Event name placeholder |
| DATE | 0.919 | 1299px | Date footer area |

### Template Structure

The IMG_0929 template (2000 x 1414 pixels) has the following structure:

```
Y=186  (0.132) - Header/Title area
Y=454  (0.321) - Subtitle area  
Y=631  (0.446) - NAME field placeholder ← Text placed here
Y=776  (0.549) - Event intro text
Y=899  (0.636) - EVENT field placeholder ← Text placed here
Y=987  (0.698) - Additional decorative text
Y=1299 (0.919) - DATE field footer ← Text placed here
```

## Recent Changes (2025-10-31)

### Problem
Certificate fields were being placed at positions that didn't align with the IMG_0929 template placeholders, causing text to appear in incorrect locations.

### Solution
Updated `app/utils/certificate_generator.py` to use positions that match the template:

**Before:**
```python
NAME:  Y=0.45  (636px)
EVENT: Y=0.65  (919px)  
DATE:  Y=0.80  (1131px)
Plus "For successfully participating in" text at Y=0.58
```

**After:**
```python
NAME:  Y=0.446 (631px) - Matches template placeholder
EVENT: Y=0.636 (899px) - Matches template placeholder
DATE:  Y=0.919 (1299px) - Matches template footer
Removed "For successfully..." text
```

### Impact
- NAME: 5px adjustment (minor)
- EVENT: 20px adjustment (improved alignment)
- DATE: 168px adjustment (significant correction)
- Cleaner output without redundant text

## How to Determine Field Positions for Custom Templates

### Method 1: Visual Inspection
1. Open your template image in an image editor
2. Identify where text placeholders or markers are located
3. Note the Y-coordinate (vertical position) for each field
4. Calculate normalized position: `y_normalized = y_pixels / template_height`

### Method 2: Image Analysis (Recommended)
Use Python to analyze the template:

```python
from PIL import Image
import numpy as np

# Load template
template = Image.open('templates/your_template.png')
width, height = template.size

# Convert to grayscale and find dark regions (text)
gray = np.array(template.convert('L'))
dark_regions = gray < 200

# Find vertical profile
vertical_profile = np.sum(dark_regions, axis=1)

# Identify peaks (likely text positions)
for y in range(height):
    if vertical_profile[y] > width * 0.05:
        norm_y = y / height
        print(f"Text at Y={y}px ({norm_y:.3f})")
```

### Method 3: Using Calibration Tools
The repository includes calibration tools for the GOONJ template. You can adapt these for other templates:

```bash
python tools/calibrate_and_patch.py --template templates/your_template.png
```

## Updating Field Positions

### In certificate_generator.py

Edit the `generate_certificate` method in `app/utils/certificate_generator.py`:

```python
def generate_certificate(self, participant_name, event_name=None, output_filename=None):
    fields = [
        {
            "text": participant_name,
            "x": 0.5,    # Horizontal center
            "y": 0.446,  # Your determined position
            "font_name": "arial.ttf",
            "font_size": 60,
            "align": "center"
        },
        # ... more fields
    ]
    return self.generate(fields, output_filename=output_filename)
```

### Using Custom Field Positions per Event

For dynamic positioning based on different templates, you can pass custom fields:

```python
from app.utils.certificate_generator import CertificateGenerator

gen = CertificateGenerator('templates/IMG_0929.png', 'output')

# Custom field positions
fields = [
    {"text": "Alice Smith", "x": 0.5, "y": 0.446, "font_size": 60, "align": "center"},
    {"text": "Workshop 2025", "x": 0.5, "y": 0.636, "font_size": 45, "align": "center"},
    {"text": "October 31, 2025", "x": 0.5, "y": 0.919, "font_size": 25, "align": "center"},
]

cert_path = gen.generate(fields)
```

## Coordinate System

### Normalized Coordinates (0.0 - 1.0)
- Used in the code for template-independent positioning
- `x = 0.0` is left edge, `x = 1.0` is right edge
- `y = 0.0` is top edge, `y = 1.0` is bottom edge
- `x = 0.5, y = 0.5` is the center of the template

### Pixel Coordinates
- Actual pixel positions on the template image
- Calculate from normalized: `pixel_x = normalized_x * template_width`
- Example: For 2000px wide template, `x=0.5` equals 1000px

## Alignment Options

Text can be aligned horizontally:
- `"left"`: Text starts at the x position
- `"center"`: Text is centered on the x position (default)
- `"right"`: Text ends at the x position

## Testing Your Changes

### 1. Generate Test Certificate
```python
from app.utils.certificate_generator import CertificateGenerator

gen = CertificateGenerator('templates/IMG_0929.png', 'test_output')
cert = gen.generate_certificate('Test Name', 'Test Event', 'test.png')
print(f"Generated: {cert}")
```

### 2. Visual Verification
Open the generated certificate and compare with the template to ensure text aligns with placeholders.

### 3. Automated Verification (GOONJ only)
For GOONJ templates, use the validation tools:
```bash
python tools/validate_certificate.py generated_certificates/test.png
```

## Troubleshooting

### Text Appears Too High or Too Low
- Adjust the `y` coordinate in smaller increments (0.01 = ~14px on IMG_0929)
- Check if `baseline_offset` is needed for fine-tuning

### Text Appears Off-Center
- Verify `align="center"` is set
- Ensure `x=0.5` for horizontal centering
- Check template dimensions are correct

### Different Fonts Change Alignment
- Different fonts have different metrics (ascent, descent)
- May need to adjust `baseline_offset` per font
- Use `text_align.py` helper for consistent alignment

## Related Files

- `app/utils/certificate_generator.py` - Main generator with default positions
- `app/utils/text_align.py` - Text alignment helper
- `tools/calibrate_and_patch.py` - Auto-calibration tool (GOONJ)
- `tools/validate_certificate.py` - Alignment validation (GOONJ)
- `docs/CERTIFICATE_ALIGNMENT.md` - Detailed alignment system docs

## Support

For questions or issues with field positioning:
1. Check this guide for coordinate calculation
2. Review the template analysis section
3. Use the image analysis method to find positions
4. Test incrementally with small adjustments
