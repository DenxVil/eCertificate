#!/bin/bash
# Certificate Alignment Validation Script
# This script runs alignment validation checks for CI/CD pipelines
# Exit codes: 0 = pass, 1 = validation failed, 2 = error

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PROJECT_ROOT"

echo "========================================================================"
echo "Certificate Alignment Validation Checks"
echo "========================================================================"
echo ""

# Configuration
TEMPLATE="${TEMPLATE:-templates/goonj_certificate.png}"
TOLERANCE="${TOLERANCE:-3}"
OUTPUT_DIR="${OUTPUT_DIR:-generated_certificates}"

# Check if template exists
if [ ! -f "$TEMPLATE" ]; then
    echo "❌ ERROR: Template not found: $TEMPLATE"
    exit 2
fi

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo "Template: $TEMPLATE"
echo "Tolerance: ${TOLERANCE}px"
echo "Output Directory: $OUTPUT_DIR"
echo ""

# Step 1: Generate a test certificate
echo "------------------------------------------------------------------------"
echo "Step 1: Generating test certificate..."
echo "------------------------------------------------------------------------"

TEST_CERT=$(python3 -c "
import sys
sys.path.insert(0, '.')
from app.utils.goonj_renderer import GOONJRenderer

renderer = GOONJRenderer('$TEMPLATE', output_folder='$OUTPUT_DIR')
test_data = {
    'name': 'CI Test User',
    'event': 'CI Test Event',
    'organiser': 'CI Test Org'
}
cert_path = renderer.render(test_data)
print(cert_path)
" 2>&1)

if [ $? -ne 0 ]; then
    echo "❌ ERROR: Failed to generate test certificate"
    echo "$TEST_CERT"
    exit 2
fi

# Extract just the path (last line)
TEST_CERT=$(echo "$TEST_CERT" | tail -n1)

echo "✅ Test certificate generated: $TEST_CERT"
echo ""

# Step 2: Run validation
echo "------------------------------------------------------------------------"
echo "Step 2: Running alignment validation..."
echo "------------------------------------------------------------------------"

python3 tools/validate_certificate.py "$TEST_CERT" "$TEMPLATE" --tolerance "$TOLERANCE"
VALIDATION_RESULT=$?

echo ""
echo "========================================================================"
if [ $VALIDATION_RESULT -eq 0 ]; then
    echo "✅ PASS: All alignment checks passed"
    echo "========================================================================"
    exit 0
elif [ $VALIDATION_RESULT -eq 1 ]; then
    echo "❌ FAIL: Alignment validation failed"
    echo ""
    echo "To fix alignment issues:"
    echo "  1. Run calibration: python3 tools/calibrate_and_patch.py"
    echo "  2. Review overlay images in: $OUTPUT_DIR"
    echo "  3. Re-run this script to verify fixes"
    echo "========================================================================"
    exit 1
else
    echo "❌ ERROR: Validation script encountered an error"
    echo "========================================================================"
    exit 2
fi
