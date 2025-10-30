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
        
        # Define bounding boxes for GOONJ certificate (2000x1414 template)
        # These positions are optimized for the GOONJ template layout
        self.name_bbox = {
            'x': width // 2,
            'y': int(height * 0.48),  # Approximately 48% down
            'font_size': 80,
            'color': '#1a5490'
        }
        
        self.event_bbox = {
            'x': width // 2,
            'y': int(height * 0.60),  # Approximately 60% down
            'font_size': 50,
            'color': '#333333'
        }
        
        self.date_bbox = {
            'x': width // 2,
            'y': int(height * 0.75),  # Approximately 75% down
            'font_size': 35,
            'color': '#555555'
        }
        
        self.email_bbox = {
            'x': width // 2,
            'y': int(height * 0.85),  # Approximately 85% down
            'font_size': 25,
            'color': '#777777'
        }
        
        self._load_fonts()
    
    def _load_fonts(self):
        """Load fonts for text rendering."""
        try:
            # Try to load Arial/Helvetica fonts
            self.name_font = ImageFont.truetype("arial.ttf", self.name_bbox['font_size'])
            self.event_font = ImageFont.truetype("arial.ttf", self.event_bbox['font_size'])
            self.date_font = ImageFont.truetype("arial.ttf", self.date_bbox['font_size'])
            self.email_font = ImageFont.truetype("arial.ttf", self.email_bbox['font_size'])
        except (OSError, IOError):
            try:
                # Try alternative font names
                self.name_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 
                                                   self.name_bbox['font_size'])
                self.event_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 
                                                     self.event_bbox['font_size'])
                self.date_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 
                                                   self.date_bbox['font_size'])
                self.email_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 
                                                    self.email_bbox['font_size'])
            except (OSError, IOError):
                # Fallback to default font
                logger.warning("Could not load TrueType fonts, using default font")
                self.name_font = ImageFont.load_default()
                self.event_font = ImageFont.load_default()
                self.date_font = ImageFont.load_default()
                self.email_font = ImageFont.load_default()
    
    def _hex_to_rgb(self, hex_color):
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def render(self, participant_data, output_format='png'):
        """Render a certificate for a single participant.
        
        Args:
            participant_data: Dictionary with participant information
                Required: 'name'
                Optional: 'event', 'date', 'email', 'certificate_id'
            output_format: Output format ('png' or 'pdf')
        
        Returns:
            Path to the generated certificate file
        """
        # Create a copy of the template
        cert_image = self.template.copy()
        draw = ImageDraw.Draw(cert_image)
        
        # Extract participant data
        name = participant_data.get('name', 'Participant')
        event = participant_data.get('event', 'GOONJ Event')
        date_str = participant_data.get('date', datetime.now().strftime("%B %d, %Y"))
        email = participant_data.get('email', '')
        cert_id = participant_data.get('certificate_id', '')
        
        # Draw participant name
        name_color = self._hex_to_rgb(self.name_bbox['color'])
        self._draw_centered_text(
            draw, 
            name.upper(), 
            self.name_bbox['x'], 
            self.name_bbox['y'],
            self.name_font,
            name_color
        )
        
        # Draw event name
        event_color = self._hex_to_rgb(self.event_bbox['color'])
        self._draw_centered_text(
            draw,
            event,
            self.event_bbox['x'],
            self.event_bbox['y'],
            self.event_font,
            event_color
        )
        
        # Draw date
        date_color = self._hex_to_rgb(self.date_bbox['color'])
        self._draw_centered_text(
            draw,
            f"Date: {date_str}",
            self.date_bbox['x'],
            self.date_bbox['y'],
            self.date_font,
            date_color
        )
        
        # Draw email if provided
        if email:
            email_color = self._hex_to_rgb(self.email_bbox['color'])
            self._draw_centered_text(
                draw,
                email,
                self.email_bbox['x'],
                self.email_bbox['y'],
                self.email_font,
                email_color
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
