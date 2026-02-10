from database import db
from run import create_app
import os
import sqlite3

print("--- DIAGNOSTIC V2 ---")

db_path = os.path.join(os.getcwd(), 'mental_health.db')
if os.path.exists(db_path):
    print(f"Removing {db_path}...")
    os.remove(db_path)

# 1. Create specific table manually
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

create_users_sql = """
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    password_hash VARCHAR(128) NOT NULL,
    created_at DATETIME,
    is_admin BOOLEAN DEFAULT 0,
    profile_data TEXT DEFAULT '{}'
);
"""
print("Executing Raw SQL...")
cursor.execute(create_users_sql)
conn.commit()

# Check immediately via SQLite
print("\n--- Direct SQLite Inspection ---")
cursor.execute("PRAGMA table_info(users)")
columns = [row[1] for row in cursor.fetchall()]
print(f"SQLite Columns: {columns}")
if 'is_admin' in columns:
    print("SUCCESS: SQLite confirms is_admin exists.")
else:
    print("FAILURE: SQLite says is_admin missing!")

conn.close()

# 2. SQLAlchemy check
app = create_app()
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

with app.app_context():
    print(f"\nSQLAlchemy Engine URL: {db.engine.url}")
    
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    cols = [c['name'] for c in inspector.get_columns('users')]
    print(f"Inspector Columns: {cols}")
