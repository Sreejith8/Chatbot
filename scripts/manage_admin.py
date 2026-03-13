
import sys
from run import create_app, db
from database import User

app = create_app()

def list_users():
    with app.app_context():
        users = User.query.all()
        print(f"{'ID':<5} {'Username':<20} {'Role':<10}")
        print("-" * 35)
        for u in users:
            role = "Admin" if u.is_admin else "User"
            print(f"{u.id:<5} {u.username:<20} {role:<10}")

def toggle_admin(username):
    with app.app_context():
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"Error: User '{username}' not found.")
            return
        
        user.is_admin = not user.is_admin
        db.session.commit()
        new_role = "Admin" if user.is_admin else "User"
        print(f"Success: User '{username}' is now a {new_role}.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python manage_admin.py list")
        print("  python manage_admin.py toggle <username>")
        sys.exit(1)
        
    command = sys.argv[1]
    
    if command == "list":
        list_users()
    elif command == "toggle" and len(sys.argv) == 3:
        toggle_admin(sys.argv[2])
    else:
        print("Invalid command or arguments.")
