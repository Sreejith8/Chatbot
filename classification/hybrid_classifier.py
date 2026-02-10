import numpy as np
import os
import joblib
# from xgboost import XGBClassifier
# from sklearn.ensemble import RandomForestClassifier

class HybridClassifier:
    def __init__(self, model_dir='models'):
        self.model_dir = model_dir
        self.rf_model = None
        self.xgb_model = None
        # self.dl_model = ... (PyTorch model)
        
        # Load models if they exist, else warn
        self._load_models()

        if os.path.exists(os.path.join(self.model_dir, 'custom_bert')):
            try:
                from transformers import pipeline
                self.custom_bert_pipeline = pipeline("text-classification", model=os.path.join(self.model_dir, 'custom_bert'), return_all_scores=True)
                print("Loaded Custom Fine-Tuned BERT Model.")
            except Exception as e:
                print(f"Failed to load custom BERT: {e}")
                self.custom_bert_pipeline = None
        else:
            self.custom_bert_pipeline = None

    def _load_models(self):
        rf_path = os.path.join(self.model_dir, 'rf_emotion.pkl')
        if os.path.exists(rf_path):
            self.rf_model = joblib.load(rf_path)

    def predict(self, feature_vector, text=None):
        """
        Input: Concatenated feature vector, optional text.
        Output: Probabilities for each class.
        """
        # 1. Priority: Custom Fine-Tuned Model
        if self.custom_bert_pipeline and text:
            try:
                # Pipeline output: [[{'label': 'Sadness', 'score': 0.9}, ...]]
                results = self.custom_bert_pipeline(text)[0]
                prediction = {res['label']: res['score'] for res in results}
                return prediction
            except Exception as e:
                print(f"BERT prediction failed: {e}")

        # 2. Random Forest (Manual Training)
        if self.rf_model is not None:
             try:
                proba = self.rf_model.predict_proba([feature_vector])[0]
                classes = self.rf_model.classes_
                return dict(zip(classes, proba))
             except Exception as e:
                print(f"RF prediction failed: {e}")

        # 3. Fallback: Zero-Shot
        try:
            from transformers import pipeline
            if not hasattr(self, 'zero_shot_classifier'):
                    self.zero_shot_classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
            
            if text:
                candidate_labels = ["Depression", "Anxiety", "Bipolar", "ADHD", "Normal", "Sadness", "Stress"]
                result = self.zero_shot_classifier(text, candidate_labels)
                return dict(zip(result['labels'], result['scores']))
        except Exception as e:
            print(f"Zero-shot failed: {e}")
            
        return {"Normal": 1.0}

    def train(self, X, y):
        pass
