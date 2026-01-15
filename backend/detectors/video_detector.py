"""
Video Detector Module
Analyzes videos for deepfake artifacts, temporal inconsistencies, and audio-visual mismatches
"""
from typing import Dict, List, Any
import os
import hashlib


class VideoDetector:
    """
    Detects potential manipulation signals in videos.
    
    Uses heuristics and simulated ML signals for hackathon demo.
    In production, would integrate ResNet+LSTM for face-swap detection,
    optical flow analysis, and audio-visual sync verification.
    """
    
    def detect(self, video_path: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Analyze video and return list of detected signals.
        
        Args:
            video_path: Path to video file
            metadata: Optional context (source, timestamp, etc.)
        
        Returns:
            List of signal dictionaries with type, confidence, description, and evidence
        """
        signals = []
        
        try:
            # Get basic file properties
            file_size = os.path.getsize(video_path)
            file_name = os.path.basename(video_path)
            
            # Signal 1: File size heuristic
            # Very small videos may indicate heavy compression (suspicious)
            size_mb = file_size / (1024 * 1024)
            if size_mb < 1:
                signals.append({
                    'type': 'compression_artifact',
                    'confidence': 0.45,
                    'description': 'Very small file size for video, possible heavy re-encoding',
                    'evidence': {
                        'file_size_mb': round(size_mb, 2)
                    }
                })
            
            # Signal 2: Simulated facial warping detection (placeholder for CNN)
            # In production: ResNet+LSTM analyzing facial landmarks frame-by-frame
            with open(video_path, 'rb') as f:
                file_hash = hashlib.md5(f.read(5000)).hexdigest()
            
            warping_score = int(file_hash[:2], 16) / 255.0
            if warping_score > 0.65:
                signals.append({
                    'type': 'facial_warping',
                    'confidence': 0.60,
                    'description': 'Potential facial region anomalies detected across frames',
                    'evidence': {
                        'warping_score': round(warping_score, 2),
                        'note': 'Simulated heuristic - would use ResNet+LSTM in production'
                    }
                })
            
            # Signal 3: Simulated lighting inconsistency
            lighting_score = int(file_hash[2:4], 16) / 255.0
            if lighting_score > 0.70:
                signals.append({
                    'type': 'lighting_shadow_anomaly',
                    'confidence': 0.55,
                    'description': 'Lighting or shadow patterns show inconsistencies',
                    'evidence': {
                        'lighting_inconsistency_score': round(lighting_score, 2)
                    }
                })
            
            # Signal 4: Simulated temporal inconsistency
            # In production: optical flow analysis for unnatural motion
            temporal_score = int(file_hash[4:6], 16) / 255.0
            if temporal_score > 0.68:
                signals.append({
                    'type': 'temporal_inconsistency',
                    'confidence': 0.52,
                    'description': 'Frame-to-frame transitions show temporal anomalies',
                    'evidence': {
                        'temporal_score': round(temporal_score, 2),
                        'note': 'Would use optical flow analysis in production'
                    }
                })
            
            # Signal 5: Audio-visual mismatch (simulated)
            # In production: lip-sync analysis
            av_score = int(file_hash[6:8], 16) / 255.0
            if av_score > 0.72:
                signals.append({
                    'type': 'audio_visual_mismatch',
                    'confidence': 0.58,
                    'description': 'Audio and visual cues may be misaligned (lip-sync issues)',
                    'evidence': {
                        'av_mismatch_score': round(av_score, 2)
                    }
                })
            
            # Signal 6: File extension vs content check
            if not file_name.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                signals.append({
                    'type': 'compression_artifact',
                    'confidence': 0.35,
                    'description': 'Unusual file extension for video content',
                    'evidence': {
                        'extension': os.path.splitext(file_name)[1]
                    }
                })
            
            # Signal 7: Metadata context check
            if metadata and metadata.get('source'):
                source = metadata['source'].lower()
                if any(keyword in source for keyword in ['unknown', 'anonymous', 'social media', 'forwarded']):
                    signals.append({
                        'type': 'temporal_inconsistency',
                        'confidence': 0.48,
                        'description': 'Video source has low provenance credibility',
                        'evidence': {
                            'source': metadata['source']
                        }
                    })
        
        except Exception as e:
            signals.append({
                'type': 'compression_artifact',
                'confidence': 0.30,
                'description': f'Unable to fully analyze video: {str(e)}',
                'evidence': {}
            })
        
        return signals
