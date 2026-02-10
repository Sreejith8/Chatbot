import re
from collections import Counter

class HeuristicSummarizer:
    def __init__(self):
        # Basic stop words list to avoid NLTK dependency/download issues
        self.stop_words = set([
            "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", "yours",
            "he", "him", "his", "she", "her", "hers", "it", "its", "they", "them", "their",
            "what", "which", "who", "whom", "this", "that", "these", "those", "am", "is", "are",
            "was", "were", "be", "been", "being", "have", "has", "had", "having", "do", "does",
            "did", "doing", "a", "an", "the", "and", "but", "if", "or", "because", "as", "until",
            "while", "of", "at", "by", "for", "with", "about", "against", "between", "into",
            "through", "during", "before", "after", "above", "below", "to", "from", "up", "down",
            "in", "out", "on", "off", "over", "under", "again", "further", "then", "once", "here",
            "there", "when", "where", "why", "how", "all", "any", "both", "each", "few", "more",
            "most", "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so",
            "than", "too", "very", "can", "will", "just", "don't", "should", "now", "feel", "feeling"
        ])

    def generate_summary(self, messages, detected_state="Neutral"):
        """
        Generates a summary string based on keywords and state.
        
        Args:
            messages (list): List of message dicts/objects with 'content_text'
            detected_state (str): The final or predominant state of the session
        """
        text_content = " ".join([m.content_text for m in messages if m.sender == 'user'])
        
        # Normalize and tokenize
        words = re.findall(r'\b\w+\b', text_content.lower())
        
        # Filter stopwords and short words
        keywords = [w for w in words if w not in self.stop_words and len(w) > 3]
        
        # Get top 3
        top_keywords = [w for w, c in Counter(keywords).most_common(3)]
        
        topic_str = ", ".join(top_keywords) if top_keywords else "General conversation"
        
        summary = f"Topic: {topic_str} | State: {detected_state}"
        return summary
