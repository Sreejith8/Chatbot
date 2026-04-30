import numpy as np

class FeatureFusion:
    @staticmethod
    def CalculateTextReliability(text_features):
        if text_features is None or len(text_features) == 0: return 0.0
        features = np.array(text_features)
        density = np.count_nonzero(features) / max(1.0, float(len(features)))
        return float(min(1.0, max(0.1, density)))

    @staticmethod
    def CalculateAudioReliability(audio_features):
        if audio_features is None or len(audio_features) == 0: return 0.0
        features = np.array(audio_features)
        var = np.var(features)
        return float(min(1.0, max(0.1, var)))

    @staticmethod
    def CalculateVisualReliability(visual_features):
        if not visual_features: return 0.0
        if isinstance(visual_features, dict):
            return float(min(1.0, max(0.1, sum(visual_features.values()))))
        return 1.0

    @staticmethod
    def fuse_features(text_features=None, audio_features=None, visual_features=None):
        """
        Attention/Reliability-based Feature Fusion: 
        Calculates dynamic modality weights before combination.
        Expected Sizes: Text=768, Audio=15, Video=7 -> Total=790
        """
        # Apply attention weights based on modality reliability
        textWeight = FeatureFusion.CalculateTextReliability(text_features)
        audioWeight = FeatureFusion.CalculateAudioReliability(audio_features)
        visualWeight = FeatureFusion.CalculateVisualReliability(visual_features)

        # Define expected dimensions
        DIM_TEXT = 768
        DIM_AUDIO = 15
        DIM_VIDEO = 7
        
        # 1. Text Features
        if text_features is None:
            vec_text = np.zeros(DIM_TEXT)
        else:
            vec_text = np.array(text_features)
            if vec_text.shape[0] != DIM_TEXT:
                # Resize/Pad if mismatch (e.g. if using different embedding)
                temp = np.zeros(DIM_TEXT)
                limit = min(DIM_TEXT, vec_text.shape[0])
                temp[:limit] = vec_text[:limit]
                vec_text = temp

        # 2. Audio Features
        if audio_features is None:
            vec_audio = np.zeros(DIM_AUDIO)
        else:
            vec_audio = np.array(audio_features)
            if vec_audio.shape[0] != DIM_AUDIO:
                temp = np.zeros(DIM_AUDIO)
                limit = min(DIM_AUDIO, vec_audio.shape[0])
                temp[:limit] = vec_audio[:limit]
                vec_audio = temp

        # 3. Video Features (Probabilities)
        if visual_features is None:
            vec_video = np.zeros(DIM_VIDEO)
        else:
            # visual_features is expected to be a dict or list
            if isinstance(visual_features, dict):
                 # Fixed order: Angry, Disgust, Fear, Happy, Sad, Surprise, Neutral
                 order = ["Angry", "Disgust", "Fear", "Happy", "Sad", "Surprise", "Neutral"]
                 vec_video = np.array([visual_features.get(k, 0.0) for k in order])
            else:
                 vec_video = np.array(visual_features)
                 
            if vec_video.shape[0] != DIM_VIDEO:
                temp = np.zeros(DIM_VIDEO)
                limit = min(DIM_VIDEO, vec_video.shape[0])
                temp[:limit] = vec_video[:limit]
                vec_video = temp

        # Apply weighted combination
        vec_text = textWeight * vec_text
        vec_audio = audioWeight * vec_audio
        vec_video = visualWeight * vec_video
        
        # Apply dimensionality reduction if needed
        # (In this architecture, concatenation implies a flat vector representation to be reduced by subsequent ML layers)
        fused = np.concatenate([vec_text, vec_audio, vec_video])
        return fused
