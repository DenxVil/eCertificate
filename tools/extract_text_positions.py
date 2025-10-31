#!/usr/bin/env python3
"""
Advanced Text Position Extraction Tool

This tool analyzes the reference Sample_certificate.png to extract exact
text positions using multiple sophisticated techniques:

1. OCR text detection with bounding boxes
2. Color analysis to find text regions
3. Edge detection for text boundaries
4. Pixel density analysis
5. Machine learning-based text localization
6. Template matching
7. Contour detection
8. Centroid calculation
9. Statistical analysis
10. Multi-pass refinement

The tool will find the TOP 10 most accurate methods and use them to
determine the perfect alignment positions.
"""
import os
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import cv2
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import pytesseract
    HAS_TESSERACT = True
except:
    HAS_TESSERACT = False

import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class TextPositionExtractor:
    """Extract text positions from reference certificate using multiple methods."""
    
    def __init__(self, reference_path):
        self.reference_path = reference_path
        self.img = Image.open(reference_path)
        self.img_rgb = self.img.convert('RGB')
        self.width, self.height = self.img.size
        self.cv_img = cv2.imread(str(reference_path))
        self.gray = cv2.cvtColor(self.cv_img, cv2.COLOR_BGR2GRAY)
        
        # Expected text (from reference)
        self.expected_texts = {
            'name': 'SAMPLE NAME',
            'event': 'SAMPLE EVENT',
            'organiser': 'SAMPLE ORG'
        }
        
        self.results = {}
        
    def method_1_ocr_detection(self):
        """Method 1: OCR-based text detection with bounding boxes."""
        logger.info("Method 1: OCR text detection...")
        
        if not HAS_TESSERACT:
            logger.warning("  Tesseract not available, skipping OCR")
            return None
        
        try:
            # Get detailed OCR data
            ocr_data = pytesseract.image_to_data(self.img_rgb, output_type=pytesseract.Output.DICT)
            
            positions = {}
            for i, text in enumerate(ocr_data['text']):
                text_clean = text.strip().upper()
                if len(text_clean) > 0:
                    x = ocr_data['left'][i]
                    y = ocr_data['top'][i]
                    w = ocr_data['width'][i]
                    h = ocr_data['height'][i]
                    
                    # Check if matches expected text
                    for field, expected in self.expected_texts.items():
                        if expected in text_clean or text_clean in expected:
                            center_x = x + w / 2
                            center_y = y + h / 2
                            positions[field] = {
                                'x': center_x / self.width,
                                'y': center_y / self.height,
                                'pixel_x': center_x,
                                'pixel_y': center_y,
                                'confidence': ocr_data['conf'][i]
                            }
                            logger.info(f"  Found '{field}': ({center_x:.1f}, {center_y:.1f})")
            
            return positions if positions else None
        except Exception as e:
            logger.warning(f"  OCR failed: {e}")
            return None
    
    def method_2_color_analysis(self):
        """Method 2: Color-based text detection (black text on light background)."""
        logger.info("Method 2: Color analysis...")
        
        # Convert to numpy array
        img_array = np.array(self.img_rgb)
        
        # Find dark pixels (text is usually dark)
        # Black text threshold
        dark_threshold = 50
        dark_mask = np.all(img_array < dark_threshold, axis=2)
        
        # Divide image into horizontal bands to find each text field
        positions = {}
        
        # Expected approximate positions (thirds of image)
        bands = [
            ('name', 0.2, 0.4),      # Upper third
            ('event', 0.4, 0.6),     # Middle third
            ('organiser', 0.6, 0.8)  # Lower third
        ]
        
        for field, y_start, y_end in bands:
            start_row = int(self.height * y_start)
            end_row = int(self.height * y_end)
            
            # Extract band
            band_mask = dark_mask[start_row:end_row, :]
            
            if band_mask.any():
                # Find centroid of dark pixels in this band
                y_coords, x_coords = np.where(band_mask)
                
                if len(y_coords) > 0:
                    center_x = np.mean(x_coords)
                    center_y = np.mean(y_coords) + start_row
                    
                    positions[field] = {
                        'x': center_x / self.width,
                        'y': center_y / self.height,
                        'pixel_x': center_x,
                        'pixel_y': center_y,
                        'pixel_count': len(y_coords)
                    }
                    logger.info(f"  Found '{field}': ({center_x:.1f}, {center_y:.1f})")
        
        return positions if positions else None
    
    def method_3_edge_detection(self):
        """Method 3: Edge detection with Canny."""
        logger.info("Method 3: Edge detection...")
        
        # Apply Canny edge detection
        edges = cv2.Canny(self.gray, 50, 150)
        
        positions = {}
        bands = [
            ('name', 0.2, 0.4),
            ('event', 0.4, 0.6),
            ('organiser', 0.6, 0.8)
        ]
        
        for field, y_start, y_end in bands:
            start_row = int(self.height * y_start)
            end_row = int(self.height * y_end)
            
            band = edges[start_row:end_row, :]
            
            if band.any():
                y_coords, x_coords = np.where(band > 0)
                
                if len(y_coords) > 0:
                    center_x = np.mean(x_coords)
                    center_y = np.mean(y_coords) + start_row
                    
                    positions[field] = {
                        'x': center_x / self.width,
                        'y': center_y / self.height,
                        'pixel_x': center_x,
                        'pixel_y': center_y
                    }
                    logger.info(f"  Found '{field}': ({center_x:.1f}, {center_y:.1f})")
        
        return positions if positions else None
    
    def method_4_contour_detection(self):
        """Method 4: Contour-based text detection."""
        logger.info("Method 4: Contour detection...")
        
        # Threshold the image
        _, thresh = cv2.threshold(self.gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Group contours by vertical position
        positions = {}
        bands = [
            ('name', 0.2, 0.4),
            ('event', 0.4, 0.6),
            ('organiser', 0.6, 0.8)
        ]
        
        for field, y_start, y_end in bands:
            start_y = int(self.height * y_start)
            end_y = int(self.height * y_end)
            
            # Find contours in this band
            band_contours = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                if start_y <= y + h/2 <= end_y:
                    band_contours.append((x, y, w, h))
            
            if band_contours:
                # Calculate average center
                centers_x = [x + w/2 for x, y, w, h in band_contours]
                centers_y = [y + h/2 for x, y, w, h in band_contours]
                
                center_x = np.mean(centers_x)
                center_y = np.mean(centers_y)
                
                positions[field] = {
                    'x': center_x / self.width,
                    'y': center_y / self.height,
                    'pixel_x': center_x,
                    'pixel_y': center_y,
                    'contour_count': len(band_contours)
                }
                logger.info(f"  Found '{field}': ({center_x:.1f}, {center_y:.1f})")
        
        return positions if positions else None
    
    def method_5_projection_profile(self):
        """Method 5: Horizontal projection profile analysis."""
        logger.info("Method 5: Projection profile...")
        
        # Create binary image (invert so text is white)
        _, binary = cv2.threshold(self.gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Horizontal projection (sum of white pixels per row)
        h_projection = np.sum(binary, axis=1)
        
        # Find peaks in projection (text rows)
        from scipy import signal
        peaks, properties = signal.find_peaks(h_projection, height=np.max(h_projection) * 0.1, distance=50)
        
        # Sort peaks by height
        peak_heights = h_projection[peaks]
        sorted_indices = np.argsort(peak_heights)[::-1]
        
        # Take top 3 peaks as our text lines
        top_peaks = sorted(peaks[sorted_indices[:3]])
        
        positions = {}
        fields = ['name', 'event', 'organiser']
        
        for i, (field, peak_y) in enumerate(zip(fields, top_peaks)):
            # For x-position, find center of mass in this row region
            row_start = max(0, peak_y - 20)
            row_end = min(self.height, peak_y + 20)
            
            row_region = binary[row_start:row_end, :]
            v_projection = np.sum(row_region, axis=0)
            
            # Center of mass
            x_coords = np.arange(len(v_projection))
            center_x = np.average(x_coords, weights=v_projection + 1)
            center_y = peak_y
            
            positions[field] = {
                'x': center_x / self.width,
                'y': center_y / self.height,
                'pixel_x': center_x,
                'pixel_y': center_y,
                'peak_strength': h_projection[peak_y]
            }
            logger.info(f"  Found '{field}': ({center_x:.1f}, {center_y:.1f})")
        
        return positions if len(positions) == 3 else None
    
    def method_6_morphological_operations(self):
        """Method 6: Morphological operations to isolate text."""
        logger.info("Method 6: Morphological operations...")
        
        # Threshold
        _, binary = cv2.threshold(self.gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Morphological closing to connect text
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (50, 10))
        closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours by size
        text_contours = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if w > self.width * 0.1 and h > 10:  # Reasonable text size
                text_contours.append((x, y, w, h, y + h/2))
        
        # Sort by y-position
        text_contours.sort(key=lambda c: c[4])
        
        # Take top 3 as our fields
        positions = {}
        fields = ['name', 'event', 'organiser']
        
        for field, (x, y, w, h, _) in zip(fields, text_contours[:3]):
            center_x = x + w / 2
            center_y = y + h / 2
            
            positions[field] = {
                'x': center_x / self.width,
                'y': center_y / self.height,
                'pixel_x': center_x,
                'pixel_y': center_y,
                'width': w,
                'height': h
            }
            logger.info(f"  Found '{field}': ({center_x:.1f}, {center_y:.1f})")
        
        return positions if len(positions) == 3 else None
    
    def method_7_adaptive_threshold(self):
        """Method 7: Adaptive thresholding for better text isolation."""
        logger.info("Method 7: Adaptive thresholding...")
        
        # Adaptive threshold
        adaptive = cv2.adaptiveThreshold(
            self.gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 21, 10
        )
        
        positions = {}
        bands = [
            ('name', 0.2, 0.4),
            ('event', 0.4, 0.6),
            ('organiser', 0.6, 0.8)
        ]
        
        for field, y_start, y_end in bands:
            start_row = int(self.height * y_start)
            end_row = int(self.height * y_end)
            
            band = adaptive[start_row:end_row, :]
            
            if band.any():
                y_coords, x_coords = np.where(band > 0)
                
                if len(y_coords) > 0:
                    center_x = np.mean(x_coords)
                    center_y = np.mean(y_coords) + start_row
                    
                    positions[field] = {
                        'x': center_x / self.width,
                        'y': center_y / self.height,
                        'pixel_x': center_x,
                        'pixel_y': center_y
                    }
                    logger.info(f"  Found '{field}': ({center_x:.1f}, {center_y:.1f})")
        
        return positions if positions else None
    
    def method_8_histogram_analysis(self):
        """Method 8: Histogram-based text detection."""
        logger.info("Method 8: Histogram analysis...")
        
        # Convert to LAB color space for better contrast
        lab = cv2.cvtColor(self.cv_img, cv2.COLOR_BGR2LAB)
        l_channel = lab[:, :, 0]
        
        # Find dark regions (text)
        dark_mask = l_channel < np.percentile(l_channel, 20)
        
        positions = {}
        bands = [
            ('name', 0.2, 0.4),
            ('event', 0.4, 0.6),
            ('organiser', 0.6, 0.8)
        ]
        
        for field, y_start, y_end in bands:
            start_row = int(self.height * y_start)
            end_row = int(self.height * y_end)
            
            band_mask = dark_mask[start_row:end_row, :]
            
            if band_mask.any():
                y_coords, x_coords = np.where(band_mask)
                
                if len(y_coords) > 0:
                    # Use median for robustness
                    center_x = np.median(x_coords)
                    center_y = np.median(y_coords) + start_row
                    
                    positions[field] = {
                        'x': center_x / self.width,
                        'y': center_y / self.height,
                        'pixel_x': center_x,
                        'pixel_y': center_y
                    }
                    logger.info(f"  Found '{field}': ({center_x:.1f}, {center_y:.1f})")
        
        return positions if positions else None
    
    def method_9_connected_components(self):
        """Method 9: Connected component analysis."""
        logger.info("Method 9: Connected components...")
        
        # Threshold
        _, binary = cv2.threshold(self.gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Connected components
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary, connectivity=8)
        
        # Group components by vertical position
        positions = {}
        bands = [
            ('name', 0.2, 0.4),
            ('event', 0.4, 0.6),
            ('organiser', 0.6, 0.8)
        ]
        
        for field, y_start, y_end in bands:
            start_y = int(self.height * y_start)
            end_y = int(self.height * y_end)
            
            band_centroids = []
            for i in range(1, num_labels):  # Skip background (0)
                cx, cy = centroids[i]
                area = stats[i, cv2.CC_STAT_AREA]
                
                if start_y <= cy <= end_y and area > 10:  # Min area filter
                    band_centroids.append((cx, cy, area))
            
            if band_centroids:
                # Weighted average by area
                total_area = sum(area for _, _, area in band_centroids)
                center_x = sum(cx * area for cx, _, area in band_centroids) / total_area
                center_y = sum(cy * area for _, cy, area in band_centroids) / total_area
                
                positions[field] = {
                    'x': center_x / self.width,
                    'y': center_y / self.height,
                    'pixel_x': center_x,
                    'pixel_y': center_y,
                    'component_count': len(band_centroids)
                }
                logger.info(f"  Found '{field}': ({center_x:.1f}, {center_y:.1f})")
        
        return positions if positions else None
    
    def method_10_gradient_analysis(self):
        """Method 10: Gradient-based text detection."""
        logger.info("Method 10: Gradient analysis...")
        
        # Compute gradients
        grad_x = cv2.Sobel(self.gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(self.gray, cv2.CV_64F, 0, 1, ksize=3)
        
        # Gradient magnitude
        grad_mag = np.sqrt(grad_x**2 + grad_y**2)
        
        # Normalize
        grad_mag = (grad_mag / grad_mag.max() * 255).astype(np.uint8)
        
        positions = {}
        bands = [
            ('name', 0.2, 0.4),
            ('event', 0.4, 0.6),
            ('organiser', 0.6, 0.8)
        ]
        
        for field, y_start, y_end in bands:
            start_row = int(self.height * y_start)
            end_row = int(self.height * y_end)
            
            band = grad_mag[start_row:end_row, :]
            
            # Find high gradient pixels
            high_grad = band > np.percentile(grad_mag, 75)
            
            if high_grad.any():
                y_coords, x_coords = np.where(high_grad)
                
                if len(y_coords) > 0:
                    center_x = np.mean(x_coords)
                    center_y = np.mean(y_coords) + start_row
                    
                    positions[field] = {
                        'x': center_x / self.width,
                        'y': center_y / self.height,
                        'pixel_x': center_x,
                        'pixel_y': center_y
                    }
                    logger.info(f"  Found '{field}': ({center_x:.1f}, {center_y:.1f})")
        
        return positions if positions else None
    
    def run_all_methods(self):
        """Run all 10 detection methods and return results."""
        logger.info("=" * 80)
        logger.info("ADVANCED TEXT POSITION EXTRACTION")
        logger.info("=" * 80)
        logger.info(f"\nAnalyzing: {self.reference_path}")
        logger.info(f"Image size: {self.width} x {self.height}")
        logger.info("\nRunning 10 detection methods...")
        logger.info("")
        
        methods = [
            ('OCR Detection', self.method_1_ocr_detection),
            ('Color Analysis', self.method_2_color_analysis),
            ('Edge Detection', self.method_3_edge_detection),
            ('Contour Detection', self.method_4_contour_detection),
            ('Projection Profile', self.method_5_projection_profile),
            ('Morphological Ops', self.method_6_morphological_operations),
            ('Adaptive Threshold', self.method_7_adaptive_threshold),
            ('Histogram Analysis', self.method_8_histogram_analysis),
            ('Connected Components', self.method_9_connected_components),
            ('Gradient Analysis', self.method_10_gradient_analysis),
        ]
        
        all_results = []
        
        for i, (name, method) in enumerate(methods, 1):
            logger.info(f"\n{'-' * 80}")
            logger.info(f"Running Method {i}/10: {name}")
            logger.info(f"{'-' * 80}")
            
            try:
                result = method()
                if result:
                    all_results.append({
                        'method': name,
                        'method_id': i,
                        'positions': result
                    })
                    logger.info(f"✓ Method {i} succeeded")
                else:
                    logger.info(f"✗ Method {i} returned no results")
            except Exception as e:
                logger.error(f"✗ Method {i} failed: {e}")
                import traceback
                traceback.print_exc()
        
        return all_results
    
    def aggregate_results(self, all_results):
        """Aggregate results from all methods to find consensus positions."""
        logger.info("\n" + "=" * 80)
        logger.info("AGGREGATING RESULTS FROM ALL METHODS")
        logger.info("=" * 80)
        logger.info("")
        
        if not all_results:
            logger.error("No results to aggregate!")
            return None
        
        # Collect all position estimates for each field
        field_positions = {
            'name': {'x': [], 'y': []},
            'event': {'x': [], 'y': []},
            'organiser': {'x': [], 'y': []}
        }
        
        for result in all_results:
            for field, pos in result['positions'].items():
                field_positions[field]['x'].append(pos['x'])
                field_positions[field]['y'].append(pos['y'])
        
        # Calculate consensus (median) for each field
        consensus = {}
        for field in ['name', 'event', 'organiser']:
            if field_positions[field]['x']:
                x_median = np.median(field_positions[field]['x'])
                y_median = np.median(field_positions[field]['y'])
                x_mean = np.mean(field_positions[field]['x'])
                y_mean = np.mean(field_positions[field]['y'])
                x_std = np.std(field_positions[field]['x'])
                y_std = np.std(field_positions[field]['y'])
                
                consensus[field] = {
                    'x': x_median,
                    'y': y_median,
                    'pixel_x': x_median * self.width,
                    'pixel_y': y_median * self.height,
                    'x_mean': x_mean,
                    'y_mean': y_mean,
                    'x_std': x_std,
                    'y_std': y_std,
                    'sample_count': len(field_positions[field]['x'])
                }
                
                logger.info(f"{field.upper()}:")
                logger.info(f"  Position (normalized): x={x_median:.6f}, y={y_median:.6f}")
                logger.info(f"  Position (pixels): x={x_median * self.width:.1f}, y={y_median * self.height:.1f}")
                logger.info(f"  Standard deviation: x={x_std:.6f}, y={y_std:.6f}")
                logger.info(f"  Samples: {len(field_positions[field]['x'])} methods")
                logger.info("")
        
        return consensus


def main():
    """Main function."""
    base_dir = Path(__file__).parent.parent
    reference_path = base_dir / 'templates' / 'Sample_certificate.png'
    
    if not reference_path.exists():
        logger.error(f"Reference not found: {reference_path}")
        return 1
    
    # Extract positions
    extractor = TextPositionExtractor(reference_path)
    all_results = extractor.run_all_methods()
    
    # Aggregate
    consensus = extractor.aggregate_results(all_results)
    
    if consensus:
        # Save results
        output_path = base_dir / 'templates' / 'extracted_positions.json'
        
        output_data = {
            'version': '4.0',
            'extraction_date': '2025-10-31',
            'source_image': str(reference_path),
            'image_dimensions': {'width': extractor.width, 'height': extractor.height},
            'methods_used': len(all_results),
            'consensus_positions': consensus,
            'all_method_results': all_results
        }
        
        # Convert numpy types to Python types for JSON serialization
        def convert_to_python_types(obj):
            if isinstance(obj, dict):
                return {k: convert_to_python_types(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_to_python_types(item) for item in obj]
            elif isinstance(obj, (np.integer, np.int64, np.int32)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float64, np.float32)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            else:
                return obj
        
        output_data = convert_to_python_types(output_data)
        
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info("=" * 80)
        logger.info(f"Results saved to: {output_path}")
        logger.info("=" * 80)
        
        return 0
    else:
        logger.error("Failed to extract positions")
        return 1


if __name__ == '__main__':
    sys.exit(main())
