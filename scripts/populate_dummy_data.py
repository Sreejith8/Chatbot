from run import create_app
from database import db, User, ChatSession, ChatMessage
from datetime import datetime, timedelta
import random
from werkzeug.security import generate_password_hash

app = create_app()

def populate():
    with app.app_context():
        print("Populating dummy data...")
        
        # Create Users
        users = []
        for i in range(1, 6):
            username = f"user_{i}"
            if not User.query.filter_by(username=username).first():
                user = User(
                    username=username,
                    password_hash=generate_password_hash("password"),
                    is_admin=False
                )
                db.session.add(user)
                users.append(user)
        
        db.session.commit()
        
        # Reload users to get IDs
        all_users = User.query.all()
        
        # Create Sessions
        base_time = datetime.utcnow() - timedelta(days=7)
        
        for i in range(20):
            user = random.choice(all_users)
            # Random time in last 7 days
            start_time = base_time + timedelta(days=random.randint(0, 7), hours=random.randint(0, 23))
            
            session = ChatSession(
                user_id=user.id,
                start_time=start_time,
                end_time=start_time + timedelta(minutes=random.randint(5, 30)),
                summary=f"Session regarding topic {random.randint(1, 5)}"
            )
            db.session.add(session)
            db.session.flush() # Get ID
            
            # Create Messages
            for _ in range(random.randint(2, 10)):
                msg = ChatMessage(
                    session_id=session.id,
                    timestamp=start_time + timedelta(seconds=random.randint(10, 300)),
                    sender=random.choice(['user', 'bot']),
                    content_text=f"Message content {random.randint(100, 999)}"
                )
                db.session.add(msg)
                
        db.session.commit()
        print("Dummy data populated!")

if __name__ == '__main__':
    populate()
