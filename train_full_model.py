
import os
import pandas as pd
import numpy as np
import torch
from sklearn.model_selection import train_test_split
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification, Trainer, TrainingArguments
from transformers import EarlyStoppingCallback

# Configuration
DATASET_PATH = "dataset.csv"
MODEL_DIR = "models/custom_bert"
NUM_EPOCHS = 3
BATCH_SIZE = 8

class EmotionDataset(torch.utils.data.Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx])
        return item

    def __len__(self):
        return len(self.labels)

def train_full_model():
    print("--- Full BERT Fine-Tuning Script ---")
    
    # Check GPU
    device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
    print(f"Using device: {device}")
    
    if not os.path.exists(DATASET_PATH):
        print(f"Error: {DATASET_PATH} not found.")
        return

    # 1. Load Data
    try:
        df = pd.read_csv(DATASET_PATH)
        df.columns = [c.lower() for c in df.columns]
        
        # Normalize columns
        if 'content' in df.columns: df.rename(columns={'content': 'text'}, inplace=True)
        if 'sentiment' in df.columns: df.rename(columns={'sentiment': 'emotion'}, inplace=True)
            
        print(f"Loaded {len(df)} samples.")
        
        # Encode Labels
        labels = df['emotion'].unique().tolist()
        label2id = {l: i for i, l in enumerate(labels)}
        id2label = {i: l for i, l in enumerate(labels)}
        
        df['label_id'] = df['emotion'].map(label2id)
        
        texts = df['text'].tolist()
        label_ids = df['label_id'].tolist()
        
    except Exception as e:
        print(f"Data load error: {e}")
        return

    # 2. Split
    train_texts, val_texts, train_labels, val_labels = train_test_split(texts, label_ids, test_size=0.2)

    # 3. Tokenize
    print("Tokenizing...")
    tokenizer = DistilBertTokenizerFast.from_pretrained('distilbert-base-uncased')
    train_encodings = tokenizer(train_texts, truncation=True, padding=True, max_length=128)
    val_encodings = tokenizer(val_texts, truncation=True, padding=True, max_length=128)

    train_dataset = EmotionDataset(train_encodings, train_labels)
    val_dataset = EmotionDataset(val_encodings, val_labels)

    # 4. Model
    print("Initializing Model...")
    model = DistilBertForSequenceClassification.from_pretrained(
        'distilbert-base-uncased', 
        num_labels=len(labels),
        id2label=id2label,
        label2id=label2id
    )
    model.to(device)

    # 5. Training Args
    training_args = TrainingArguments(
        output_dir='./results',
        num_train_epochs=NUM_EPOCHS,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        warmup_steps=500,
        weight_decay=0.01,
        logging_dir='./logs',
        logging_steps=10,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=1)]
    )

    print("Starting Training (this takes time)...")
    trainer.train()

    # 6. Save
    print(f"Saving model to {MODEL_DIR}...")
    model.save_pretrained(MODEL_DIR)
    tokenizer.save_pretrained(MODEL_DIR)
    print("Done! You can now restart the app.")

if __name__ == "__main__":
    train_full_model()
