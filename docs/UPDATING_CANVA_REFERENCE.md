# Updating Reference Certificate from Canva

This guide explains how to update the reference certificate (`templates/Sample_certificate.png`) from a Canva design.

## Current Reference Image

**Canva Design URL:**
https://www.canva.com/design/DAG3WWj3eUk/yThBfXKr0YLNUBzigPzSUA/view

This is the authoritative reference design that all generated certificates should match.

## Why Update the Reference?

The reference certificate (`Sample_certificate.png`) is used by the alignment verification system to ensure:
- All generated certificates have correct field positions
- Text alignment is pixel-perfect
- Image dimensions are consistent (2000x1414)
- Certificate quality standards are maintained

When the Canva design is updated, the reference must be updated to match.

## Step-by-Step Instructions

### Method 1: Using the Update Script (Recommended)

1. **Download the Canva Design**
   - Open the Canva design URL in your browser
   - Click the "Share" button (top right)
   - Select "Download"
   - Choose "PNG" format
   - Click "Download"
   - Save the file (e.g., `certificate.png`)

2. **Run the Update Script**
   ```bash
   python tools/update_reference_from_canva.py ~/Downloads/certificate.png
   ```

3. **The Script Will:**
   - Check the image format and dimensions
   - Resize if needed (to 2000x1414)
   - Convert to RGB mode if needed
   - Backup the current reference
   - Save the new reference
   - Provide next steps

4. **Verify the Update**
   ```bash
   python scripts/verify_alignment.py
   ```

### Method 2: Manual Update

1. **Download the Canva Design** (same as Method 1)

2. **Verify Image Properties**
   - Open the downloaded image in an image editor
   - Check dimensions: Should be 2000x1414 pixels
   - Check format: Should be PNG
   - Check mode: Should be RGB

3. **Resize if Needed**
   ```python
   from PIL import Image
   img = Image.open('downloaded_certificate.png')
   img = img.resize((2000, 1414), Image.LANCZOS)
   img = img.convert('RGB')
   img.save('resized_certificate.png', 'PNG')
   ```

4. **Replace the Reference**
   ```bash
   # Backup current reference
   cp templates/Sample_certificate.png templates/Sample_certificate_backup.png
   
   # Copy new reference
   cp ~/Downloads/certificate.png templates/Sample_certificate.png
   ```

5. **Verify Alignment**
   ```bash
   python scripts/verify_alignment.py
   ```

## What Happens After Update?

### If Alignment Verification Passes ✅

The new reference is working correctly. Generated certificates will match the Canva design.

```
✅ PERFECT ALIGNMENT - 0.00px difference
The generated certificate is IDENTICAL to the reference.
```

### If Alignment Verification Fails ❌

The current renderer settings don't match the new reference. This is normal when updating to a new design.

```
❌ ALIGNMENT CHECK FAILED
Difference: 1.5104% (exceeds 0.01px tolerance)
```

**Option A: Update Renderer to Match Reference**

If the Canva design has different field positions, update the renderer configuration:

1. **Identify Field Positions** in the Canva design
   - Measure vertical positions of Name, Event, and Organiser fields
   - Calculate as percentage of image height

2. **Update Configuration**
   Edit `templates/goonj_template_offsets.json`:
   ```json
   {
     "fields": {
       "name": {
         "x": 0.5,
         "y": 0.33,
         "baseline_offset": 0
       },
       "event": {
         "x": 0.5,
         "y": 0.42,
         "baseline_offset": 0
       },
       "organiser": {
         "x": 0.5,
         "y": 0.51,
         "baseline_offset": 0
       }
     }
   }
   ```

3. **Verify Again**
   ```bash
   python scripts/verify_alignment.py
   ```

**Option B: Let Auto-Fix System Handle It**

The auto-fix system can regenerate the reference to match current renderer settings:

```bash
python tools/regenerate_sample.py
```

This will create a reference that matches your current configuration, but it won't match the Canva design anymore.

## Auto-Fix System Behavior

When certificates are generated, the auto-fix system:

1. **Verifies Alignment** - Compares generated certificate with reference
2. **Detects Mismatch** - If not pixel-perfect, triggers auto-fix
3. **Regenerates Reference** - Creates new reference using current renderer
4. **Re-verifies** - Confirms alignment is now perfect

**Important:** If you want to keep the Canva design as the reference, you should:
- Update renderer configuration to match the Canva design (Option A above)
- **OR** disable auto-fix to prevent reference from being regenerated

To disable auto-fix temporarily:
```bash
# In .env file
ENABLE_ALIGNMENT_CHECK=False
```

## Field Position Calibration

If you need precise field positions for the Canva design:

1. **Open Canva Design** and note text positions
2. **Use Calibration Tool**:
   ```bash
   python tools/calibrate_precise.py
   ```

3. **Or Calculate Manually**:
   ```python
   # For a 1414px tall image
   # If "Name" field is at 466px from top
   y_percentage = 466 / 1414  # = 0.33 (33%)
   ```

## Testing After Update

Run comprehensive tests:

```bash
# 1. Verify alignment
python scripts/verify_alignment.py

# 2. Test certificate generation
python tests/test_new_features.py

# 3. Generate a test certificate
curl -X POST http://localhost:5000/goonj/generate \
  -F "name=Test User" \
  -F "event=Test Event" \
  -F "organiser=Test Org" \
  -F "return_json=true"
```

## Troubleshooting

### Issue: Downloaded image is wrong size

**Solution:** Canva may have exported at different resolution. Resize:
```bash
python tools/update_reference_from_canva.py <path> 
# Script will prompt to resize
```

### Issue: Colors look different

**Solution:** Ensure RGB mode:
```python
from PIL import Image
img = Image.open('certificate.png').convert('RGB')
img.save('certificate_rgb.png', 'PNG')
```

### Issue: Alignment always fails

**Solutions:**
1. Update renderer configuration to match Canva positions
2. Use calibration tool to find exact positions
3. Check font rendering (ensure ARIALBD.TTF is used)

### Issue: Auto-fix keeps regenerating reference

**Solution:** This means renderer doesn't match the Canva reference. Either:
- Fix renderer configuration, OR
- Accept current renderer and let auto-fix update reference

## Best Practices

1. **Keep Canva URL Updated** - Document the current design URL
2. **Version Control** - Commit reference updates with clear messages
3. **Test Thoroughly** - Verify alignment after each update
4. **Backup Old References** - Keep backups in case rollback needed
5. **Update Documentation** - Note any position changes in config

## Summary

```bash
# Quick update workflow
# 1. Download Canva design as PNG
# 2. Update reference
python tools/update_reference_from_canva.py ~/Downloads/certificate.png

# 3. Verify alignment
python scripts/verify_alignment.py

# 4. If needed, update renderer config
# Edit templates/goonj_template_offsets.json

# 5. Test certificate generation
python tests/test_new_features.py
```

## Related Documentation

- [Auto Alignment Fixing](AUTO_ALIGNMENT_FIXING.md)
- [Alignment Verification](ALIGNMENT_VERIFICATION.md)
- [UI Improvements](UI_IMPROVEMENTS.md)
