from flask import Flask, request, jsonify, send_from_directory, session, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import timedelta, datetime
from markdown import markdown
from urllib.parse import unquote
import urllib
import mimetypes
import os
import shutil
import traceback
import re
import socket

# タイムアウトは環境に応じて調整可能（初期値60秒）
socket.setdefaulttimeout(60)

app = Flask(__name__, static_folder='../frontend/dist', template_folder='../frontend/dist')

# CORSは全て許可（本番環境では必要に応じて制限）
CORS(app, resources={r"/*": {"origins": "*"}})

# セッション設定
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'
app.secret_key = 'REPLACE_WITH_SECRET_KEY'
Session(app)

# アップロードディレクトリ設定（パスはローカルで調整）
UPLOAD_DIR = r"/path/to/upload"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///replace_with_database.db'
app.config['UPLOAD_FOLDER'] = UPLOAD_DIR
app.config['MAX_CONTENT_LENGTH'] = 10000 * 1024 * 1024

# データベース初期化
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default="user")

class SystemUpdate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

mimetypes.add_type('image/webp', '.webp')
mimetypes.add_type('text/plain', '.txt')
mimetypes.add_type('application/pdf', '.pdf')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

def is_safe_path(base_path, user_path):
    abs_base = os.path.abspath(base_path)
    user_path_decoded = urllib.parse.unquote(user_path)
    abs_user_path = os.path.abspath(os.path.join(base_path, os.path.normpath(user_path_decoded)))
    return abs_user_path.startswith(abs_base)

# サニタイズ関数
def sanitize_input(input_string):
    try:
        allowed_pattern = r'[^\w\s\-/ぁ-んァ-ヶ一-龠々ー]'
        sanitized = re.sub(allowed_pattern, '', input_string)
        if re.search(r'[<>:"\\|?*]', input_string):
            raise ValueError("Invalid characters in input")
        return sanitized.strip()
    except ValueError as e:
        raise ValueError(f"Sanitization failed: {str(e)}")


# ユーザーログインエンドポイント
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    # ユーザーをデータベースから取得
    user = User.query.filter_by(username=username).first()

    if user:
        # パスワードを確認
        if check_password_hash(user.password, password):
            session.clear()
            session['user_id'] = user.id
            session['username'] = user.username
            session['logged_in'] = True
            session['role'] = user.role 
            session.permanent = True  
            app.permanent_session_lifetime = timedelta(hours=720) 
            return jsonify({"message": "Login successful"}), 200

        # ハッシュ化されていないパスワードを検出した場合、ハッシュ化して保存
        elif user.password == password:
            user.password = generate_password_hash(password)
            db.session.commit()
            session.clear()
            session['user_id'] = user.id
            session['username'] = user.username
            session['logged_in'] = True
            session['role'] = user.role 
            session.permanent = True 
            app.permanent_session_lifetime = timedelta(hours=720) 
            return jsonify({"message": "Login successful"}), 200

    return jsonify({"message": "Invalid credentials"}), 401


# セッション確認エンドポイント
@app.route('/session', methods=['GET'])
def check_session():
    if 'user_id' in session:
        return jsonify({"loggedIn": True, "username": session['username']}), 200
    return jsonify({"loggedIn": False}), 200


# ログアウトエンドポイント
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"message": "Logged out successfully"}), 200


# ログイン中のユーザー情報を取得するエンドポイント
@app.route('/api/user', methods=['GET'])
def get_user():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    user = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'id': user.id,
        'username': user.username,
        'role': user.role
    })


# システムアップデートを取得するエンドポイント
@app.route('/api/system-updates', methods=['GET'])
def get_system_updates():
    updates = SystemUpdate.query.order_by(SystemUpdate.created_at.asc()).all()
    if not updates:
        return jsonify({'content': ''})  

    return jsonify({'content': '<br>'.join([update.content for update in updates])})


# システムアップデートを保存するエンドポイント（管理者専用）
@app.route('/api/system-updates', methods=['POST'])
def save_system_updates():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Unauthorized'}), 401

    user = User.query.filter_by(id=user_id).first()
    if not user or user.role != 'admin':  
        return jsonify({'error': 'Forbidden'}), 403

    content = request.json.get('content')
    if not content:
        return jsonify({'error': 'Content is required.'}), 400

    try:
        SystemUpdate.query.delete()
        db.session.commit()

        lines = content.split("<br>")
        for line in lines:
            if line.strip():
                db.session.add(SystemUpdate(content=line.strip()))

        db.session.commit()
        return jsonify({'message': '保存が完了しました。'})
    except Exception as e:
        return jsonify({'error': f'保存に失敗しました: {str(e)}'}), 500


# ファイルアップロードエンドポイント
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'username' not in session or not session.get('logged_in'):
        return jsonify({"message": "Unauthorized: You must be logged in to upload files."}), 401

    if 'file' not in request.files:
        return jsonify({"message": "No file part"}), 400

    file = request.files['file']
    folder = request.form.get('folder', '').strip() 

    try:
        folder = sanitize_input(folder)
    except ValueError as e:
        return jsonify({"message": f"Invalid folder name: {str(e)}"}), 400

    if not file or file.filename == '':
        return jsonify({"message": "No selected file"}), 400

    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], os.path.normpath(folder)) if folder else app.config['UPLOAD_FOLDER']

    if not is_safe_path(app.config['UPLOAD_FOLDER'], upload_path):
        return jsonify({"message": "権限がありません。"}), 400

    try:
        os.makedirs(upload_path, exist_ok=True)
        file.save(os.path.join(upload_path, file.filename))
        return jsonify({"message": "アップロードが完了しました。"}), 200
    except Exception as e:
        return jsonify({"message": f"uploadに失敗しました。: {str(e)}"}), 500


