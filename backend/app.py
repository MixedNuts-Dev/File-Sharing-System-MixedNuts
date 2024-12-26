from flask import Flask, request, jsonify, send_from_directory, render_template, session
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
import socket
import mimetypes
import os
import shutil 

app = Flask(__name__, static_folder='../frontend/dist', template_folder='../frontend/dist')
socket.setdefaulttimeout(6000)  # 6000秒（60分）

CORS(app, resources={r"/*": {"origins": ["http://111.108.31.73"]}})

# セッション設定
app.config['SESSION_TYPE'] = 'filesystem'
app.secret_key = 'your_secret_key'  # セッション暗号化用のキー
Session(app)

# アップロード設定
UPLOAD_DIR = r"E:\\upload"  # アップロード先をE:\uploadに指定
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['UPLOAD_FOLDER'] = UPLOAD_DIR
app.config['MAX_CONTENT_LENGTH'] = 10000 * 1024 * 1024  # 10000MB制限

db = SQLAlchemy(app)

# Userモデル
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

# アップロードディレクトリの作成
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# データベース初期化
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)

# ユーザーログインエンドポイント
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username', '')
    password = data.get('password', '')

    # ユーザーを検索
    user = User.query.filter_by(username=username).first()

    if user:
        # 既存パスワードがハッシュ化されている場合
        if check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            return jsonify({"message": "Login successful"}), 200

        # パスワードが平文で保存されている場合
        elif user.password == password:
            # パスワードをハッシュ化して保存
            user.password = generate_password_hash(password)
            db.session.commit()
            session['user_id'] = user.id
            session['username'] = user.username
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

# ファイルアップロードエンドポイント
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"message": "No file part"}), 400
    file = request.files['file']
    folder = request.form.get('folder', '')
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], folder) if folder else app.config['UPLOAD_FOLDER']
    if not os.path.exists(upload_path):
        return jsonify({"message": f"Folder '{folder}' does not exist."}), 400
    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400
    file.save(os.path.join(upload_path, file.filename))
    return jsonify({"message": "File uploaded successfully"}), 200

# ファイルリスト取得エンドポイント
@app.route('/files', methods=['GET'])
def list_files():
    folder = request.args.get('folder', '')  # クエリパラメータからフォルダを取得
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder) if folder else app.config['UPLOAD_FOLDER']
    
    if not os.path.exists(folder_path):
        return jsonify({"message": f"Folder '{folder}' does not exist."}), 404

    items = os.listdir(folder_path)
    categorized_files = {
        "images": [],
        "videos": [],
        "audio": [],
        "others": []
    }
    folders = []
    for item in items:
        item_path = os.path.join(folder_path, item)
        if os.path.isdir(item_path):
            folders.append(item)
        else:
            mime_type, _ = mimetypes.guess_type(item_path)
            if mime_type:
                if mime_type.startswith('image/'):
                    categorized_files["images"].append(item)
                elif mime_type.startswith('video/'):
                    categorized_files["videos"].append(item)
                elif mime_type.startswith('audio/'):
                    categorized_files["audio"].append(item)
                else:
                    categorized_files["others"].append(item)
            else:
                categorized_files["others"].append(item)
    return jsonify({"files": categorized_files, "folders": folders})

# ファイル削除エンドポイント
@app.route('/delete/<path:filename>', methods=['DELETE'])
def delete_file(filename):
    folder = request.args.get('folder', '')  # クエリパラメータからフォルダを取得
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder) if folder else app.config['UPLOAD_FOLDER']
    file_path = os.path.join(folder_path, filename)

    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            return jsonify({"message": f"File '{filename}' deleted successfully."}), 200
        return jsonify({"message": f"File '{filename}' not found."}), 404
    except Exception as e:
        return jsonify({"message": f"Failed to delete file: {str(e)}"}), 500

# フォルダ作成エンドポイント
@app.route('/create-folder/<foldername>', methods=['POST'])
def create_folder(foldername):
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], foldername)
    try:
        os.makedirs(folder_path, exist_ok=True)
        return jsonify({"message": f"Folder '{foldername}' created successfully."}), 200
    except Exception as e:
        return jsonify({"message": f"Failed to create folder: {str(e)}"}), 500

# フォルダ削除エンドポイント
@app.route('/delete-folder/<foldername>', methods=['DELETE'])
def delete_folder(foldername):
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], foldername)
    try:
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)  # 中身を含めてフォルダを削除
            return jsonify({"message": f"Folder '{foldername}' and its contents deleted successfully."}), 200
        return jsonify({"message": f"Folder '{foldername}' not found."}), 404
    except Exception as e:
        return jsonify({"message": f"Failed to delete folder: {str(e)}"}), 500
    
# ファイルダウンロードエンドポイント
@app.route('/download/<path:filename>', methods=['GET'])
def download_file(filename):
    folder = request.args.get('folder', '')  # クエリパラメータからフォルダを取得
    folder_path = os.path.join(app.config['UPLOAD_FOLDER'], folder) if folder else app.config['UPLOAD_FOLDER']
    file_path = os.path.join(folder_path, filename)

    if not os.path.exists(file_path):
        return jsonify({"message": f"File '{filename}' not found."}), 404

    return send_from_directory(folder_path, filename, as_attachment=True)


# アプリケーションの実行
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)
