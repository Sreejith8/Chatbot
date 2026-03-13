"""
hybrid_classifier.py
Simplified orchestrator per SDD architecture.
Delegates actual fusion and classification to DecisionFusion (late fusion).
Runs the Zero-Shot text classifier for text modality.
"""
import os
import joblib
import numpy as np
from classification.decision_fusion import DecisionFusion, MENTAL_HEALTH_LABELS


class HybridClassifier:
    def __init__(self, model_dir='models'):
        self.model_dir = model_dir
        self.decision_fusion = DecisionFusion()
        self.zero_shot_classifier = None
        self.custom_bert_pipeline = None
        self.rf_model = None  # Audio Random Forest (optional)
        self.text_rf_model = None
        self.text_extractor = None

        self._load_models()

    def _load_models(self):
        # Load custom fine-tuned BERT if available
        bert_path = os.path.join(self.model_dir, 'custom_bert')
        if os.path.exists(bert_path):
            try:
                from transformers import pipeline
                self.custom_bert_pipeline = pipeline(
                    "text-classification",
                    model=bert_path,
                    return_all_scores=True
                )
                print("[Classifier] Loaded Custom Fine-Tuned BERT.")
            except Exception as e:
                print(f"[Classifier] Custom BERT load failed: {e}")

        # Load audio RF model if available
        rf_path = os.path.join(self.model_dir, 'rf_audio.pkl')
        if os.path.exists(rf_path):
            try:
                loaded_data = joblib.load(rf_path)
                if isinstance(loaded_data, dict) and 'model' in loaded_data:
                    self.rf_model = loaded_data['model']
                    self.audio_scaler = loaded_data.get('scaler')
                else:
                    self.rf_model = loaded_data
                    self.audio_scaler = None
                print("[Classifier] Loaded RF Audio Model and Preprocessors.")
            except Exception as e:
                print(f"[Classifier] RF Audio load failed: {e}")
                
        # Load text RF model if available
        text_rf_path = os.path.join(self.model_dir, 'rf_emotion.pkl')
        if os.path.exists(text_rf_path):
            try:
                loaded_data = joblib.load(text_rf_path)
                if isinstance(loaded_data, dict) and 'model' in loaded_data:
                    self.text_rf_model = loaded_data['model']
                    self.text_scaler = loaded_data.get('scaler')
                    self.text_vectorizer = loaded_data.get('vectorizer')
                else:
                    self.text_rf_model = loaded_data
                    self.text_scaler = None
                    self.text_vectorizer = None
                print("[Classifier] Loaded Custom RF Text Model and Preprocessors.")
            except Exception as e:
                print(f"[Classifier] Custom RF Text load failed: {e}")

    def _classify_text(self, text):
        """
        Run text through a mental-health-aware classifier.
        Returns dict of {mental_state: probability}
        """
        if not text or not text.strip():
            return {}

        # Priority 1: Custom fine-tuned BERT on mental health data
        if self.custom_bert_pipeline:
            try:
                results = self.custom_bert_pipeline(text)[0]
                return {r['label']: r['score'] for r in results}
            except Exception as e:
                print(f"[Classifier] Custom BERT failed: {e}")
                
        # Priority 1.5: Custom Text Model (Random Forest or Logistic Regression)
        if self.text_rf_model:
            try:
                if hasattr(self, 'text_vectorizer') and self.text_vectorizer is not None:
                    # High Accuracy TF-IDF pipeline completely skips BERT
                    emb_array = self.text_vectorizer.transform([text])
                else:
                    # Legacy BERT embedding pipeline
                    if self.text_extractor is None:
                        from feature_extraction.text_features import TextFeatureExtractor
                        self.text_extractor = TextFeatureExtractor()
                    embedding = self.text_extractor.get_embedding(text)
                    emb_array = np.array([embedding])
                    if hasattr(self, 'text_scaler') and self.text_scaler is not None:
                        emb_array = self.text_scaler.transform(emb_array)
                        
                probs = self.text_rf_model.predict_proba(emb_array)[0]
                classes = self.text_rf_model.classes_
                return dict(zip(classes, probs))
            except Exception as e:
                print(f"[Classifier] Custom Text Model prediction failed: {e}")

        # Priority 2: Zero-Shot with mental health labels
        try:
            if self.zero_shot_classifier is None:
                from transformers import pipeline
                self.zero_shot_classifier = pipeline(
                    "zero-shot-classification",
                    model="facebook/bart-large-mnli"
                )
            
            # Predict only clinical/active states independently (multi_label=True)
            clinical_labels = [l for l in MENTAL_HEALTH_LABELS if l != "Normal"]
            result = self.zero_shot_classifier(text, clinical_labels, multi_label=True)
            
            # Apply dynamic thresholds. Rare/severe conditions need much higher confidence to trigger 
            # than common conditions to prevent false-positives on neutral sentences.
            raw_probs = dict(zip(result['labels'], result['scores']))
            probs = {}
            for label, score in raw_probs.items():
                 if label in ["Bipolar", "ADHD"]:
                      # Extremely high threshold required for rare diagnoses
                      probs[label] = score if score > 0.85 else 0.0
                 elif label in ["Depression", "Anxiety", "Fear", "Angry"]:
                      # High threshold for significant conditions
                      probs[label] = score if score > 0.60 else 0.0
                 else:
                      # Default threshold for common states like Stress, Sadness
                      probs[label] = score
            
            # Dynamically assign "Normal" based on the absence of strong clinical indicators
            max_clinical_score = max(probs.values()) if probs else 0.0
            if max_clinical_score < 0.4:
                probs["Normal"] = 1.0 - max_clinical_score
            else:
                probs["Normal"] = 0.1
                
            return {k: v for k, v in probs.items() if v > 0}
        except Exception as e:
            print(f"[Classifier] Zero-shot failed: {e}")

        return {}

    def _classify_audio(self, audio_features):
        """
        Run raw PNCC audio features through the trained Random Forest model.
        Returns dict of {mental_state: probability}
        """
        if self.rf_model is None or audio_features is None or np.all(audio_features == 0):
            return {}

        try:
            # Reshape for single prediction
            emb_array = np.array([audio_features])
            
            # Apply scaler
            if hasattr(self, 'audio_scaler') and self.audio_scaler is not None:
                emb_array = self.audio_scaler.transform(emb_array)
                
            probs = self.rf_model.predict_proba(emb_array)[0]
            classes = self.rf_model.classes_
            return dict(zip(classes, probs))
        except Exception as e:
            print(f"[Classifier] Audio ML prediction failed: {e}")
            return {}

    def predict(self, text=None, video_emotion_dict=None, audio_features=None):
        """
        Per-SDD: each modality is classified independently, then late-fused.

        Args:
            text             (str):   Transcribed or typed user text
            video_emotion_dict (dict): Raw DeepFace output {"Sad": 0.6, "Neutral": 0.3}
            audio_features   (ndarray): 15-dim prosodic feature vector

        Returns:
            dict of {mental_state: probability}
        """
        # Step 1: Independent text and audio classification
        text_probs = self._classify_text(text)
        print(f"[Classifier] Text probs: {dict(sorted(text_probs.items(), key=lambda x: -x[1])[:3])}")
        
        audio_probs = self._classify_audio(audio_features)
        if audio_probs:
            print(f"[Classifier] Audio ML probs: {dict(sorted(audio_probs.items(), key=lambda x: -x[1])[:3])}")

        # Step 2: Late Decision Fusion across all modalities
        final_scores = self.decision_fusion.fuse_decisions(
            text_probs=text_probs,
            audio_probs=audio_probs,
            video_emotion_dict=video_emotion_dict,
            audio_features=audio_features
        )
        print(f"[Classifier] Fused scores: {dict(sorted(final_scores.items(), key=lambda x: -x[1])[:3])}")

        return final_scores

    def train(self, X, y):
        pass
