# Project Diary: Project Lead & AI Systems Developer
**(Implementation Phase)**

**Role:** Project Lead & AI Systems Developer
**Focus:** Full Implementation, Technical Troubleshooting, System Integration, AI Model Deployment.

---

## Week 1: Environment Setup & Scaffolding
**Goal:** Establish the development environment and core backend structure.
*   **Activity:** Set up the Python virtual environment and installed core dependencies (`Flask`, `SQLAlchemy`, `PyTorch`).
*   **Implementation:** Initialized the Flask application structure (`run.py`, `config.py`) and defined the database models (`User`, `ChatSession`, `ChatMessage`) using **SQLAlchemy**.
*   **Challenge faced:** Encountered circular import errors between `database.py` and `app.py`. Resolved by restructuring the import logic and using Flask blueprints.
*   **Technology Used:** Python 3.9, Flask 2.0, SQLite.

## Week 2: Text Processing Implementation (DistilBERT)
**Goal:** Implement the primary text-based emotion detection capabilities.
*   **Activity:** Integrated the **HuggingFace Transformers** library for text feature extraction.
*   **Implementation:** Chose **DistilBERT** (`distilbert-base-uncased`) over traditional BERT because it is 40% lighter and 60% faster while retaining 97% of performance.
*   **Technical Decision:** Realized that raw text needed cleaning before tokenization. Implemented `input_preprocessing/text_clean.py` as a prerequisite step to remove non-alphanumeric noise which was confusing the model.
*   **Technology Used:** HuggingFace Transformers, PyTorch, NLTK.

## Week 3: Contextual Memory Integration (ChromaDB)
**Goal:** Enable the chatbot to "remember" past interactions.
*   **Activity:** Researched vector databases suitable for local storage. Selected **ChromaDB** for its simplicity and persistence capabilities.
*   **Implementation:** Developed the `ContextualMemory` module. Implemented logic to store conversation snippets as vector embeddings and retrieve the top-k most similar past interactions during a chat.
*   **Challenge faced:** The vector store was returning irrelevant historical data for short greetings ("Hi"). Modified the retrieval logic to only query memory if the input length > 3 words.
*   **Technology Used:** ChromaDB, Sentence-Transformers.

## Week 4: Multimodal Fusion Logic
**Goal:** Combine Text, Audio, and Video inputs into a single prediction.
*   **Activity:** Designed the `Fusion` class to aggregate probabilities from different classifiers.
*   **Implementation:** Developed a weighted average formula: `Final_Score = 0.4*Text + 0.2*Audio + 0.4*Video`.
*   **Reasoning:** Audio was given lower weight because background noise in the browser recordings was causing frequent misclassifications. Text features (BERT) proved most reliable, so assigned higher weight.
*   **Technology Used:** NumPy, Scikit-learn (Random Forest).

## Week 5: Pivoting Response Generation (Generative AI vs Rule-Based)
**Goal:** Build the engine that generates therapeutic responses.
*   **Activity (Attempt 1):** Integrated a local Large Language Model (`google/flan-t5-base`) to generate dynamic, empathetic responses.
*   **Critical Fault:** The 1GB model caused significant latency (20s+ response time) and frequently crashed the development server due to memory overload.
*   **Modification:** Made a strategic decision to **pivot to an Enhanced Rule-Based CBT Engine**.
*   **Implementation (Final):** Built a sophisticated template system with keyword mirroring and state tracking (Validation -> Questioning -> Coping) which mimicked intelligence without the heavy compute cost.
*   **Technology Used:** Python Regex (`re`), Custom Logic.

## Week 6: Safety Guard & Risk Assessment
**Goal:** Ensure the chatbot can detect and handle crisis situations safely.
*   **Activity:** Implemented the `RiskAssessor` class to scan for keywords indicative of self-harm.
*   **Challenge faced:** The initial logic was too aggressive. Phrases like "stressed about studies" were flagged as "High Risk" because the word "die" is a substring of "studies".
*   **Correction:** Modified the `SafetyGuard` to use **Regex Word Boundaries (`\b`)** to ensure only whole words are matched. This eliminated the false positives.
*   **Technology Used:** Regex, Python Logic.

## Week 7: System Integration & Admin Dashboard
**Goal:** Connect all independent modules and provide monitoring tools.
*   **Activity:** Connected the Frontend (processed by other team members) to the Backend API endpoints.
*   **Implementation:** Built the Admin Dashboard (`admin.py`) to visualize chat sessions and user states.
*   **Feature Addition:** Added **Session Summarization** logic. Since running a summary model on every message was slow, implemented "Lazy Summarization" that only generates the summary when the admin views the session list.
*   **Technology Used:** Flask-Admin, Jinja2 Templates.

## Week 8: Evaluation & Final Optimization
**Goal:** Benchmark system performance and prepare for demonstration.
*   **Activity:** Created the `evaluate_models.py` script to run the models against the test dataset.
*   **Outcome:** Achieved satisfactory F1-scores for text and video, but identified that audio accuracy dropped in noisy environments. Documented this limitation.
*   **Final Tasks:** Code cleanup, commenting, and generating the detailed technical documentation (`PROJECT_OVERVIEW.md`). Verified that the system runs smoothly via the single entry point `run.py`.
*   **Technology Used:** Scikit-learn Metrics (Precision/Recall), Matplotlib (Confusion Matrix).
