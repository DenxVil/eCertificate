# Quick Fix Guide: Alignment Issues

## Problem 1: Max Attempts Not Respected

### Symptom
"I set `ALIGNMENT_MAX_ATTEMPTS=30` but it still uses 150 attempts"

### Root Cause
Hardcoded default values in `config.py`

### ✅ FIXED
- Changed default from 150 to 30 in `config.py`
- Ensured configuration is read from `.env` file
- Updated all function defaults to match

### How to Verify
1. Check `.env` file:
   ```bash
   grep ALIGNMENT_MAX_ATTEMPTS .env
   ```

2. Check it's working:
   ```bash
   # Generate a certificate and check logs
   # Should show "attempt X/30" instead of "attempt X/150"
   ```

---

## Problem 2: Fields Show 0.0px Difference Despite Being Misaligned

### Symptom
"Certificate generated has name and event vertically irregularly placed, but difference shows 0.0px"

### Root Cause
Missing field detection was broken - if a field wasn't detected, it was silently skipped from comparison

### ✅ FIXED
- Modified `calculate_position_difference()` to require ALL three fields
- Missing fields now return `inf` (infinite) difference
- Added detailed logging for each field's detection status

### How to Verify
Use the new diagnostic tool:

```bash
python tools/diagnose_alignment.py generated_certificates/your_cert.png
```

**Expected output for properly aligned certificate:**
```
✅ PERFECT NAME:
   Y difference:    0.00 px  (gen= 422.50, ref= 422.50)
   X difference:    0.00 px  (gen= 999.50, ref= 999.50)

✅ PERFECT EVENT:
   Y difference:    0.00 px  (gen= 723.50, ref= 723.50)
   X difference:    0.00 px  (gen= 951.00, ref= 951.00)

✅ PERFECT ORGANISER:
   Y difference:    0.00 px  (gen= 894.50, ref= 894.50)
   X difference:    0.00 px  (gen=1043.50, ref=1043.50)
```

**Expected output for misaligned certificate:**
```
❌ FAILED NAME:
   Y difference:   45.00 px  (gen= 467.50, ref= 422.50)
   X difference:    7.50 px  (gen=1007.00, ref= 999.50)
```

**Expected output for missing fields:**
```
❌ event:
   Error: Field not detected
   Detected in generated: false
   Detected in reference: true
```

---

## Quick Configuration Guide

### Recommended Settings

Add to your `.env` file:

```bash
# Alignment Verification
ENABLE_ALIGNMENT_CHECK=True
ALIGNMENT_TOLERANCE_PX=0.02
ALIGNMENT_MAX_ATTEMPTS=30

# Email Retries
EMAIL_MAX_RETRIES=3
```

### What These Mean

| Setting | Default | Description |
|---------|---------|-------------|
| `ENABLE_ALIGNMENT_CHECK` | `True` | Enable/disable alignment verification |
| `ALIGNMENT_TOLERANCE_PX` | `0.02` | Maximum allowed pixel difference |
| `ALIGNMENT_MAX_ATTEMPTS` | `30` | Max regeneration attempts |
| `EMAIL_MAX_RETRIES` | `3` | Max email send attempts |

### For Different Use Cases

**Development/Testing** (fast feedback):
```bash
ALIGNMENT_MAX_ATTEMPTS=10
ALIGNMENT_TOLERANCE_PX=2.0
```

**Production** (strict quality):
```bash
ALIGNMENT_MAX_ATTEMPTS=30
ALIGNMENT_TOLERANCE_PX=0.02
```

**Debugging** (detailed logs):
```bash
ALIGNMENT_MAX_ATTEMPTS=5
LOG_LEVEL=DEBUG
```

---

## Diagnostic Commands

### 1. Check Configuration
```bash
# View current settings
grep ALIGNMENT .env

# Expected output:
# ALIGNMENT_MAX_ATTEMPTS=30
# ALIGNMENT_TOLERANCE_PX=0.02
```

### 2. Test Field Detection
```bash
# Check if fields are detected in reference
python tools/diagnose_alignment.py templates/Sample_certificate.png

# Should show all three fields detected
```

### 3. Diagnose Generated Certificate
```bash
# Check a specific certificate
python tools/diagnose_alignment.py generated_certificates/cert_name.png

# Shows:
# - Which fields were detected
# - Individual field differences
# - Overall alignment status
```

