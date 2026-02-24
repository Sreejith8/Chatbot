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
from input_preprocessing.audio_processor import AudioProcessor
from feature_extraction.text_features import TextFeatureExtractor
from classification.hybrid_classifier import HybridClassifier
from feature_extraction.fusion import FeatureFusion
from response_generation.cbt_engine import CBTEngine
from response_generation.summarizer import HeuristicSummarizer
from contextual_memory.chroma_manager import ContextualMemory
from database import db, ChatSession, ChatMessage, User, Assessment
from config import config

multimodal_bp = Blueprint('multimodal', __name__)

# Initialize Processors
sync_ctrl = SyncController()
video_prep = VideoPreprocessor()
audio_prep = AudioProcessor() 
# Activate BERT and Hybrid Classifier (Architecture Alignment)
text_extractor = TextFeatureExtractor()
classifier = HybridClassifier()
cbt = CBTEngine()
summarizer = HeuristicSummarizer()
# Memory initialized (Architecture Alignment)
memory = ContextualMemory(config.CHROMA_DB_PATH)

@multimodal_bp.route('/multimodal_session/start', methods=['POST'])
@jwt_required(optional=True)
def start_session():
    """
    Create a new multimodal conversation session.
    Returns session_id for tracking conversation context.
    """
    user_id = get_jwt_identity()
    
    if not user_id:
        user_id = 1 
        try:
            user = User.query.get(1)
            if not user:
                guest = User(username="guest", password_hash="guest_hash")
                existing_guest = User.query.filter_by(username="guest").first()
                if existing_guest:
                    user_id = existing_guest.id
                else:
                    db.session.add(guest)
                    db.session.commit()
                    user_id = guest.id
        except Exception as e:
            print(f"[Session] DB Init Error: {e}")

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
                messages = ChatMessage.query.filter_by(session_id=session.id).all()
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
    session_id = request.form.get('session_id')
    current_user_id = get_jwt_identity()

    # ── DIAGNOSTIC: log what we actually received from the browser ────────────
    # Log to file instead of just stdout so we can read it programmatically
    log_path = os.path.join(os.getcwd(), 'diagnostics.log')
    def dlog(msg):
        with open(log_path, 'a') as lf:
            lf.write(msg + "\n")
        print(msg)

    dlog(f"\n{'='*60}")
    dlog(f"[Multimodal] Audio file: '{audio_file.filename}', content_type='{audio_file.content_type}'")
    # Read size without consuming the stream
    audio_file.stream.seek(0, 2)
    audio_size = audio_file.stream.tell()
    audio_file.stream.seek(0)
    dlog(f"[Multimodal] Audio size: {audio_size} bytes")
    dlog(f"[Multimodal] Video frames received: {len(video_frames)}")
    dlog(f"[Multimodal] Session ID: {session_id}")
    dlog(f"{'='*60}")
    # ──────────────────────────────────────────────────────────────────────────

    # 2. Parallel Processing Definition
    def process_audio(f):
        filename = secure_filename(f.filename) if f.filename else "audio.webm"
        path = os.path.join('/tmp', filename)
        f.save(path)
        dlog(f"[Audio] Saved to: {path} ({os.path.getsize(path)} bytes)")

        # TRANSCRIPTION (Whisper — auto-converts webm→wav)
        text = audio_prep.transcribe(path)
        dlog(f"[Audio] Transcribed text: '{text}'")

        # Audio prosodic features
        audio_features = audio_prep.extract_prosodic_features(path)
        # Also compute from same file (already saved)
        text_features = text_extractor.get_embedding(text) if text and text.strip() else None

        return {
            "text": text,
            "text_features": text_features,
            "audio_features": audio_features,
            "audio_emotion": None
        }

    def process_video(frame_list):
        emotions = []
        for i, frame in enumerate(frame_list):
            frame_bytes = frame.read()
            res = video_prep.extract_face_emotions(frame_bytes)
            if res:
                emotions.append(res)
                dlog(f"[Video] Frame {i}: {dict(sorted(res.items(), key=lambda x: -x[1])[:3])}")
            else:
                dlog(f"[Video] Frame {i}: DeepFace returned None (no face detected)")

        if not emotions:
            dlog("[Video] No usable frames — video_res will be empty")
            return {}

        # Average across all detected frames
        avg_emotion = {}
        for k in emotions[0].keys():
            avg_emotion[k] = sum(d.get(k, 0.0) for d in emotions) / len(emotions)

        dlog(f"[Video] Averaged emotion: {dict(sorted(avg_emotion.items(), key=lambda x: -x[1])[:3])}")
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
        dlog(f"[Multimodal] Parallel processing FAILED: {e}")
        import traceback; dlog(traceback.format_exc()); traceback.print_exc()
        return jsonify({"error": f"Processing failed: {str(e)}\n{traceback.format_exc()}"}), 500

    dlog(f"[Multimodal] Pipeline result — text='{audio_res.get('text')}', video_empty={not bool(video_res)}")

    # 4. Hybrid Classification — Late-Decision Fusion (Per SDD)
    # Pass each modality INDEPENDENTLY to the classifier, not as a concat vector
    final_scores = classifier.predict(
        text=audio_res.get('text'),
        video_emotion_dict=video_res if video_res else None,     # Raw DeepFace dict
        audio_features=audio_res.get('audio_features')           # Raw 15-dim prosody
    )
    dlog(f"[Classifier] Final fused scores: {dict(sorted(final_scores.items(), key=lambda x: -x[1])[:4]) if final_scores else 'None'}")

    # Determine Max State
    detected_state = "Neutral"
    if final_scores:
        detected_state = max(final_scores, key=final_scores.get)
        # Only override to Neutral if confidence is extremely low
        if final_scores[detected_state] < 0.15:
            detected_state = "Neutral"
        dlog(f"[Route] Final scores: {dict(sorted(final_scores.items(), key=lambda x: -x[1])[:4])} → {detected_state}")

    # Risk Assessment
    risk = "Low"
    if detected_state in ["Depression", "Suicide", "Self Harm"]:
         risk = "High"
    elif detected_state in ["Sadness", "Anxiety", "Stress", "fear", "Fear", "sad", "Sad"]:
         risk = "Medium"
    
    # 5. Response Generation with Context
    
    # A. Vector Memory Retrieval (Architecture Compliance)
    retrieved_context = []
    if current_user_id:
        try:
             # Retrieve past relevant interactions
             # Note: We pass this to CBT or just use it to adjust state
             retrieved_context = memory.retrieve_context(
                 user_id=current_user_id, 
                 query_text=audio_res.get('text', ''),
                 n_results=2
             )
             if retrieved_context:
                 print(f"[Memory] Retrieved {len(retrieved_context)} context items for user {current_user_id}")
        except Exception as e:
             print(f"[Memory] Retrieval failed: {e}")

    # B. Session History (SQL)
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
                                .limit(6).all()
                # Reorder to chronological
                for msg in reversed(recent_msgs):
                     if msg.sender == 'user':
                         conversation_history_text.append({"role": "user", "content": msg.content_text})
                     else:
                         conversation_history_text.append({"role": "assistant", "content": msg.content_text})
        except:
             pass

    conversation_history = conversation_history_text if conversation_history_text else None
    
    # Pass pure text or enriched context? 
    # For now, we pass the retrieved context as a "system note" equivalent if we had an LLM.
    # Here we just log it.
    
    response_text = cbt.get_cbt_response(detected_state, risk, conversation_history=conversation_history, user_input=audio_res['text'])
    
    # C. Save to Vector Memory
    if current_user_id and audio_res.get('text'):
        try:
            memory.add_memory(
                user_id=current_user_id,
                text=audio_res['text'],
                metadata={
                    "state": detected_state,
                    "risk": risk,
                    "session_id": str(session_id)
                }
            )
        except Exception as e:
            print(f"[Memory] Save failed: {e}")
    
    # Update Database with New Turn
    if current_session:
        try:
            # 1. User Message
            user_msg = ChatMessage(
                session_id=current_session.id,
                sender='user',
                content_text=audio_res.get('text', ''),
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
            
            # 3. Assessment Record
            assessment = Assessment(
                user_id=current_session.user_id,
                predicted_state=detected_state,
                risk_level=risk,
                confidence_score=final_scores.get(detected_state, 0.0)
            )
            db.session.add(assessment)
            
            db.session.commit()
            print(f"[Session] Persisted DB turn for Session {session_id}")
        except Exception as e:
            print(f"[Session] Failed to persist turn: {e}")
            db.session.rollback()

    final_resp = {
        "response": response_text,
        "state": detected_state,
        "risk_level": risk,
        "transcription": audio_res.get('text', ''),
        "debug_info": {
            "video_emotion": video_res,
            "audio_emotion": audio_res.get('audio_emotion', {})
        }
    }

    return jsonify(clean_obj(final_resp))

# Sanitize Helper
def clean_obj(obj):
    if isinstance(obj, np.generic):
        return obj.item()
    if isinstance(obj, dict):
        return {k: clean_obj(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [clean_obj(i) for i in obj]
    return obj
