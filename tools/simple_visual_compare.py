#!/usr/bin/env python3
"""Simple visual comparison without Flask dependencies"""

import cv2
import numpy as np
import sys

def create_comparison(generated_path, reference_path, output_path):
    """Create side-by-side comparison image"""
    # Load images
    generated = cv2.imread(generated_path)
    reference = cv2.imread(reference_path)
    
    if generated is None or reference is None:
        print("Error loading images")
        return
    
    # Resize to same dimensions if needed
    if generated.shape != reference.shape:
        generated = cv2.resize(generated, (reference.shape[1], reference.shape[0]))
    
    # Create side by side comparison
    h, w = reference.shape[:2]
    comparison = np.zeros((h, w*2, 3), dtype=np.uint8)
    comparison[:, :w] = reference
    comparison[:, w:] = generated
    
    # Add labels
    cv2.putText(comparison, "REFERENCE (Original Canva)", (20, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 255, 255), 3)
    cv2.putText(comparison, "GENERATED (PPTX Positions)", (w + 20, 50), 
                cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
    
    # Calculate difference
    diff = cv2.absdiff(generated, reference)
    gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray_diff, 10, 255, cv2.THRESH_BINARY)
    different_pixels = np.sum(thresh > 0)
    total_pixels = thresh.size
    diff_percent = (different_pixels / total_pixels) * 100
    
    # Add difference info
    info_text = f"Pixel Difference: {diff_percent:.2f}%"
    cv2.putText(comparison, info_text, (w//2 - 200, h - 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 255), 3)
    
    cv2.imwrite(output_path, comparison)
    print(f"✅ Created comparison: {output_path}")
    print(f"   Difference: {diff_percent:.2f}%")
    
    # Create difference heatmap
    diff_color = cv2.applyColorMap(gray_diff, cv2.COLORMAP_JET)
    diff_output = output_path.replace('.png', '_heatmap.png')
    cv2.imwrite(diff_output, diff_color)
    print(f"✅ Created heatmap: {diff_output}")
    
    return diff_percent

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python simple_visual_compare.py <generated> <reference> <output>")
        sys.exit(1)
    
    create_comparison(sys.argv[1], sys.argv[2], sys.argv[3])
