from flask import Blueprint, request, jsonify
from database import db, User
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({"msg": "Missing username or password"}), 400
        
    if User.query.filter_by(username=username).first():
        return jsonify({"msg": "Username already exists"}), 400
    
    # Auto-Admin: First user becomes admin
    is_first_user = User.query.count() == 0
    
    user = User(
        username=username,
        password_hash=generate_password_hash(password),
        is_admin=is_first_user
    )
    db.session.add(user)
    db.session.commit()
    
    role = "Admin" if is_first_user else "User"
    return jsonify({"msg": f"User created successfully. Role: {role}"}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username).first()
    
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"msg": "Invalid credentials"}), 401
        
    # Include role in token claims
    access_token = create_access_token(
        identity=str(user.id), 
        additional_claims={"is_admin": user.is_admin}
    )
    
    return jsonify({
        "access_token": access_token,
        "username": user.username,
        "is_admin": user.is_admin
    })

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    return jsonify({
        "id": user.id,
        "username": user.username,
        "profile": user.get_profile()
    })
