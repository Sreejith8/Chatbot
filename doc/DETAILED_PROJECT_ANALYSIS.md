# Detailed Project Analysis: Multimodal Mental Health Chatbot

## 1. Introduction
This project is an advanced **Multimodal AI Chatbot** designed to detect and support users through mental health challenges. Unlike traditional chatbots that rely solely on text analysis, this system integrates **Audio (Voice Prosody)** and **Video (Facial Expressions)** to form a holistic understanding of the user's emotional state.

### Core Objectives
1.  **Multimodal Emotion Detection**: Combine Text, Audio, and Video inputs to classify emotions (Depression, Anxiety, Stress, etc.).
2.  **Empathetic Response Generation**: Use a sophisticated Rule-Based Engine (CBT Principles) to provide therapeutic support.
3.  **Risk Assessment**: Detect high-risk indicators (Suicide/Self-Harm) and intervene immediately.
4.  **Long-Term Context**: Maintain user history and summaries to provide personalized care over multiple sessions.

---

## 2. Full System Architecture

### 2.1 High-Level Data Flow
1.  **User Input**: The user interacts via a web interface (Mic/Camera/Text).
2.  **Frontend Processing**: JavaScript captures media streams and sends them to the Flask API.
3.  **Backend Ingestion**: Flask routes (`api/routes.py`, `api/multimodal_routes.py`) receive the data.
4.  **Preprocessing**: Data is cleaned and normalized (`input_preprocessing/`).
5.  **Feature Extraction**: Deep Learning models convert raw data into numerical vectors (`feature_extraction/`).
6.  **Fusion & Classification**: Vectors are combined and passed to classifiers to predict the "Dominant State" (`classification/`).
7.  **Response Generation**: The CBT Engine selects the best therapeutic response based on the state and history (`response_generation/`).
8.  **Storage**: Interactions are saved to SQLite (Structured) and ChromaDB (Vector Memory).

### 2.2 Directory Structure Breakdown
```
project_root/
├── run.py                 # Entry Point. Initializes the App.
├── config.py              # Global Configuration (DB URI, Secret Keys).
├── database.py            # SQLAlchemy Database Models.
├── api/                   # REST API Blueprints.
│   ├── routes.py          # Chat Logic (Text).
│   ├── multimodal_routes.py # Audio/Video Upload Logic.
│   ├── auth.py            # User Authentication (Login/Signup).
│   └── admin.py           # Admin Dashboard Logic.
├── classification/        # The AI Brain.
│   ├── hybrid_classifier.py # Main logic to choose model.
│   ├── fusion.py          # Weighted Average of Text/Audio/Video scores.
│   └── risk_assessor.py   # Suicide/Self-Harm Detection.
├── feature_extraction/    # Model Loaders.
│   └── text_features.py   # BERT Feature Extractor.
├── input_preprocessing/   # Data Cleaners.
│   ├── text_clean.py      # Regex cleaning.
│   ├── audio_processor.py # Librosa Feature extraction.
│   └── video_preprocess.py# DeepFace Emotion detection.
├── response_generation/   # The AI Voice.
│   ├── cbt_engine.py      # Rule-Based Therapeutic Logic.
│   └── safety_guard.py    # Safety Filter (prevents unsafe responses).
├── frontend/              # UI Code.
│   ├── templates/         # HTML Pages.
│   └── static/            # CSS/JS Assets.
└── models/                # Saved ML Models (.pkl).
```

---

## 3. Detailed Component Analysis

### 3.1 Backend API (`api/`)
*   **`routes.py`**: The heartbeat of the text chat.
    *   **Logic**: Receives message -> Cleans it -> Extracts BERT features -> Classifies State -> Checks Risk -> Generates Response -> Saves to DB.
    *   **Key Function**: `chat()` handles the POST request from the frontend.
*   **`multimodal_routes.py`**: Similar to `routes.py` but handles file uploads.
    *   **Logic**: Defines `upload_audio` and `upload_video` endpoints. It fuses the results from these modalities with text analysis.

### 3.2 Machine Learning Pipeline (`classification/` & `feature_extraction/`)
*   **Text Analysis**:
    *   **Model**: DistilBERT (via HuggingFace Transformers).
    *   **Extraction**: Converts sentences into 768-dimensional embeddings.
    *   **Classification**: A trained Random Forest model (`rf_emotion.pkl`) predicts the emotion from this embedding.
