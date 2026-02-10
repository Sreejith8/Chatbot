from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from database import db, ChatSession, ChatMessage, Assessment, User
from config import config

# Module Imports
from input_preprocessing.text_clean import TextPreprocessor
from feature_extraction.text_features import TextFeatureExtractor
from classification.hybrid_classifier import HybridClassifier
from classification.risk_assessor import RiskAssessor
from response_generation.cbt_engine import CBTEngine
from response_generation.safety_guard import SafetyGuard
from contextual_memory.chroma_manager import ContextualMemory

api_bp = Blueprint('api', __name__)

# Initialize singletons (In real app, might want to do this in app factory)
# Models are lazy loaded inside classes usually, but good to init here
text_cleaner = TextPreprocessor()
feature_extractor = TextFeatureExtractor() # This loads BERT, might take a sec
classifier = HybridClassifier()
risk_assessor = RiskAssessor()
cbt_engine = CBTEngine()
safety_guard = SafetyGuard()
memory_manager = ContextualMemory(config.CHROMA_DB_PATH)

@api_bp.route('/chat', methods=['POST'])
@jwt_required()
def chat():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    raw_message = data.get('message', '')
    
    # 1. Safety Check
    is_safe, warning = safety_guard.is_safe(raw_message)
    if not is_safe:
         return jsonify({
            "response": "I cannot continue this conversation due to safety concerns. Please contact emergency services.",
            "risk_level": "High"
         })

    # 2. Input Preprocessing
    clean_text = text_cleaner.clean_text(raw_message)
    
    # 3. Context Retrieval (RAG)
    # Get last 3 relevant memories
    context = memory_manager.retrieve_context(current_user_id, clean_text)
    
    # 4. Feature Extraction (Text Only for this endpoint)
    # Real app would handle multimodal here if file uploaded
    features = feature_extractor.get_embedding(clean_text)
    
    # 5. Classification
    probs = classifier.predict(features, text=clean_text)
    # Determine dominant state
    predicted_state = max(probs, key=probs.get) if probs else "Normal"
    
    # 6. Risk Assessment
    # Simple keyword count for demo (in real app, more complex NLP)
    risk_keywords = ["sad", "hopeless", "dark"]
    risk_count = sum(1 for w in risk_keywords if w in clean_text)
    risk_level, risk_score = risk_assessor.calculate_risk(probs, risk_count)
    
    # 7. Session Resolution (Moved up)
    session_id = data.get('session_id')
    session = None
    
    if session_id:
        session = ChatSession.query.filter_by(id=session_id, user_id=current_user_id).first()
        
    if not session:
        # Fallback to latest ACTIVE session
        session = ChatSession.query.filter_by(user_id=current_user_id, end_time=None).order_by(ChatSession.start_time.desc()).first()
        
    if not session:
        from datetime import datetime
        session = ChatSession(user_id=current_user_id, start_time=datetime.utcnow())
        db.session.add(session)
        db.session.flush()

    # 8. Response Generation
    # History for Context-Aware Rule Engine
    conversation_history = []
    if session.id:
        recent_msgs = ChatMessage.query.filter_by(session_id=session.id).order_by(ChatMessage.timestamp.desc()).limit(6).all()
        for msg in reversed(recent_msgs):
            role = "User" if msg.sender == "user" else "Assistant"
            conversation_history.append({"role": role, "content": msg.content_text, "detected_state": "Unknown"})

    response_text = cbt_engine.get_cbt_response(predicted_state, risk_level, conversation_history, user_input=raw_message)
    
    # 9. Save Interaction to SQL DB
    user_msg = ChatMessage(session_id=session.id, sender="user", content_text=raw_message)
    db.session.add(user_msg)
    
    bot_msg = ChatMessage(session_id=session.id, sender="bot", content_text=response_text, 
                          metadata_json=f'{{"state": "{predicted_state}", "risk": "{risk_level}"}}')
    db.session.add(bot_msg)
    
    # 9. Save Assessment
    assessment = Assessment(user_id=current_user_id, predicted_state=predicted_state, risk_level=risk_level, confidence_score=risk_score)
    db.session.add(assessment)
    
    # 10. Save to Chroma Memory
    memory_manager.add_memory(current_user_id, clean_text, {"state": predicted_state})
    
    db.session.commit()
    
    return jsonify({
        "response": response_text,
        "state": predicted_state,
        "risk_level": risk_level
    })

@api_bp.route('/upload_audio', methods=['POST'])
@jwt_required()
def upload_audio():
    # Placeholder for Audio Logic
    if 'file' not in request.files:
        return jsonify({"msg": "No file part"}), 400
    
    # TODO: Process with input_preprocessing/audio_processor.py
    
    return jsonify({"msg": "Audio received (Stub)"})

@api_bp.route('/chat_history', methods=['GET'])
@jwt_required()
def get_chat_history():
    current_user_id = get_jwt_identity()
    
    # Fetch last 50 messages across all sessions for this user
    # Join with ChatSession to filter by user_id
    messages = db.session.query(ChatMessage).\
        join(ChatSession).\
        filter(ChatSession.user_id == current_user_id).\
        order_by(ChatMessage.timestamp.desc()).\
        limit(50).all()
        
    history = []
    import json
    for msg in reversed(messages): # Oldest first
        meta = {}
        try:
            if msg.metadata_json:
                meta = json.loads(msg.metadata_json)
        except:
            pass
            
        history.append({
            "sender": msg.sender,
            "text": msg.content_text,
            "timestamp": msg.timestamp.isoformat(),
            "state": meta.get('state') or meta.get('predicted_state'),
            "risk_level": meta.get('risk') or meta.get('risk_level')
        })
        
    return jsonify({"messages": history})
