import os
import pandas as pd
import numpy as np
import joblib
from sklearn.metrics import classification_report, confusion_matrix
from input_preprocessing.audio_processor import AudioProcessor
import glob
from tqdm import tqdm

# Configuration
TEXT_DATASET = "dataset/text/dataset_7_classes.csv"
AUDIO_DATASET = "dataset/audio"
MODEL_DIR = "models"

def evaluate_text_model():
    print("\n--- Evaluating Text Model ---")
    
    model_path_rf = os.path.join(MODEL_DIR, "rf_emotion.pkl")
    
    if not os.path.exists(model_path_rf):
        print(f"No trained text model found at {model_path_rf}")
        return

    print(f"Found Custom Text Model at {model_path_rf}")
    loaded_data = joblib.load(model_path_rf)
    
    if isinstance(loaded_data, dict) and 'model' in loaded_data:
        model = loaded_data['model']
        vectorizer = loaded_data.get('vectorizer')
    else:
        print("Error: Text Model is not in the updated dictionary format with a vectorizer.")
        return

    if not os.path.exists(TEXT_DATASET):
        print(f"Dataset '{TEXT_DATASET}' not found. Cannot evaluate.")
        return
        
    try:
        df = pd.read_csv(TEXT_DATASET)
        df = df.dropna(subset=['text', 'emotion'])
        df['text'] = df['text'].astype(str)
        
        print(f"Evaluating on {len(df)} samples...")
        
        y_true = df['emotion'].tolist()
        
        print("Extracting features (TF-IDF Vectorizer)...")
        # Apply the exact same vectorizer used during training
        X = vectorizer.transform(df['text'])
        
        print("Predicting (Logistic Regression / LinearSVC)...")
        y_pred = model.predict(X)

        # 4. Metrics
        print("\n=== Text Model Classification Report ===")
        print(classification_report(y_true, y_pred))
        
        print("\n=== Confusion Matrix ===")
        print(confusion_matrix(y_true, y_pred))
        unique_labels = sorted(list(set(y_true)))
        print(f"Labels: {unique_labels}")
        
    except Exception as e:
        print(f"Evaluation failed: {e}")

def evaluate_audio_model():
    print("\n--- Evaluating Audio Model ---")
    
    model_path = os.path.join(MODEL_DIR, "rf_audio.pkl")
    if not os.path.exists(model_path):
        print("No trained audio model found ('rf_audio.pkl').")
        return
        
    if not os.path.exists(AUDIO_DATASET):
        print(f"Audio dataset directory '{AUDIO_DATASET}' not found.")
        return

    print("Loading model and scaler...")
    loaded_data = joblib.load(model_path)
    if isinstance(loaded_data, dict) and 'model' in loaded_data:
        model = loaded_data['model']
        scaler = loaded_data.get('scaler')
    else:
        print("Error: Audio Model is not in the updated dictionary format with a scaler.")
        return

    processor = AudioProcessor()
    
    X = []
    y_true = []
    
    # Iterate folders
    classes = [d for d in os.listdir(AUDIO_DATASET) if os.path.isdir(os.path.join(AUDIO_DATASET, d))]
    print(f"Classes found: {classes}")
    
    if not classes:
        print("No emotion subfolders found.")
        return

    print("Extracting features (this may take time)...")
    for label in classes:
        folder = os.path.join(AUDIO_DATASET, label)
        wav_files = glob.glob(os.path.join(folder, "*.wav"))
        print(f"Processing {label}: {len(wav_files)} files...")
        
        for f in tqdm(wav_files):
            try:
                feat = processor.extract_prosodic_features(f)
                # Check for zero vector (failure)
                if np.any(feat):
                    X.append(feat)
                    y_true.append(label)
            except Exception as e:
                pass
                
    if not X:
        print("No valid audio features extracted.")
        return
        
    X = np.array(X)
    print(f"Predicting on {len(X)} samples...")
    
    if scaler is not None:
        X = scaler.transform(X)
        
    y_pred = model.predict(X)
    
    print("\n=== Audio Model Classification Report ===")
    print(classification_report(y_true, y_pred))
    
    print("\n=== Confusion Matrix ===")
    cm = confusion_matrix(y_true, y_pred)
    unique_labels = sorted(list(set(y_true)))
    print(f"Labels: {unique_labels}")
    print(cm)

if __name__ == "__main__":
    evaluate_text_model()
    evaluate_audio_model()
