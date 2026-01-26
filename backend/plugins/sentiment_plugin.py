# =============================================================================
# Sentiment Analysis Plugin
# =============================================================================
#
# Analyzes the sentiment of posts and agent responses.
# Can be used to flag negative content or track mood trends.
#
# =============================================================================

from plugins import Plugin, PluginMetadata, PluginHook, hook
from typing import Dict, Any


class SentimentPlugin(Plugin):
    """Analyzes sentiment in posts and responses"""

    metadata = PluginMetadata(
        name="sentiment",
        version="1.0.0",
        description="Analyzes sentiment of posts and agent responses",
        author="Agent Twitter Team",
        enabled=True,
    )

    def __init__(self):
        super().__init__()
        self.sentiment_scores: Dict[str, float] = {}

    def _analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Simple sentiment analysis (can be enhanced with NLP library)"""
        positive_words = [
            "good",
            "great",
            "awesome",
            "excellent",
            "happy",
            "love",
            "wonderful",
            "amazing",
            "best",
            "fantastic",
            "thanks",
        ]
        negative_words = [
            "bad",
            "terrible",
            "awful",
            "hate",
            "worst",
            "horrible",
            "sad",
            "angry",
            "upset",
            "disappointed",
            "error",
            "fail",
        ]

        text_lower = text.lower()
        words = text_lower.split()

        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)

        total = positive_count + negative_count
        if total == 0:
            score = 0.5  # Neutral
        else:
            score = (positive_count + 1) / (total + 2)  # Normalized 0-1

        sentiment = "neutral"
        if score > 0.6:
            sentiment = "positive"
        elif score < 0.4:
            sentiment = "negative"

        return {
            "score": score,
            "sentiment": sentiment,
            "positive_words": positive_count,
            "negative_words": negative_count,
        }

    @hook(PluginHook.ON_POST_CREATE)
    def analyze_post_sentiment(
        self, post_id: str, text: str, author_id: str
    ) -> Dict[str, Any]:
        """Analyze sentiment of new posts"""
        result = self._analyze_sentiment(text)
        self.sentiment_scores[post_id] = result["score"]

        # Add metadata to post
        return {"sentiment": result, "post_id": post_id}

    @hook(PluginHook.ON_AGENT_RESPONSE)
    def analyze_agent_sentiment(
        self, agent_name: str, response: str, post_id: str
    ) -> Dict[str, Any]:
        """Analyze sentiment of agent responses"""
        result = self._analyze_sentiment(response)

        return {"agent": agent_name, "sentiment": result, "post_id": post_id}

    def get_sentiment_stats(self) -> Dict[str, Any]:
        """Get overall sentiment statistics"""
        if not self.sentiment_scores:
            return {"message": "No data yet"}

        scores = list(self.sentiment_scores.values())
        avg_sentiment = sum(scores) / len(scores)

        positive_count = sum(1 for s in scores if s > 0.6)
        negative_count = sum(1 for s in scores if s < 0.4)

        return {
            "average": avg_sentiment,
            "total_analyzed": len(scores),
            "positive": positive_count,
            "negative": negative_count,
            "neutral": len(scores) - positive_count - negative_count,
        }
