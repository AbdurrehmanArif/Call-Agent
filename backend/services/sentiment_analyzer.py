"""
Sentiment analysis service.
"""
from typing import Tuple, Dict
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from backend.utils.config import config


class SentimentAnalyzer:
    """Analyze sentiment of text."""

    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
        self.negative_threshold = config.NEGATIVE_SENTIMENT_THRESHOLD
        self.positive_threshold = config.POSITIVE_SENTIMENT_THRESHOLD

    def analyze(self, text: str) -> Dict[str, float]:
        """
        Get sentiment scores for text.

        Args:
            text: Text to analyze

        Returns:
            Dict with neg, neu, pos, compound scores
        """
        scores = self.analyzer.polarity_scores(text)
        return scores

    def get_sentiment_label(self, text: str) -> Tuple[str, float]:
        """
        Get sentiment label and score.

        Args:
            text: Text to analyze

        Returns:
            Tuple of (label, compound_score)
        """
        scores = self.analyze(text)
        compound = scores["compound"]

        if compound <= self.negative_threshold:
            label = "negative"
        elif compound >= self.positive_threshold:
            label = "positive"
        else:
            label = "neutral"

        return label, compound

    def is_escalation_needed(self, text: str) -> bool:
        """
        Check if sentiment indicates need for escalation.

        Args:
            text: Text to analyze

        Returns:
            True if escalation may be needed
        """
        scores = self.analyze(text)

        # Highly negative sentiment
        if scores["compound"] < -0.6:
            return True

        # High anger specifically
        if scores["neg"] > 0.7:
            return True

        return False

    def analyze_conversation(self, messages: list) -> Dict:
        """
        Analyze sentiment across a conversation.

        Args:
            messages: List of message dicts with "text" key

        Returns:
            Aggregated sentiment analysis
        """
        if not messages:
            return {"overall": "neutral", "trend": "stable", "scores": {}}

        scores_list = [self.analyze(msg.get("text", "")) for msg in messages]

        # Calculate average scores
        avg_scores = {
            "neg": sum(s["neg"] for s in scores_list) / len(scores_list),
            "neu": sum(s["neu"] for s in scores_list) / len(scores_list),
            "pos": sum(s["pos"] for s in scores_list) / len(scores_list),
            "compound": sum(s["compound"] for s in scores_list) / len(scores_list),
        }

        # Determine trend (comparing first half to second half)
        if len(scores_list) >= 2:
            mid = len(scores_list) // 2
            first_half_compound = sum(s["compound"] for s in scores_list[:mid]) / mid
            second_half_compound = sum(s["compound"] for s in scores_list[mid:]) / (len(scores_list) - mid)

            if second_half_compound > first_half_compound + 0.1:
                trend = "improving"
            elif second_half_compound < first_half_compound - 0.1:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "stable"

        # Overall label
        if avg_scores["compound"] <= self.negative_threshold:
            overall = "negative"
        elif avg_scores["compound"] >= self.positive_threshold:
            overall = "positive"
        else:
            overall = "neutral"

        return {
            "overall": overall,
            "trend": trend,
            "scores": avg_scores,
            "message_count": len(messages)
        }


# Singleton instance
sentiment_analyzer = SentimentAnalyzer()
