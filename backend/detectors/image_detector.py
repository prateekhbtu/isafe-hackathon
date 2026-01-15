"""
Image Detector Module
Analyzes images for manipulation artifacts, metadata inconsistencies, and visual anomalies
"""
from typing import Dict, List, Any
from PIL import Image
import os
import hashlib
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from ml_detectors import ml_image_detector


class ImageDetector:
    """
    Detects potential manipulation signals in images.
    
    Uses lightweight heuristics and simulated ML signals for hackathon demo.
    In production, would integrate CNNs for tampering detection.
    """
    
    def detect(self, image_path: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Analyze image and return list of detected signals.
        
        Args:
            image_path: Path to image file
            metadata: Optional context (source, timestamp, etc.)
        
        Returns:
            List of signal dictionaries with type, confidence, description, and evidence
        """
        signals = []
        
        try:
            with Image.open(image_path) as img:
                # Signal 1: Check image dimensions and aspect ratio
                width, height = img.size
                aspect_ratio = width / height
                
                # Unusual aspect ratios can indicate cropping/manipulation
                if aspect_ratio < 0.5 or aspect_ratio > 3.0:
                    signals.append({
                        'type': 'manipulation_artifacts',
                        'confidence': 0.45,
                        'description': 'Unusual aspect ratio detected, possible cropping or resizing',
                        'evidence': {
                            'aspect_ratio': round(aspect_ratio, 2),
                            'dimensions': f"{width}x{height}"
                        }
                    })
                
                # Signal 2: Check file size vs resolution (compression anomaly)
                file_size = os.path.getsize(image_path)
                expected_size = width * height * 3  # Rough estimate for RGB
                compression_ratio = file_size / expected_size
                
                if compression_ratio < 0.02:  # Very high compression
                    signals.append({
                        'type': 'compression_anomaly',
                        'confidence': 0.55,
                        'description': 'High compression detected, may indicate re-encoding or quality loss',
                        'evidence': {
                            'compression_ratio': round(compression_ratio, 4),
                            'file_size_kb': round(file_size / 1024, 2)
                        }
                    })
                
                # Signal 3: Check for EXIF metadata
                exif_data = img.getexif()
                if not exif_data or len(exif_data) < 3:
                    signals.append({
                        'type': 'metadata_inconsistency',
                        'confidence': 0.40,
                        'description': 'Missing or stripped EXIF metadata, possible editing history removal',
                        'evidence': {
                            'exif_fields_found': len(exif_data) if exif_data else 0
                        }
                    })
                
                # Signal 4: Color mode check
                if img.mode not in ['RGB', 'RGBA']:
                    signals.append({
                        'type': 'manipulation_artifacts',
                        'confidence': 0.35,
                        'description': f'Unusual color mode ({img.mode}), may indicate processing',
                        'evidence': {
                            'color_mode': img.mode
                        }
                    })
                
                # Signal 5: ML-based Error Level Analysis (ELA)
                ela_result = ml_image_detector.error_level_analysis(image_path)
                if ela_result.get('ela_score', 0) > 0.4:
                    signals.append({
                        'type': 'manipulation_artifacts',
                        'confidence': min(ela_result['ela_score'] * 1.2, 0.95),
                        'description': 'Error Level Analysis detected inconsistent compression patterns',
                        'evidence': {
                            'ela_score': round(ela_result['ela_score'], 2),
                            'std_error': round(ela_result.get('std_error', 0), 2),
                            'suspicious_regions': ela_result.get('suspicious_regions', False),
                            'method': 'ML-based ELA'
                        }
                    })
                
                # Signal 6: Copy-Move Forgery Detection
                copy_move = ml_image_detector.detect_copy_move(image_path)
                if copy_move.get('copy_move_score', 0) > 0.3:
                    signals.append({
                        'type': 'manipulation_artifacts',
                        'confidence': copy_move['copy_move_score'] * 0.8,
                        'description': 'Possible copy-move forgery detected (duplicated regions)',
                        'evidence': {
                            'suspicion_score': round(copy_move['copy_move_score'], 2),
                            'similar_blocks': copy_move.get('similar_blocks', 0),
                            'method': 'Block matching analysis'
                        }
                    })
                
                # Signal 7: Metadata context check
                if metadata and metadata.get('source'):
                    source = metadata['source'].lower()
                    if any(keyword in source for keyword in ['unknown', 'anonymous', 'forwarded']):
                        signals.append({
                            'type': 'metadata_inconsistency',
                            'confidence': 0.50,
                            'description': 'Source marked as unknown or forwarded, provenance unclear',
                            'evidence': {
                                'source': metadata['source']
                            }
                        })
        
        except Exception as e:
            # If image analysis fails, return error signal
            signals.append({
                'type': 'manipulation_artifacts',
                'confidence': 0.30,
                'description': f'Unable to fully analyze image: {str(e)}',
                'evidence': {}
            })
        
        return signals
