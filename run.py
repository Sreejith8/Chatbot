from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import config
from database import db
import os

def create_app():
    app = Flask(__name__, 
                template_folder='frontend/templates',
                static_folder='frontend/static')
    
    app.config.from_object(config)
    
    # Initialize Extensions
    db.init_app(app)
    jwt = JWTManager(app)
    CORS(app)
    
    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Register Blueprints (Imports inside to avoid circular deps)
    from api.routes import api_bp
    from api.auth import auth_bp
    from api.admin import admin_bp
    
    from api.multimodal_routes import multimodal_bp
    
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(multimodal_bp, url_prefix='/api')
    
    # Main UI Route
    from flask import render_template
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/admin')
    def admin():
        return render_template('admin.html')


        
    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5001)
