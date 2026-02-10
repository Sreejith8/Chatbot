import os
from datetime import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev_key_super_secret_mental_health_project'
    
    # Database Config
    # Default to sqlite for ease of local testing if POSTGRES_URL not set
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///mental_health.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT Config
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt_dev_key_secret'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    
    # ChromaDB Config
    CHROMA_DB_PATH = os.path.join(os.getcwd(), 'chroma_data')
    
    # Uploads
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload

    # Model Paths (Placeholders)
    WHISPER_MODEL_SIZE = "base"
    BERT_MODEL_NAME = "bert-base-uncased"
    
config = Config()
