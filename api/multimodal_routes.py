from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os
import json
import numpy as np
import uuid
from datetime import datetime

# Processing Modules
from input_preprocessing.sync_controller import SyncController
from input_preprocessing.video_preprocess import VideoPreprocessor
from input_preprocessing.audio_processor import AudioProcessor # Assuming this exists or I'll stub it
from feature_extraction.text_features import TextFeatureExtractor
from classification.hybrid_classifier import HybridClassifier
from response_generation.cbt_engine import CBTEngine
from response_generation.summarizer import HeuristicSummarizer # Import Summarizer
from contextual_memory.chroma_manager import ContextualMemory
from database import db, ChatSession, ChatMessage, User, Assessment
from sqlalchemy.exc import IntegrityError
from config import config

multimodal_bp = Blueprint('multimodal', __name__)

# Initialize Processors
sync_ctrl = SyncController()
video_prep = VideoPreprocessor()
audio_prep = AudioProcessor() 
# text_extractor = TextFeatureExtractor()
# classifier = HybridClassifier()
cbt = CBTEngine()
summarizer = HeuristicSummarizer() # Initialize
# memory = ContextualMemory(config.CHROMA_DB_PATH)

# Re-using singletons from routes.py would be better in a production appFactory, 
# but for this structure we'll re-instantiate or import. 
# Better pattern: Import from a common 'extensions.py' or 'services.py'.
# For now, to avoid refactoring the whole app, I will re-import classes but 
# be aware of memory usage (loading BERT twice is bad).
# OPTIMIZATION: I should assume they are singletons or lightweight.

@multimodal_bp.route('/multimodal_session/start', methods=['POST'])
@jwt_required(optional=True)
def start_session():
    """
    Create a new multimodal conversation session.
    Returns session_id for tracking conversation context.
    """
    # 1. Resolve User
    user_id = get_jwt_identity()
    
    if not user_id:
        # Fallback to Guest (ID 1)
        user_id = 1 
        try:
            user = User.query.get(1)
            if not user:
                # Create default guest if missing
                guest = User(username="guest", password_hash="guest_hash")
                # Force ID 1 if possible, or just let DB assign and generic logic handles it?
                # SQLite usually auto-increments. 
                # Better: Find user by username "guest"
                existing_guest = User.query.filter_by(username="guest").first()
                if existing_guest:
                    user_id = existing_guest.id
                else:
                    db.session.add(guest)
                    db.session.commit()
                    user_id = guest.id
        except Exception as e:
            print(f"[Session] DB Init Error: {e}")

    # 2. Create Session Record
    new_session = ChatSession(user_id=user_id, start_time=datetime.utcnow())
    db.session.add(new_session)
    db.session.commit()
    
    session_id = str(new_session.id)
    print(f"[Session] Created DB Session: {session_id} for User {user_id}")
    
    return jsonify({
        "session_id": session_id,
        "status": "started"
    })

@multimodal_bp.route('/multimodal_session/end', methods=['POST'])
def end_session():
    """
    End a multimodal conversation session and clean up resources.
    """
    data = request.get_json()
    session_id = data.get('session_id') if data else None
    
    if session_id:
        try:
            session = ChatSession.query.get(int(session_id))
            if session:
                # Generate Summary
                messages = ChatMessage.query.filter_by(session_id=session.id).all()
                
                # Determine predominant emotion (simple frequency of bot responses for now)
                # Or use the last detected state
                last_msg = ChatMessage.query.filter_by(session_id=session.id, sender='bot')\
                            .order_by(ChatMessage.timestamp.desc()).first()
                
                final_state = "Neutral"
                if last_msg and last_msg.metadata_json:
                    try:
                       meta = json.loads(last_msg.metadata_json)
                       final_state = meta.get('state', 'Neutral')
                    except:
                       pass
                
                summary_text = summarizer.generate_summary(messages, final_state)
                
                session.end_time = datetime.utcnow()
                session.summary = summary_text
                
                db.session.commit()
                print(f"[Session] Ended DB Session: {session_id} with summary: {summary_text}")
                return jsonify({"status": "ended", "summary": summary_text})
        except Exception as e:
            print(f"[Session] Error ending session: {e}")
            return jsonify({"error": str(e)}), 500
            
    return jsonify({"status": "not_found"}), 404

