"""
decision_fusion.py
Implements Late-Decision Fusion as specified in the SRS/SDD.

Architecture:
  Text  → Independent Classifier (Zero-Shot) → Mental Health Probabilities ─┐
  Video → DeepFace → Mapping Matrix           → Mental Health Probabilities ─┼→ Weighted Vote → Final State
  Audio → Prosody Features → Rule-Based       → Mental Health Probabilities ─┘
"""

# ─── Facial Emotion → Mental Health Mapping Matrix ───────────────────────────
# Based on clinical psychology literature mapping basic emotions to mental states.
# Each basic emotion distributes probability across mental health categories.
FACIAL_TO_MH_MAP = {
    "Sad":     {"Depression": 0.55, "Sadness": 0.25, "Stress": 0.15, "Normal": 0.05},
    "Angry":   {"Stress": 0.55,    "Anxiety": 0.25, "Angry": 0.10,  "Normal": 0.10},
    "Fear":    {"Anxiety": 0.65,   "Stress":  0.20, "Depression": 0.10, "Normal": 0.05},
    "Happy":   {"Normal": 0.85,    "Happy":   0.15},
    "Surprise":{"Anxiety": 0.35,   "Normal":  0.55, "Stress": 0.10},
    "Disgust": {"Stress": 0.45,    "Normal":  0.40, "Anxiety": 0.15},
    # Neutral is mapped last resort — should not drive the final state
    # Weight lowered significantly so it doesn't overpower genuine negative emotions
    "Neutral": {"Normal": 0.30},
}

# Mental health states recognized by the CBT engine
MENTAL_HEALTH_LABELS = [
    "Depression", "Anxiety", "Stress", "Sadness",
    "Bipolar", "ADHD", "Normal", "Angry", "Fear", "Happy"
]

# ─── Audio Prosody → Mental Health heuristic rules ───────────────────────────
def map_audio_to_mental_health(audio_features):
    """
    Maps raw prosodic feature vector to mental health probabilities.
    audio_features: numpy array of shape (15,) — [MFCCs x13, Pitch, Energy]
    Uses simple heuristic rules since we don't have a trained audio RF model.
    """
    import numpy as np
    if audio_features is None or np.all(audio_features == 0):
        return {}

    # Feature indices: 0-12 = MFCCs, 13 = Pitch (ZCR), 14 = Energy (RMS)
    pitch  = float(audio_features[13]) if len(audio_features) > 13 else 0
    energy = float(audio_features[14]) if len(audio_features) > 14 else 0

    # Low energy + low pitch → Depression/Sadness heuristic
    if energy < 0.002 and pitch < 0.05:
        return {"Depression": 0.45, "Sadness": 0.35, "Normal": 0.20}
    # High energy + high pitch → Anxiety/Stress
    elif energy > 0.05 and pitch > 0.15:
        return {"Anxiety": 0.40, "Stress": 0.40, "Normal": 0.20}
    # High energy + low pitch → Anger/Stress
    elif energy > 0.05 and pitch < 0.05:
        return {"Stress": 0.50, "Angry": 0.30, "Normal": 0.20}
    # Default — mood ambiguous from prosody alone (e.g. empty audio file)
    else:
        # Weak fallback so empty audio doesn't force a 'Normal' diagnosis
        return {"Normal": 0.20}


class DecisionFusion:
    """
    Late-Fusion module per SDD.
    Each modality produces an INDEPENDENT probability distribution over mental
    health states, then a dynamic weighted vote produces the final prediction.
    """

    # Weights: Text (always most reliable), Video (strong signal), Audio prosody
    WEIGHTS = {
        "text":  0.55,  # Spoken / typed words are most semantically rich
        "video": 0.30,  # Facial expressions add strong emotional cues
        "audio": 0.15,  # Prosody alone is weakest signal without ASR
    }

    def map_facial_to_mental_health(self, video_emotion_dict):
        """
        Converts DeepFace basic emotion dict → mental health probability dict.
        video_emotion_dict: e.g. {"Sad": 0.6, "Neutral": 0.3, "Happy": 0.1}
        Returns: {"Depression": X, "Anxiety": Y, ...}
        """
        if not video_emotion_dict:
            return {}

        # Accumulate weighted contributions from each detected basic emotion
        mh_probs = {}
        for basic_emotion, confidence in video_emotion_dict.items():
            if basic_emotion not in FACIAL_TO_MH_MAP:
                continue
            mapping = FACIAL_TO_MH_MAP[basic_emotion]
            for mh_state, fraction in mapping.items():
                contribution = confidence * fraction
                mh_probs[mh_state] = mh_probs.get(mh_state, 0.0) + contribution

        # Normalize so they sum to 1
        total = sum(mh_probs.values())
        if total > 0:
            mh_probs = {k: v / total for k, v in mh_probs.items()}

        return mh_probs

    def fuse_decisions(self, text_probs, audio_features=None, video_emotion_dict=None):
        """
        Main fusion entry point (Late Fusion — per SDD).

        Args:
            text_probs       (dict): Mental health probabilities from text ZeroShot
            audio_features   (np.array): Raw 15-dim prosodic feature vector
            video_emotion_dict (dict): Raw DeepFace output {"Sad": 0.7, "Neutral": 0.3}

        Returns:
            dict: Final fused mental health probabilities
        """
        modality_outputs = []

        # ── Modality 1: Text ──────────────────────────────────────────────────
        if text_probs:
            modality_outputs.append(("text", text_probs))

        # ── Modality 2: Facial (Video) ────────────────────────────────────────
        if video_emotion_dict:
            video_mh = self.map_facial_to_mental_health(video_emotion_dict)
            if video_mh:
                modality_outputs.append(("video", video_mh))

        # ── Modality 3: Audio Prosody ─────────────────────────────────────────
        audio_mh = map_audio_to_mental_health(audio_features)
        if audio_mh:
            modality_outputs.append(("audio", audio_mh))

        if not modality_outputs:
            return {"Normal": 1.0}

        # ── Dynamic Re-weighting (only weight available modalities) ───────────
        available_weight_total = sum(self.WEIGHTS[m] for m, _ in modality_outputs)

        # ── Weighted Vote ─────────────────────────────────────────────────────
        fused = {}
        all_states = set()
        for _, probs in modality_outputs:
            all_states.update(probs.keys())

        for state in all_states:
            score = 0.0
            for modality, probs in modality_outputs:
                w = self.WEIGHTS[modality] / available_weight_total
                score += probs.get(state, 0.0) * w
            if score > 0:
                fused[state] = score

        return fused
