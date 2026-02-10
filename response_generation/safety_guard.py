class SafetyGuard:
    def __init__(self):
        self.prohibited_words = ["die", "kill", "suicide", "hurt myself"]
        
    def is_safe(self, text):
        """
         Checks if the text contains prohibited content using whole-word matching.
        """
        import re
        text = text.lower()
        for word in self.prohibited_words:
            # Use regex to match whole words only (e.g., 'die' but not 'studies')
            if re.search(r'\b' + re.escape(word) + r'\b', text):
                return False, "Unsafe content detected."
        return True, ""

    def sanitize_output(self, text):
        """
        Ensures output doesn't contain hallucinated medical advice.
        (Simplified logic)
        """
        disclaimer = " [Disclaimer: I am an AI, not a doctor.]"
        if "diagnose" in text or "prescription" in text:
            return text + disclaimer
        return text
