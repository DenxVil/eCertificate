"""Certificate generator utility using Pillow."""
import os
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime


class CertificateGenerator:
    """Generate certificates by placing text on templates."""
    
    def __init__(self, template_path, output_folder='generated_certificates'):
        """Initialize the certificate generator.
        
        Args:
            template_path: Path to the certificate template image
            output_folder: Folder to save generated certificates
        """
        self.template_path = template_path
        self.output_folder = output_folder
        
        # Create output folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)
        
        # Load template
        self.template = Image.open(template_path)
        
        # Default positions (can be customized)
        self.name_position = (self.template.width // 2, self.template.height // 2 - 50)
        self.event_position = (self.template.width // 2, self.template.height // 2 + 50)
        self.date_position = (self.template.width // 2, self.template.height - 150)
        
        # Font settings (try to use a good font, fallback to default)
        self.name_font_size = 60
        self.event_font_size = 40
        self.date_font_size = 30
        
        self._load_fonts()
    
    def _load_fonts(self):
        """Load fonts for text rendering."""
        try:
            # Try to load a nice font
            self.name_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", 
                                                self.name_font_size)
            self.event_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf", 
                                                 self.event_font_size)
            self.date_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf", 
                                                self.date_font_size)
        except OSError:
            # Fallback to default font
            self.name_font = ImageFont.load_default()
            self.event_font = ImageFont.load_default()
            self.date_font = ImageFont.load_default()
    
    def generate_certificate(self, participant_name, event_name=None, output_filename=None):
        """Generate a certificate for a participant.
        
        Args:
            participant_name: Name of the participant
            event_name: Name of the event (optional)
            output_filename: Custom output filename (optional)
            
        Returns:
            Path to the generated certificate
        """
        # Create a copy of the template
        certificate = self.template.copy()
        draw = ImageDraw.Draw(certificate)
        
        # Draw participant name
        self._draw_centered_text(draw, participant_name, self.name_position, 
                                self.name_font, fill='black')
        
        # Draw event name if provided
        if event_name:
            self._draw_centered_text(draw, event_name, self.event_position, 
                                    self.event_font, fill='black')
        
        # Draw date
        date_str = datetime.now().strftime("%B %d, %Y")
        self._draw_centered_text(draw, date_str, self.date_position, 
                                self.date_font, fill='black')
        
        # Save certificate
        if output_filename is None:
            # Sanitize participant name for filename
            safe_name = "".join(c for c in participant_name if c.isalnum() or c in (' ', '-', '_')).strip()
            output_filename = f"{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        output_path = os.path.join(self.output_folder, output_filename)
        certificate.save(output_path, 'PNG')
        
        return output_path
    
    def _draw_centered_text(self, draw, text, position, font, fill='black'):
        """Draw text centered at the given position.
        
        Args:
            draw: ImageDraw object
            text: Text to draw
            position: (x, y) tuple for center position
            font: Font to use
            fill: Text color
        """
        # Get text bounding box
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Calculate position to center the text
        x = position[0] - text_width // 2
        y = position[1] - text_height // 2
        
        # Draw the text
        draw.text((x, y), text, font=font, fill=fill)
    
    def set_positions(self, name_pos=None, event_pos=None, date_pos=None):
        """Set custom positions for text fields.
        
        Args:
            name_pos: (x, y) tuple for name position
            event_pos: (x, y) tuple for event position
            date_pos: (x, y) tuple for date position
        """
        if name_pos:
            self.name_position = name_pos
        if event_pos:
            self.event_position = event_pos
        if date_pos:
            self.date_position = date_pos
