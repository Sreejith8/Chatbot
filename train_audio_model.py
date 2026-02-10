
import os
import joblib
import numpy as np
import glob
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from input_preprocessing.audio_processor import AudioProcessor
from collections import Counter

# Configuration
DATASET_ROOT = "dataset/audio"  # Assuming structure: dataset/audio/happy/*.wav
MODEL_PATH = "models/rf_audio.pkl"

def train_audio_model():
    print("--- Audio Emotion Model Training ---")
    
    # 1. Check Directories
    if not os.path.exists(DATASET_ROOT):
        print(f"Error: Dataset directory '{DATASET_ROOT}' not found.")
        print("Please create subfolders for each emotion (e.g., 'dataset/audio/happy').")
        os.makedirs(DATASET_ROOT, exist_ok=True)
        return

    processor = AudioProcessor()
    X = []
    y = []

    # 2. Iterate Subfolders
    classes = [d for d in os.listdir(DATASET_ROOT) if os.path.isdir(os.path.join(DATASET_ROOT, d))]
    
    if not classes:
        print("No emotion subfolders found inside dataset/audio.")
        return

    print(f"Found classes: {classes}")

    for label in classes:
        folder_path = os.path.join(DATASET_ROOT, label)
        wav_files = glob.glob(os.path.join(folder_path, "*.wav"))
        print(f"Processing {label}: {len(wav_files)} files...")
        
        for file_path in wav_files:
            try:
                features = processor.extract_prosodic_features(file_path)
                # Check for validity (zeros usually imply failure/silence)
                if np.all(features == 0):
                    continue
                    
                X.append(features)
                y.append(label)
            except Exception as e:
                print(f"Skipping {file_path}: {e}")

    X = np.array(X)
    y = np.array(y)

    if len(X) == 0:
        print("No valid features extracted. Exiting.")
        return

    print(f"Training on {len(X)} samples with {X.shape[1]} features.")
    print(f"Class distribution: {Counter(y)}")

    # 3. Train/Test Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 4. Train Random Forest
    rf = RandomForestClassifier(n_estimators=100, random_state=42)
    rf.fit(X_train, y_train)

    # 5. Evaluate
    accuracy = rf.score(X_test, y_test)
    print(f"Test Accuracy: {accuracy:.4f}")

    # 6. Save Model
    if not os.path.exists("models"):
        os.makedirs("models")
        
    joblib.dump(rf, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")

if __name__ == "__main__":
    train_audio_model()
