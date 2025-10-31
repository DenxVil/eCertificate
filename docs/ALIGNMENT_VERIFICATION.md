# Certificate Alignment Verification

## Overview

The eCertificate system includes automated pixel-perfect alignment verification to ensure all generated certificates match the reference sample with **less than 0.01px difference** before being sent to recipients.

## Purpose

This verification system guarantees:
- **Absolute precision** in certificate field positioning
- **Standardization** across all certificates
- **Quality assurance** before delivery
- **Prevention** of misaligned certificates being sent

## How It Works

### 1. Generation Phase
When a certificate is generated, the system:
1. Creates the certificate image using the GOONJ renderer
2. Immediately performs pixel-level comparison with the reference sample
3. Verifies the difference is within the 0.01px tolerance
4. Retries if necessary (configurable, default: 3 attempts)
5. Blocks sending if alignment check fails

### 2. Verification Algorithm

The verification process uses:
- **PIL (Pillow)** ImageChops for pixel-by-pixel difference calculation
- **Sub-pixel accuracy** through strict tolerance thresholds
- **Percentage-based metrics** for overall image similarity
- **Maximum pixel difference** tracking for worst-case analysis

#### Tolerance Mapping
- **0.01px tolerance** maps to <0.001% pixel difference
- **Perfect match**: 0.000% difference, max_pixel_diff=0
- **Acceptable match**: <0.001% difference, max_pixel_diff≤1

### 3. Email Sending Phase
Before sending any certificate via email, the system:
1. Performs a **final alignment check**
2. Verifies the certificate still matches the reference
3. **Blocks sending** if verification fails
4. Logs all verification attempts and results

## Configuration

### Environment Variables

Add these to your `.env` file:

```env
# Alignment Verification Settings
ENABLE_ALIGNMENT_CHECK=True           # Enable/disable alignment verification
ALIGNMENT_TOLERANCE_PX=0.01           # Maximum allowed pixel difference
ALIGNMENT_MAX_ATTEMPTS=3              # Number of verification attempts
```

### Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_ALIGNMENT_CHECK` | `True` | Enable alignment verification |
| `ALIGNMENT_TOLERANCE_PX` | `0.01` | Maximum pixel difference tolerance |
| `ALIGNMENT_MAX_ATTEMPTS` | `3` | Maximum verification attempts |

## Verification Results

### Success Response
When verification passes:
```json
{
  "passed": true,
  "difference_pct": 0.000000,
  "max_pixel_diff": 0,
  "tolerance_px": 0.01,
  "message": "PERFECT MATCH: Certificate is pixel-identical to reference (0.00px difference)"
}
```

### Failure Response
When verification fails:
```json
{
  "error": "Certificate alignment verification failed",
  "message": "Certificate alignment verification failed after 3 attempts...",
  "details": {
    "passed": false,
    "difference_pct": 0.015000,
    "max_pixel_diff": 5,
    "tolerance_px": 0.01,
    "message": "FAILED: Certificate differs from reference by 0.015000% (exceeds 0.01px tolerance)"
  }
}
```

## Logging

The system logs all verification attempts:

### Success Logs
```
INFO: Starting alignment verification for certificate
INFO: Alignment check attempt 1/3
INFO: ✅ Alignment verification PASSED on attempt 1: PERFECT MATCH: Certificate is pixel-identical to reference (0.00px difference)
INFO: Certificate alignment verification completed successfully: diff=0.000000%, max_pixel_diff=0
INFO: ✅ Final alignment check passed: PERFECT MATCH: Certificate is pixel-identical to reference (0.00px difference)
INFO: Certificate email sent successfully to user@example.com
```

### Failure Logs
```
INFO: Starting alignment verification for certificate
INFO: Alignment check attempt 1/3
WARNING: ❌ Alignment verification FAILED on attempt 1: FAILED: Certificate differs from reference by 0.015000% (exceeds 0.01px tolerance)
INFO: Retrying alignment check...
INFO: Alignment check attempt 2/3
WARNING: ❌ Alignment verification FAILED on attempt 2: FAILED: Certificate differs from reference by 0.015000% (exceeds 0.01px tolerance)
INFO: Retrying alignment check...
INFO: Alignment check attempt 3/3
WARNING: ❌ Alignment verification FAILED on attempt 3: FAILED: Certificate differs from reference by 0.015000% (exceeds 0.01px tolerance)
ERROR: Certificate alignment verification failed after 3 attempts. Certificate does not match reference sample within 0.01px tolerance. Certificate will NOT be sent. Difference: 0.015000%
INFO: Removed failed certificate: /path/to/certificate.png
```

