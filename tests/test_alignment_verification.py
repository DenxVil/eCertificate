"""Tests for certificate alignment verification.

This module tests the alignment verification functionality to ensure
certificates are verified against reference samples with <0.01px tolerance.
"""
import os
import sys
import tempfile
import pytest
from pathlib import Path
from PIL import Image

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.alignment_checker import (
    verify_certificate_alignment,
    calculate_image_difference,
    get_reference_certificate_path,
    verify_with_retry,
    AlignmentVerificationError
)
from app.utils.goonj_renderer import GOONJRenderer


class TestImageDifferenceCalculation:
    """Test image difference calculation functions."""
    
    def test_identical_images(self):
        """Test that identical images have 0% difference."""
        # Create identical test images
        img1 = Image.new('RGB', (100, 100), 'white')
        img2 = Image.new('RGB', (100, 100), 'white')
        
        diff_pct, max_diff, has_diff = calculate_image_difference(img1, img2, tolerance=1)
        
        assert diff_pct == 0.0
        assert max_diff == 0
        assert has_diff is False
    
    def test_different_sizes(self):
        """Test that different sized images return maximum difference."""
        img1 = Image.new('RGB', (100, 100), 'white')
        img2 = Image.new('RGB', (200, 200), 'white')
        
        diff_pct, max_diff, has_diff = calculate_image_difference(img1, img2, tolerance=1)
        
        assert diff_pct == 100.0
        assert max_diff == 255
        assert has_diff is True
    
    def test_slight_difference(self):
        """Test detection of slight differences."""
        # Create nearly identical images
        img1 = Image.new('RGB', (100, 100), 'white')
        img2 = img1.copy()
        
        # Add a single pixel with larger difference
        pixels = img2.load()
        pixels[50, 50] = (250, 250, 250)  # Different from white (255, 255, 255) by 5
        
        diff_pct, max_diff, has_diff = calculate_image_difference(img1, img2, tolerance=1)
        
        # Should detect the difference (difference of 5 > tolerance of 1)
        assert diff_pct > 0
        assert max_diff >= 5


class TestAlignmentVerification:
    """Test certificate alignment verification."""
    
    def test_verify_identical_certificates(self):
        """Test verification passes for identical certificates."""
        # Create a test certificate
        test_img = Image.new('RGB', (800, 600), 'white')
        
        with tempfile.TemporaryDirectory() as tmpdir:
            # Save as both generated and reference
            gen_path = os.path.join(tmpdir, 'generated.png')
            ref_path = os.path.join(tmpdir, 'reference.png')
            test_img.save(gen_path)
            test_img.save(ref_path)
            
            # Verify
            result = verify_certificate_alignment(gen_path, ref_path, tolerance_px=0.01)
            
            assert result['passed'] is True
            assert result['difference_pct'] == 0.0
            assert result['max_pixel_diff'] == 0
            assert result['tolerance_px'] == 0.01
            assert 'PERFECT MATCH' in result['message']
    
    def test_verify_different_certificates(self):
        """Test verification fails for different certificates."""
        # Create different images
        img1 = Image.new('RGB', (800, 600), 'white')
        img2 = Image.new('RGB', (800, 600), 'black')
        
        with tempfile.TemporaryDirectory() as tmpdir:
            gen_path = os.path.join(tmpdir, 'generated.png')
            ref_path = os.path.join(tmpdir, 'reference.png')
            img1.save(gen_path)
            img2.save(ref_path)
            
            # Verify
            result = verify_certificate_alignment(gen_path, ref_path, tolerance_px=0.01)
            
            assert result['passed'] is False
            assert result['difference_pct'] > 0
            assert 'FAILED' in result['message']
    
    def test_missing_generated_file(self):
        """Test error handling for missing generated file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            gen_path = os.path.join(tmpdir, 'nonexistent.png')
            ref_path = os.path.join(tmpdir, 'reference.png')
            
            # Create reference
            test_img = Image.new('RGB', (100, 100), 'white')
            test_img.save(ref_path)
            
            # Should raise FileNotFoundError
            with pytest.raises(FileNotFoundError):
                verify_certificate_alignment(gen_path, ref_path)
    
    def test_missing_reference_file(self):
        """Test error handling for missing reference file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            gen_path = os.path.join(tmpdir, 'generated.png')
            ref_path = os.path.join(tmpdir, 'nonexistent.png')
            
            # Create generated
            test_img = Image.new('RGB', (100, 100), 'white')
            test_img.save(gen_path)
            
            # Should raise FileNotFoundError
            with pytest.raises(FileNotFoundError):
                verify_certificate_alignment(gen_path, ref_path)


