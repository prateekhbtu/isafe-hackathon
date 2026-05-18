"""
NewsAPI Client
Integrates with NewsAPI.org to verify credibility of text/image claims
by cross-referencing against 150,000+ news sources.
"""
import os
import httpx
from typing import Dict, Any, Optional, List
from urllib.parse import quote_plus
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()


class NewsAPIClient:
    """Client for verifying content credibility via NewsAPI.org"""

    BASE_URL = "https://newsapi.org/v2"

    def __init__(self):
        self.api_key = os.getenv("NEWSAPI_KEY", "")
        self.timeout = 10.0  # Keep short for Render free tier

    def is_available(self) -> bool:
        """Check if NewsAPI key is configured"""
        return bool(self.api_key)

    async def search_related_articles(
        self,
        query: str,
        from_date: Optional[str] = None,
        sort_by: str = "relevancy",
        page_size: int = 5,
    ) -> Optional[Dict[str, Any]]:
        """
        Search for articles related to the query using /v2/everything

        Args:
            query: Search keywords (extracted claims or key phrases)
            from_date: ISO date string to search from (default: 30 days ago)
            sort_by: Sort order - relevancy, popularity, publishedAt
            page_size: Number of results (keep small for speed)

        Returns:
            Dict with articles and metadata, or None on failure
        """
        if not self.is_available():
            return None

        if not from_date:
            from_date = (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")

        params = {
            "q": query[:256],  # API limit
            "from": from_date,
            "sortBy": sort_by,
            "pageSize": min(page_size, 10),  # Cap at 10 to stay lightweight
            "apiKey": self.api_key,
            "language": "en",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.BASE_URL}/everything", params=params)

                if response.status_code == 200:
                    data = response.json()
                    return {
                        "status": data.get("status"),
                        "total_results": data.get("totalResults", 0),
                        "articles": self._sanitize_articles(
                            data.get("articles", [])
                        ),
                    }
                elif response.status_code == 426:
                    # Free tier limitation - too old date range
                    return None
                else:
                    print(f"NewsAPI error: {response.status_code} - {response.text[:200]}")
                    return None

        except Exception as e:
            print(f"NewsAPI request error: {e}")
            return None

    async def get_top_headlines(
        self,
        query: Optional[str] = None,
        country: str = "us",
        category: Optional[str] = None,
        page_size: int = 5,
    ) -> Optional[Dict[str, Any]]:
        """
        Get top headlines using /v2/top-headlines

        Args:
            query: Optional search keyword
            country: Country code (us, gb, in, etc.)
            category: Category filter (business, technology, science, health, etc.)
            page_size: Number of results

        Returns:
            Dict with headline articles, or None on failure
        """
        if not self.is_available():
            return None

        params = {
            "apiKey": self.api_key,
            "pageSize": min(page_size, 10),
        }

        if query:
            params["q"] = query[:256]
        if country:
            params["country"] = country
        if category:
            params["category"] = category

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    f"{self.BASE_URL}/top-headlines", params=params
                )

                if response.status_code == 200:
                    data = response.json()
                    return {
                        "status": data.get("status"),
                        "total_results": data.get("totalResults", 0),
                        "articles": self._sanitize_articles(
                            data.get("articles", [])
                        ),
                    }
                return None

        except Exception as e:
            print(f"NewsAPI headlines error: {e}")
            return None

    async def verify_claim(self, text: str) -> Dict[str, Any]:
        """
        Verify a text claim by extracting key phrases and cross-referencing
        against news sources.

        Args:
            text: The text content to verify

        Returns:
            Credibility assessment with source evidence
        """
        if not self.is_available():
            return {
                "newsapi_available": False,
                "credibility_score": None,
                "message": "NewsAPI not configured",
            }

        # Extract key phrases for search (simplified NLP)
        search_queries = self._extract_search_queries(text)

        if not search_queries:
            return {
                "newsapi_available": True,
                "credibility_score": None,
                "message": "Could not extract searchable claims from text",
                "queries_tried": [],
            }

        all_articles = []
        source_names = set()
        queries_tried = []

        for query in search_queries[:3]:  # Max 3 queries to stay fast
            result = await self.search_related_articles(
                query=query, page_size=5, sort_by="relevancy"
            )

            if result and result.get("articles"):
                all_articles.extend(result["articles"])
                for article in result["articles"]:
                    src = article.get("source", {}).get("name")
                    if src:
                        source_names.add(src)
                queries_tried.append(
                    {"query": query, "results_found": result.get("total_results", 0)}
                )
            else:
                queries_tried.append({"query": query, "results_found": 0})

        # Also check top headlines for breaking news context
        headline_result = await self.get_top_headlines(
            query=search_queries[0] if search_queries else None, page_size=3
        )
        headline_matches = 0
        if headline_result and headline_result.get("articles"):
            headline_matches = len(headline_result["articles"])
            all_articles.extend(headline_result["articles"])
            for article in headline_result["articles"]:
                src = article.get("source", {}).get("name")
                if src:
                    source_names.add(src)

        # Calculate credibility score
        credibility = self._calculate_credibility(
            total_articles=len(all_articles),
            unique_sources=len(source_names),
            headline_matches=headline_matches,
            text=text,
        )

        # Deduplicate articles by URL
        seen_urls = set()
        unique_articles = []
        for article in all_articles:
            url = article.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_articles.append(article)

        return {
            "newsapi_available": True,
            "credibility_score": credibility["score"],
            "credibility_level": credibility["level"],
            "credibility_reasoning": credibility["reasoning"],
            "corroborating_sources": len(source_names),
            "total_related_articles": len(unique_articles),
            "headline_matches": headline_matches,
            "top_sources": list(source_names)[:10],
            "sample_articles": unique_articles[:5],
            "queries_tried": queries_tried,
        }

    async def reverse_image_search_context(
        self, image_context: str
    ) -> Optional[Dict[str, Any]]:
        """
        For images: search news for context about what the image claims to show.

        Args:
            image_context: Descriptive text about the image (from user or OCR)

        Returns:
            Related news articles for context verification
        """
        if not image_context or not self.is_available():
            return None

        return await self.search_related_articles(
            query=image_context, page_size=5, sort_by="relevancy"
        )

    def _extract_search_queries(self, text: str) -> List[str]:
        """
        Extract meaningful search queries from text content.
        Uses simple heuristic extraction - no heavy NLP.

        Args:
            text: Raw text content

        Returns:
            List of search query strings
        """
        import re

        queries = []

        # Clean the text
        clean_text = re.sub(r"[^\w\s.,!?'\"-]", " ", text)
        clean_text = re.sub(r"\s+", " ", clean_text).strip()

        # Strategy 1: Use the first substantial sentence as primary query
        sentences = re.split(r"[.!?]+", clean_text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

        if sentences:
            # Take first sentence, truncate to reasonable length
            first_sentence = sentences[0][:150]
            queries.append(first_sentence)

        # Strategy 2: Extract named entities / capitalized phrases
        # Simple heuristic: consecutive capitalized words (likely proper nouns)
        caps_pattern = re.findall(r"(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)", text)
        for phrase in caps_pattern[:2]:
            if len(phrase) > 5 and phrase not in queries:
                queries.append(phrase)

        # Strategy 3: Extract quoted text (often claims)
        quoted = re.findall(r'"([^"]{10,100})"', text)
        for q in quoted[:1]:
            if q not in queries:
                queries.append(q)

        # Strategy 4: If still no queries, use first 100 chars
        if not queries and len(clean_text) > 10:
            queries.append(clean_text[:100])

        return queries

    def _calculate_credibility(
        self,
        total_articles: int,
        unique_sources: int,
        headline_matches: int,
        text: str,
    ) -> Dict[str, Any]:
        """
        Calculate a credibility score based on corroboration evidence.

        Higher score = more credible (more sources corroborate).
        Lower score = less credible (no corroboration found).

        Returns:
            Dict with score (0-100), level, and reasoning
        """
        score = 50  # Start neutral
        reasons = []

        # Factor 1: Number of corroborating articles
        if total_articles == 0:
            score -= 25
            reasons.append("No corroborating news articles found from major sources")
        elif total_articles <= 2:
            score -= 10
            reasons.append(
                f"Limited corroboration: only {total_articles} related article(s) found"
            )
        elif total_articles <= 5:
            score += 10
            reasons.append(
                f"Moderate corroboration: {total_articles} related articles found"
            )
        else:
            score += 20
            reasons.append(
                f"Strong corroboration: {total_articles}+ related articles from news sources"
            )

        # Factor 2: Source diversity
        if unique_sources == 0:
            score -= 15
            reasons.append("No reputable news sources covering this topic")
        elif unique_sources >= 3:
            score += 15
            reasons.append(
                f"Multiple independent sources ({unique_sources}) reporting on this topic"
            )
        elif unique_sources >= 1:
            score += 5
            reasons.append(
                f"Some source diversity: {unique_sources} source(s) found"
            )

        # Factor 3: Headline presence (breaking news)
        if headline_matches > 0:
            score += 10
            reasons.append(
                f"Topic appears in {headline_matches} current headline(s) - actively reported"
            )

        # Clamp score
        score = max(0, min(100, score))

        # Determine level
        if score >= 70:
            level = "High"
        elif score >= 40:
            level = "Medium"
        else:
            level = "Low"

        return {
            "score": score,
            "level": level,
            "reasoning": "; ".join(reasons),
        }

    def _sanitize_articles(self, articles: list) -> list:
        """
        Strip unnecessary fields from articles to reduce response size.

        Args:
            articles: Raw articles from NewsAPI

        Returns:
            Sanitized article list with only essential fields
        """
        sanitized = []
        for article in articles:
            sanitized.append(
                {
                    "source": {
                        "name": article.get("source", {}).get("name", "Unknown")
                    },
                    "title": article.get("title", ""),
                    "description": (article.get("description") or "")[:200],
                    "url": article.get("url", ""),
                    "publishedAt": article.get("publishedAt", ""),
                }
            )
        return sanitized


# Global instance
newsapi_client = NewsAPIClient()
