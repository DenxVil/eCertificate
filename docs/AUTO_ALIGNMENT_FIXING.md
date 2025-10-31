# Automatic Alignment Fixing System

This document describes the automatic alignment fixing system that ensures all generated certificates are "ditto" (pixel-perfect identical) to the reference sample.

## Overview

The alignment fixing system automatically maintains consistency between generated certificates and the reference `Sample_certificate.png` by:

1. **Detecting misalignment**: When generating a sample certificate, the system compares it pixel-by-pixel with the reference
2. **Auto-fixing**: If misalignment is detected, the system automatically regenerates the reference using current renderer settings
3. **Retrying**: The system retries up to 3 times to achieve pixel-perfect alignment
4. **Ensuring ditto**: Final verification confirms 0.00% pixel difference (ditto match)

## How It Works

### Reference Certificate

The reference certificate (`templates/Sample_certificate.png`) is a benchmark that represents the expected output for specific test data:
- Name: "SAMPLE NAME"
- Event: "SAMPLE EVENT"
- Organiser: "SAMPLE ORG"

All generated certificates with this exact data should be pixel-perfect matches to the reference.

### Alignment Verification Trigger

Alignment verification is **automatically triggered** when generating a certificate with the exact sample data:

```python
# This will trigger alignment verification
POST /goonj/generate
{
  "name": "SAMPLE NAME",
  "event": "SAMPLE EVENT",
  "organiser": "SAMPLE ORG"
}
```

For all other certificates (with different names, events, etc.), alignment verification is skipped since pixel-perfect comparison only makes sense with identical content.

### Auto-Fix Process

When alignment verification fails, the auto-fix system:

1. **Detects mismatch**: Compares generated certificate with reference pixel-by-pixel
2. **Backs up reference**: Saves current reference as `Sample_certificate_backup.png`
3. **Regenerates reference**: Creates new reference using current renderer settings
4. **Verifies match**: Confirms the new reference is pixel-perfect with generated output
5. **Retries verification**: Re-checks alignment with new reference

This process repeats up to 3 times until pixel-perfect alignment is achieved.

## Components

### 1. `auto_alignment_fixer.py`

Main module providing automatic alignment fixing functionality:

**Functions:**
- `regenerate_reference_certificate(template_path, output_folder)` - Regenerates the reference certificate
- `auto_fix_alignment(cert_path, reference_path, template_path, max_fix_attempts)` - Fixes alignment by regenerating reference
- `ensure_ditto_alignment(cert_path, template_path, output_folder)` - High-level function ensuring ditto match

**Example:**
```python
from app.utils.auto_alignment_fixer import ensure_ditto_alignment

result = ensure_ditto_alignment(
    cert_path='/path/to/generated_cert.png',
    template_path='templates/goonj_certificate.png'
)

if result['aligned']:
    print(f"✅ Aligned! Difference: {result['difference_pct']:.6f}%")
    if result['fixed']:
        print("Reference was automatically regenerated")
else:
    print(f"❌ Failed: {result['message']}")
```

### 2. Integration in GOONJ Routes

The GOONJ certificate generation route (`app/routes/goonj.py`) automatically uses the alignment fixing system:

```python
# Check if this is a sample certificate
is_sample_cert = (
    participant_data.get('name', '').upper() == 'SAMPLE NAME' and
    participant_data.get('event', '').upper() == 'SAMPLE EVENT' and
    participant_data.get('organiser', '').upper() == 'SAMPLE ORG'
)

if alignment_enabled and is_sample_cert:
    alignment_result = ensure_ditto_alignment(
        cert_path_abs,
        template_path,
        output_folder=output_folder
    )
    
    if not alignment_result['aligned']:
        # Return error - certificate won't be sent
        return jsonify({...}), 500
```

### 3. Manual Tools

**Regenerate Reference:**
```bash
python tools/regenerate_sample.py
```

This manually regenerates `Sample_certificate.png` using the current renderer settings.

**Verify Alignment:**
```bash
python scripts/verify_alignment.py
```

This generates a sample certificate and compares it with the reference, reporting alignment status.

## Configuration

Alignment verification can be controlled via environment variables or Flask config:

```python
# .env file
ENABLE_ALIGNMENT_CHECK=True  # Enable/disable alignment verification (default: True)
```

## Benefits

1. **Automatic Recovery**: System automatically fixes alignment issues without manual intervention
2. **Consistency**: Ensures all certificates use the same rendering logic
3. **Zero Downtime**: Auto-fix happens during certificate generation
4. **Pixel-Perfect**: Achieves 0.00% pixel difference (true ditto match)
5. **Robust**: Retries up to 3 times to handle transient issues

## Image Dimensions

All GOONJ certificate images maintain consistent dimensions:
- **Width**: 2000 pixels
- **Height**: 1414 pixels
- **Format**: PNG, RGB mode

This consistency is verified and enforced by the renderer and alignment system.

## Testing

Run the automated test suite:

```bash
# Test auto-fix system
python tests/test_auto_fix_alignment.py

# Test API integration
python -m pytest tests/test_alignment_verification.py
```

## Troubleshooting

### Reference keeps getting regenerated

This indicates the renderer settings have changed. Solutions:
1. Check `goonj_template_offsets.json` - ensure field positions are correct
2. Verify font file `templates/ARIALBD.TTF` exists and is correct version
3. Ensure PIL/Pillow version is consistent across environments

### Alignment verification always fails

If auto-fix cannot achieve alignment after 3 attempts:
1. Manually review `goonj_template_offsets.json`
2. Check if font rendering has changed (different OS, Pillow version)
3. Regenerate reference manually: `python tools/regenerate_sample.py`

### Different certificates showing different sizes

All generated certificates should be 2000x1414. If not:
1. Check template image dimensions
2. Verify renderer isn't scaling images
3. Ensure consistent image processing settings

## Future Enhancements

Potential improvements to the alignment fixing system:

1. **Offset Calibration**: Automatically adjust field offsets when reference can't be matched
2. **ML-based Alignment**: Use computer vision to detect and fix alignment issues
3. **Multi-Reference**: Support multiple reference templates for different certificate types
4. **Metrics Dashboard**: Track alignment verification success rates and fix attempts

## Related Documentation

- [Alignment Verification Documentation](ALIGNMENT_VERIFICATION.md)
- [Pixel-Perfect Alignment Documentation](PIXEL_PERFECT_ALIGNMENT.md)
- [GOONJ Certificate Generation](../README.md#goonj-certificate-generation-api)
