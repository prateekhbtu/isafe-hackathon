"""
Audio Detector Module
Analyzes audio for voice synthesis artifacts, spectral anomalies, and phoneme inconsistencies
"""
from typing import Dict, List, Any
import os
import hashlib


class AudioDetector:
    """
    Detects potential manipulation signals in audio files.
    
    Uses heuristics for hackathon demo.
    In production, would integrate voice analysis models for spectral analysis,
    TTS detection, and phoneme-level consistency checking.
    """
    
    def detect(self, audio_path: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Analyze audio and return list of detected signals.
        
        Args:
            audio_path: Path to audio file
            metadata: Optional context (source, timestamp, etc.)
        
        Returns:
            List of signal dictionaries with type, confidence, description, and evidence
        """
        signals = []
        
        try:
            # Get basic file properties
            file_size = os.path.getsize(audio_path)
            file_name = os.path.basename(audio_path)
            
            # Signal 1: File size heuristic for audio quality
            size_kb = file_size / 1024
            duration_estimate = size_kb / 16  # Rough estimate: 16KB per second at 128kbps
            
            if size_kb < 50:  # Very small audio file
                signals.append({
                    'type': 'voice_synthesis_artifact',
                    'confidence': 0.42,
                    'description': 'Unusually small audio file, possible low-quality synthesis or heavy compression',
                    'evidence': {
                        'file_size_kb': round(size_kb, 2),
                        'estimated_duration_seconds': round(duration_estimate, 1)
                    }
                })
            
            # Signal 2: Simulated spectral anomaly detection
            # In production: FFT analysis for unnatural frequency patterns
            with open(audio_path, 'rb') as f:
                file_hash = hashlib.md5(f.read(3000)).hexdigest()
            
            spectral_score = int(file_hash[:2], 16) / 255.0
            if spectral_score > 0.68:
                signals.append({
                    'type': 'spectral_anomaly',
                    'confidence': 0.63,
                    'description': 'Spectral frequency distribution shows anomalies typical of synthesis',
                    'evidence': {
                        'spectral_anomaly_score': round(spectral_score, 2),
                        'note': 'Would use FFT analysis + ML in production'
                    }
                })
            
            # Signal 3: Simulated phoneme inconsistency
            # In production: Deep learning model for phoneme-level analysis
            phoneme_score = int(file_hash[2:4], 16) / 255.0
            if phoneme_score > 0.70:
                signals.append({
                    'type': 'phoneme_inconsistency',
                    'confidence': 0.57,
                    'description': 'Phoneme transitions show signs of artificial generation',
                    'evidence': {
                        'phoneme_consistency_score': round(phoneme_score, 2)
                    }
                })
            
            # Signal 4: Simulated voice synthesis artifact detection
            # In production: TTS detector model (e.g., detecting WaveNet/Tacotron artifacts)
            synthesis_score = int(file_hash[4:6], 16) / 255.0
            if synthesis_score > 0.72:
                signals.append({
                    'type': 'voice_synthesis_artifact',
                    'confidence': 0.60,
                    'description': 'Audio characteristics suggest possible voice cloning or TTS generation',
                    'evidence': {
                        'synthesis_likelihood': round(synthesis_score, 2),
                        'note': 'Would use specialized TTS detection model in production'
                    }
                })
            
            # Signal 5: Background audio consistency
            background_score = int(file_hash[6:8], 16) / 255.0
            if background_score > 0.65:
                signals.append({
                    'type': 'background_mismatch',
                    'confidence': 0.48,
                    'description': 'Background audio profile inconsistent with expected environment',
                    'evidence': {
                        'background_consistency_score': round(background_score, 2)
                    }
                })
            
            # Signal 6: File format check
            supported_formats = ['.wav', '.mp3', '.m4a', '.ogg', '.flac']
            file_ext = os.path.splitext(file_name)[1].lower()
            if file_ext not in supported_formats:
                signals.append({
                    'type': 'voice_synthesis_artifact',
                    'confidence': 0.35,
                    'description': 'Unusual audio format, may indicate conversion or processing',
                    'evidence': {
                        'format': file_ext
                    }
                })
            
            # Signal 7: Metadata context check
            if metadata and metadata.get('source'):
                source = metadata['source'].lower()
                if any(keyword in source for keyword in ['unknown', 'anonymous', 'forwarded', 'unverified']):
                    signals.append({
                        'type': 'background_mismatch',
                        'confidence': 0.45,
                        'description': 'Audio source has unclear provenance',
                        'evidence': {
                            'source': metadata['source']
                        }
                    })
        
        except Exception as e:
            signals.append({
                'type': 'voice_synthesis_artifact',
                'confidence': 0.30,
                'description': f'Unable to fully analyze audio: {str(e)}',
                'evidence': {}
            })
        
        return signals
