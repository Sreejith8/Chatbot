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
                self.rf_model = joblib.load(rf_path)
                print("[Classifier] Loaded RF Audio Model.")
            except Exception as e:
                print(f"[Classifier] RF Audio load failed: {e}")

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

        # Priority 2: Zero-Shot with mental health labels
        try:
            if self.zero_shot_classifier is None:
                from transformers import pipeline
                self.zero_shot_classifier = pipeline(
                    "zero-shot-classification",
                    model="facebook/bart-large-mnli"
                )
            result = self.zero_shot_classifier(text, MENTAL_HEALTH_LABELS)
            return dict(zip(result['labels'], result['scores']))
        except Exception as e:
            print(f"[Classifier] Zero-shot failed: {e}")

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
        # Step 1: Independent text classification
        text_probs = self._classify_text(text)
        print(f"[Classifier] Text probs: {dict(sorted(text_probs.items(), key=lambda x: -x[1])[:3])}")

        # Step 2: Late Decision Fusion across all modalities
        final_scores = self.decision_fusion.fuse_decisions(
            text_probs=text_probs,
            audio_features=audio_features,
            video_emotion_dict=video_emotion_dict
        )
        print(f"[Classifier] Fused scores: {dict(sorted(final_scores.items(), key=lambda x: -x[1])[:3])}")

        return final_scores

    def train(self, X, y):
        pass
