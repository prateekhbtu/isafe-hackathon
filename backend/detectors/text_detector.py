"""
Text Detector Module
Analyzes text for sensational language, stylometric anomalies, and misinformation patterns
"""
from typing import Dict, List, Any
import re
from collections import Counter
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
# from ml_detectors import ml_text_detector  # Not implemented yet


class TextDetector:
    """
    Detects potential deception signals in text content.
    
    Uses linguistic heuristics and pattern matching for hackathon demo.
    In production, would integrate NLP models for sentiment analysis,
    fact-checking APIs, and stylometric analysis.
    """
    
    # Sensational language indicators
    SENSATIONAL_KEYWORDS = [
        'shocking', 'unbelievable', 'breaking', 'urgent', 'must see',
        'you won\'t believe', 'exposed', 'secret', 'hidden truth',
        'they don\'t want you to know', 'exclusive', 'bombshell',
        'devastating', 'alarming', 'terrifying', 'mind-blowing'
    ]
    
    # Emotional manipulation indicators
    EMOTIONAL_TRIGGERS = [
        'outrage', 'fury', 'anger', 'fear', 'panic', 'threat',
        'danger', 'crisis', 'emergency', 'disaster', 'tragedy',
        'heartbreaking', 'infuriating', 'disgusting'
    ]
    
    # Credibility markers (lack of these is suspicious)
    CREDIBILITY_MARKERS = [
        'according to', 'research shows', 'study finds', 'experts say',
        'data indicates', 'official', 'confirmed', 'verified'
    ]
    
    def detect(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Analyze text and return list of detected signals.
        
        Args:
            text: Text content to analyze
            metadata: Optional context (source, timestamp, etc.)
        
        Returns:
            List of signal dictionaries with type, confidence, description, and evidence
        """
        signals = []
        text_lower = text.lower()
        
        # Signal 1: Sensational language detection
        sensational_matches = [kw for kw in self.SENSATIONAL_KEYWORDS if kw in text_lower]
        if sensational_matches:
            confidence = min(0.8, 0.35 + (len(sensational_matches) * 0.1))
            signals.append({
                'type': 'sensational_language',
                'confidence': confidence,
                'description': f'Text contains {len(sensational_matches)} sensational language patterns',
                'evidence': {
                    'matches': sensational_matches[:5],  # Show first 5
                    'count': len(sensational_matches)
                }
            })
        
        # Signal 2: Emotional manipulation
        emotional_matches = [kw for kw in self.EMOTIONAL_TRIGGERS if kw in text_lower]
        if emotional_matches:
            confidence = min(0.75, 0.30 + (len(emotional_matches) * 0.12))
            signals.append({
                'type': 'emotional_manipulation',
                'confidence': confidence,
                'description': f'Text uses emotionally charged language ({len(emotional_matches)} triggers)',
                'evidence': {
                    'triggers': emotional_matches[:5],
                    'count': len(emotional_matches)
                }
            })
        
        # Signal 3: Lack of credibility markers
        credibility_found = sum(1 for marker in self.CREDIBILITY_MARKERS if marker in text_lower)
        if len(text) > 200 and credibility_found == 0:
            signals.append({
                'type': 'source_credibility',
                'confidence': 0.50,
                'description': 'Text lacks credibility markers (citations, sources, expert references)',
                'evidence': {
                    'credibility_markers_found': 0,
                    'text_length': len(text)
                }
            })
        
        # Signal 4: Excessive capitalization
        caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
        if caps_ratio > 0.15:  # More than 15% capitals
            signals.append({
                'type': 'sensational_language',
                'confidence': 0.45,
                'description': 'Excessive capitalization suggests emotional amplification',
                'evidence': {
                    'capitalization_ratio': round(caps_ratio, 2)
                }
            })
        
        # Signal 5: Excessive punctuation (!!!, ???)
        exclamation_count = text.count('!')
        question_count = text.count('?')
        total_punct = exclamation_count + question_count
        
        if total_punct > 5 and len(text) < 500:
            signals.append({
                'type': 'emotional_manipulation',
                'confidence': 0.48,
                'description': 'Excessive punctuation indicates emotional manipulation',
                'evidence': {
                    'exclamation_marks': exclamation_count,
                    'question_marks': question_count
                }
            })
        
        # Signal 6: All caps words
        words = text.split()
        all_caps_words = [w for w in words if w.isupper() and len(w) > 2]
        if len(all_caps_words) > 3:
            signals.append({
                'type': 'sensational_language',
                'confidence': 0.42,
                'description': f'Multiple all-caps words used for emphasis ({len(all_caps_words)} found)',
                'evidence': {
                    'all_caps_words': all_caps_words[:5],
                    'count': len(all_caps_words)
                }
            })
        
        # Signal 7: Factual inconsistency indicators (simulated)
        # In production: integrate fact-checking APIs
        inconsistency_patterns = ['reportedly', 'allegedly', 'unconfirmed', 'rumor', 'claims']
        inconsistency_matches = [p for p in inconsistency_patterns if p in text_lower]
        
        if len(inconsistency_matches) > 2:
            signals.append({
                'type': 'factual_inconsistency',
                'confidence': 0.52,
                'description': 'Text contains multiple uncertainty/unverified claim indicators',
                'evidence': {
                    'patterns': inconsistency_matches,
                    'note': 'Would integrate fact-checking API in production'
                }
            })
        
        # Signal 8: Stylometric analysis (simplified)
        # Check sentence length variance
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) > 3:
            sentence_lengths = [len(s.split()) for s in sentences]
            avg_length = sum(sentence_lengths) / len(sentence_lengths)
            
            # Very short or very long average sentence length
            if avg_length < 5 or avg_length > 40:
                signals.append({
                    'type': 'stylometric_drift',
                    'confidence': 0.38,
                    'description': 'Unusual sentence structure patterns detected',
                    'evidence': {
                        'average_sentence_length': round(avg_length, 1),
                        'sentence_count': len(sentences)
                    }
                })
        
        # Signal 9: ML-based sentiment manipulation (disabled - not implemented)
        # sentiment_result = ml_text_detector.analyze_sentiment_manipulation(text)
        # if sentiment_result.get('manipulation_score', 0) > 0.6:
        #     signals.append({
        #         'type': 'emotional_manipulation',
        #         'confidence': sentiment_result['manipulation_score'] * 0.9,
        #         'description': 'ML analysis detected extreme sentiment manipulation',
        #         'evidence': {
        #             'polarity': round(sentiment_result.get('sentiment_polarity', 0), 2),
        #             'subjectivity': round(sentiment_result.get('subjectivity', 0), 2),
        #             'is_extreme': sentiment_result.get('is_extreme', False),
        #             'method': 'TextBlob sentiment analysis'
        #         }
        #     })
        
        # Signal 10: Urgency pattern detection (disabled - not implemented)
        # urgency_result = ml_text_detector.detect_urgency_patterns(text)
        # if urgency_result.get('urgency_score', 0) > 0.4:
        #     signals.append({
        #         'type': 'emotional_manipulation',
        #         'confidence': urgency_result['urgency_score'],
        #         'description': f'Text uses urgency tactics to pressure immediate action',
        #         'evidence': {
        #             'urgency_keywords': urgency_result['urgency_keywords_found'],
        #             'time_pressure': urgency_result['time_pressure_detected'],
        #             'urgency_score': round(urgency_result['urgency_score'], 2)
        #         }
        #     })
        
        # Signal 11: Source metadata check
        if metadata and metadata.get('source'):
            source = metadata['source'].lower()
            if any(keyword in source for keyword in ['unknown', 'anonymous', 'forwarded', 'viral', 'social media']):
                signals.append({
                    'type': 'source_credibility',
                    'confidence': 0.55,
                    'description': 'Text source has low credibility or unclear provenance',
                    'evidence': {
                        'source': metadata['source']
                    }
                })
        
        return signals
