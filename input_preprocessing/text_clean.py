import re
import html

class TextPreprocessor:
    @staticmethod
    def clean_text(text):
        """
        Cleans raw input text: reports, HTML, special chars.
        """
        if not text:
            return ""
        
        # Decode HTML entities
        text = html.unescape(text)
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
        
        # Remove special characters but keep punctuation relevant for emotion (?!.)
        text = re.sub(r'[^a-zA-Z0-9\s.,!?\'"]', '', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text.lower()
