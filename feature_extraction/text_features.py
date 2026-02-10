import numpy as np

class TextFeatureExtractor:
    def __init__(self, model_name='bert-base-uncased'):
        self.tokenizer = None
        self.model = None
        try:
            # Removed forced mock
            
            from transformers import BertTokenizer, BertModel
            import torch
            # Use Standard BERT instead of MentalBERT (Gated)
            model_name = 'bert-base-uncased'
            self.tokenizer = BertTokenizer.from_pretrained(model_name)
            self.model = BertModel.from_pretrained(model_name)
            self.model.eval() # Set to evaluation mode
            self.torch = torch
        except ImportError:
             print("Warning: Transformers/Torch not found (or mocked). Text features will be mocked.")

    def get_embedding(self, text):
        """
        Returns the CLS token embedding for the input text.
        """
        if self.model is None:
            # Return random or zero vector of size 768 (BERT size)
            # Use deterministic seed for consistency if needed
            return np.ones(768) * 0.1

        with self.torch.no_grad():
            inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=128)
            outputs = self.model(**inputs)
            # CLS token is at index 0
            cls_embedding = outputs.last_hidden_state[:, 0, :].numpy()
            
        return cls_embedding.flatten()
