
import os
import pandas as pd
import numpy as np
import joblib
from sklearn.metrics import classification_report, confusion_matrix
from feature_extraction.text_features import TextFeatureExtractor
from input_preprocessing.audio_processor import AudioProcessor
import glob
from tqdm import tqdm

# Configuration
TEXT_DATASET = "dataset.csv"
AUDIO_DATASET = "dataset/audio"
MODEL_DIR = "models"

def evaluate_text_model():
    print("\n--- Evaluating Text Model ---")
    
    # 1. Determine Model Type
    model_path_rf = os.path.join(MODEL_DIR, "rf_emotion.pkl")
    model_path_bert = os.path.join(MODEL_DIR, "custom_bert")
    
    model = None
    model_type = None
    
    # Check for BERT first
    if os.path.exists(model_path_bert):
        print(f"Found Fine-Tuned BERT at {model_path_bert}")
        try:
            from transformers import pipeline
            model = pipeline("text-classification", model=model_path_bert, return_all_scores=False)
            model_type = "bert"
        except Exception as e:
            print(f"Failed to load BERT pipeline: {e}")
            
    # Check for RF if BERT not loaded
    if not model and os.path.exists(model_path_rf):
        print(f"Found Random Forest at {model_path_rf}")
        model = joblib.load(model_path_rf)
        model_type = "rf"
        
    if not model:
        print("No trained text model found (neither 'rf_emotion.pkl' nor 'custom_bert').")
        return

    # 2. Load Data
    if not os.path.exists(TEXT_DATASET):
        print(f"Dataset '{TEXT_DATASET}' not found. Cannot evaluate.")
        return
        
    try:
        df = pd.read_csv(TEXT_DATASET)
        # Normalize columns
        df.columns = [c.lower() for c in df.columns]
        if 'content' in df.columns: df.rename(columns={'content': 'text'}, inplace=True)
        if 'sentiment' in df.columns: df.rename(columns={'sentiment': 'emotion'}, inplace=True)
        
        if 'text' not in df.columns or 'emotion' not in df.columns:
            print("Invalid dataset format. Needs 'text' and 'emotion' columns.")
            return
            
        print(f"Evaluating on {len(df)} samples...")
        
        y_true = df['emotion'].tolist()
        y_pred = []
        
        # 3. Predict
        if model_type == "rf":
            extractor = TextFeatureExtractor()
            print("Extracting features (BERT embeddings)...")
            X = []
            valid_indices = []
            for idx, text in tqdm(enumerate(df['text']), total=len(df)):
                try:
                    emb = extractor.get_embedding(str(text))
                    X.append(emb)
                    valid_indices.append(idx)
                except:
                    pass
            
            if not X:
                print("Feature extraction failed.")
                return
                
            X = np.array(X)
            y_true = [y_true[i] for i in valid_indices] # Align
            
            print("Predicting (Random Forest)...")
            y_pred = model.predict(X)
            
        elif model_type == "bert":
            print("Predicting (Full BERT)...")
            texts = [str(t)[:512] for t in df['text']]  # Truncate
            
            # Batch prediction if possible, or sequential
            results = model(texts)
            # Result format: [{'label': 'LABEL', 'score': 0.9}, ...]
            y_pred = [r['label'] for r in results]

        # 4. Metrics
        print("\n=== Text Model Classification Report ===")
        print(classification_report(y_true, y_pred))
        
        print("\n=== Confusion Matrix ===")
        print(confusion_matrix(y_true, y_pred))
        
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

    print("Loading model...")
    model = joblib.load(model_path)
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
                # print(f"Error {f}: {e}")
                pass
                
    if not X:
        print("No valid audio features extracted.")
        return
        
    X = np.array(X)
    print(f"Predicting on {len(X)} samples...")
    y_pred = model.predict(X)
    
    print("\n=== Audio Model Classification Report ===")
    print(classification_report(y_true, y_pred))
    
    print("\n=== Confusion Matrix ===")
    cm = confusion_matrix(y_true, y_pred)
    # Print labels with CM
    unique_labels = sorted(list(set(y_true)))
    print(f"Labels: {unique_labels}")
    print(cm)

if __name__ == "__main__":
    evaluate_text_model()
    evaluate_audio_model()