*   **Audio Analysis**:
    *   **Library**: `librosa`.
    *   **Features**: Extracts MFCCs (Timbre), Pitch (Tone), and Energy (Volume).
    *   **Classification**: A Random Forest model (`rf_audio.pkl`) predicts emotion from these acoustic features.
*   **Video Analysis**:
    *   **Library**: `deepface` (Wrapper around VGG-Face/ResNet).
    *   **Logic**: Detects faces in frames -> Predicts 7 emotions (Angry, Disgust, Fear, Happy, Sad, Surprise, Neutral).

### 3.3 Fusion Logic (`classification/fusion.py`)
How do we combine 3 inputs?
```python
Final_Score = (Text_Score * 0.4) + (Audio_Score * 0.2) + (Video_Score * 0.4)
```
*   **Why?** Video and Text are usually more reliable indicators of explicit content/emotion than audio tone alone.
*   **Conflict Resolution**: If Audio says "Happy" (loud voice) but Text says "I want to die" (sad content), the Text weight (0.4) combined with Risk Assessment overrides the Audio.

### 3.4 Response Generation (`response_generation/cbt_engine.py`)
The system uses a **Rule-Based Hybrid Engine** rather than a pure Generative LLM (to avoid hallucinations and resource crashes).
*   **Input**: `detected_state` (e.g., "Anxiety"), `user_text`, `risk_level`.
*   **Process**:
    1.  **Safety Check**: If `Risk == High`, return emergency contacts immediately.
    2.  **Reflection**: Regex matches keywords (e.g., "exam" -> "Academic pressure").
    3.  **Strategy Selection**: Based on conversation depth, chooses:
        *   *Validation*: "It sounds like you're going through a lot."
        *   *Questioning*: "What is the root cause of this feeling?"
        *   *Coping*: "Let's try a breathing exercise."
*   **Output**: A constructed string sent back to the user.

---

## 4. Database Schema
The project uses SQLite with SQLAlchemy ORM.

### 4.1 Tables
*   **User**: `id`, `username`, `password_hash`, `created_at`.
*   **ChatSession**: `id`, `user_id`, `start_time`, `end_time`, `summary` (generated after session ends).
*   **ChatMessage**: `id`, `session_id`, `sender` ('user'/'bot'), `content_text`, `timestamp`, `metadata_json` (stores detected state/risk).

---

## 5. Program Flow (From Scratch)

### Scenario: User says "I feel hopeless."
1.  **Frontend**: JS captures text "I feel hopeless" and POSTs to `/api/chat`.
2.  **API**:
    *   Calls `safety_guard.is_safe("I feel hopeless")` -> Returns Safe (True).
    *   Calls `text_cleaner.clean("I feel hopeless")` -> "i feel hopeless".
    *   Calls `feature_extractor.get_embedding(...)` -> Returns `[0.12, -0.5, ...]` (768 dims).
3.  **Classifier**:
    *   Calls `classifier.predict(vector)` -> Returns `{"Depression": 0.85, "Sadness": 0.10, ...}`.
    *   Determines `detected_state = "Depression"`.
4.  **Risk Assessor**:
    *   Scans for keywords ("hopeless").
    *   Calculates `risk_level = "Medium"` (due to "hopeless").
5.  **CBT Engine**:
    *   Receives `State="Depression"`, `Risk="Medium"`.
    *   Selects **Validation Strategy**.
    *   Returns: "I hear you, and it sounds heavy. Have you tried identifying one small thing you can control right now?"
6.  **Database**:
    *   Saves User Message ("I feel hopeless").
    *   Saves Bot Message (Response + Metadata `{"state": "Depression", "risk": "Medium"}`).
7.  **Frontend**: Displays the response.

---

## 6. How to Run & Extend
1.  **Install Dependencies**: `pip install -r requirements.txt`.
2.  **Initialize DB**: `python init_db_manual.py`.
3.  **Run Server**: `python run.py`.
4.  **Train Models** (Optional):
    *   Text: `python train_text_model.py`.
    *   Audio: `python train_audio_model.py`.
5.  **Evaluate**: `python evaluate_models.py`.

This project is fully modular. To add a new modality (e.g., physiological sensors), you would simply add a new `processor` in `input_preprocessing/` and update `fusion.py` weights.