@multimodal_bp.route('/multimodal_input', methods=['POST'])
@jwt_required(optional=True) 
def multimodal_input():
    # 1. Validation
    if 'audio' not in request.files:
        print("!!! ERROR: No audio file in request")
        return jsonify({'error': 'No audio file provided'}), 400

    audio_file = request.files['audio']
    video_frames = request.files.getlist('frames')
    metadata = request.form.get('metadata')
    session_id = request.form.get('session_id')  # New: Get session ID

    # Debug logs...
    
    current_user_id = get_jwt_identity()
    # If session is guest, current_user_id might be None, which is fine.
    
    # 2. Parallel Processing Definition
    def process_audio(f):
        # Save temp
        filename = secure_filename(f.filename)
        path = os.path.join('/tmp', filename)
        f.save(path)
        
        
        # TRANSCRIPTION (Real Whisper)
        # Use global audio_prep to retrieve cached model
        text = audio_prep.transcribe(path)
        
        # Audio Features (Real Librosa)
        audio_features = audio_prep.extract_prosodic_features(path)
        
        # Audio Features (Librosa)
        # audio_features = ...
        
        # BERT Embeddings
        # text_features = text_extractor.get_embedding(text)
        
        return {
            "text": text,
            "text_features": np.zeros(768), # Stub
            "audio_features": audio_features, # Pass features for prediction
            "audio_emotion": None # Will be filled by classifier
        }

    def process_video(frame_list):
        emotions = []
        for frame in frame_list:
            res = video_prep.extract_face_emotions(frame.read())
            if res:
                emotions.append(res)
        
        # Aggregate
        if not emotions:
            return {"Neutral": 1.0}
            
        # Average probabilities
        avg_emotion = {}
        for k in emotions[0].keys():
            avg_emotion[k] = sum(d[k] for d in emotions) / len(emotions)
            
        return avg_emotion

    # 3. Execute Parallel
    try:
        audio_res, video_res = sync_ctrl.process_parallel(
            audio_func=process_audio,
            video_func=process_video,
            audio_args=(audio_file,),
            video_args=(video_frames,)
        )
    except Exception as e:
        return jsonify({"error": f"Processing failed: {str(e)}"}), 500

    # 4. Fusion & Decision (Weighted Average)
    # Weights: Text=0.4, Video=0.4, Audio(Prosody)=0.2
    
    # Text Analysis (Simple keyword heuristic + BERT in real flow)
    # Since text_features stub is zeros, we use the text content directly for strong cues
    text_cues = {
        "Sadness": 1.0 if any(w in audio_res['text'].lower() for w in ['sad', 'down', 'depressed', 'cry', 'heavy']) else 0.0,
        "Anxiety": 1.0 if any(w in audio_res['text'].lower() for w in ['anxious', 'worry', 'scared', 'panic']) else 0.0,
        "Stress": 1.0 if any(w in audio_res['text'].lower() for w in ['stress', 'overwhelmed', 'tired', 'busy']) else 0.0,
        "Happy": 1.0 if any(w in audio_res['text'].lower() for w in ['happy', 'good', 'great', 'joy']) else 0.0
    }
    
    # Video Analysis (Normalized from DeepFace)
    # DeepFace keys: 'sad', 'angry', 'surprise', 'fear', 'happy', 'disgust', 'neutral'
    vid = video_res
    
    # Load Audio Model (Lazy Load)
    import joblib
    audio_probs = {"Neutral": 0.5} # Default
    if audio_res.get('audio_features') is not None:
        model_path = os.path.join("models", "rf_audio.pkl")
        if os.path.exists(model_path):
            try:
                if not hasattr(multimodal_input, "audio_model"):
                    multimodal_input.audio_model = joblib.load(model_path)
                
                # Predict
                feats = audio_res['audio_features'].reshape(1, -1)
                probs = multimodal_input.audio_model.predict_proba(feats)[0]
                classes = multimodal_input.audio_model.classes_
                audio_probs = dict(zip(classes, probs))
            except Exception as e:
                print(f"Audio prediction failed: {e}")
        else:
             # Fallback Stub if no model trained
             audio_probs = {"Sad": 0.1, "Neutral": 0.9}

    # Fusion Calculation
    # Weights: Text=0.4, Video=0.4, Audio=0.2
    final_scores = {
         "Sadness": 0.4 * text_cues.get("Sadness", 0) + 0.4 * vid.get("Sad", 0) + 0.2 * audio_probs.get("sad", 0),
         "Anxiety": 0.4 * text_cues.get("Anxiety", 0) + 0.4 * vid.get("Fear", 0) + 0.2 * audio_probs.get("fear", 0),
         "Stress": 0.4 * text_cues.get("Stress", 0) + 0.4 * vid.get("Angry", 0) + 0.2 * audio_probs.get("angry", 0),
         "Happy": 0.4 * text_cues.get("Happy", 0) + 0.4 * vid.get("Happy", 0) + 0.2 * audio_probs.get("happy", 0),
         "Neutral": 0.4 * 0.5 + 0.4 * vid.get("Neutral", 0) + 0.2 * audio_probs.get("neutral", 0)
    }

    # Determine Max State
    detected_state = max(final_scores, key=final_scores.get)
    if final_scores[detected_state] < 0.3:
        detected_state = "Neutral"

    # Risk Assessment
    risk = "Low"
    if detected_state in ["Depression", "Suicide", "Self Harm"]:
         risk = "High"
    elif detected_state in ["Sadness", "Anxiety", "Stress", "fear", "Fear", "sad", "Sad"]:
         risk = "Medium"
    
    # 5. Response Generation with Context
    # Use global cbt engine
    
    # Get conversation history if session exists
    conversation_history_text = []
    current_session = None
    
    if session_id:
        try:
            current_session = ChatSession.query.get(int(session_id))
            if current_session:
                # Fetch recent messages
                recent_msgs = ChatMessage.query.filter_by(session_id=current_session.id)\
                                .order_by(ChatMessage.timestamp.desc())\
                                .limit(6).all() # Last 3 turns (3 user + 3 bot)
                # Reorder to chronological
                for msg in reversed(recent_msgs):
                     # Construct simplified history for CBT engine
                     if msg.sender == 'user':
                         conversation_history_text.append({"role": "user", "content": msg.content_text})
                     else:
                         conversation_history_text.append({"role": "assistant", "content": msg.content_text})
        except:
             pass

    # Use stub if no history
    conversation_history = conversation_history_text if conversation_history_text else None
    
    response_text = cbt.get_cbt_response(detected_state, risk, conversation_history=conversation_history, user_input=audio_res['text'])
    
    # Update Database with New Turn
    if current_session:
        try:
            # 1. User Message
            user_msg = ChatMessage(
                session_id=current_session.id,
                sender='user',
                content_text=audio_res['text'],
                metadata_json=json.dumps({
                    "audio_emotion": audio_res.get('audio_emotion', {}),
                    "video_emotion": clean_obj(video_res)
                })
            )
            db.session.add(user_msg)
            
            # 2. Bot Message
            bot_msg = ChatMessage(
                session_id=current_session.id,
                sender='bot',
                content_text=response_text,
                metadata_json=json.dumps({
                    "state": detected_state,
                    "risk_level": risk
                })
            )
            db.session.add(bot_msg)
            
            # 3. Assessment Record (for analytics)
            assessment = Assessment(
                user_id=current_session.user_id,
                predicted_state=detected_state,
                risk_level=risk,
                confidence_score=0.85 # Placeholder confidence
            )
            db.session.add(assessment)
            
            db.session.commit()
            print(f"[Session] Persisted DB turn for Session {session_id}")
        except Exception as e:
            print(f"[Session] Failed to persist turn: {e}")
            db.session.rollback()

    # Sanitize for JSON (Convert numpy types)
    def clean_obj(obj):
        if isinstance(obj, np.generic):
            return obj.item()
        if isinstance(obj, dict):
            return {k: clean_obj(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [clean_obj(i) for i in obj]
        return obj

    final_resp = {
        "response": response_text,
        "state": detected_state,
        "risk_level": risk,
        "transcription": audio_res['text'],
        "debug_info": {
            "video_emotion": video_res,
            "audio_emotion": audio_res.get('audio_emotion', {})
        }
    }

    return jsonify(clean_obj(final_resp))
