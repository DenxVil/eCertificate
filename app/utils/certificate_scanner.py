"""
Smart Certificate Template Scanner & Auto-Aligner

This module intelligently scans certificate templates (PDF/PNG) uploaded by users,
detects text fields, extracts their properties, and creates perfectly aligned
certificates with accurate sizing and positioning.

Features:
- PDF/PNG template scanning
- OCR field detection using pytesseract
- Position and size extraction
- Font analysis and color detection
- Automatic template creation from scanned certificate
- Precise value alignment and placement
- Smart field matching and replacement
"""

import os
import json
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, asdict, field
from datetime import datetime
import tempfile
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageStat
import pytesseract
from pdf2image import convert_from_path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DetectedField:
    """Represents a detected text field on a certificate."""
    text: str
    x: float  # Normalized position (0-1)
    y: float  # Normalized position (0-1)
    width: float  # Normalized width
    height: float  # Normalized height
    font_size: int  # Estimated font size in points
    color: str  # Hex color
    alignment: str  # "left", "center", "right"
    confidence: float  # 0-1, detection confidence
    field_type: str  # "placeholder" or "static"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class TemplateAnalysis:
    """Analysis result of a scanned certificate template."""
    width: int  # Template width in pixels
    height: int  # Template height in pixels
    dpi: int  # Detected DPI
    detected_fields: List[DetectedField] = field(default_factory=list)
    background_color: str = "#FFFFFF"
    text_regions: List[Dict] = field(default_factory=list)
    confidence_score: float = 0.0  # Overall detection confidence
    scan_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        data = asdict(self)
        data['detected_fields'] = [f.to_dict() for f in self.detected_fields]
        return data


