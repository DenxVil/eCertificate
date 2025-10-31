#!/usr/bin/env python
"""
Integration test for alignment verification fixes.

Tests:
1. Configuration is read from environment/config
2. Missing fields are properly detected
3. Individual field differences are calculated
4. Diagnostic tool works correctly
"""
import os
import sys
import tempfile
from PIL import Image, ImageDraw, ImageFont

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_config_defaults():
    """Test that config defaults are updated."""
    print("=" * 70)
    print("Test 1: Configuration Defaults")
    print("=" * 70)
    
    from config import Config
    
    # These should now be 30 and 3, not 150
    max_attempts = Config.ALIGNMENT_MAX_ATTEMPTS
    email_retries = Config.EMAIL_MAX_RETRIES
    
    print(f"ALIGNMENT_MAX_ATTEMPTS: {max_attempts}")
    print(f"EMAIL_MAX_RETRIES: {email_retries}")
    
    # If .env is not set, these should use new defaults
    if 'ALIGNMENT_MAX_ATTEMPTS' not in os.environ:
        assert max_attempts == 30, f"Expected 30, got {max_attempts}"
        print("✅ ALIGNMENT_MAX_ATTEMPTS default is 30")
    else:
        print(f"ℹ️  ALIGNMENT_MAX_ATTEMPTS set in environment to {max_attempts}")
    
    if 'EMAIL_MAX_RETRIES' not in os.environ:
        assert email_retries == 3, f"Expected 3, got {email_retries}"
        print("✅ EMAIL_MAX_RETRIES default is 3")
    else:
        print(f"ℹ️  EMAIL_MAX_RETRIES set in environment to {email_retries}")
    
    print()


def test_missing_field_detection():
    """Test that missing fields are properly detected."""
    print("=" * 70)
    print("Test 2: Missing Field Detection")
    print("=" * 70)
    
    # Import functions directly
    import importlib.util
    script_dir = os.path.dirname(os.path.abspath(__file__))
    verifier_path = os.path.join(script_dir, 'app', 'utils', 'iterative_alignment_verifier.py')
    spec = importlib.util.spec_from_file_location(
        "iterative_alignment_verifier",
        verifier_path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    extract_field_positions = module.extract_field_positions
    calculate_position_difference = module.calculate_position_difference
    
    # Create reference certificate with all fields
    ref_img = Image.new('RGB', (2000, 1415), color='white')
    ref_draw = ImageDraw.Draw(ref_img)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 80)
    except:
        font = ImageFont.load_default()
    
    # Draw all three fields in expected positions
    ref_draw.text((1000, 422), "Reference Name", fill='black', font=font, anchor='mm')
    ref_draw.text((1000, 723), "Reference Event", fill='black', font=font, anchor='mm')
    ref_draw.text((1000, 894), "Reference Org", fill='black', font=font, anchor='mm')
    
    # Create test certificate with only one field (missing event and organiser)
    test_img = Image.new('RGB', (2000, 1415), color='white')
    test_draw = ImageDraw.Draw(test_img)
    test_draw.text((1000, 422), "Test Name", fill='black', font=font, anchor='mm')
    
    # Save to temp files
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as ref_file:
        ref_path = ref_file.name
        ref_img.save(ref_path)
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as test_file:
        test_path = test_file.name
        test_img.save(test_path)
    
    try:
        # Extract positions
        ref_positions = extract_field_positions(ref_path)
        test_positions = extract_field_positions(test_path)
        
        print(f"Reference fields detected: {list(ref_positions.keys())}")
        print(f"Test fields detected: {list(test_positions.keys())}")
        
        # Calculate difference
        diff_result = calculate_position_difference(test_positions, ref_positions)
        max_diff = diff_result['max_difference_px']
        
        print(f"Max difference: {max_diff}")
        
        # Verify missing fields are detected
        assert 'missing_fields' in diff_result, "Missing fields should be reported"
        assert len(diff_result['missing_fields']) >= 1, "Should have at least 1 missing field"
        assert max_diff == float('inf'), f"Max diff should be inf for missing fields, got {max_diff}"
        
        print(f"✅ Missing fields detected: {diff_result['missing_fields']}")
        print(f"✅ Max difference correctly set to infinity")
        
    finally:
        # Cleanup
        os.unlink(ref_path)
        os.unlink(test_path)
    
    print()


def test_individual_field_reporting():
    """Test that individual field differences are reported."""
    print("=" * 70)
    print("Test 3: Individual Field Difference Reporting")
    print("=" * 70)
    
    # Import functions
    import importlib.util
    script_dir = os.path.dirname(os.path.abspath(__file__))
    verifier_path = os.path.join(script_dir, 'app', 'utils', 'iterative_alignment_verifier.py')
    spec = importlib.util.spec_from_file_location(
        "iterative_alignment_verifier",
        verifier_path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    calculate_position_difference = module.calculate_position_difference
    
    # Create mock positions
    ref_positions = {
        'name': {'y_center': 422.5, 'x_center': 999.5},
        'event': {'y_center': 723.5, 'x_center': 951.0},
        'organiser': {'y_center': 894.5, 'x_center': 1043.5}
    }
    
    test_positions = {
        'name': {'y_center': 422.5, 'x_center': 999.5},  # Perfect
        'event': {'y_center': 733.5, 'x_center': 951.0},  # 10px off in Y
        'organiser': {'y_center': 894.5, 'x_center': 1053.5}  # 10px off in X
    }
    
    diff_result = calculate_position_difference(test_positions, ref_positions)
    
    # Check individual field reporting
    assert 'name' in diff_result['fields'], "Name field should be in results"
    assert 'event' in diff_result['fields'], "Event field should be in results"
    assert 'organiser' in diff_result['fields'], "Organiser field should be in results"
    
    name_diff = diff_result['fields']['name']
    event_diff = diff_result['fields']['event']
    org_diff = diff_result['fields']['organiser']
    
    print(f"Name Y diff: {name_diff['y_diff']:.2f}px, X diff: {name_diff['x_diff']:.2f}px")
    print(f"Event Y diff: {event_diff['y_diff']:.2f}px, X diff: {event_diff['x_diff']:.2f}px")
    print(f"Organiser Y diff: {org_diff['y_diff']:.2f}px, X diff: {org_diff['x_diff']:.2f}px")
    
    assert name_diff['y_diff'] == 0.0, "Name Y should be perfect"
    assert event_diff['y_diff'] == 10.0, "Event Y should be 10px off"
    assert org_diff['x_diff'] == 10.0, "Organiser X should be 10px off"
    
    print("✅ Individual field differences correctly calculated")
    print()


def main():
    """Run all integration tests."""
    print("\n")
    print("=" * 70)
    print("INTEGRATION TESTS FOR ALIGNMENT VERIFICATION FIXES")
    print("=" * 70)
    print()
    
    try:
        test_config_defaults()
        test_missing_field_detection()
        test_individual_field_reporting()
        
        print("=" * 70)
        print("✅ ALL TESTS PASSED")
        print("=" * 70)
        print()
        return 0
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
