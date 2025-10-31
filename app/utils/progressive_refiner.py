"""
Progressive refinement for certificate alignment.

Instead of random regeneration, this module uses intelligent position adjustment
to progressively refine alignment and converge faster to the target.
"""
import logging
from typing import Dict, Any, Tuple, Optional, Callable

logger = logging.getLogger(__name__)


class ProgressiveRefiner:
    """
    Progressive alignment refiner that adjusts positions based on measured differences.
    """
    
    def __init__(self, tolerance_px: float = 0.02):
        """
        Initialize progressive refiner.
        
        Args:
            tolerance_px: Target tolerance in pixels
        """
        self.tolerance_px = tolerance_px
        self.adjustment_history = []
    
    def calculate_adjustment(
        self,
        field_differences: Dict[str, Dict[str, float]],
        attempt_number: int
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate position adjustments based on measured differences.
        
        Args:
            field_differences: Dictionary with field differences from verify_alignment
            attempt_number: Current attempt number
            
        Returns:
            Dictionary with suggested adjustments for each field:
            {
                'name': {'y_adjust': float, 'x_adjust': float},
                'event': {'y_adjust': float, 'x_adjust': float},
                'organiser': {'y_adjust': float, 'x_adjust': float}
            }
        """
        adjustments = {}
        
        # Use adaptive step size: larger steps early, smaller steps later
        step_factor = max(0.5, 1.0 / (1.0 + attempt_number * 0.1))
        
        for field_name in ['name', 'event', 'organiser']:
            if field_name not in field_differences:
                continue
            
            field_diff = field_differences[field_name]
            
            # Skip if field has error (not detected)
            if 'error' in field_diff:
                adjustments[field_name] = {'y_adjust': 0, 'x_adjust': 0}
                continue
            
            # Calculate adjustment based on difference
            # If gen > ref, we need to move UP (negative adjustment)
            # If gen < ref, we need to move DOWN (positive adjustment)
            y_diff = field_diff.get('y_diff', 0)
            x_diff = field_diff.get('x_diff', 0)
            
            # Determine direction
            y_gen = field_diff.get('y_center_gen', 0)
            y_ref = field_diff.get('y_center_ref', 0)
            x_gen = field_diff.get('x_center_gen', 0)
            x_ref = field_diff.get('x_center_ref', 0)
            
            # Apply correction: move generated toward reference
            y_adjust = (y_ref - y_gen) * step_factor
            x_adjust = (x_ref - x_gen) * step_factor
            
            adjustments[field_name] = {
                'y_adjust': y_adjust,
                'x_adjust': x_adjust
            }
            
            logger.debug(
                f"Field '{field_name}': diff=({y_diff:.2f}, {x_diff:.2f})px, "
                f"adjustment=({y_adjust:.2f}, {x_adjust:.2f})px (step={step_factor:.2f})"
            )
        
        # Store in history
        self.adjustment_history.append({
            'attempt': attempt_number,
            'adjustments': adjustments,
            'step_factor': step_factor
        })
        
        return adjustments
    
    def is_converging(self, window_size: int = 3) -> bool:
        """
        Check if adjustments are converging (getting smaller).
        
        Args:
            window_size: Number of recent attempts to check
            
        Returns:
            True if converging, False otherwise
        """
        if len(self.adjustment_history) < window_size:
            return True  # Not enough data yet
        
        recent = self.adjustment_history[-window_size:]
        
        # Calculate average adjustment magnitude for each window element
        magnitudes = []
        for entry in recent:
            total_mag = 0
            count = 0
            for field_adj in entry['adjustments'].values():
                y_adj = field_adj.get('y_adjust', 0)
                x_adj = field_adj.get('x_adjust', 0)
                total_mag += abs(y_adj) + abs(x_adj)
                count += 1
            
            if count > 0:
                magnitudes.append(total_mag / count)
        
        # Check if magnitudes are generally decreasing
        if len(magnitudes) >= 2:
            # Simple check: is the latest smaller than the first?
            is_decreasing = magnitudes[-1] < magnitudes[0]
            logger.debug(f"Convergence check: {magnitudes} -> {'converging' if is_decreasing else 'not converging'}")
            return is_decreasing
        
        return True
    
    def should_abort(self, max_non_converging: int = 5) -> bool:
        """
        Check if refinement should be aborted due to non-convergence.
        
        Args:
            max_non_converging: Maximum non-converging attempts before aborting
            
        Returns:
            True if should abort, False otherwise
        """
        if len(self.adjustment_history) < max_non_converging:
            return False
        
        # Check if we've been non-converging for too long
        recent = self.adjustment_history[-max_non_converging:]
        
        # If adjustments are not getting smaller, we might be oscillating
        first_magnitude = sum(
            abs(adj.get('y_adjust', 0)) + abs(adj.get('x_adjust', 0))
            for field_adj in recent[0]['adjustments'].values()
            for adj in [field_adj]
        )
        
        last_magnitude = sum(
            abs(adj.get('y_adjust', 0)) + abs(adj.get('x_adjust', 0))
            for field_adj in recent[-1]['adjustments'].values()
            for adj in [field_adj]
        )
        
        # If magnitude increased significantly, we're not converging
        if last_magnitude > first_magnitude * 1.5:
            logger.warning("Progressive refinement not converging - aborting")
            return True
        
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get refinement statistics.
        
        Returns:
            Dictionary with statistics
        """
        if not self.adjustment_history:
            return {
                'total_attempts': 0,
                'converging': None,
                'average_adjustment': 0
            }
        
        # Calculate average adjustment magnitude
        total_mag = 0
        count = 0
        
        for entry in self.adjustment_history:
            for field_adj in entry['adjustments'].values():
                total_mag += abs(field_adj.get('y_adjust', 0)) + abs(field_adj.get('x_adjust', 0))
                count += 1
        
        avg_mag = total_mag / count if count > 0 else 0
        
        return {
            'total_attempts': len(self.adjustment_history),
            'converging': self.is_converging(),
            'average_adjustment': avg_mag,
            'tolerance_px': self.tolerance_px
        }


def apply_progressive_refinement(
    field_differences: Dict[str, Dict[str, float]],
    current_offsets: Dict[str, Dict[str, float]],
    refiner: ProgressiveRefiner,
    attempt_number: int
) -> Dict[str, Dict[str, float]]:
    """
    Apply progressive refinement to field positions.
    
    Args:
        field_differences: Current field differences from verification
        current_offsets: Current field position offsets
        refiner: ProgressiveRefiner instance
        attempt_number: Current attempt number
        
    Returns:
        Updated field offsets with adjustments applied
    """
    adjustments = refiner.calculate_adjustment(field_differences, attempt_number)
    
    updated_offsets = {}
    
    for field_name in ['name', 'event', 'organiser']:
        if field_name not in current_offsets:
            continue
        
        current = current_offsets[field_name]
        adjustment = adjustments.get(field_name, {'y_adjust': 0, 'x_adjust': 0})
        
        # Apply adjustments to normalized positions
        # Note: We adjust the Y position directly in pixels, then normalize
        updated_offsets[field_name] = {
            'x': current.get('x', 0.5),
            'y': current.get('y', 0.5),
            'baseline_offset': current.get('baseline_offset', 0) + adjustment['y_adjust']
        }
        
        logger.debug(
            f"Applied adjustment to {field_name}: "
            f"baseline_offset {current.get('baseline_offset', 0):.2f} -> "
            f"{updated_offsets[field_name]['baseline_offset']:.2f}"
        )
    
    return updated_offsets