class CertificateScanner:
    """
    Scans and analyzes certificate templates to extract structure and positioning.
    """
    
    # Common field placeholders to detect
    COMMON_PLACEHOLDERS = {
        'name': ['name', 'participant', 'recipient', 'attendee'],
        'event': ['event', 'course', 'program', 'training'],
        'date': ['date', 'awarded', 'issued', 'completion'],
        'organization': ['organization', 'institution', 'presented by', 'organization'],
    }
    
    def __init__(self, dpi: int = 300, ocr_lang: str = 'eng'):
        """
        Initialize the certificate scanner.
        
        Args:
            dpi: DPI for image processing (affects accuracy)
            ocr_lang: OCR language (default: English)
        """
        self.dpi = dpi
        self.ocr_lang = ocr_lang
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Verify required dependencies are installed."""
        try:
            pytesseract.get_tesseract_version()
        except pytesseract.TesseractNotFoundError:
            logger.warning("Tesseract OCR not found. Some features may be limited.")
    
    def scan_certificate(self, certificate_path: str) -> TemplateAnalysis:
        """
        Scan a certificate template (PDF or image) and analyze its structure.
        
        Args:
            certificate_path: Path to certificate template (PDF/PNG/JPG)
        
        Returns:
            TemplateAnalysis with detected fields and metadata
        """
        logger.info(f"Scanning certificate: {certificate_path}")
        
        # Convert to image if PDF
        if certificate_path.lower().endswith('.pdf'):
            image = self._pdf_to_image(certificate_path)
        else:
            image = Image.open(certificate_path)
        
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Get basic info
        width, height = image.size
        
        # Detect text fields
        detected_fields = self._detect_fields(image)
        
        # Detect background color
        bg_color = self._detect_background_color(image)
        
        # Calculate overall confidence
        confidence = self._calculate_confidence(detected_fields)
        
        # Create analysis result
        analysis = TemplateAnalysis(
            width=width,
            height=height,
            dpi=self.dpi,
            detected_fields=detected_fields,
            background_color=bg_color,
            confidence_score=confidence
        )
        
        logger.info(f"Detected {len(detected_fields)} text fields with {confidence:.1%} confidence")
        
        return analysis
    
    def _pdf_to_image(self, pdf_path: str, page: int = 0) -> Image.Image:
        """Convert PDF page to PIL Image."""
        logger.info(f"Converting PDF page {page} to image")
        images = convert_from_path(pdf_path, dpi=self.dpi, first_page=page+1, last_page=page+1)
        return images[0] if images else Image.new('RGB', (800, 600))
    
    def _detect_fields(self, image: Image.Image) -> List[DetectedField]:
        """
        Detect text fields in the certificate image using OCR and image analysis.
        """
        fields = []
        
        # Use Tesseract OCR to detect text regions
        try:
            # Get detailed OCR results
            data = pytesseract.image_to_data(image, lang=self.ocr_lang, output_type=pytesseract.Output.DICT)
            
            # Process detected text regions
            width, height = image.size
            
            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                confidence = int(data['conf'][i]) / 100.0
                
                # Skip empty text or low confidence detections
                if not text or confidence < 0.3:
                    continue
                
                # Extract position and size
                left = data['left'][i]
                top = data['top'][i]
                w = data['width'][i]
                h = data['height'][i]
                
                # Normalize coordinates (0-1)
                x_norm = (left + w/2) / width
                y_norm = (top + h/2) / height
                w_norm = w / width
                h_norm = h / height
                
                # Estimate font size (rough approximation)
                font_size = max(8, int(h * 0.5))
                
                # Detect text color
                text_color = self._detect_text_color(image, left, top, w, h)
                
                # Determine alignment (simple heuristic)
                alignment = self._determine_alignment(image, left, w, width)
                
                # Determine field type (placeholder or static)
                field_type = self._classify_field_type(text)
                
                # Create detected field
                field = DetectedField(
                    text=text,
                    x=x_norm,
                    y=y_norm,
                    width=w_norm,
                    height=h_norm,
                    font_size=font_size,
                    color=text_color,
                    alignment=alignment,
                    confidence=confidence,
                    field_type=field_type
                )
                
                fields.append(field)
                logger.debug(f"Detected field: '{text}' at ({x_norm:.2f}, {y_norm:.2f})")
        
        except Exception as e:
            logger.error(f"OCR detection error: {e}")
        
        # Deduplicate and sort fields
        fields = self._deduplicate_fields(fields)
        fields.sort(key=lambda f: (f.y, f.x))
        
        return fields
    
    def _detect_text_color(self, image: Image.Image, x: int, y: int, w: int, h: int) -> str:
        """Detect the dominant color of text in a region."""
        try:
            # Crop region around text
            region = image.crop((max(0, x-5), max(0, y-5), 
                               min(image.width, x+w+5), min(image.height, y+h+5)))
            
            # Get dominant color
            colors = region.getcolors(maxcolors=region.width * region.height)
            if colors:
                dominant_color = max(colors, key=lambda x: x[0])[1]
                return self._rgb_to_hex(dominant_color)
        except Exception as e:
            logger.debug(f"Color detection error: {e}")
        
        return "#000000"  # Default to black
    
    def _determine_alignment(self, image: Image.Image, left: int, width: int, img_width: int) -> str:
        """Determine text alignment based on position."""
        center_x = left + width / 2
        image_center = img_width / 2
        
        tolerance = img_width * 0.05  # 5% tolerance
        
        if abs(center_x - image_center) < tolerance:
            return "center"
        elif center_x < image_center - tolerance:
            return "left"
        else:
            return "right"
    
    def _classify_field_type(self, text: str) -> str:
        """Classify if field is a placeholder or static text."""
        text_lower = text.lower()
        
        # Check against common placeholders
        for field_type, keywords in self.COMMON_PLACEHOLDERS.items():
            if any(keyword in text_lower for keyword in keywords):
                return "placeholder"
        
        # If text matches common certificate keywords, it's static
        static_keywords = ['certificate', 'achievement', 'recognized', 'completed', 
                          'hereby', 'awarded', 'successfully']
        if any(keyword in text_lower for keyword in static_keywords):
            return "static"
        
        # If very short and centered, likely a placeholder
        if len(text) <= 20:
            return "placeholder"
        
        return "static"
    
    def _deduplicate_fields(self, fields: List[DetectedField]) -> List[DetectedField]:
        """Remove duplicate or very close fields."""
        if not fields:
            return fields
        
        deduplicated = []
        for field in fields:
            # Check if similar field already exists
            is_duplicate = False
            for existing in deduplicated:
                # If position is very close, it's a duplicate
                if (abs(field.x - existing.x) < 0.05 and 
                    abs(field.y - existing.y) < 0.05):
                    # Keep field with higher confidence
                    if field.confidence > existing.confidence:
                        deduplicated.remove(existing)
                    else:
                        is_duplicate = True
                    break
            
            if not is_duplicate:
                deduplicated.append(field)
        
        return deduplicated
    
    def _detect_background_color(self, image: Image.Image) -> str:
        """Detect the background/dominant color of the certificate."""
        try:
            # Resize for faster processing
            small = image.resize((150, 150))
            # Get all colors
            colors = small.getcolors(maxcolors=150*150)
            if colors:
                # Find most common color (likely background)
                bg_color = max(colors, key=lambda x: x[0])[1]
                return self._rgb_to_hex(bg_color)
        except Exception as e:
            logger.debug(f"Background color detection error: {e}")
        
        return "#FFFFFF"  # Default to white
    
    def _calculate_confidence(self, fields: List[DetectedField]) -> float:
        """Calculate overall detection confidence."""
        if not fields:
            return 0.0
        
        avg_confidence = sum(f.confidence for f in fields) / len(fields)
        
        # Bonus if we detected multiple fields
        field_bonus = min(0.1, len(fields) * 0.02)
        
        return min(1.0, avg_confidence + field_bonus)
    
    @staticmethod
    def _rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
        """Convert RGB tuple to hex color string."""
        if isinstance(rgb, int):  # Grayscale
            return f"#{rgb:02x}{rgb:02x}{rgb:02x}"
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


class SmartCertificateAligner:
    """
    Aligns and places values on certificates with precise positioning and sizing.
    Uses scanned template information for accurate placement.
    """
    
    def __init__(self, template_analysis: TemplateAnalysis):
        """
        Initialize the aligner with template analysis.
        
        Args:
            template_analysis: TemplateAnalysis from CertificateScanner
        """
        self.analysis = template_analysis
        self.field_mapping = {}
    
    def map_fields(self, fields_data: Dict[str, str]) -> Dict[str, DetectedField]:
        """
        Map user-provided field values to detected template fields.
        
        Args:
            fields_data: User field values (e.g., {'participant_name': 'John Doe'})
        
        Returns:
            Mapping of detected fields to values
        """
        mapping = {}
        
        for field in self.analysis.detected_fields:
            # Try to match field to user data
            best_match = self._find_best_match(field.text, fields_data)
            if best_match:
                mapping[field.text] = best_match
        
        self.field_mapping = mapping
        return mapping
    
    def _find_best_match(self, detected_text: str, user_fields: Dict[str, str]) -> Optional[str]:
        """Find the best matching user field for a detected text."""
        detected_lower = detected_text.lower()
        
        for key, value in user_fields.items():
            key_lower = key.lower()
            
            # Exact match
            if key_lower == detected_lower:
                return value
            
            # Partial match
            if key_lower in detected_lower or detected_lower in key_lower:
                return value
        
        return None
    
    def generate_aligned_certificate(
        self,
        template_image_path: str,
        fields_data: Dict[str, str],
        output_path: str
    ) -> str:
        """
        Generate certificate with precisely aligned values on template.
        
        Args:
            template_image_path: Path to certificate template image
            fields_data: Field values to place
            output_path: Path to save generated certificate
        
        Returns:
            Path to generated certificate
        """
        # Load template image
        image = Image.open(template_image_path).convert('RGB')
        draw = ImageDraw.Draw(image)
        
        # Map fields
        mapping = self.map_fields(fields_data)
        
        # Draw replacements
        for field in self.analysis.detected_fields:
            if field.text in mapping:
                replacement_text = mapping[field.text]
                self._draw_field(
                    draw,
                    replacement_text,
                    field,
                    image.size
                )
        
        # Save
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        image.save(output_path, 'PNG')
        logger.info(f"Generated aligned certificate: {output_path}")
        
        return output_path
    
    def _draw_field(
        self,
        draw: ImageDraw.ImageDraw,
        text: str,
        field: DetectedField,
        image_size: Tuple[int, int]
    ):
        """Draw text field with precise alignment and sizing."""
        width, height = image_size
        
        # Calculate pixel coordinates
        x = field.x * width
        y = field.y * height
        
        # Load font with detected size
        try:
            font = ImageFont.truetype("arial.ttf", field.font_size)
        except:
            font = ImageFont.load_default()
        
        # Get text color
        try:
            color = int(field.color.lstrip('#'), 16)
            color = tuple(int(field.color[i:i+2], 16) for i in (1, 3, 5))
        except:
            color = (0, 0, 0)
        
        # Apply alignment
        if field.alignment == "center":
            draw.text((x, y), text, font=font, fill=color, anchor="mm")
        elif field.alignment == "right":
            draw.text((x, y), text, font=font, fill=color, anchor="rm")
        else:  # left
            draw.text((x, y), text, font=font, fill=color, anchor="lm")


class TemplateCreator:
    """
    Creates a reusable certificate template configuration from scanned analysis.
    """
    
    @staticmethod
    def create_template_from_scan(analysis: TemplateAnalysis, template_name: str) -> Dict:
        """
        Create a template configuration from scanner analysis.
        
        Args:
            analysis: TemplateAnalysis from CertificateScanner
            template_name: Name for the template
        
        Returns:
            Dictionary template configuration
        """
        # Convert detected fields to template elements
        elements = []
        
        for field in analysis.detected_fields:
            element = {
                "text": f"{{{{{field.text}}}}}",  # Use detected text as placeholder
                "x": field.x,
                "y": field.y,
                "font_name": "Helvetica",
                "font_size": field.font_size,
                "color": field.color,
                "alignment": field.alignment,
                "bold": False,
                "confidence": field.confidence,
            }
            elements.append(element)
        
        template = {
            "name": template_name,
            "description": f"Auto-generated from scanned certificate ({datetime.now().strftime('%Y-%m-%d')})",
            "width": analysis.width / 96,  # Convert pixels to inches (96 DPI)
            "height": analysis.height / 96,
            "background_color": analysis.background_color,
            "elements": elements,
            "detection_confidence": analysis.confidence_score,
            "scan_timestamp": analysis.scan_timestamp,
        }
        
        return template
    
    @staticmethod
    def save_template_to_file(template: Dict, filepath: str):
        """Save template configuration to JSON file."""
        os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(template, f, indent=2)
        logger.info(f"Template saved to: {filepath}")


# Example usage function
def example_workflow():
    """
    Example workflow: scan certificate, create template, generate aligned certificates.
    """
    # 1. Scan certificate template
    scanner = CertificateScanner(dpi=300)
    analysis = scanner.scan_certificate('path/to/certificate_template.png')
    
    print(f"Scanned certificate: {analysis.width}x{analysis.height}px")
    print(f"Detected {len(analysis.detected_fields)} fields")
    print(f"Confidence: {analysis.confidence_score:.1%}")
    
    for field in analysis.detected_fields:
        print(f"  - '{field.text}' at ({field.x:.2f}, {field.y:.2f}), size: {field.font_size}")
    
    # 2. Create template configuration
    creator = TemplateCreator()
    template_config = creator.create_template_from_scan(analysis, "My Certificate")
    creator.save_template_to_file(template_config, 'templates/auto_generated.json')
    
    # 3. Generate aligned certificates
    aligner = SmartCertificateAligner(analysis)
    
    fields_data = {
        'name': 'John Doe',
        'event': 'Python Summit 2025',
        'date': '2025-10-29',
    }
    
    cert_path = aligner.generate_aligned_certificate(
        'path/to/certificate_template.png',
        fields_data,
        'generated_certificates/john_doe_aligned.png'
    )
    
    print(f"Generated: {cert_path}")


if __name__ == '__main__':
    # Quick test
    print("Smart Certificate Scanner & Aligner module loaded")
    print("Use CertificateScanner to scan templates")
    print("Use SmartCertificateAligner to align values")
    print("Use TemplateCreator to generate template configs")
