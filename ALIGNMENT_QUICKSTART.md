# Certificate Alignment Validator - Quick Start

This branch implements a complete certificate alignment validation system for the eCertificate project.

## Quick Commands

```bash
# Run all tests
pytest tests/test_certificate_alignment.py -v

# Validate a certificate  
python tools/validate_certificate.py generated_certificates/cert.png

# Auto-calibrate alignment
python tools/calibrate_and_patch.py

# CI validation check
./tools/run_alignment_checks.sh
```

## Branch: fix/alignment-validator

See `docs/CERTIFICATE_ALIGNMENT.md` for complete documentation.
