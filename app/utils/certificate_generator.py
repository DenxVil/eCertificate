"""Certificate generator utility using Pillow."""
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from datetime import datetime
# & .\.venv\Scripts\Activate.ps1; python app.py

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
        self.template = Image.open(template_path).convert("RGBA")
        
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
            self.name_font = ImageFont.truetype("arial.ttf", self.name_font_size)
            self.event_font = ImageFont.truetype("arial.ttf", self.event_font_size)
            self.date_font = ImageFont.truetype("arial.ttf", self.date_font_size)
        except OSError:
            # Fallback to default font
            self.name_font = ImageFont.load_default()
            self.event_font = ImageFont.load_default()
            self.date_font = ImageFont.load_default()

    def _get_font(self, font_name, size):
        """Load a font, falling back to default if not found."""
        try:
            return ImageFont.truetype(font_name, size)
        except OSError:
            return ImageFont.load_default()

    def _get_text_color(self, image, region):
        """Analyze a region of the image to determine a contrasting text color."""
        try:
            box = image.crop(region)
            # Convert to grayscale and get average brightness
            avg_brightness = box.convert("L").resize((1, 1)).getpixel((0, 0))
            return "black" if avg_brightness > 128 else "white"
        except Exception:
            return "black"  # Default to black on error

    def generate(self, fields, output_filename=None):
        """
        Generate a certificate with dynamically placed and styled text.

        Args:
            fields (list): A list of dictionaries, each representing a text field.
                           Each dict should have: 'text', 'x', 'y', 'font_name', 'font_size', 'align'.
            output_filename (str, optional): Custom output filename.

        Returns:
            str: Path to the generated certificate.
        """
        certificate = self.template.copy()
        draw = ImageDraw.Draw(certificate)

        for field in fields:
            font = self._get_font(field.get("font_name", "arial.ttf"), field["font_size"])
            
            # Define a small region around the text to determine color
            w, h = self.template.size
            x, y = int(field["x"] * w), int(field["y"] * h)
            region_size = field["font_size"] * 2
            region = (x - region_size//2, y - region_size//2, x + region_size//2, y + region_size//2)
            
            fill = self._get_text_color(self.template, region)

            self._draw_text(
                draw,
                field["text"],
                (x, y),
                font,
                fill=fill,
                align=field.get("align", "center")
            )

        if output_filename is None:
            safe_name = "".join(c for c in fields[0].get('text', 'cert') if c.isalnum()).strip()
            output_filename = f"{safe_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"

        output_path = os.path.join(self.output_folder, output_filename)
        certificate.save(output_path, 'PNG')
        return output_path

    def _draw_text(self, draw, text, position, font, fill, align="center"):
        """Draw text with specified alignment."""
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x, y = position
        if align == "center":
            x -= text_width / 2
        elif align == "right":
            x -= text_width

        draw.text((x, y - text_height / 2), text, font=font, fill=fill)
    
    def generate_certificate(self, participant_name, event_name=None, output_filename=None):
        """Generate a certificate using a default layout with the advanced generator.
        
        Args:
            participant_name: Name of the participant
            event_name: Name of the event (optional)
            output_filename: Custom output filename (optional)
            
        Returns:
            Path to the generated certificate
        """
        # Define a default, well-aligned layout using the advanced 'generate' method
        fields = [
            {
                "text": participant_name,
                "x": 0.5, "y": 0.45,
                "font_name": "arial.ttf", "font_size": 60, "align": "center"
            },
            {
                "text": "For successfully participating in",
                "x": 0.5, "y": 0.58,
                "font_name": "arial.ttf", "font_size": 30, "align": "center"
            }
        ]
        if event_name:
            fields.append({
                "text": event_name,
                "x": 0.5, "y": 0.65,
                "font_name": "arial.ttf", "font_size": 45, "align": "center"
            })
        
        fields.append({
            "text": datetime.now().strftime("%B %d, %Y"),
            "x": 0.5, "y": 0.8,
            "font_name": "arial.ttf", "font_size": 25, "align": "center"
        })

        # Call the advanced generator with the predefined layout
        return self.generate(fields, output_filename=output_filename)

    def _draw_centered_text(self, draw, text, position, font, fill):
        """
        DEPRECATED: This method is no longer used. Text is drawn via _draw_text.
        All calls now go through the `generate` method which uses a more precise
        drawing implementation.
        """
        pass
        
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
