"""
Alignment statistics tracker for monitoring and optimization.

This module tracks alignment verification statistics to identify patterns,
monitor performance, and enable data-driven optimization.
"""
import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


class AlignmentStats:
    """Track and analyze alignment verification statistics."""
    
    def __init__(self, stats_file: str = 'alignment_stats.json'):
        """
        Initialize alignment statistics tracker.
        
        Args:
            stats_file: Path to statistics file
        """
        self.stats_file = stats_file
        self.stats = self._load_stats()
    
    def _load_stats(self) -> Dict[str, Any]:
        """Load statistics from file."""
        if not os.path.exists(self.stats_file):
            return {
                'total_verifications': 0,
                'successful_verifications': 0,
                'failed_verifications': 0,
                'attempts_histogram': defaultdict(int),
                'field_failures': defaultdict(int),
                'average_attempts': 0.0,
                'records': []
            }
        
        try:
            with open(self.stats_file, 'r') as f:
                data = json.load(f)
                # Convert histogram back to defaultdict
                if 'attempts_histogram' in data:
                    data['attempts_histogram'] = defaultdict(int, data['attempts_histogram'])
                if 'field_failures' in data:
                    data['field_failures'] = defaultdict(int, data['field_failures'])
                logger.debug(f"Loaded alignment statistics from {self.stats_file}")
                return data
        except Exception as e:
            logger.warning(f"Could not load alignment statistics: {e}")
            return {
                'total_verifications': 0,
                'successful_verifications': 0,
                'failed_verifications': 0,
                'attempts_histogram': defaultdict(int),
                'field_failures': defaultdict(int),
                'average_attempts': 0.0,
                'records': []
            }
    
    def _save_stats(self):
        """Save statistics to file."""
        try:
            # Convert defaultdict to regular dict for JSON serialization
            save_data = dict(self.stats)
            save_data['attempts_histogram'] = dict(self.stats['attempts_histogram'])
            save_data['field_failures'] = dict(self.stats['field_failures'])
            
            with open(self.stats_file, 'w') as f:
                json.dump(save_data, f, indent=2)
            logger.debug(f"Saved alignment statistics to {self.stats_file}")
        except Exception as e:
            logger.error(f"Could not save alignment statistics: {e}")
    
    def record_verification(
        self,
        passed: bool,
        attempts: int,
        max_difference_px: float,
        field_differences: Dict[str, Dict[str, float]],
        tolerance_px: float,
        participant_data: Optional[Dict[str, str]] = None
    ):
        """
        Record a verification attempt.
        
        Args:
            passed: Whether verification passed
            attempts: Number of attempts taken
            max_difference_px: Maximum difference in pixels
            field_differences: Per-field differences
            tolerance_px: Tolerance used
            participant_data: Optional participant data
        """
        self.stats['total_verifications'] += 1
        
        if passed:
            self.stats['successful_verifications'] += 1
        else:
            self.stats['failed_verifications'] += 1
        
        # Update attempts histogram
        attempts_key = str(attempts)
        self.stats['attempts_histogram'][attempts_key] += 1
        
        # Track field failures
        for field_name, field_diff in field_differences.items():
            if 'error' in field_diff or field_diff.get('y_diff', 0) > tolerance_px or field_diff.get('x_diff', 0) > tolerance_px:
                self.stats['field_failures'][field_name] += 1
        
        # Update average attempts
        total = self.stats['total_verifications']
        current_avg = self.stats['average_attempts']
        self.stats['average_attempts'] = (current_avg * (total - 1) + attempts) / total
        
        # Store record (keep last 100)
        record = {
            'timestamp': datetime.now().isoformat(),
            'passed': passed,
            'attempts': attempts,
            'max_difference_px': max_difference_px,
            'tolerance_px': tolerance_px,
            'field_count': len([f for f in field_differences.values() if 'error' not in f])
        }
        
        if participant_data:
            # Store text lengths for pattern analysis
            record['text_lengths'] = {
                'name': len(str(participant_data.get('name', ''))),
                'event': len(str(participant_data.get('event', ''))),
                'organiser': len(str(participant_data.get('organiser', '')))
            }
        
        self.stats['records'].append(record)
        
        # Keep only last 100 records
        if len(self.stats['records']) > 100:
            self.stats['records'] = self.stats['records'][-100:]
        
        self._save_stats()
        
        logger.info(
            f"Recorded verification: passed={passed}, attempts={attempts}, "
            f"max_diff={max_difference_px:.4f}px"
        )
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics.
        
        Returns:
            Dictionary with summary statistics
        """
        total = self.stats['total_verifications']
        
        if total == 0:
            return {
                'total_verifications': 0,
                'success_rate': 0.0,
                'average_attempts': 0.0,
                'most_common_attempts': None,
                'problem_fields': []
            }
        
        success_rate = self.stats['successful_verifications'] / total * 100
        
        # Find most common number of attempts
        most_common_attempts = None
        if self.stats['attempts_histogram']:
            most_common_attempts = max(
                self.stats['attempts_histogram'].items(),
                key=lambda x: x[1]
            )[0]
        
        # Identify problem fields (fields that fail most often)
        problem_fields = sorted(
            self.stats['field_failures'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]  # Top 3 problem fields
        
        return {
            'total_verifications': total,
            'successful_verifications': self.stats['successful_verifications'],
            'failed_verifications': self.stats['failed_verifications'],
            'success_rate': success_rate,
            'average_attempts': self.stats['average_attempts'],
            'most_common_attempts': int(most_common_attempts) if most_common_attempts else None,
            'problem_fields': [{'field': f, 'failures': c} for f, c in problem_fields],
            'attempts_distribution': dict(self.stats['attempts_histogram'])
        }
    
    def get_recommendations(self) -> List[str]:
        """
        Get recommendations based on statistics.
        
        Returns:
            List of recommendation strings
        """
        recommendations = []
        summary = self.get_summary()
        
        if summary['total_verifications'] == 0:
            return ["No data collected yet. Generate some certificates to get recommendations."]
        
        # Check success rate
        if summary['success_rate'] < 80:
            recommendations.append(
                f"❌ Low success rate ({summary['success_rate']:.1f}%). "
                "Consider reviewing field positions in goonj_template_offsets.json"
            )
        elif summary['success_rate'] < 95:
            recommendations.append(
                f"⚠️  Moderate success rate ({summary['success_rate']:.1f}%). "
                "Some alignment tuning may improve reliability."
            )
        else:
            recommendations.append(
                f"✅ Good success rate ({summary['success_rate']:.1f}%)!"
            )
        
        # Check average attempts
        if summary['average_attempts'] > 10:
            recommendations.append(
                f"⚠️  High average attempts ({summary['average_attempts']:.1f}). "
                "Consider using position caching or progressive refinement."
            )
        elif summary['average_attempts'] > 5:
            recommendations.append(
                f"ℹ️  Average attempts: {summary['average_attempts']:.1f}. "
                "Performance is acceptable but could be optimized."
            )
        else:
            recommendations.append(
                f"✅ Low average attempts ({summary['average_attempts']:.1f})!"
            )
        
        # Check for problem fields
        if summary['problem_fields']:
            problem_field_names = [f['field'] for f in summary['problem_fields']]
            recommendations.append(
                f"🔧 Problem fields detected: {', '.join(problem_field_names)}. "
                "Consider adjusting baseline_offset for these fields."
            )
        
        # Check attempt distribution
        if summary['most_common_attempts'] and int(summary['most_common_attempts']) == 1:
            recommendations.append(
                "✨ Most certificates align on first attempt - excellent calibration!"
            )
        
        return recommendations
    
    def reset(self):
        """Reset all statistics."""
        self.stats = {
            'total_verifications': 0,
            'successful_verifications': 0,
            'failed_verifications': 0,
            'attempts_histogram': defaultdict(int),
            'field_failures': defaultdict(int),
            'average_attempts': 0.0,
            'records': []
        }
        self._save_stats()
        logger.info("Reset alignment statistics")


# Global stats instance
_alignment_stats = None


def get_alignment_stats(stats_file: str = 'alignment_stats.json') -> AlignmentStats:
    """
    Get the global alignment statistics instance.
    
    Args:
        stats_file: Path to statistics file
        
    Returns:
        AlignmentStats instance
    """
    global _alignment_stats
    
    if _alignment_stats is None:
        _alignment_stats = AlignmentStats(stats_file)
    
    return _alignment_stats
