import os
import joblib
import numpy as np
import pandas as pd
import glob
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from input_preprocessing.audio_processor import AudioProcessor
from collections import Counter
from sklearn.metrics import classification_report, accuracy_score

# Configuration
DATASET_ROOT = "dataset/audio"  # Assuming structure: dataset/audio/happy/*.wav
MODEL_PATH = "models/rf_audio.pkl"

def train_audio_model():
    print("--- Audio Emotion Model Training (Optimized) ---")
    
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

    print(f"\nExtracted {len(X)} valid audio samples across {X.shape[1]} features.")
    print(f"Original class distribution: {Counter(y)}")

    # 3. Physical Data Oversampling (Balance Classes)
    print("\nBalancing Dataset via Physical Oversampling...")
    df = pd.DataFrame(X)
    df['emotion'] = y
    max_size = df['emotion'].value_counts().max()
    
    balanced_frames = []
    for emotion_type, group in df.groupby('emotion'):
        oversampled_group = group.sample(max_size, replace=True, random_state=42)
        balanced_frames.append(oversampled_group)
        
    df_balanced = pd.concat(balanced_frames).sample(frac=1, random_state=42).reset_index(drop=True)
    
    X_balanced = df_balanced.drop('emotion', axis=1).values
    y_balanced = df_balanced['emotion'].values
    print(f"Balanced Dataset Size: {len(X_balanced)} samples.")

    # 4. Train/Test Split
    X_train, X_test, y_train, y_test = train_test_split(X_balanced, y_balanced, test_size=0.2, random_state=42)

    # 5. Scale the Features (Mandatory for overlapping prosodic ranges)
    print("Scaling Features (StandardScaler)...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # 6. Train Random Forest (15 dense continuous features are perfect for RF)
    print("Training Balanced Random Forest Classifier...")
    rf_model = RandomForestClassifier(n_estimators=200, max_depth=20, random_state=42)
    rf_model.fit(X_train_scaled, y_train)

    # 7. Evaluate
    print("\nEvaluating Model...")
    y_pred = rf_model.predict(X_test_scaled)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"\nAccuracy: {accuracy:.4f} ({(accuracy * 100):.1f}%)")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))

    # 8. Save Model and Scaler bundle
    if not os.path.exists("models"):
        os.makedirs("models")
        
    model_data = {
        'model': rf_model,
        'scaler': scaler
    }
    joblib.dump(model_data, MODEL_PATH)
    print(f"Model and Scaler successfully bundled and saved to {MODEL_PATH}")

if __name__ == "__main__":
    train_audio_model()
