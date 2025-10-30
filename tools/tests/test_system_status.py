#!/usr/bin/env python
"""
Smoke test for system status endpoint.

This script validates that the new system status API endpoint
returns the expected data structure.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app import create_app


def test_system_status_endpoint():
    """Test the system status API endpoint."""
    print("\n" + "="*60)
    print("Testing System Status API Endpoint")
    print("="*60)
    
    app = create_app()
    
    with app.test_client() as client:
        # Test system status endpoint
        response = client.get('/goonj/api/system-status')
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ FAIL: Expected 200, got {response.status_code}")
            return 1
        
        data = response.get_json()
        print(f"Response Data: {data}")
        
        # Validate required fields
        required_fields = [
            'template_exists',
            'smtp_configured',
            'engine_status',
            'latency_ms',
            'active_jobs_count',
            'last_updated'
        ]
        
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            print(f"❌ FAIL: Missing fields: {missing_fields}")
            return 1
        
        # Validate field types
        if not isinstance(data['template_exists'], bool):
            print(f"❌ FAIL: template_exists should be bool")
            return 1
        
        if not isinstance(data['smtp_configured'], bool):
            print(f"❌ FAIL: smtp_configured should be bool")
            return 1
        
        if data['engine_status'] not in ['operational', 'degraded', 'error']:
            print(f"❌ FAIL: Invalid engine_status: {data['engine_status']}")
            return 1
        
        if not isinstance(data['latency_ms'], int):
            print(f"❌ FAIL: latency_ms should be int")
            return 1
        
        if not isinstance(data['active_jobs_count'], int):
            print(f"❌ FAIL: active_jobs_count should be int")
            return 1
        
        print("\n✅ PASS: All fields present and valid")
        print(f"  - Template Exists: {data['template_exists']}")
        print(f"  - SMTP Configured: {data['smtp_configured']}")
        print(f"  - Engine Status: {data['engine_status']}")
        print(f"  - Latency: {data['latency_ms']}ms")
        print(f"  - Active Jobs: {data['active_jobs_count']}")
        
        return 0


def test_backward_compatibility():
    """Test that existing endpoints still work."""
    print("\n" + "="*60)
    print("Testing Backward Compatibility")
    print("="*60)
    
    app = create_app()
    
    with app.test_client() as client:
        # Test original status endpoint
        response = client.get('/goonj/status')
        
        if response.status_code != 200:
            print(f"❌ FAIL: /goonj/status returned {response.status_code}")
            return 1
        
        data = response.get_json()
        
        # Validate old endpoint still has expected fields
        if 'status' not in data or 'template_exists' not in data:
            print(f"❌ FAIL: Original status endpoint missing fields")
            return 1
        
        print(f"✅ PASS: Original /goonj/status endpoint works")
        print(f"  - Status: {data['status']}")
        print(f"  - Template: {data['template_exists']}")
        
        return 0


def main():
    """Run all smoke tests."""
    print("\n" + "="*60)
    print("SYSTEM STATUS API SMOKE TESTS")
    print("="*60)
    
    results = []
    
    try:
        results.append(test_system_status_endpoint())
        results.append(test_backward_compatibility())
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Summary
    print("\n" + "="*60)
    if all(r == 0 for r in results):
        print("✅ ALL TESTS PASSED")
        print("="*60)
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("="*60)
        return 1


if __name__ == '__main__':
    sys.exit(main())