class TestVerifyWithRetry:
    """Test retry logic for alignment verification."""
    
    def test_retry_success_first_attempt(self):
        """Test that retry succeeds on first attempt for identical images."""
        # Create identical images
        test_img = Image.new('RGB', (100, 100), 'white')
        
        with tempfile.TemporaryDirectory() as tmpdir:
            gen_path = os.path.join(tmpdir, 'generated.png')
            ref_path = os.path.join(tmpdir, 'reference.png')
            test_img.save(gen_path)
            test_img.save(ref_path)
            
            # Should succeed on first attempt
            result = verify_with_retry(gen_path, ref_path, max_attempts=3)
            
            assert result['passed'] is True
            assert result['attempts'] == 1
    
    def test_retry_fails_all_attempts(self):
        """Test that retry fails after max attempts for different images."""
        # Create different images
        img1 = Image.new('RGB', (100, 100), 'white')
        img2 = Image.new('RGB', (100, 100), 'black')
        
        with tempfile.TemporaryDirectory() as tmpdir:
            gen_path = os.path.join(tmpdir, 'generated.png')
            ref_path = os.path.join(tmpdir, 'reference.png')
            img1.save(gen_path)
            img2.save(ref_path)
            
            # Should fail after all attempts
            with pytest.raises(AlignmentVerificationError) as exc_info:
                verify_with_retry(gen_path, ref_path, max_attempts=3)
            
            assert 'failed after 3 attempts' in str(exc_info.value)


class TestReferencePathResolution:
    """Test reference certificate path resolution."""
    
    def test_get_reference_from_template(self):
        """Test finding reference certificate next to template."""
        template_path = 'templates/goonj_certificate.png'
        
        if not os.path.exists(template_path):
            pytest.skip("GOONJ template not found")
        
        # Should find reference certificate
        reference_path = get_reference_certificate_path(template_path)
        
        assert os.path.exists(reference_path)
        assert 'Sample_certificate.png' in reference_path
    
    def test_missing_reference_raises_error(self):
        """Test error when reference certificate is missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            template_path = os.path.join(tmpdir, 'test_template.png')
            
            # Should raise FileNotFoundError
            with pytest.raises(FileNotFoundError) as exc_info:
                get_reference_certificate_path(template_path)
            
            assert 'Reference certificate not found' in str(exc_info.value)


class TestIntegrationWithActualCertificates:
    """Integration tests with actual certificate generation."""
    
    def test_verify_generated_certificate_against_sample(self):
        """Test verification of a generated certificate against the sample."""
        template_path = 'templates/goonj_certificate.png'
        reference_path = 'templates/Sample_certificate.png'
        
        if not os.path.exists(template_path) or not os.path.exists(reference_path):
            pytest.skip("GOONJ template or reference not found")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            renderer = GOONJRenderer(template_path, output_folder=tmpdir)
            
            # Use the exact same data as the reference
            sample_data = {
                'name': 'SAMPLE NAME',
                'event': 'SAMPLE EVENT',
                'organiser': 'SAMPLE ORG'
            }
            
            cert_path = renderer.render(sample_data, output_format='png')
            
            # Verify alignment
            result = verify_certificate_alignment(
                cert_path,
                reference_path,
                tolerance_px=0.01
            )
            
            # Should pass with perfect or near-perfect alignment
            assert result['passed'] is True
            assert result['difference_pct'] < 0.001  # Less than 0.001%
            
            print(f"\n✅ Integration test result:")
            print(f"   Passed: {result['passed']}")
            print(f"   Difference: {result['difference_pct']:.6f}%")
            print(f"   Message: {result['message']}")


def test_smoke_alignment_verification():
    """Smoke test: Generate and verify a certificate end-to-end."""
    template_path = 'templates/goonj_certificate.png'
    reference_path = 'templates/Sample_certificate.png'
    
    if not os.path.exists(template_path) or not os.path.exists(reference_path):
        pytest.skip("GOONJ template or reference not found")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        renderer = GOONJRenderer(template_path, output_folder=tmpdir)
        
        # Generate certificate
        test_data = {
            'name': 'SAMPLE NAME',
            'event': 'SAMPLE EVENT',
            'organiser': 'SAMPLE ORG'
        }
        
        cert_path = renderer.render(test_data)
        
        # Verify with retry
        result = verify_with_retry(
            cert_path,
            reference_path,
            max_attempts=100,
            tolerance_px=0.02
        )
        
        # Should succeed
        assert result['passed'] is True
        assert result['attempts'] >= 1
        
        print(f"\n✅ Smoke test: Certificate verified in {result['attempts']} attempt(s)")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
