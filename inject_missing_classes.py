import pandas as pd
import random
import os

DATASET_PATH = "dataset/text/mental_health_dataset_final.csv"

print("--- Injecting Missing Clinical Classes into Dataset ---")

if not os.path.exists(DATASET_PATH):
    print(f"Error: {DATASET_PATH} not found.")
    exit(1)

# Read original kaggle data
try:
    df = pd.read_csv(DATASET_PATH)
except Exception as e:
    print(f"Failed to read CSV: {e}")
    exit(1)

# Ensure columns are normalized as expected by train script
if 'text_input' in df.columns and 'mental_label' in df.columns:
    df.rename(columns={'text_input': 'text', 'mental_label': 'emotion'}, inplace=True)
elif 'text' not in df.columns:
    df.columns = ['text', 'emotion']

original_length = len(df)

# We will synthesize varied phrases for the 5 missing classes
# To ensure the BERT embeddings aren't perfectly identical, we add slight variations
subjects = ["I ", "I really ", "I honestly ", "Lately I ", "Today I ", "Right now I ", "My mind ", "My body ", "I just "]
verbs_stress = ["am overwhelmed by", "am stressed about", "can't handle", "am crushed by", "am panicking over"]
nouns_stress = ["work", "my deadlines", "these exams", "the pressure", "all these tasks"]

verbs_dep = ["feel hopeless about", "see no point in", "am severely depressed by", "feel empty about", "am drained by"]
nouns_dep = ["my life", "everything", "getting out of bed", "the future", "my existence"]

verbs_bipo = ["feel manic about", "am experiencing severe mood swings over", "am rapidly shifting between highs and lows regarding", "feel invincible then crushed by"]
nouns_bipo = ["everything", "my daily routine", "my decisions", "my energy levels"]

verbs_adhd = ["can't focus on", "am completely distracted from", "keep losing my attention on", "am too restless for", "can't sit still for"]
nouns_adhd = ["my homework", "this meeting", "my chores", "reading", "one single task"]

verbs_fear = ["am terrified of", "am deeply afraid of", "feel intense dread about", "am scared for", "am panicked by"]
nouns_fear = ["the dark", "what might happen", "my safety", "the unknown", "this situation"]

synthetic_data = []

# Generate 500 unique-ish sentences per missing class
def generate_sentences(emotion, v_list, n_list, count=500):
    for _ in range(count):
        s = random.choice(subjects)
        v = random.choice(v_list)
        n = random.choice(n_list)
        
        # Add random punctuation
        punct = random.choice([".", "...", "!", ""])
        sentence = f"{s}{v} {n}{punct}"
        synthetic_data.append({"text": sentence, "emotion": emotion})

generate_sentences("Stress", verbs_stress, nouns_stress)
generate_sentences("Depression", verbs_dep, nouns_dep)
generate_sentences("Bipolar", verbs_bipo, nouns_bipo)
generate_sentences("ADHD", verbs_adhd, nouns_adhd)
generate_sentences("Fear", verbs_fear, nouns_fear)

# Append to dataframe
df_synthetic = pd.DataFrame(synthetic_data)
df_combined = pd.concat([df, df_synthetic], ignore_index=True)

# Save back to CSV
df_combined.to_csv(DATASET_PATH, index=False)

print(f"Original Dataset Size: {original_length}")
print(f"Added {len(synthetic_data)} synthetic rows for Stress, Depression, Bipolar, ADHD, Fear.")
print(f"New Dataset Size: {len(df_combined)}")
print("Dataset successfully augmented. You can now re-run train_text_model.py!")
