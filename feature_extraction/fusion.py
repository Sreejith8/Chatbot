import numpy as np

class FeatureFusion:
    @staticmethod
    def fuse_features(text_features=None, audio_features=None, visual_features=None):
        """
        Early fusion: Concatenates available feature vectors.
        Handles missing modalities by padding with zeros or using specific flags (simplified here).
        """
        vectors = []
        
        if text_features is not None:
            vectors.append(text_features)
        
        if audio_features is not None:
             # Normalize audio if needed, skipped for brevity
            vectors.append(audio_features)
            
        if visual_features is not None:
            # Visual features can be large (1400+), might need PCA reduction in real world
            # For now, we append raw or a reduced version
            vectors.append(visual_features)
            
        if not vectors:
            return None
            
        return np.concatenate(vectors)
