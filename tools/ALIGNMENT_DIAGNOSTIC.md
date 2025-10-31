# Certificate Alignment Diagnostic Tool

This tool helps diagnose alignment issues in generated certificates by comparing them against the reference certificate (`Sample_certificate.png`).

## Features

- ✅ Extracts individual field positions (name, event, organiser) from certificates
- ✅ Compares generated certificate against reference
- ✅ Reports per-field alignment differences (Y and X coordinates)
- ✅ Detects missing or undetected fields
- ✅ Provides clear visual feedback with status indicators
- ✅ Returns appropriate exit codes for automation

## Usage

### Basic Usage
```bash
# Check a generated certificate against the default reference
python tools/diagnose_alignment.py <path_to_generated_certificate>
```

### Custom Reference
```bash
# Check against a specific reference certificate
python tools/diagnose_alignment.py <generated_cert> <reference_cert>
```

## Examples

### Example 1: Check a generated certificate
```bash
python tools/diagnose_alignment.py generated_certificates/goonj_cert_john_20241031_123456.png
```

### Example 2: Check against custom reference
```bash
python tools/diagnose_alignment.py my_certificate.png templates/Sample_certificate.png
```

## Output Interpretation

### Status Indicators

- **✅ PERFECT**: Difference ≤ 0.02 px (sub-pixel precision)
- **✓ GOOD**: Difference ≤ 2.0 px (acceptable alignment)
- **⚠️ WARNING**: Difference ≤ 10.0 px (noticeable issues)
- **❌ FAILED/POOR**: Difference > 10.0 px (significant issues)

### Exit Codes

- **0**: Alignment is PERFECT or GOOD
- **1**: Alignment has issues (WARNING, POOR, or FAILED)

## Sample Output

```
======================================================================
CERTIFICATE ALIGNMENT DIAGNOSTIC TOOL
======================================================================

📄 Generated Certificate: generated_certificates/test_cert.png
   Size: (2000, 1415), Mode: RGB

📄 Reference Certificate: templates/Sample_certificate.png
   Size: (2000, 1415), Mode: RGBA

======================================================================
DETECTED FIELDS
======================================================================

📊 Generated Certificate Fields:
  ✅ name      : y= 422.50px, x= 999.50px (y=283-562)
  ✅ event     : y= 723.50px, x= 951.00px (y=628-819)
  ✅ organiser : y= 894.50px, x=1043.50px (y=800-989)

======================================================================
ALIGNMENT ANALYSIS
======================================================================

📏 Individual Field Differences:

  ✅ PERFECT NAME:
     Y difference:    0.00 px  (gen= 422.50, ref= 422.50)
     X difference:    0.00 px  (gen= 999.50, ref= 999.50)

  ✅ PERFECT EVENT:
     Y difference:    0.00 px  (gen= 723.50, ref= 723.50)
     X difference:    0.00 px  (gen= 951.00, ref= 951.00)

  ✅ PERFECT ORGANISER:
     Y difference:    0.00 px  (gen= 894.50, ref= 894.50)
     X difference:    0.00 px  (gen=1043.50, ref=1043.50)

======================================================================
OVERALL VERDICT
======================================================================

✅ PERFECT ALIGNMENT: Max difference = 0.0000 px (≤ 0.02 px)
```

## Troubleshooting

### "Field not detected" Error

If a field is not detected, it means the text was not found in the expected region:
- **Name**: Searched in 20%-40% of image height
- **Event**: Searched in 40%-58% of image height  
- **Organiser**: Searched in 55%-70% of image height

**Solutions:**
1. Ensure all three fields have visible text
2. Verify text is dark enough (pixel value < 200)
3. Check that text has sufficient width (min 100 dark pixels per row)
4. Ensure fields are positioned roughly in the expected regions

### Large Alignment Differences

If you see large differences (> 10px):
1. Check the `goonj_template_offsets.json` configuration
2. Verify the template image matches the reference
3. Ensure fonts are rendering consistently
4. Run the certificate generation with alignment retry enabled

## Configuration

The tool uses the same field detection logic as the main alignment verifier:
- Search windows defined in `app/utils/iterative_alignment_verifier.py`
- Default reference: `templates/Sample_certificate.png`
- Threshold for text detection: pixel value < 200
- Minimum pixels for text detection: 100 dark pixels per row

## Integration with CI/CD

You can use this tool in automated workflows:

```bash
# Exit code 0 = success, 1 = failure
python tools/diagnose_alignment.py generated_cert.png
if [ $? -eq 0 ]; then
    echo "Certificate alignment verified"
else
    echo "Certificate alignment failed"
    exit 1
fi
```
