import sys
import os
import random
import numpy as np
import pandas as pd
from sklearn.metrics import classification_report, accuracy_score, precision_recall_fscore_support

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

from classification.decision_fusion import DecisionFusion, MENTAL_HEALTH_LABELS

def evaluate_video_logic(mock_test_size=100):
    """
    Evaluates the Video Emotion Extraction mapping logic.
    In a real scenario, you iterate through FER-2013 image folders and run DeepFace.analyze().
    Here we simulate the DeepFace raw extraction to demonstrate the mapping accuracy.
    """
    print("\n" + "="*50)
    print("🎬 EVALUATING VIDEO MODALITY (DEEPFACE + MAPPING)")
    print("="*50)
    
    fusion_engine = DecisionFusion()
    
    # Ground truth mapping expectation
    # DeepFace "Sad" -> Should map to "Depression" or "Sadness"
    # DeepFace "Fear" -> Should map to "Anxiety"
    test_cases = [
        ({"Sad": 0.8, "Neutral": 0.2}, "Depression"),
        ({"Fear": 0.7, "Surprise": 0.3}, "Anxiety"),
        ({"Angry": 0.9, "Disgust": 0.1}, "Stress"),
        ({"Happy": 0.85, "Neutral": 0.15}, "Normal"),
        ({"Neutral": 0.9, "Sad": 0.1}, "Normal")
    ]
    
    # Generate larger test set from templates
    y_true = []
    y_pred = []
    
    print(f"Running evaluation on {mock_test_size} video frame benchmarks...")
    for _ in range(mock_test_size):
        case = random.choice(test_cases)
        deepface_output = case[0]
        true_label = case[1]
        
        # 1. Map raw face emotion to Mental Health state
        mh_probs = fusion_engine.map_facial_to_mental_health(deepface_output)
        
        # 2. Get highest probability
        if mh_probs:
            predicted_label = max(mh_probs, key=mh_probs.get)
        else:
            predicted_label = "Normal"
            
        y_true.append(true_label)
        y_pred.append(predicted_label)
        
    print("\n--- Video Modality Classification Report ---")
    print(classification_report(y_true, y_pred, zero_division=0))
    print(f"Overall Video Accuracy: {accuracy_score(y_true, y_pred)*100:.2f}%")


def evaluate_hybrid_fusion(mock_test_size=200):
    """
    Evaluates the Late-Decision Fusion Engine.
    Demonstrates how intersecting modalities override single-modality false positives.
    """
    print("\n" + "="*50)
    print("🧠 EVALUATING HYBRID FUSION MULTIMODAL ENGINE")
    print("="*50)
    
    fusion_engine = DecisionFusion()
    
    y_true = []
    y_pred_text_only = []
    y_pred_video_only = []
    y_pred_fusion = []
    
    print(f"Running multi-modal conflict resolution tests on {mock_test_size} benchmarks...")
    
    for _ in range(mock_test_size):
        # We simulate scenarios where Text, Audio, and Video have slightly conflicting confidence.
        # Example 1: True Label is Depression.
        # Text says Depression (0.6), Video says Sad (0.8), Audio says Low Pitch (0.7)
        # The Fusion should confidently lock in Depression.
        
        scenarios = [
            {
                "true_label": "Depression",
                "text": {"Depression": 0.55, "Sadness": 0.3},
                "video": {"Sad": 0.8, "Neutral": 0.2},
                "audio": np.array([0]*13 + [0.05, 0.02]) # Pitch 0.05, Energy 0.02 -> Low/Low = Depressed contour
            },
            {
                "true_label": "Anxiety",
                "text": {"Anxiety": 0.45, "Stress": 0.45}, # Text is unsure
                "video": {"Fear": 0.7, "Surprise": 0.2},   # Video shows Fear (Anxiety mapping)
                "audio": np.array([0]*13 + [0.15, 0.08]) # High pitch/energy
            },
            {
                # Edge Case: The user implies they are fine (Text: Normal), but Voice/Video show severe stress
                "true_label": "Stress",
                "text": {"Normal": 0.7, "Stress": 0.1},
                "video": {"Angry": 0.6, "Disgust": 0.4},
                "audio": np.array([0]*13 + [0.06, 0.09]) # Stress prosody
            }
        ]
        
        case = random.choice(scenarios)
        true_label = case["true_label"]
        
        # Standalone Text Prediction
        pred_text = max(case["text"], key=case["text"].get)
        
        # Standalone Video Prediction
        vid_mapped = fusion_engine.map_facial_to_mental_health(case["video"])
        pred_vid = max(vid_mapped, key=vid_mapped.get) if vid_mapped else "Normal"
        
        # HYBRID FUSION PREDICTION
        # The engine mathematically weighs Text (0.55), Video (0.30), and Audio (0.15)
        fusion_probs = fusion_engine.fuse_decisions(
            text_probs=case["text"],
            video_emotion_dict=case["video"],
            audio_features=case["audio"]
        )
        pred_fusion = max(fusion_probs, key=fusion_probs.get) if fusion_probs else "Normal"
        
        y_true.append(true_label)
        y_pred_text_only.append(pred_text)
        y_pred_video_only.append(pred_vid)
        y_pred_fusion.append(pred_fusion)

    print("\n--- Independent Text Accuracy ---")
    print(f"{accuracy_score(y_true, y_pred_text_only)*100:.2f}%")
    
    print("\n--- Independent Video Accuracy ---")
    print(f"{accuracy_score(y_true, y_pred_video_only)*100:.2f}%")
    
    print("\n--- HYBRID FUSION ENGINE ACCURACY ---")
    print(f"{accuracy_score(y_true, y_pred_fusion)*100:.2f}%")
    print("\nHybrid Fusion Classification Report:")
    print(classification_report(y_true, y_pred_fusion, zero_division=0))

if __name__ == "__main__":
    evaluate_video_logic()
    evaluate_hybrid_fusion()
