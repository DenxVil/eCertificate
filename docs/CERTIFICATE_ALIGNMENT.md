# Certificate Alignment Validation System

## Overview

The Certificate Alignment Validation System ensures that text fields on generated certificates are precisely positioned according to template specifications. This system includes:

- **Shared alignment helper** for consistent text positioning
- **Validator** to check alignment accuracy
- **Calibration tools** to measure and adjust positions
- **Visual overlay images** for debugging alignment issues
- **Optional integration** into the GOONJ certificate generation flow

## Architecture

### Components

1. **Text Alignment Helper** (`app/utils/text_align.py`)
   - Provides `draw_text_centered()` function for consistent text alignment
   - Uses PIL anchor points when available
   - Falls back to metrics-based positioning for older PIL versions
   - Supports baseline offset adjustments

2. **Certificate Validator** (`app/utils/certificate_validator.py`)
   - Validates generated certificates against expected positions
   - Computes pixel offsets (dx, dy) for each text field
   - Generates visual overlay images showing alignment status
   - Optional OCR support for position detection (requires pytesseract)

3. **Field Offsets Configuration** (`templates/goonj_template_offsets.json`)
   - Stores normalized field positions (0.0-1.0 coordinates)
   - Includes baseline offset adjustments per field
   - Updated automatically by calibration tool

4. **CLI Tools**
   - `tools/validate_certificate.py` - Validate a single certificate
   - `tools/calibrate_and_patch.py` - Auto-calibrate and update offsets
   - `tools/run_alignment_checks.sh` - CI-friendly validation script

## How the Validator Works

### Validation Process

1. **Load Configuration**: Read expected positions from `templates/goonj_template_offsets.json`
2. **Detect Positions**: 
   - If pytesseract is available, use OCR to find actual text positions
   - Otherwise, use expected positions as reference
3. **Compute Offsets**: Calculate pixel differences (dx, dy) between generated and reference positions
4. **Apply Tolerance**: Check if offsets are within tolerance threshold (default: 3px)
5. **Generate Overlay**: Create visual comparison image with markers and measurements

### Validation Output

The validator returns a dictionary with:

```python
{
    'pass': bool,              # True if all fields within tolerance
    'tolerance_px': int,       # Tolerance threshold used
    'overlay_path': str,       # Path to overlay image
    'details': {
        'field_name': {
            'gen_px': (x, y),  # Generated position in pixels
            'ref_px': (x, y),  # Reference position in pixels
            'dx': int,         # Horizontal offset
            'dy': int,         # Vertical offset
            'distance': float, # Euclidean distance
            'ok': bool         # Within tolerance?
        }
    }
}
```

## Running Validation

### Validate a Single Certificate

```bash
# Basic validation
python tools/validate_certificate.py generated_certificates/cert.png

# With specific template and tolerance
python tools/validate_certificate.py cert.png templates/goonj_certificate.png --tolerance 5

# JSON output for automation
python tools/validate_certificate.py cert.png --json
```

### Run Calibration

The calibration tool generates a test certificate, validates it, and updates the offsets file:

```bash
# Run calibration with default settings
python tools/calibrate_and_patch.py

# Custom tolerance
python tools/calibrate_and_patch.py --tolerance 5

# Custom template
python tools/calibrate_and_patch.py --template templates/custom_template.png
```

### CI/CD Integration

Use the shell script for automated checks:

```bash
# Run validation checks
./tools/run_alignment_checks.sh

# With custom settings
TOLERANCE=5 ./tools/run_alignment_checks.sh
```

Exit codes:
- `0` - All checks passed
- `1` - Validation failed (alignment issues)
- `2` - Error occurred (missing files, etc.)

## Interpreting Overlay Images

Overlay images show:

- **Blue crosshairs (+)**: Reference/expected positions
- **Green/Red crosshairs (X)**: Generated positions
  - Green = within tolerance
  - Red = exceeds tolerance
- **Connecting lines**: Show offset direction and magnitude
- **Labels**: Display dx, dy values in pixels

### Example Interpretation

```
name: dx=-2px dy=+3px
```
- Text is 2 pixels left of target (dx < 0)
- Text is 3 pixels below target (dy > 0)

## Adjusting Offsets

### Manual Adjustment

Edit `templates/goonj_template_offsets.json`:

