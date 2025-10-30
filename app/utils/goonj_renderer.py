"""GOONJ Certificate Renderer - Renders participant data on GOONJ template."""
import os
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class GOONJRenderer:
    """Render GOONJ certificates with participant information."""
    
    def __init__(self, template_path, output_folder='generated_certificates'):
        """Initialize the GOONJ renderer.
        
        Args:
            template_path: Path to the GOONJ certificate template image
            output_folder: Folder to save generated certificates
        """
        self.template_path = template_path
        self.output_folder = output_folder
        
        # Create output folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)
        
        # Load template
        if not os.path.exists(template_path):
            raise FileNotFoundError(f"GOONJ template not found at: {template_path}")
        
        self.template = Image.open(template_path).convert("RGB")
        width, height = self.template.size
        
        # Store dimensions
        self.width = width
        self.height = height
        
        # Define bounding boxes for GOONJ certificate (supports three fields only)
        # Positions as percentage of template height for vertical placement
        # NAME at ~33% (32-35%), EVENT at ~42% (41-43%), ORGANISED BY at ~51% (49-52%)
        self.name_bbox = {
            'x': width // 2,
            'y': int(height * 0.33),  # 33% down
            'base_font_size': int(height * 0.05),  # ~5% of height
            'color': '#000000'  # Pure black
        }
        
        self.event_bbox = {
            'x': width // 2,
            'y': int(height * 0.42),  # 42% down
            'base_font_size': int(height * 0.042),  # ~4.2% of height
            'color': '#000000'  # Pure black
        }
        
        self.organiser_bbox = {
            'x': width // 2,
            'y': int(height * 0.51),  # 51% down
            'base_font_size': int(height * 0.042),  # ~4.2% of height
            'color': '#000000'  # Pure black
        }
        
        # Max width for text (80-85% of image width)
        self.max_text_width = int(width * 0.825)  # 82.5% of width
        
        self._load_fonts()
    
    def _load_fonts(self):
        """Load bold sans-serif fonts for text rendering.
        
        Attempts to load Arial Black or arialbd.ttf, falls back to DejaVuSans-Bold.
        """
        # Font paths to try (bold sans-serif)
        font_paths = [
            "arialbd.ttf",  # Arial Bold
            "/usr/share/fonts/truetype/msttcorefonts/arialbd.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",  # macOS
        ]
        
        self.font_path = None
        for path in font_paths:
            try:
                # Test if font can be loaded
                ImageFont.truetype(path, 20)
                self.font_path = path
                logger.info(f"Using font: {path}")
                break
            except (OSError, IOError):
                continue
        
        if not self.font_path:
            logger.warning("Could not load bold TrueType fonts, using default font")
            self.font_path = None  # Will use default
    
    def _hex_to_rgb(self, hex_color):
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _get_font(self, size):
        """Get a font at the specified size."""
        if self.font_path:
            try:
                return ImageFont.truetype(self.font_path, size)
            except (OSError, IOError):
                pass
        return ImageFont.load_default()
    
    def _fit_text_to_width(self, draw, text, base_font_size, max_width):
        """Scale down text to fit within max_width.
        
        Args:
            draw: ImageDraw object
            text: Text to fit
            base_font_size: Starting font size
            max_width: Maximum width in pixels
            
        Returns:
            Font object that fits the text within max_width
        """
        font_size = base_font_size
        font = self._get_font(font_size)
        
        # Get text width
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        
        # Scale down if needed
        while text_width > max_width and font_size > 10:
            font_size -= 1
            font = self._get_font(font_size)
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
        
        return font
    
    def render(self, participant_data, output_format='png'):
        """Render a certificate for a single participant.
        
        Args:
            participant_data: Dictionary with participant information
                Required: 'name'
                Optional: 'event', 'organiser' (or 'organizer')
            output_format: Output format ('png' or 'pdf')
        
        Returns:
            Path to the generated certificate file
        """
        # Create a copy of the template
        cert_image = self.template.copy()
        draw = ImageDraw.Draw(cert_image)
        
        # Extract participant data (only three fields supported)
        name = participant_data.get('name', 'Participant')
        event = participant_data.get('event', 'GOONJ')
        # Accept both British and American spellings
        organiser = participant_data.get('organiser') or participant_data.get('organizer', 'AMA')
        
        # Uppercase all fields as per specification
        name_upper = name.upper()
        event_upper = event.upper()
        organiser_upper = organiser.upper()
        
        # Color is pure black for all fields
        text_color = self._hex_to_rgb(self.name_bbox['color'])
        
        # Draw participant name (centered, ~33% down)
        name_font = self._fit_text_to_width(
            draw, 
            name_upper, 
            self.name_bbox['base_font_size'],
            self.max_text_width
        )
        self._draw_centered_text(
            draw, 
            name_upper, 
            self.name_bbox['x'], 
            self.name_bbox['y'],
            name_font,
            text_color
        )
        
        # Draw event name (centered, ~42% down)
        event_font = self._fit_text_to_width(
            draw,
            event_upper,
            self.event_bbox['base_font_size'],
            self.max_text_width
        )
        self._draw_centered_text(
            draw,
            event_upper,
            self.event_bbox['x'],
            self.event_bbox['y'],
            event_font,
            text_color
        )
        
        # Draw organiser (centered, ~51% down)
        organiser_font = self._fit_text_to_width(
            draw,
            organiser_upper,
            self.organiser_bbox['base_font_size'],
            self.max_text_width
        )
        self._draw_centered_text(
            draw,
            organiser_upper,
            self.organiser_bbox['x'],
            self.organiser_bbox['y'],
            organiser_font,
            text_color
        )
        
        # Generate filename
        safe_name = "".join(c if c.isalnum() or c in (' ', '-', '_') else '_' for c in name)
        safe_name = safe_name.replace(' ', '_')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"goonj_cert_{safe_name}_{timestamp}.{output_format}"
        output_path = os.path.join(self.output_folder, filename)
        
        # Save the certificate
        if output_format.lower() == 'pdf':
            # Convert to PDF
            cert_image_rgb = cert_image.convert('RGB')
            cert_image_rgb.save(output_path, 'PDF', resolution=100.0)
        else:
            # Save as PNG
            cert_image.save(output_path, 'PNG')
        
        logger.info(f"Generated GOONJ certificate: {output_path}")
        return output_path
    
    def _draw_centered_text(self, draw, text, x, y, font, color):
        """Draw text centered at the given position."""
        # Get text bounding box
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Calculate position to center the text
        position = (x - text_width // 2, y - text_height // 2)
        
        # Draw the text
        draw.text(position, text, font=font, fill=color)
