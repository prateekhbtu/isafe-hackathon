"""
Gemini API Client
Integrates with deployed Gemini API for advanced analysis and verification
"""
import os
import httpx
from typing import Dict, Any, Optional
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class GeminiClient:
    """Client for interacting with Gemini API on Render"""
    
    def __init__(self):
        self.base_url = os.getenv("GEMINI_API_URL", "")
        self.timeout = 30.0
        
    def is_available(self) -> bool:
        """Check if Gemini API is configured and reachable"""
        if not self.base_url:
            return False
        try:
            response = httpx.get(f"{self.base_url}/health", timeout=5.0)
            return response.status_code == 200
        except:
            return False
    
    async def generate(self, prompt: str) -> Optional[str]:
        """
        Send prompt to Gemini API and get response
        
        Args:
            prompt: Text prompt to send
            
        Returns:
            Generated text response or None if failed
        """
        if not self.base_url:
            return None
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/generate",
                    json={"text": prompt},
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    # Extract text from response (adapt based on your API response format)
                    if isinstance(result, dict):
                        return result.get("text") or result.get("response") or str(result)
                    return str(result)
                return None
        except Exception as e:
            print(f"Gemini API error: {str(e)}")
            return None
    
    async def analyze_media_risk(
        self, 
        modality: str, 
        signals: list, 
        metadata: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Use Gemini to analyze detected signals and provide additional insights
        
        Args:
            modality: Type of media (image, video, audio, text)
            signals: List of detected signals
            metadata: Context metadata
            
        Returns:
            Gemini analysis with risk factors and additional signals
        """
        if not self.is_available():
            return None
        
        # Build prompt for Gemini
        signal_summary = "\n".join([
            f"- {s['type']}: {s['description']} (confidence: {s['confidence']:.0%})"
            for s in signals[:5]  # Limit to top 5 signals
        ])
        
        source = metadata.get('source', 'Unknown')
        context = metadata.get('context', 'No context provided')
        
        prompt = f"""Analyze this {modality} content for deception risk.

Detected Signals:
{signal_summary}

Source: {source}
Context: {context}

Please provide:
1. Overall risk assessment (Low/Medium/High)
2. 3-4 additional risk factors not covered by the signals
3. Contextual red flags based on source and timing
4. Confidence level in your assessment

Keep response concise and factual. Focus on verifiable risk indicators."""

        response = await self.generate(prompt)
        
        if not response:
            return None
        
        # Parse Gemini response
        return {
            "gemini_analysis": response,
            "gemini_available": True,
            "additional_context": self._extract_risk_factors(response)
        }
    
    async def verify_text_content(self, text: str, metadata: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Use Gemini to verify text content for misinformation patterns
        
        Args:
            text: Text content to analyze
            metadata: Context metadata
            
        Returns:
            Gemini verification results
        """
        if not self.is_available():
            return None
        
        source = metadata.get('source', 'Unknown')
        
        prompt = f"""Analyze this text for misinformation risk indicators:

Text: "{text[:500]}..."

Source: {source}

Identify:
1. Factual claims that can be verified
2. Emotional manipulation techniques
3. Logical fallacies or misleading framing
4. Credibility red flags
5. Risk score (0-100) with reasoning

Be objective and evidence-based."""

        response = await self.generate(prompt)
        
        if not response:
            return None
        
        return {
            "verification": response,
            "gemini_verified": True
        }
    
    def _extract_risk_factors(self, gemini_response: str) -> list:
        """
        Extract structured risk factors from Gemini's text response
        
        Args:
            gemini_response: Raw text from Gemini
            
        Returns:
            List of risk factor strings
        """
        # Simple extraction - look for numbered or bulleted points
        risk_factors = []
        lines = gemini_response.split('\n')
        
        for line in lines:
            line = line.strip()
            # Match numbered items (1., 2., etc.) or bullets (-, *, •)
            if line and (
                line[0].isdigit() or 
                line.startswith('-') or 
                line.startswith('*') or 
                line.startswith('•')
            ):
                # Clean up the line
                cleaned = line.lstrip('0123456789.-*• ').strip()
                if len(cleaned) > 10:  # Meaningful content
                    risk_factors.append(cleaned)
        
        return risk_factors[:4]  # Return up to 4 factors


# Global instance
gemini_client = GeminiClient()
