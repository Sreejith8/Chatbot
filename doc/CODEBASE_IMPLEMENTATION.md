# Codebase Implementation Details

This document provides a detailed breakdown of the technical implementation of the core features in the Mental Health Chatbot project.

## 1. Preprocessing (`input_preprocessing/`)
*   **Audio**: `input_preprocessing/audio_processor.py` uses `librosa` to load audio files, resample them to 22kHz, and convert stereo to mono.
*   **Video**: `input_preprocessing/video_preprocess.py` uses `cv2` to read video frames. It relies on the `DeepFace` library (or MediaPipe) to detect faces and crop/normalize them before analysis.
*   **Text**: Text is produced by the Whisper model (in `audio_processor.py`). Further preprocessing like Tokenization happens implicitly inside the BERT model in `feature_extraction/text_features.py`.

## 2. Feature Extraction (`feature_extraction/`)
*   **Text**: `feature_extraction/text_features.py` extracts a **768-dimensional embedding** using the `all-mpnet-base-v2` SentenceTransformer model.
*   **Audio**: `input_preprocessing/audio_processor.py` extracts **PNCCs** (Texture), **Zero-Crossing Rate** (Pitch), and **RMS** (Energy) into a **15-dimensional vector**.
*   **Video**: `input_preprocessing/vision_processor.py` processes raw frames and yields a dictionary of 7 basic emotion probabilities using `DeepFace`., resulting in a **7-dimensional vector**.

## 3. Hybrid Classification (`classification/hybrid_classifier.py`)
This file contains the core logic for emotion detection.
*   **Logic**: The `predict` method takes the fused vector and:
    1.  **Slices** it back into components (Text, Audio, Video).
    2.  **Routes** inputs to specific models:
        *   **Transformer**: Uses `custom_bert_pipeline` (if available) or zero-shot BART for text.
        *   **Ensemble RF**: Uses `self.rf_model` (Random Forest) for audio features.
        *   *(Note: XGBoost is currently commented out/unused)*.
    3.  **Ensembles**: It combines the independent scores from these models using a **Weighted Voting Logic** (Self-Ensemble) to decide the final state.

## 4. Response Generation (`response_generation/cbt_engine.py`)
The system uses a **Rule-Based Retrieval System** for safety and clinical accuracy.
*   **Input**: Detected State (e.g., "Anxiety") and Risk Level.
*   **Logic**: It looks up a dictionary of **CBT Strategies** (Validation -> Questioning -> Coping) in `self.templates`.
*   **Empathy**: Is achieved by selecting pre-written therapeutic phrasing rather than generating text from scratch.

## 5. Contextual Memory (`contextual_memory/chroma_manager.py`)
*   **Storage**: Uses **ChromaDB** to store the raw **Text** of the user's message.
*   **Metadata**: It attaches `state` (Emotion), `risk`, and `session_id` to each stored text. It does not store a single "score" but rather the full semantic context of what was said, tagged with how the user felt at that moment.

## 6. PNCC Extraction (`input_preprocessing/audio_processor.py`)

*   **Code**: Uses `spafe.features.pncc(sig=y, fs=sr, num_ceps=13)`.
*   **Result**: 13 PNCC features + ZCR + RMS = 15 features.
*   **Deviation**: None. The system correctly evaluates prosody features from live audio captures.

## 7. Context Retrieval
*   **Location**: `contextual_memory/chroma_manager.py`.
*   **Method**: Uses **Cosine Similarity**. ChromaDB automatically converts the query text into a vector (using its internal embedding function) and finds the closest past vectors (messages) in the high-dimensional space.

## 8. CBT Templates
*   **Location**: `response_generation/cbt_engine.py`.
*   **Generation**: Responses are **Selectively Retrieved**, not generated.
*   **Mechanism**: The code randomly picks a template from the appropriate category (`random.choice(self.templates[State][Strategy])`) to ensure the response matches the user's emotion and the conversation stage.
