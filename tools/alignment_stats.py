#!/usr/bin/env python
"""
Alignment statistics viewer and manager.

View statistics, get recommendations, and manage alignment data.

Usage:
    python tools/alignment_stats.py [command]

Commands:
    summary      - Show statistics summary
    recommend    - Get recommendations
    reset        - Reset statistics
    export       - Export statistics to JSON
"""
import sys
import os
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Direct import to avoid Flask dependencies
import importlib.util

stats_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'app', 'utils', 'alignment_stats.py'
)
spec = importlib.util.spec_from_file_location("alignment_stats", stats_path)
stats_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stats_module)

get_alignment_stats = stats_module.get_alignment_stats


def show_summary():
    """Show statistics summary."""
    stats = get_alignment_stats()
    summary = stats.get_summary()
    
    print("=" * 70)
    print("ALIGNMENT VERIFICATION STATISTICS")
    print("=" * 70)
    
    print(f"\n📊 Overall Statistics:")
    print(f"   Total verifications: {summary['total_verifications']}")
    print(f"   Successful: {summary['successful_verifications']}")
    print(f"   Failed: {summary['failed_verifications']}")
    print(f"   Success rate: {summary['success_rate']:.1f}%")
    
    print(f"\n⏱️  Performance:")
    print(f"   Average attempts: {summary['average_attempts']:.2f}")
    if summary['most_common_attempts']:
        print(f"   Most common attempts: {summary['most_common_attempts']}")
    
    if summary['problem_fields']:
        print(f"\n⚠️  Problem Fields:")
        for field_info in summary['problem_fields']:
            print(f"   {field_info['field']}: {field_info['failures']} failures")
    
    if summary['attempts_distribution']:
        print(f"\n📈 Attempts Distribution:")
        for attempts, count in sorted(summary['attempts_distribution'].items(), key=lambda x: int(x[0])):
            bar = "█" * min(50, count)
            print(f"   {attempts:>3} attempts: {bar} ({count})")
    
    print()


def show_recommendations():
    """Show recommendations based on statistics."""
    stats = get_alignment_stats()
    recommendations = stats.get_recommendations()
    
    print("=" * 70)
    print("ALIGNMENT RECOMMENDATIONS")
    print("=" * 70)
    print()
    
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")
        print()


def reset_stats():
    """Reset statistics."""
    print("⚠️  This will delete all alignment statistics.")
    response = input("Are you sure? (yes/no): ")
    
    if response.lower() in ['yes', 'y']:
        stats = get_alignment_stats()
        stats.reset()
        print("✅ Statistics reset successfully")
    else:
        print("❌ Reset cancelled")


def export_stats():
    """Export statistics to JSON."""
    stats = get_alignment_stats()
    output_file = 'alignment_stats_export.json'
    
    with open(output_file, 'w') as f:
        json.dump(stats.stats, f, indent=2, default=str)
    
    print(f"✅ Statistics exported to {output_file}")


def show_help():
    """Show help message."""
    print("""
Alignment Statistics Tool

Usage: python tools/alignment_stats.py [command]

Commands:
    summary      - Show statistics summary (default)
    recommend    - Get recommendations based on statistics
    reset        - Reset all statistics
    export       - Export statistics to JSON file
    help         - Show this help message

Examples:
    python tools/alignment_stats.py
    python tools/alignment_stats.py summary
    python tools/alignment_stats.py recommend
    python tools/alignment_stats.py export
    """)


def main():
    """Main entry point."""
    command = sys.argv[1] if len(sys.argv) > 1 else 'summary'
    
    if command == 'summary':
        show_summary()
    elif command == 'recommend':
        show_recommendations()
    elif command == 'reset':
        reset_stats()
    elif command == 'export':
        export_stats()
    elif command == 'help':
        show_help()
    else:
        print(f"Unknown command: {command}")
        show_help()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