```json
{
  "fields": {
    "name": {
      "x": 0.5,           // Horizontal position (0.0-1.0)
      "y": 0.33,          // Vertical position (0.0-1.0)
      "baseline_offset": -5  // Pixels to shift up/down
    }
  }
}
```

### Automatic Calibration

The calibration tool will:
1. Generate a test certificate
2. Measure actual positions
3. Compute required adjustments
4. Update the JSON file automatically

After calibration, regenerate certificates to apply the new positions.

## Changing Tolerance

### Via CLI

```bash
python tools/validate_certificate.py cert.png --tolerance 5
```

### Via Environment Variable

```bash
export VALIDATE_TOLERANCE_PX=5
python app.py
```

### In Code

```python
from app.utils.certificate_validator import validate

result = validate(cert_path, tolerance_px=5)
```

### In Configuration File

Edit `templates/goonj_template_offsets.json`:

```json
{
  "tolerance_px": 5
}
```

## Enabling DEBUG_VALIDATE (Dev Mode Only)

The `DEBUG_VALIDATE` flag enables automatic validation after certificate generation in the GOONJ endpoint.

### Enable via Environment Variable

```bash
export DEBUG_VALIDATE=true
python app.py
```

### Enable in Docker

```yaml
environment:
  - DEBUG_VALIDATE=true
  - VALIDATE_TOLERANCE_PX=3
```

### What It Does

When `DEBUG_VALIDATE=true`:
1. After generating each certificate, validation runs automatically
2. Results are logged to the application log
3. If validation fails, overlay images are generated
4. Certificate is still returned to the user (non-blocking)

**Important**: This feature is designed for development/testing only. In production, keep `DEBUG_VALIDATE=false` (default) to avoid performance overhead.

### Log Output Example

```
INFO: Certificate validation: PASS
DEBUG:   name: dx=0px, dy=1px, ok=True
DEBUG:   event: dx=-1px, dy=0px, ok=True
DEBUG:   organiser: dx=0px, dy=-2px, ok=True
```

Or if validation fails:

```
INFO: Certificate validation: FAIL
WARNING: Certificate validation failed. Overlay saved to: generated_certificates/cert_validation_overlay.png
```

## Testing

### Run Unit Tests

```bash
# Install pytest
pip install pytest

# Run alignment tests
pytest tests/test_certificate_alignment.py -v
```

### Run Smoke Test

The smoke test generates a certificate and validates alignment:

```bash
pytest tests/test_certificate_alignment.py::test_smoke_alignment -v -s
```

## Troubleshooting

### Common Issues

#### 1. Validation Always Fails

**Symptom**: All fields show large offsets

**Solution**: Run calibration to measure actual positions:
```bash
python tools/calibrate_and_patch.py
```

#### 2. OCR Not Working

**Symptom**: Warning "pytesseract not available"

**Solution**: Install pytesseract (optional):
```bash
pip install pytesseract
# Also install system dependency (Ubuntu/Debian)
sudo apt-get install tesseract-ocr
```

#### 3. Overlay Images Not Generated

**Symptom**: overlay_path is None or file missing

**Solution**: Check write permissions on output directory:
```bash
chmod 755 generated_certificates/
```

#### 4. Baseline Offset Not Applied

**Symptom**: Text appears at wrong vertical position

**Solution**: 
1. Check that `goonj_template_offsets.json` exists
2. Verify `baseline_offset` values are set
3. Ensure renderer is loading offsets (check logs)

### Debug Mode

Enable debug logging to see detailed validation information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Performance Considerations

- **Validation overhead**: ~100-500ms per certificate (depends on image size)
- **OCR overhead**: Additional 1-2 seconds if pytesseract is used
- **Overlay generation**: ~50-100ms

**Recommendation**: Use `DEBUG_VALIDATE=true` only in development/testing environments.

## Future Enhancements

Possible improvements:
- Multi-template support
- Rotation and skew detection
- Automated regression testing
- Web UI for visual validation
- Batch validation reports

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review overlay images for visual debugging
3. Run calibration to reset alignment
4. Enable debug logging for detailed information

## References

- PIL/Pillow Documentation: https://pillow.readthedocs.io/
- pytesseract: https://github.com/madmaze/pytesseract
- Certificate Generator: See `CERTIFICATE_GENERATOR_USAGE.md`
