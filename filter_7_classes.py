import pandas as pd
import os

INPUT_PATH = "dataset/text/mental_health_dataset_final.csv"
OUTPUT_PATH = "dataset/text/dataset_7_classes.csv"

ALLOWED_CLASSES = ["Normal", "Happy", "Sadness", "Anxiety", "Stress", "Angry", "Fear"]

print(f"--- Filtering dataset to 7 classes ---")
if not os.path.exists(INPUT_PATH):
    print(f"Error: {INPUT_PATH} not found.")
    exit(1)

df = pd.read_csv(INPUT_PATH)

# Ensure columns are correct
if 'text_input' in df.columns and 'mental_label' in df.columns:
    df.rename(columns={'text_input': 'text', 'mental_label': 'emotion'}, inplace=True)
elif 'text' not in df.columns:
    df.columns = ['text', 'emotion']

original_len = len(df)

# Filter
filtered_df = df[df['emotion'].isin(ALLOWED_CLASSES)]

print(f"Original rows: {original_len}")
print(f"Rows after dropping unwanted classes: {len(filtered_df)}")
print(f"Classes retained: {filtered_df['emotion'].unique()}")

filtered_df.to_csv(OUTPUT_PATH, index=False)
print(f"Successfully saved to {OUTPUT_PATH}")