### 4. Check Logs
```bash
# During certificate generation, check logs for:
grep "Field.*detected" logs/*.log
grep "Max difference" logs/*.log

# Should show individual field detections and differences
```

---

## Common Issues and Solutions

### Issue: "Field not detected"

**Cause**: Text isn't dark enough or in expected position

**Solutions**:
1. Verify text is actually rendered in certificate
2. Check text is dark (not gray or light colored)
3. Ensure field is in expected vertical region:
   - Name: 20%-40% of height
   - Event: 40%-58% of height
   - Organiser: 55%-70% of height

### Issue: "Max attempts reached"

**Cause**: Alignment cannot be achieved with current configuration

**Solutions**:
1. Run diagnostic tool to see actual differences
2. Check if calibration is needed (see ALIGNMENT_BEST_PRACTICES.md)
3. Verify reference certificate matches template
4. Consider adjusting baseline offsets in `goonj_template_offsets.json`

### Issue: "Alignment passes but certificate looks wrong"

**Cause**: Might be using wrong reference or tolerance is too loose

**Solutions**:
1. Verify reference certificate: `templates/Sample_certificate.png`
2. Check tolerance setting (should be ≤ 2.0 for visible quality)
3. Use diagnostic tool to see exact positions
4. Compare generated certificate visually with reference

---

## File Changes Summary

### Configuration Files
- ✅ `.env.example` - Updated defaults (30 attempts, 3 email retries)
- ✅ `config.py` - Changed hardcoded defaults
- ✅ `templates/goonj_template_offsets.json` - Removed hardcoded max_attempts

### Code Files
- ✅ `app/utils/iterative_alignment_verifier.py` - Enhanced field detection and logging
- ✅ `app/utils/alignment_checker.py` - Updated function defaults
- ✅ `app/routes/goonj.py` - Updated comments and defaults
- ✅ `app/utils/mail.py` - Updated email retry defaults
- ✅ `app/utils/email_sender.py` - Updated email retry defaults

### New Tools
- ✨ `tools/diagnose_alignment.py` - Alignment diagnostic tool
- ✨ `tools/ALIGNMENT_DIAGNOSTIC.md` - Tool documentation
- ✨ `docs/ALIGNMENT_BEST_PRACTICES.md` - Best practices guide

---

## Testing Your Setup

### Step 1: Verify Configuration
```bash
cat .env | grep ALIGNMENT_MAX_ATTEMPTS
# Should show: ALIGNMENT_MAX_ATTEMPTS=30
```

### Step 2: Test Reference Detection
```bash
python tools/diagnose_alignment.py templates/Sample_certificate.png
# Should show: ✅ PERFECT ALIGNMENT
```

### Step 3: Generate Test Certificate
```bash
# Use the web interface or API to generate a certificate
# Check the logs for alignment verification output
```

### Step 4: Diagnose Generated Certificate
```bash
# Find the generated certificate
ls -lt generated_certificates/ | head -5

# Run diagnostic
python tools/diagnose_alignment.py generated_certificates/<latest_cert>.png
```

### Expected Results
- All three fields detected ✅
- Differences ≤ 0.02px for perfect alignment ✅
- Alignment passes within configured max_attempts ✅

---

## Getting Help

If issues persist:

1. **Check logs**: Look for "Field not detected" or "Max difference" messages
2. **Run diagnostic**: `python tools/diagnose_alignment.py <your_cert>`
3. **Review docs**: See `docs/ALIGNMENT_BEST_PRACTICES.md`
4. **Report issue**: Include diagnostic output and configuration

---

## Summary of Fixes

✅ **Fixed hardcoded max attempts** - Now respects `.env` configuration  
✅ **Fixed missing field detection** - Returns `inf` instead of 0.0px when fields missing  
✅ **Added individual field logging** - Shows Y and X differences per field  
✅ **Created diagnostic tool** - Easy troubleshooting of alignment issues  
✅ **Updated all defaults** - Consistent 30 attempts across codebase  
✅ **Enhanced error reporting** - Clear messages for missing/misaligned fields  
✅ **Added best practices guide** - Comprehensive alignment improvement strategies
