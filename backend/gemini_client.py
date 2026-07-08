"""
Gemini API Client

Supports TWO ways of reaching Gemini, in priority order:

  1. Direct Google Generative Language API using an API key.
     The key can come from the GEMINI_API_KEY env var, or be supplied
     per-request by the user (bring-your-own-key / BYOK).

  2. A self-hosted Gemini proxy (GEMINI_API_URL) exposing /health and
     /generate. Used as a fallback when no API key is available.

When a request carries the user's own API key, that key is always
preferred over the hosted URL.
"""
import os
import httpx
from typing import Dict, Any, Optional
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Google Generative Language API (direct, API-key access)
GOOGLE_GENAI_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
)
DEFAULT_GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")


class GeminiClient:
    """Client for interacting with Gemini, via direct API key or a hosted proxy."""

    def __init__(self):
        self.base_url = os.getenv("GEMINI_API_URL", "")
        self.api_key = os.getenv("GEMINI_API_KEY", "")
        self.default_model = DEFAULT_GEMINI_MODEL
        self.timeout = 30.0

    def is_available(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> bool:
        """
        Check whether Gemini can be reached with the given (optional) overrides.

        A direct API key (per-request or env) is assumed usable — its validity
        is verified at call time to avoid an extra round-trip on every request.
        Otherwise fall back to a reachability check against the hosted proxy.
        """
        if (api_key or self.api_key or "").strip():
            return True

        url = (base_url or self.base_url or "").strip()
        if not url:
            return False
        try:
            response = httpx.get(f"{url}/health", timeout=5.0)
            return response.status_code == 200
        except Exception:
            return False

    async def generate(
        self,
        prompt: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Optional[str]:
        """
        Send a prompt to Gemini and return the text response.

        Prefers a direct API key (per-request or env) and falls back to the
        hosted proxy. Returns None if neither is configured or the call fails.
        """
        key = (api_key or self.api_key or "").strip()
        if key:
            return await self._generate_direct(prompt, key, (model or self.default_model))

        url = (base_url or self.base_url or "").strip()
        if url:
            return await self._generate_hosted(prompt, url)

        return None

    async def _generate_direct(
        self, prompt: str, api_key: str, model: str
    ) -> Optional[str]:
        """Call Google's Generative Language API directly with an API key."""
        endpoint = GOOGLE_GENAI_ENDPOINT.format(model=model)
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    endpoint,
                    params={"key": api_key},
                    json={"contents": [{"parts": [{"text": prompt}]}]},
                    timeout=self.timeout,
                )

                if response.status_code == 200:
                    data = response.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        texts = [p.get("text", "") for p in parts if p.get("text")]
                        if texts:
                            return "".join(texts)
                    return None

                print(
                    f"Gemini direct API error: HTTP {response.status_code} - "
                    f"{response.text[:200]}"
                )
                return None
        except Exception as e:
            print(f"Gemini direct API error: {str(e)}")
            return None

    async def _generate_hosted(self, prompt: str, base_url: str) -> Optional[str]:
        """Call the self-hosted Gemini proxy (/generate)."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{base_url}/generate",
                    json={"text": prompt},
                    timeout=self.timeout,
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
        metadata: Dict[str, Any],
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Use Gemini to analyze detected signals and provide additional insights.

        Args:
            modality: Type of media (image, video, audio, text)
            signals: List of detected signals
            metadata: Context metadata
            api_key: Optional per-request Gemini API key (BYOK)
            base_url: Optional per-request hosted proxy URL
            model: Optional per-request Gemini model name

        Returns:
            Gemini analysis with risk factors and additional signals
        """
        if not self.is_available(api_key=api_key, base_url=base_url):
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

        response = await self.generate(
            prompt, api_key=api_key, base_url=base_url, model=model
        )

        if not response:
            return None

        # Parse Gemini response
        return {
            "gemini_analysis": response,
            "gemini_available": True,
            "additional_context": self._extract_risk_factors(response)
        }

    async def verify_text_content(
        self,
        text: str,
        metadata: Dict[str, Any],
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Use Gemini to verify text content for misinformation patterns.

        Args:
            text: Text content to analyze
            metadata: Context metadata
            api_key: Optional per-request Gemini API key (BYOK)
            base_url: Optional per-request hosted proxy URL
            model: Optional per-request Gemini model name

        Returns:
            Gemini verification results
        """
        if not self.is_available(api_key=api_key, base_url=base_url):
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

        response = await self.generate(
            prompt, api_key=api_key, base_url=base_url, model=model
        )

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
