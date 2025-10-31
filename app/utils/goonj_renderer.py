"""GOONJ Certificate Renderer - Renders participant data on GOONJ template."""
import os
import json
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import logging
from .text_align import draw_text_centered, get_font

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
        
        # Load field offsets from JSON if available
        self._load_field_offsets()
        
        # Define bounding boxes for GOONJ certificate (supports three fields only)
        # Positions as percentage of template height for vertical placement
        # NAME at ~33% (32-35%), EVENT at ~42% (41-43%), ORGANISED BY at ~51% (49-52%)
        self.name_bbox = {
            'x': width // 2,
            'y': int(height * self.field_offsets['name']['y']),
            'base_font_size': int(height * 0.05),  # ~5% of height
            'color': '#000000',  # Pure black
            'baseline_offset': self.field_offsets['name'].get('baseline_offset', 0)
        }
        
        self.event_bbox = {
            'x': width // 2,
            'y': int(height * self.field_offsets['event']['y']),
            'base_font_size': int(height * 0.042),  # ~4.2% of height
            'color': '#000000',  # Pure black
            'baseline_offset': self.field_offsets['event'].get('baseline_offset', 0)
        }
        
        self.organiser_bbox = {
            'x': width // 2,
            'y': int(height * self.field_offsets['organiser']['y']),
            'base_font_size': int(height * 0.042),  # ~4.2% of height
            'color': '#000000',  # Pure black
            'baseline_offset': self.field_offsets['organiser'].get('baseline_offset', 0)
        }
        
        # Max width for text (80-85% of image width)
        self.max_text_width = int(width * 0.825)  # 82.5% of width
        
        self._load_fonts()
    
    def _load_field_offsets(self):
        """Load field position offsets from JSON configuration.
        
        Reads templates/goonj_template_offsets.json for normalized field positions
        and baseline offsets. Falls back to default positions if file not found.
        """
        # Default offsets
        self.field_offsets = {
            'name': {'x': 0.5, 'y': 0.33, 'baseline_offset': 0},
            'event': {'x': 0.5, 'y': 0.42, 'baseline_offset': 0},
            'organiser': {'x': 0.5, 'y': 0.51, 'baseline_offset': 0}
        }
        
        # Try to load from JSON file
        template_dir = os.path.dirname(self.template_path)
        offsets_path = os.path.join(template_dir, 'goonj_template_offsets.json')
        
        if os.path.exists(offsets_path):
            try:
                with open(offsets_path, 'r') as f:
                    data = json.load(f)
                    if 'fields' in data:
                        # Update offsets with values from JSON
                        for field in ['name', 'event', 'organiser']:
                            if field in data['fields']:
                                self.field_offsets[field].update(data['fields'][field])
                        logger.info(f"Loaded field offsets from {offsets_path}")
            except Exception as e:
                logger.warning(f"Could not load field offsets from {offsets_path}: {e}, using defaults")
        else:
            logger.debug(f"Offsets file not found at {offsets_path}, using default positions")
    
    def _load_fonts(self):
        """Load the bundled ARIALBD.TTF font for text rendering.
        
        Uses the bundled font file at templates/ARIALBD.TTF exclusively.
        Does not check for or use system fonts.
        """
        # Use bundled font file
        template_dir = os.path.dirname(self.template_path)
        bundled_font_path = os.path.join(template_dir, 'ARIALBD.TTF')
        
        if not os.path.exists(bundled_font_path):
            raise FileNotFoundError(
                f"Required font file not found at: {bundled_font_path}. "
                "Please ensure templates/ARIALBD.TTF is present."
            )
        
        self.font_path = bundled_font_path
        logger.info(f"Using bundled font: {bundled_font_path}")
    
    def _hex_to_rgb(self, hex_color):
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    def _get_font(self, size):
        """Get a font at the specified size using the shared helper."""
        return get_font(self.font_path, size)
    
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
            text_color,
            baseline_offset=self.name_bbox['baseline_offset']
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
            text_color,
            baseline_offset=self.event_bbox['baseline_offset']
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
            text_color,
            baseline_offset=self.organiser_bbox['baseline_offset']
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
    
    def _draw_centered_text(self, draw, text, x, y, font, color, baseline_offset=0):
        """Draw text centered at the given position using shared alignment helper.
        
        Uses draw_text_centered from text_align module for consistent alignment.
        """
        draw_text_centered(
            draw, 
            (x, y), 
            text, 
            font, 
            color, 
            align="center",
            baseline_offset=baseline_offset
        )
