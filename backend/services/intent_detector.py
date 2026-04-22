"""
Intent detection service using rule-based and ML approaches.
"""
import re
from typing import Tuple, Optional, List, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
import joblib
from pathlib import Path


class IntentDetector:
    """Detect user intent from text."""

    # Predefined intents with keywords
    INTENT_PATTERNS = {
        "greeting": [
            r"\b(hi|hello|hey|good morning|good afternoon|good evening)\b",
            r"\bhow are you\b",
        ],
        "goodbye": [
            r"\b(bye|goodbye|see you|take care|have a good day)\b",
        ],
        "support": [
            r"\b(help|support|issue|problem|error|not working|broken)\b",
            r"\bneed assistance\b",
        ],
        "inquiry": [
            r"\b(what|when|where|how|why|can you|do you)\b",
            r"\btell me about\b",
            r"\bi want to know\b",
        ],
        "complaint": [
            r"\b(unhappy|dissatisfied|complaint|frustrated|angry|disappointed)\b",
            r"\bthis is unacceptable\b",
        ],
        "confirmation": [
            r"\b(yes|yeah|yep|sure|okay|ok|correct|right)\b",
        ],
        "denial": [
            r"\b(no|nope|nah|incorrect|wrong|not really)\b",
        ],
        "escalation": [
            r"\b(speak to manager|talk to supervisor|human agent|real person)\b",
            r"\btransfer me\b",
        ],
        "account": [
            r"\b(account|login|password|reset|update|change email)\b",
        ],
        "billing": [
            r"\b(bill|payment|charge|refund|invoice|pricing|cost)\b",
        ],
    }

    def __init__(self, model_path: str = None):
        self.model_path = model_path or Path(__file__).parent.parent / "models" / "intent_model.pkl"
        self.model: Optional[Pipeline] = None
        self._load_model()

    def _load_model(self):
        """Load trained model if available."""
        try:
            if Path(self.model_path).exists():
                self.model = joblib.load(self.model_path)
        except Exception:
            self.model = None

    def detect(self, text: str) -> Tuple[str, float]:
        """
        Detect intent from text.

        Args:
            text: User input text

        Returns:
            Tuple of (intent_label, confidence_score)
        """
        text_lower = text.lower()

        # Rule-based detection first (high confidence matches)
        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return intent, 0.9

        # ML-based detection if model available
        if self.model:
            try:
                prediction = self.model.predict([text])[0]
                proba = self.model.predict_proba([text])[0].max()
                return prediction, float(proba)
            except Exception:
                pass

        # Default fallback
        return "general", 0.5

    def detect_multiple(self, texts: List[str]) -> List[Tuple[str, float]]:
        """Detect intents for multiple texts."""
        return [self.detect(text) for text in texts]

    def train(self, training_data: List[Dict[str, str]]):
        """
        Train the intent detection model.

        Args:
            training_data: List of {"text": str, "intent": str} dicts
        """
        texts = [item["text"] for item in training_data]
        labels = [item["intent"] for item in training_data]

        self.model = Pipeline([
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_features=5000)),
            ("clf", MultinomialNB())
        ])

        self.model.fit(texts, labels)

        # Save model
        Path(self.model_path).parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self.model, self.model_path)

    def get_all_intents(self) -> List[str]:
        """Get list of all known intents."""
        return list(self.INTENT_PATTERNS.keys())


# Singleton instance
intent_detector = IntentDetector()