def get_folder_structure(folder_path, relative_path=""):
    """フォルダ構造を再帰的に取得"""
    items = os.listdir(folder_path)
    folders = []
    files = []

    for item in items:
        item_path = os.path.join(folder_path, item)
        if os.path.isdir(item_path):
            subfolder_structure = get_folder_structure(item_path, os.path.join(relative_path, item))
            folders.append({
                "name": item,
                "path": os.path.join(relative_path, item).replace("\\", "/")  
            })
        else:
            files.append({
                "name": item,
                "path": os.path.join(relative_path, item).replace("\\", "/") 
            })

    return {"folders": folders, "files": files}


# ファイル・フォルダリストのエンドポイント
@app.route('/files', methods=['GET'])
def list_files():
    folder = request.args.get('folder', '')  
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder) if folder else app.config['UPLOAD_FOLDER']

    if not os.path.exists(folder_path):
        return jsonify({"message": f"Folder '{folder}' does not exist."}), 404

    folder_structure = get_folder_structure(folder_path, folder)
    return jsonify(folder_structure)


# フォルダ作成エンドポイント
@app.route('/create-folder', methods=['POST'])
def create_folder():
    if 'username' not in session or not session.get('logged_in'):
        return jsonify({"message": "Unauthorized: You must be logged in to create a folder."}), 401

    data = request.json
    foldername = sanitize_input(data.get('foldername', '').strip())  
    base_folder = sanitize_input(data.get('base_folder', '').strip())  

    if not foldername:
        return jsonify({"message": "Folder name is required."}), 400

    full_path = os.path.join(app.config['UPLOAD_FOLDER'], base_folder, foldername) if base_folder else os.path.join(app.config['UPLOAD_FOLDER'], foldername)

    if not is_safe_path(app.config['UPLOAD_FOLDER'], full_path):
        return jsonify({"message": "Access outside of the allowed directory is not permitted."}), 400

    if os.path.exists(full_path):
        return jsonify({"message": f"Folder '{foldername}' already exists in '{base_folder}'."}), 409

    try:
        os.makedirs(full_path, exist_ok=True)
        return jsonify({"message": f"'{foldername}' フォルダの作成が完了しました。 '{base_folder}'."}), 200
    except Exception as e:
        return jsonify({"message": f"フォルダの作成に失敗しました。: {str(e)}"}), 500


# フォルダおよびファイル削除エンドポイント
@app.route('/delete', methods=['DELETE'])
def delete_item():
    try:
        data = request.get_json()
        item_path = data.get('path', '').strip()
        if not item_path:
            return jsonify({"message": "Path is required."}), 400

        absolute_path = os.path.join(app.config['UPLOAD_FOLDER'], item_path)

        if os.path.exists(absolute_path):
            if os.path.isfile(absolute_path):
                os.remove(absolute_path) 
                return jsonify({"message": f"'{item_path}' の削除が完了しました。"}), 200
            elif os.path.isdir(absolute_path):
                shutil.rmtree(absolute_path) 
                return jsonify({"message": f"'{item_path}' の削除が完了しました。"}), 200
            else:
                return jsonify({"message": f"'{item_path}' is neither a file nor a folder."}), 400
        else:
            return jsonify({"message": f"Path '{item_path}' does not exist."}), 404
    except Exception as e:
        print("Error deleting item:", traceback.format_exc())  
        return jsonify({"message": f"削除に失敗しました。: {str(e)}"}), 500
    

# プレビュー用エンドポイント
@app.route('/preview/<path:filename>', methods=['GET'])
def preview_file(filename):
    folder = request.args.get('folder', '')
    folder = urllib.parse.unquote(folder)  
    filename = urllib.parse.unquote(filename)  

    if folder:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], folder, os.path.basename(filename))
    else:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    if not is_safe_path(app.config['UPLOAD_FOLDER'], file_path):
        return jsonify({"message": "Access outside of the allowed directory is not permitted."}), 400

    if not os.path.exists(file_path):
        return jsonify({"message": f"File '{filename}' not found."}), 404

    try:
        directory = os.path.dirname(file_path)
        filename_only = os.path.basename(file_path)
        return send_from_directory(
            directory=directory,
            path=filename_only,
            as_attachment=False,
        )
    except Exception as e:
        print(f"ERROR: Failed to send file for preview: {str(e)}")
        return jsonify({"message": f"プレビューに失敗しました。: {str(e)}"}), 500
    

# Markdownプレビュー
@app.route('/preview-markdown/<path:filename>', methods=['GET'])
def preview_markdown(filename):
    folder = request.args.get('folder', '')
    folder = urllib.parse.unquote(folder)
    filename = urllib.parse.unquote(filename)

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], folder, filename) if folder else os.path.join(app.config['UPLOAD_FOLDER'], filename)

    if not os.path.exists(file_path):
        return jsonify({"message": f"File '{filename}' not found."}), 404

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            markdown_content = file.read()

        html_content = markdown(markdown_content, extensions=['extra', 'codehilite', 'toc'])
        return jsonify({"html": html_content}), 200
    except Exception as e:
        return jsonify({"message": f"Failed to process markdown file: {str(e)}"}), 500

# アプリケーションの実行
if __name__ == '__main__':
    # ローカルでSSL証明書のパスを設定する必要あり
    init_db()
    app.run(debug=True, host='0.0.0.0', port=443, ssl_context=(
        '/path/to/fullchain.pem',  # 証明書チェーンファイル
        '/path/to/privkey.pem'     # 秘密鍵ファイル
    ))
