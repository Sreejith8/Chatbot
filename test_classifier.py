"""
Quick verification test for the new Late Decision Fusion pipeline.
Run: python test_classifier.py
"""
from classification.hybrid_classifier import HybridClassifier

def run_tests():
    cf = HybridClassifier()

    print("\n" + "="*60)
    print("TEST 1: Text='I am stressed about my studies', Video=sad face")
    result = cf.predict(
        text="I am stressed about my studies",
        video_emotion_dict={"Sad": 0.55, "Neutral": 0.30, "Fear": 0.10, "Happy": 0.05},
        audio_features=None
    )
    top = sorted(result.items(), key=lambda x: -x[1])[:4]
    print(f"Result: {top}")
    winner = top[0][0] if top else "None"
    print(f"Detected state: {winner}")
    assert winner in ("Stress", "Depression", "Sadness", "Anxiety"), f"Expected negative state, got {winner}"
    print("PASS ✓")

    print("\n" + "="*60)
    print("TEST 2: Text='I feel so hopeless', Video=angry")
    result = cf.predict(
        text="I feel so hopeless and empty",
        video_emotion_dict={"Angry": 0.10, "Sad": 0.70, "Neutral": 0.20},
        audio_features=None
    )
    top = sorted(result.items(), key=lambda x: -x[1])[:4]
    print(f"Result: {top}")
    winner = top[0][0] if top else "None"
    print(f"Detected state: {winner}")
    assert winner in ("Depression", "Sadness", "Anxiety"), f"Expected depression-type state, got {winner}"
    print("PASS ✓")

    print("\n" + "="*60)
    print("TEST 3: Text=empty, Video=scared face")
    result = cf.predict(
        text="",
        video_emotion_dict={"Fear": 0.65, "Neutral": 0.25, "Sad": 0.10},
        audio_features=None
    )
    top = sorted(result.items(), key=lambda x: -x[1])[:4]
    print(f"Result: {top}")
    winner = top[0][0] if top else "None"
    print(f"Detected state: {winner}")
    assert winner in ("Anxiety", "Stress", "Fear"), f"Expected anxiety/stress, got {winner}"
    print("PASS ✓")

    print("\n" + "="*60)
    print("All tests passed!")

if __name__ == "__main__":
    run_tests()
