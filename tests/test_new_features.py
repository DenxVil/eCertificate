#!/usr/bin/env python3
"""
Comprehensive test for the new certificate generation features.

Tests:
1. Universal alignment verification for all certificates
2. JSON response mode with detailed status
3. SMTP configuration checking and error messages
4. Certificate download endpoint
5. View and download options
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ['SECRET_KEY'] = 'test-key'
os.environ['DATABASE_URL'] = 'sqlite:///test.db'

from app import create_app
import json

def test_json_response():
    """Test certificate generation with JSON response."""
    print("\n" + "=" * 70)
    print("TEST 1: JSON Response Mode")
    print("=" * 70)
    
    app = create_app('development')
    with app.test_client() as client:
        response = client.post('/goonj/generate', 
            data={
                'name': 'Test User',
                'event': 'Test Event 2025',
                'organiser': 'Test Org',
                'return_json': 'true'
            }
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.is_json, "Response should be JSON"
        
        data = response.get_json()
        assert data['success'], "Generation should succeed"
        assert 'certificate' in data, "Should have certificate data"
        assert 'alignment_status' in data, "Should have alignment status"
        assert 'email_status' in data, "Should have email status"
        
        print("✅ JSON response includes all required fields")
        print(f"   - Certificate: {data['certificate']['filename']}")
        print(f"   - Alignment: {data['alignment_status']['passed']}")
        print(f"   - Email attempted: {data['email_status']['attempted']}")
        
        return data

def test_alignment_verification():
    """Test universal alignment verification."""
    print("\n" + "=" * 70)
    print("TEST 2: Universal Alignment Verification")
    print("=" * 70)
    
    app = create_app('development')
    with app.test_client() as client:
        response = client.post('/goonj/generate', 
            data={
                'name': 'Alignment Test',
                'event': 'Verification Test',
                'organiser': 'QA Team',
                'return_json': 'true'
            }
        )
        
        data = response.get_json()
        alignment = data['alignment_status']
        
        assert alignment['enabled'], "Alignment check should be enabled"
        assert alignment['passed'], "Alignment verification should pass"
        assert 'details' in alignment, "Should have alignment details"
        
        details = alignment['details']
        assert 'dimensions' in details, "Should check dimensions"
        assert 'format' in details, "Should check format"
        assert 'template' in details, "Should check template"
        
        print("✅ Alignment verification passed for regular certificate")
        print(f"   - Dimensions: {details['dimensions']['passed']}")
        print(f"   - Format: {details['format']['passed']}")
        print(f"   - Template: {details['template']['passed']}")

def test_smtp_error_messages():
    """Test SMTP configuration error messages."""
    print("\n" + "=" * 70)
    print("TEST 3: SMTP Configuration Error Messages")
    print("=" * 70)
    
    app = create_app('development')
    with app.test_client() as client:
        response = client.post('/goonj/generate', 
            data={
                'name': 'Email Test',
                'event': 'SMTP Test',
                'organiser': 'DevTeam',
                'email': 'test@example.com',
                'return_json': 'true'
            }
        )
        
        data = response.get_json()
        email_status = data['email_status']
        
        assert email_status['attempted'], "Should attempt email"
        assert not email_status['sent'], "Email should not be sent (no SMTP config)"
        assert email_status['smtp_config'] is not None, "Should have SMTP config info"
        
        smtp_config = email_status['smtp_config']
        assert not smtp_config['configured'], "SMTP should not be configured"
        assert len(smtp_config['issues']) > 0, "Should list configuration issues"
        
        print("✅ SMTP error messages are detailed and helpful")
        print(f"   - Configured: {smtp_config['configured']}")
        print(f"   - Issues found: {len(smtp_config['issues'])}")
        for issue in smtp_config['issues']:
            print(f"     • {issue}")

def test_certificate_download():
    """Test certificate download endpoint."""
    print("\n" + "=" * 70)
    print("TEST 4: Certificate Download Endpoint")
    print("=" * 70)
    
    app = create_app('development')
    with app.test_client() as client:
        # First generate a certificate
        gen_response = client.post('/goonj/generate', 
            data={
                'name': 'Download Test',
                'event': 'Download Event',
                'organiser': 'DownloadOrg',
                'return_json': 'true'
            }
        )
        
        data = gen_response.get_json()
        filename = data['certificate']['filename']
        download_url = data['certificate']['download_url']
        
        # Now download it
        dl_response = client.get(download_url)
        
        assert dl_response.status_code == 200, f"Download should succeed, got {dl_response.status_code}"
        assert dl_response.mimetype == 'image/png', "Should be PNG image"
        assert len(dl_response.data) > 0, "Should have data"
        
        print("✅ Certificate download works correctly")
        print(f"   - Filename: {filename}")
        print(f"   - Download URL: {download_url}")
        print(f"   - Size: {len(dl_response.data)} bytes")

def test_download_security():
    """Test download endpoint security (path traversal protection)."""
    print("\n" + "=" * 70)
    print("TEST 5: Download Endpoint Security")
    print("=" * 70)
    
    app = create_app('development')
    with app.test_client() as client:
        # Try path traversal attack
        bad_filenames = [
            '../../../etc/passwd',
            '..%2F..%2F..%2Fetc%2Fpasswd',
            'test/../../sensitive.txt',
        ]
        
        for bad_filename in bad_filenames:
            response = client.get(f'/goonj/download/{bad_filename}')
            assert response.status_code in [400, 404], f"Should reject bad filename: {bad_filename}"
        
        print("✅ Download endpoint properly validates filenames")
        print(f"   - Tested {len(bad_filenames)} path traversal attempts")
        print(f"   - All properly rejected")

def run_all_tests():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "COMPREHENSIVE FEATURE TESTS" + " " * 25 + "║")
    print("╚" + "=" * 68 + "╝")
    
    try:
        test_json_response()
        test_alignment_verification()
        test_smtp_error_messages()
        test_certificate_download()
        test_download_security()
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        print("\nNew features are working correctly:")
        print("  ✓ JSON response mode with detailed status")
        print("  ✓ Universal alignment verification for all certificates")
        print("  ✓ Detailed SMTP error messages")
        print("  ✓ Certificate download endpoint")
        print("  ✓ Security validation")
        print()
        
        return True
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
