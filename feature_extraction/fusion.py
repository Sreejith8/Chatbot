import numpy as np

class FeatureFusion:
    @staticmethod
    def fuse_features(text_features=None, audio_features=None, visual_features=None):
        """
        Early Fusion: Concatenates available feature vectors.
        Standardizes missing modalities with zero-padding.
        Expected Sizes: Text=768, Audio=15, Video=7 -> Total=790
        """
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

        # Concatenate
        return np.concatenate([vec_text, vec_audio, vec_video])
