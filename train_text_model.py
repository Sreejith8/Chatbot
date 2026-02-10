
import pandas as pd
import numpy as np
import os
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from feature_extraction.text_features import TextFeatureExtractor
from tqdm import tqdm  # Progress bar

# Configuration
DATASET_PATH = "dataset.csv"  # Place your dataset here
MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "rf_emotion.pkl")

def train_emotion_model():
    print("--- Emotion Model Training Script ---")
    
    # 1. Load Dataset
    if not os.path.exists(DATASET_PATH):
        print(f"Error: Dataset not found at '{DATASET_PATH}'.")
        print("Please place a CSV file with 'text' and 'emotion' columns in the project root.")
        return

    print("Loading dataset...")
    try:
        df = pd.read_csv(DATASET_PATH)
        # Normalize column names
        df.columns = [c.lower() for c in df.columns]
        
        if 'text' not in df.columns or 'emotion' not in df.columns:
            # Try to infer if names are different (e.g., 'content', 'label')
            if 'content' in df.columns: df.rename(columns={'content': 'text'}, inplace=True)
            if 'label' in df.columns: df.rename(columns={'label': 'emotion'}, inplace=True)
            if 'sentiment' in df.columns: df.rename(columns={'sentiment': 'emotion'}, inplace=True)
            
        if 'text' not in df.columns or 'emotion' not in df.columns:
             print("Error: Dataset must have 'text' and 'emotion' columns.")
             return
             
        # Filter supported emotions if needed, or map them
        print(f"Dataset loaded: {len(df)} samples.")
        print(f"Emotions found: {df['emotion'].unique()}")
        
    except Exception as e:
        print(f"Failed to read dataset: {e}")
        return

    # 2. Extract Features (BERT)
    print("\nExtracting Features (BERT Embeddings)... This may take a while.")
    extractor = TextFeatureExtractor()
    
    X = []
    y = []
    
    # Progress bar for extraction
    for index, row in tqdm(df.iterrows(), total=df.shape[0]):
        try:
            text = str(row['text'])
            emotion = str(row['emotion'])
            
            # Get BERT embedding (768-dim vector)
            embedding = extractor.get_embedding(text)
            
            X.append(embedding)
            y.append(emotion)
        except Exception as e:
            # Skip bad rows
            continue
            
    X = np.array(X)
    y = np.array(y)
    
    print(f"Features extracted. Shape: {X.shape}")

    # 3. Train/Test Split
    print("\nSplitting data...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 4. Train Model (Random Forest)
    print("Training Random Forest Classifier...")
    rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
    rf_model.fit(X_train, y_train)

    # 5. Evaluate
    print("\nEvaluating Model...")
    y_pred = rf_model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"Accuracy: {accuracy:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))

    # 6. Save Model
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)
        
    print(f"Saving model to {MODEL_PATH}...")
    joblib.dump(rf_model, MODEL_PATH)
    print("Model saved successfully!")
    print("\nNext Steps: Restart the application to load the new model.")

if __name__ == "__main__":
    train_emotion_model()
