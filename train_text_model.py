import pandas as pd
import numpy as np
import os
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

# Configuration
DATASET_PATH = "dataset/text/dataset_7_classes.csv"  # The exactly 7-class Kaggle CSV
MODEL_DIR = "models"
MODEL_PATH = os.path.join(MODEL_DIR, "rf_emotion.pkl")

def train_emotion_model():
    print("--- Emotion Model Training Script (Maximizing Accuracy) ---")
    
    # 1. Load Dataset
    if not os.path.exists(DATASET_PATH):
        print(f"Error: Dataset not found at '{DATASET_PATH}'.")
        return

    print("Loading dataset...")
    try:
        df = pd.read_csv(DATASET_PATH)
        # Ensure text is string and drop NaNs
        df = df.dropna(subset=['text', 'emotion'])
        df['text'] = df['text'].astype(str)
        
        print(f"Dataset loaded: {len(df)} samples.")
        print(f"Emotions found: {df['emotion'].unique()}")
    except Exception as e:
        print(f"Failed to read dataset: {e}")
        return

    # 1.5 Physical Data Oversampling
    # The mathematical ceiling is caused by severe data imbalance (e.g. thousands of 'Normal' vs 100 'Stress').
    print("\nBalancing Dataset via Physical Oversampling...")
    max_size = df['emotion'].value_counts().max()
    
    balanced_frames = []
    for emotion_type, group in df.groupby('emotion'):
        # Duplicate the minority rows until they match the massive majority class
        oversampled_group = group.sample(max_size, replace=True, random_state=42)
        balanced_frames.append(oversampled_group)
        
    df = pd.concat(balanced_frames).sample(frac=1, random_state=42).reset_index(drop=True)
    print(f"Balanced Dataset Size: {len(df)} samples (Classes are now mathematically equal).")

    # 2. Extract Features (TF-IDF Vectorization)
    print("\nExtracting Features using Advanced TF-IDF Vectorizer...")
    # Since dataset is physically huge now, we cap features to keep RAM safe
    vectorizer = TfidfVectorizer(max_features=20000, ngram_range=(1,2), sublinear_tf=True, stop_words='english')
    
    X = vectorizer.fit_transform(df['text'])
    y = df['emotion']
    
    print(f"Features extracted. Shape: {X.shape}")

    # 3. Train/Test Split
    print("\nSplitting data...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.1, random_state=42)

    # 4. Train Model 
    print("Training Optimized Linear Model (Logistic Regression)...")
    # Switch back to Logistic Regression. Neural Networks overfit on oversampled data, SVM gets too slow.
    from sklearn.linear_model import LogisticRegression
    # class_weight='balanced' is no longer needed since the physical data is balanced!
    model = LogisticRegression(max_iter=3000, n_jobs=-1, random_state=42)
    model.fit(X_train, y_train)

    # 5. Evaluate
    print("\nEvaluating Model...")
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    print(f"\nAccuracy: {accuracy:.4f} ({(accuracy * 100):.1f}%)")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))

    # 6. Save Model AND Vectorizer as a bundle
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)
        
    print(f"Saving model and TF-IDF vectorizer to {MODEL_PATH}...")
    model_data = {
        'model': model,
        'vectorizer': vectorizer
    }
    joblib.dump(model_data, MODEL_PATH)
    print("Model saved successfully!")
    print("\nNext Steps: Restart the application to load the new optimized model.")

if __name__ == "__main__":
    train_emotion_model()