## API Integration

### Certificate Generation Endpoint

The `/goonj/generate` endpoint now includes automatic alignment verification:

```bash
curl -X POST http://localhost:5000/goonj/generate \
  -F "name=John Doe" \
  -F "event=GOONJ 2025" \
  -F "organiser=AMA" \
  -F "email=john@example.com"
```

If alignment verification fails, the API returns:
- **HTTP 500** error
- Error message with details
- Certificate is **not** returned or sent

## Testing

### Unit Tests
Run the alignment verification tests:
```bash
python -m pytest tests/test_alignment_verification.py -v
```

### Integration Test
Test with actual certificate generation:
```bash
python scripts/verify_alignment.py
```

Expected output:
```
============================================================
GOONJ Certificate Alignment Verification
============================================================

Generating sample certificate...
✓ Generated: /path/to/certificate.png
✓ Saved as: templates/generated_sample.png

Comparing with reference certificate...
  Difference: 0.0000% of pixels
  Max pixel diff: 0/255

============================================================
✅ PERFECT ALIGNMENT - 0.00px difference
============================================================

The generated certificate is IDENTICAL to the reference.
Pixel-perfect match achieved (0.01px requirement met).
```

## Technical Details

### Reference Certificate
- **Path**: `templates/Sample_certificate.png`
- **Purpose**: Gold standard for comparison
- **Generated with**: Sample data (SAMPLE NAME, SAMPLE EVENT, SAMPLE ORG)
- **Regeneration**: Use `tools/regenerate_sample.py` if template changes

### Comparison Method
1. Load generated and reference images
2. Convert both to RGB color space
3. Calculate pixel-by-pixel difference using ImageChops.difference()
4. Count pixels exceeding tolerance threshold
5. Calculate difference percentage: (significant_diffs / total_pixels) × 100
6. Determine pass/fail based on <0.001% threshold

### Retry Logic
- **Deterministic generation**: Certificates should be identical each time
- **Retry mechanism**: Provides resilience against transient issues
- **Max attempts**: Configurable (default: 3)
- **Cleanup**: Failed certificates are automatically removed

## Error Handling

### Graceful Degradation
If alignment verification encounters errors:
- **Missing reference**: Logs warning, proceeds without verification (degraded mode)
- **Unexpected errors**: Logs exception, proceeds without verification (degraded mode)
- **Verification failure**: **Blocks** certificate sending, returns error

### Security
- Path validation ensures certificates are within expected directories
- Failed certificates are cleaned up to prevent unauthorized access
- All file operations are logged for audit trail

## Best Practices

1. **Never disable** alignment verification in production
2. **Monitor logs** for verification failures
3. **Regenerate reference** after template changes
4. **Test thoroughly** after any renderer modifications
5. **Use strict tolerance** (0.01px) for production

## Troubleshooting

### Issue: All certificates fail verification
**Solution**: Check if template or reference has changed. Regenerate reference sample.

### Issue: Intermittent failures
**Solution**: Check for non-deterministic rendering (e.g., timestamps). Ensure reproducible generation.

### Issue: Performance concerns
**Solution**: Verification adds <100ms per certificate. Disable for bulk operations if needed, but verify samples manually.

### Issue: Reference not found
**Solution**: Ensure `templates/Sample_certificate.png` exists. Generate using `tools/regenerate_sample.py`.

## Related Documentation
- [Alignment Quick Start](ALIGNMENT_QUICKSTART.md)
- [Alignment Solution Summary](ALIGNMENT_SOLUTION_SUMMARY.md)
- [Pixel-Perfect Alignment](docs/PIXEL_PERFECT_ALIGNMENT.md)

## Summary

The alignment verification system ensures every certificate sent from the eCertificate system meets the highest quality standards with pixel-perfect precision. This guarantees consistency, professionalism, and reliability in certificate delivery.
