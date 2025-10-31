#!/usr/bin/env python3
"""Test alignment attempt tracking and best certificate selection."""
import os
import sys
import tempfile
from PIL import Image, ImageDraw, ImageFont

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.iterative_alignment_verifier import (
    verify_alignment_with_retries,
    extract_field_positions,
    calculate_position_difference
)


def create_test_certificate(path, y_offset=0):
    """Create a test certificate image with text at specific positions."""
    width, height = 800, 600
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a default font, fallback to PIL's default
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 40)
    except:
        font = ImageFont.load_default()
    
    # Draw text at specific positions (with optional offset)
    # These positions match the search windows in extract_field_positions
    # Name field (0.20 - 0.40 of height = 120-240)
    draw.text((width // 2, 180 + y_offset), "Test Name", fill='black', font=font, anchor="mm")
    
    # Event field (0.40 - 0.58 of height = 240-348)
    draw.text((width // 2, 300 + y_offset), "Test Event", fill='black', font=font, anchor="mm")
    
    # Organiser field (0.55 - 0.70 of height = 330-420)
    draw.text((width // 2, 390 + y_offset), "Test Organiser", fill='black', font=font, anchor="mm")
    
    img.save(path)
    return path


def test_alignment_with_perfect_match():
    """Test alignment verification with perfect match."""
    print("\n" + "="*60)
    print("TEST 1: Perfect Alignment Match")
    print("="*60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        ref_path = os.path.join(tmpdir, "reference.png")
        gen_path = os.path.join(tmpdir, "generated.png")
        
        # Create identical certificates
        create_test_certificate(ref_path, y_offset=0)
        create_test_certificate(gen_path, y_offset=0)
        
        # Verify alignment
        result = verify_alignment_with_retries(
            gen_path, 
            ref_path,
            tolerance_px=0.02,
            max_attempts=5
        )
        
        print(f"✅ Passed: {result['passed']}")
        print(f"✅ Attempts: {result['attempts']}/5")
        print(f"✅ Max Difference: {result['max_difference_px']:.4f} px")
        print(f"✅ Message: {result['message']}")
        
        assert result['passed'], "Perfect match should pass"
        assert result['attempts'] == 1, "Should pass on first attempt"
        assert 'all_attempts' in result, "Should include all_attempts"
        
    print("✅ TEST 1 PASSED\n")


def test_alignment_with_max_attempts():
    """Test alignment verification when max attempts is reached."""
    print("\n" + "="*60)
    print("TEST 2: Max Attempts Reached - Using Best Available")
    print("="*60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        ref_path = os.path.join(tmpdir, "reference.png")
        
        # Create reference
        create_test_certificate(ref_path, y_offset=0)
        
        attempt_count = [0]
        cert_offsets = [10, 5, 3, 8, 4]  # Different offsets for each attempt
        
        def regenerate_cert():
            """Regenerate certificate with different offset each time."""
            gen_path = os.path.join(tmpdir, "generated.png")
            offset = cert_offsets[attempt_count[0] % len(cert_offsets)]
            create_test_certificate(gen_path, y_offset=offset)
            attempt_count[0] += 1
            return gen_path
        
        # Initial generation
        gen_path = regenerate_cert()
        
        # Verify alignment with limited attempts
        result = verify_alignment_with_retries(
            gen_path,
            ref_path,
            tolerance_px=0.02,  # Very tight tolerance - won't pass
            max_attempts=5,
            regenerate_func=regenerate_cert
        )
        
        print(f"⚠️  Passed: {result['passed']}")
        print(f"✅ Attempts: {result['attempts']}/5")
        print(f"✅ Max Difference: {result['max_difference_px']:.4f} px")
        print(f"✅ Message: {result['message']}")
        print(f"✅ Used Best Available: {result.get('used_best_available', False)}")
        
        if 'best_attempt' in result:
            print(f"✅ Best Attempt: #{result['best_attempt']['attempt_number']} "
                  f"with {result['best_attempt']['max_difference_px']:.4f} px difference")
        
        if 'all_attempts' in result:
            print(f"✅ Total Attempts Tracked: {len(result['all_attempts'])}")
            for i, attempt in enumerate(result['all_attempts'], 1):
                print(f"   Attempt {i}: {attempt['max_difference_px']:.4f} px")
        
        # Verify that we got the best attempt
        assert not result['passed'], "Should not pass with tight tolerance"
        assert result['attempts'] == 5, "Should use all 5 attempts"
        assert result.get('used_best_available', False), "Should use best available"
        assert 'best_attempt' in result, "Should include best_attempt"
        assert 'all_attempts' in result, "Should include all_attempts"
        assert len(result['all_attempts']) == 5, "Should track all 5 attempts"
        
        # Best attempt should have the minimum difference
        best_diff = result['best_attempt']['max_difference_px']
        all_diffs = [a['max_difference_px'] for a in result['all_attempts']]
        assert best_diff == min(all_diffs), "Best attempt should have minimum difference"
        
    print("✅ TEST 2 PASSED\n")


def test_position_extraction():
    """Test field position extraction."""
    print("\n" + "="*60)
    print("TEST 3: Field Position Extraction")
    print("="*60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        cert_path = os.path.join(tmpdir, "test.png")
        create_test_certificate(cert_path, y_offset=0)
        
        positions = extract_field_positions(cert_path)
        
        print(f"✅ Fields Detected: {list(positions.keys())}")
        
        for field_name, field_data in positions.items():
            print(f"\n   {field_name}:")
            print(f"      Y Center: {field_data['y_center']:.2f}")
            print(f"      X Center: {field_data['x_center']:.2f}")
            print(f"      Normalized Y: {field_data['normalized_y']:.4f}")
        
        # Verify all expected fields are detected
        expected_fields = ['name', 'event', 'organiser']
        for field in expected_fields:
            assert field in positions, f"Field {field} should be detected"
        
    print("\n✅ TEST 3 PASSED\n")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("ALIGNMENT ATTEMPT TRACKING TEST SUITE")
    print("="*60)
    
    try:
        test_alignment_with_perfect_match()
        test_alignment_with_max_attempts()
        test_position_extraction()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\nKey Features Verified:")
        print("  ✅ Alignment verification with retry logic")
        print("  ✅ Tracking of all alignment attempts")
        print("  ✅ Selection of best certificate when max attempts reached")
        print("  ✅ Field position extraction and comparison")
        print("  ✅ Proper reporting of attempt counts and differences")
        print("="*60 + "\n")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
