
from run import create_app, db
from database import ChatSession, ChatMessage
from response_generation.summarizer import HeuristicSummarizer

def backfill_summaries():
    app = create_app()
    summarizer = HeuristicSummarizer()
    
    with app.app_context():
        # Find sessions with empty or null summaries
        sessions = ChatSession.query.filter(
            (ChatSession.summary == None) | (ChatSession.summary == "")
        ).all()
        
        print(f"Found {len(sessions)} sessions to backfill.")
        
        count = 0
        for session in sessions:
            # Get messages for this session
            messages = ChatMessage.query.filter_by(session_id=session.id).order_by(ChatMessage.timestamp).all()
            
            if not messages:
                print(f"Session {session.id} has no messages. Skipping.")
                continue
                
            # Generate summary
            # We don't have stored state per session easily accessible without parsing metadata,
            # so we'll use a default or try to extract from last message metadata if available.
            detected_state = "Neutral"
            if messages:
                last_msg = messages[-1]
                # Simple extraction if metadata exists (optional improvement)
                # metadata = json.loads(last_msg.metadata_json)
                # detected_state = metadata.get('emotion_detected', 'Neutral')
            
            summary = summarizer.generate_summary(messages, detected_state="Analyzed")
            
            session.summary = summary
            count += 1
            print(f"Generated summary for Session {session.id}: {summary}")
            
        db.session.commit()
        print(f"Successfully backfilled {count} session summaries.")

if __name__ == "__main__":
    backfill_summaries()
