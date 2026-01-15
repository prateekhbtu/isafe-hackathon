"""
Risk Scoring Engine
Transparent, weighted aggregation of signals into a risk score (0-100)
"""
from typing import Dict, List, Any
import math
import asyncio
from gemini_client import gemini_client


class RiskScoringEngine:
    """
    Transparent risk scoring engine with configurable weights.
    
    Design principles:
    - No binary "fake/real" claims
    - Probabilistic risk assessment
    - Explainable signal weighting
    - Human-in-the-loop decision support
    """
    
    # Signal weights by modality (configurable)
    WEIGHTS = {
        'image': {
            'manipulation_artifacts': 0.35,
            'metadata_inconsistency': 0.20,
            'compression_anomaly': 0.15,
            'lighting_inconsistency': 0.15,
            'noise_pattern': 0.15
        },
        'video': {
            'facial_warping': 0.30,
            'lighting_shadow_anomaly': 0.20,
            'temporal_inconsistency': 0.20,
            'audio_visual_mismatch': 0.15,
            'compression_artifact': 0.15
        },
        'audio': {
            'spectral_anomaly': 0.30,
            'phoneme_inconsistency': 0.25,
            'voice_synthesis_artifact': 0.25,
            'background_mismatch': 0.20
        },
        'text': {
            'sensational_language': 0.25,
            'stylometric_drift': 0.20,
            'emotional_manipulation': 0.20,
            'factual_inconsistency': 0.20,
            'source_credibility': 0.15
        }
    }
    
    # Risk thresholds
    THRESHOLDS = {
        'low': 30,
        'medium': 60,
        'high': 100
    }
    
    async def calculate_risk(self, modality: str, signals: List[Dict[str, Any]], metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Calculate risk score from detected signals.
        
        Args:
            modality: Type of media (image, video, audio, text)
            signals: List of detected signals with confidence scores
            metadata: Optional context (source, timestamp, etc.)
        
        Returns:
            Risk assessment with score, level, explanation, and recommendations
        """
        if not signals:
            return self._generate_low_risk_response(modality)
        
        # Get weights for this modality
        weights = self.WEIGHTS.get(modality, {})
        
        # Calculate weighted risk score
        total_score = 0.0
        signal_contributions = []
        
        for signal in signals:
            signal_type = signal['type']
            confidence = signal['confidence']
            weight = weights.get(signal_type, 0.1)  # Default weight if not defined
            
            contribution = confidence * weight * 100
            total_score += contribution
            
            signal_contributions.append({
                'signal': signal_type,
                'description': signal['description'],
                'confidence': round(confidence, 2),
                'weight': weight,
                'contribution': round(contribution, 2),
                'evidence': signal.get('evidence', {})
            })
        
        # Cap at 100
        risk_score = min(100, round(total_score))
        
        # Determine risk level
        risk_level = self._determine_risk_level(risk_score)
        
        # Generate explanation
        explanation = self._generate_explanation(modality, signal_contributions, risk_score)
        
        # Generate recommendation
        recommendation = self._generate_recommendation(risk_level, modality)
        
        # Try to get Gemini analysis
        gemini_analysis = None
        gemini_signals = []
        
        if gemini_client.is_available():
            try:
                gemini_analysis = await gemini_client.analyze_media_risk(
                    modality, signals, metadata or {}
                )
                
                if gemini_analysis:
                    # Extract additional risk factors from Gemini
                    additional_factors = gemini_analysis.get('additional_context', [])
                    for i, factor in enumerate(additional_factors[:3]):  # Max 3 additional
                        gemini_signals.append({
                            'signal': 'ai_verified_risk_factor',
                            'description': factor,
                            'confidence': 0.70,  # Moderate confidence for AI insights
                            'weight': 0.15,
                            'contribution': 10.5,  # ~10 points each
                            'evidence': {'source': 'Gemini AI', 'factor_id': i+1}
                        })
                    
                    # Add Gemini signals to total if they add value
                    if gemini_signals:
                        for gs in gemini_signals:
                            total_score += gs['contribution']
                        signal_contributions.extend(gemini_signals)
                        
                        # Recalculate risk score with Gemini input
                        risk_score = min(100, round(total_score))
                        risk_level = self._determine_risk_level(risk_score)
            except Exception as e:
                print(f"Gemini analysis error: {e}")
        
        # Compile result
        result = {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'modality': modality,
            'signals_detected': len(signals) + len(gemini_signals),
            'signal_breakdown': signal_contributions,
            'explanation': explanation,
            'recommendation': recommendation,
            'gemini_analysis': gemini_analysis.get('gemini_analysis') if gemini_analysis else None,
            'gemini_verified': gemini_analysis is not None,
            'disclaimer': 'This is a probabilistic risk assessment. Human verification is essential for decision-making.',
            'timestamp': metadata.get('timestamp') if metadata else None,
            'source': metadata.get('source') if metadata else None
        }
        
        return result
    
    def _determine_risk_level(self, score: int) -> str:
        """Categorize risk score into Low/Medium/High"""
        if score < self.THRESHOLDS['low']:
            return 'Low'
        elif score < self.THRESHOLDS['medium']:
            return 'Medium'
        else:
            return 'High'
    
    def _generate_explanation(self, modality: str, contributions: List[Dict], score: int) -> str:
        """Generate human-readable explanation of risk score"""
        if not contributions:
            return f"No significant risk signals detected in this {modality}."
        
        top_signals = sorted(contributions, key=lambda x: x['contribution'], reverse=True)[:3]
        
        explanation_parts = [
            f"Risk score of {score}/100 calculated from {len(contributions)} detected signals.",
            "\nTop contributing factors:"
        ]
        
        for i, sig in enumerate(top_signals, 1):
            explanation_parts.append(
                f"\n{i}. {sig['signal'].replace('_', ' ').title()}: "
                f"{sig['description']} (Confidence: {sig['confidence']:.0%}, "
                f"Contribution: {sig['contribution']:.1f} points)"
            )
        
        return "".join(explanation_parts)
    
    def _generate_recommendation(self, risk_level: str, modality: str) -> Dict[str, Any]:
        """Generate actionable recommendations based on risk level"""
        recommendations = {
            'Low': {
                'action': 'Proceed with Caution',
                'priority': 'Low',
                'suggested_steps': [
                    'Content appears to have minimal risk indicators',
                    'Standard verification practices apply',
                    'Monitor for context changes if sharing publicly'
                ],
                'human_review_required': False
            },
            'Medium': {
                'action': 'Human Verification Advised',
                'priority': 'Medium',
                'suggested_steps': [
                    'Manual review recommended before publication',
                    'Verify source credibility independently',
                    f'Cross-check {modality} content with alternative sources',
                    'Consider consulting domain experts'
                ],
                'human_review_required': True
            },
            'High': {
                'action': 'Escalation Recommended',
                'priority': 'High',
                'suggested_steps': [
                    '⚠️ Multiple risk signals detected - immediate human review required',
                    'Do not publish or share without thorough verification',
                    'Consult fact-checking organizations',
                    'Conduct forensic analysis if appropriate',
                    'Document all verification steps'
                ],
                'human_review_required': True
            }
        }
        
        return recommendations[risk_level]
    
    def _generate_low_risk_response(self, modality: str) -> Dict[str, Any]:
        """Generate response when no signals detected"""
        return {
            'risk_score': 0,
            'risk_level': 'Low',
            'modality': modality,
            'signals_detected': 0,
            'signal_breakdown': [],
            'explanation': f"No significant deception risk signals detected in this {modality}. "
                          f"However, absence of detected signals does not guarantee authenticity.",
            'recommendation': {
                'action': 'Proceed with Standard Verification',
                'priority': 'Low',
                'suggested_steps': [
                    'No automated risk indicators found',
                    'Apply standard content verification practices',
                    'Note: Advanced manipulations may evade detection'
                ],
                'human_review_required': False
            },
            'disclaimer': 'This system cannot detect all forms of manipulation. Human judgment remains essential.',
            'timestamp': None,
            'source': None
        }
