#!/usr/bin/env python3
"""
Category G rules: vision quality checks (strongly recommended).
Corresponds to G1–G2 checks in Instruction.md.

Note: these checks require image decoding and may be slow.
Enable them only when needed.
"""

from typing import Any
import numpy as np


def check_image_integrity(reader: Any, report: Any) -> None:
    """
    G1: Image integrity check.
    - Not all black / all white.
    - Resolution is constant.
    - No severe tearing.
    """
    image_topics = {}
    sample_count = 0
    max_samples = 100  # only sample a subset of images
    
    for _, channel, message in reader.iter_messages():
        if "image" not in channel.topic:
            continue
        
        if sample_count >= max_samples:
            break
        
        try:
            # Here we would need to decode according to actual image message format,
            # usually sensor_msgs/Image or compressed image.
            #
            # Placeholder implementation. A real implementation should:
            # 1. Decode the image according to encoding.
            # 2. Check image dimensions.
            # 3. Check pixel value distribution.
            
            if channel.topic not in image_topics:
                image_topics[channel.topic] = {
                    'count': 0,
                    'width': None,
                    'height': None
                }
            
            image_topics[channel.topic]['count'] += 1
            sample_count += 1
            
        except Exception as e:
            report.warn("G1: Cannot decode image", f"{channel.topic}: {e}")
            return
    
    if not image_topics:
        report.warn("G1: No images to check")
        return
    
    # Simplified version: only report images found
    for topic, info in image_topics.items():
        report.ok("G1: Images found", f"{topic}: {info['count']} samples")
    
    report.warn("G1: Image quality check not fully implemented", 
               "Enable ENABLE_VISION_CHECKS for detailed analysis")


def check_illumination(reader: Any, report: Any) -> None:
    """
    G2: Illumination & flicker check.
    - No periodic brightness flicker.
    - Brightness changes smoothly.
    """
    # Would require:
    # 1. Computing average image brightness.
    # 2. Detecting periodic changes (FFT).
    # 3. Checking brightness gradients.
    
    report.warn("G2: Illumination check not implemented", 
               "Requires image decoding and brightness analysis")


def decode_image(message: Any, encoding: str) -> np.ndarray:
    """
    Helper: decode an image message.
    Decode according to different encoding formats.

    Common encodings:
    - rgb8, bgr8, rgba8, bgra8
    - mono8, mono16
    - compressed (JPEG, PNG)
    """
    # Real implementation must depend on message format.
    # This is only a placeholder.
    raise NotImplementedError("Image decoding not implemented")


def check_brightness(image: np.ndarray) -> dict:
    """
    Check image brightness and return statistics.
    """
    if len(image.shape) == 3:
        # Color image, convert to grayscale
        gray = np.mean(image, axis=2)
    else:
        gray = image
    
    return {
        'mean': np.mean(gray),
        'std': np.std(gray),
        'min': np.min(gray),
        'max': np.max(gray)
    }
