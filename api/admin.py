from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from database import User, ChatSession, ChatMessage, db
from sqlalchemy import func
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

def is_admin():
    claims = get_jwt()
    return claims.get("is_admin", False)

@admin_bp.route('/stats', methods=['GET'])
@jwt_required()
def stats():
    if not is_admin():
        return jsonify({"msg": "Admins only!"}), 403
        
    user_count = User.query.count()
    session_count = ChatSession.query.count()
    msg_count = ChatMessage.query.count()
    
    # Calculate average sessions per user
    avg_sessions = round(session_count / user_count, 1) if user_count > 0 else 0
    
    
    # Daily Activity (Last 7 Days)
    from datetime import timedelta
    last_7_days = datetime.utcnow() - timedelta(days=7)
    
    # SQLite strict group by might behave differently, but this is standard
    daily_stats = db.session.query(
        func.date(ChatSession.start_time).label('date'),
        func.count(ChatSession.id)
    ).filter(ChatSession.start_time >= last_7_days)\
     .group_by('date').all()
     
    # Format for Chart.js
    activity_data = {
        "labels": [str(d[0]) for d in daily_stats],
        "values": [d[1] for d in daily_stats]
    }

    return jsonify({
        "total_users": user_count,
        "total_sessions": session_count,
        "total_messages": msg_count,
        "avg_sessions_per_user": avg_sessions,
        "active_models": ["BERT (Text)", "Whisper (Audio)", "MediaPipe (Video)", "RF-XGBoost (Risk)"],
        "daily_activity": activity_data
    })

@admin_bp.route('/users', methods=['GET'])
@jwt_required()
def list_users():
    if not is_admin():
        return jsonify({"msg": "Admins only!"}), 403
        
    users = User.query.all()
    user_list = []
    for u in users:
        session_count = ChatSession.query.filter_by(user_id=u.id).count()
        user_list.append({
            "id": u.id,
            "username": u.username,
            "joined": u.created_at.strftime("%Y-%m-%d"),
            "role": "Admin" if u.is_admin else "User",
            "sessions": session_count
        })
        
    return jsonify(user_list)

@admin_bp.route('/sessions', methods=['GET'])
@jwt_required()
def list_sessions():
    if not is_admin():
        return jsonify({"msg": "Admins only!"}), 403
        
    # Get last 20 sessions
    sessions = ChatSession.query.order_by(ChatSession.start_time.desc()).limit(20).all()
    session_list = []
    
    # Lazy Initialization
    from response_generation.summarizer import HeuristicSummarizer
    summarizer = HeuristicSummarizer()

    try:
        updated_any = False
        for s in sessions:
            # We need to access user even if lazy loading
            user = User.query.get(s.user_id)
            username = user.username if user else "Unknown"
            
            # Get messages efficiently
            msgs = ChatMessage.query.filter_by(session_id=s.id).order_by(ChatMessage.timestamp).all()
            msg_count = len(msgs)
            
            # Lazy Summary Logic
            if (not s.summary or s.summary == "No summary") and msg_count > 0:
                try:
                    # Attempt to get state
                    detected_state = "Neutral"
                    if msgs:
                        # Find last bot message with metadata
                        last_bot = next((m for m in reversed(msgs) if m.sender == 'bot'), None)
                        if last_bot and last_bot.metadata_json:
                            import json
                            try:
                                meta = json.loads(last_bot.metadata_json)
                                detected_state = meta.get('state', meta.get('predicted_state', 'Neutral'))
                            except:
                                pass
                    
                    new_summary = summarizer.generate_summary(msgs, detected_state)
                    s.summary = new_summary
                    updated_any = True
                except Exception as e:
                    print(f"Error summarising session {s.id}: {e}")

            session_list.append({
                "id": s.id,
                "user": username,
                "start": s.start_time.strftime("%Y-%m-%d %H:%M"),
                "messages": msg_count,
                "summary": s.summary or "No summary"
            })
        
        if updated_any:
            db.session.commit()
            
    except Exception as e:
        print(f"Admin sessions error: {e}")
        db.session.rollback()
        
    return jsonify(session_list)
