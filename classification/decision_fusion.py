class DecisionFusion:
    def __init__(self):
        pass

    def fuse_decisions(self, text_pred, audio_pred=None, visual_pred=None):
        """
        Late Fusion: Combine probabilities from different independent classifiers 
        (if we had separate classifiers for each modality instead of one feature vector).
        
        For this architecture, we primarily use Early Fusion (concatenating features),
        but this module is kept for ensemble voting if needed.
        """
        # Weighted average example
        # final_score = (text_pred * 0.5) + (audio_pred * 0.3) + (visual_pred * 0.2)
        
        return text_pred # Fallback to text only for now
