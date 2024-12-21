from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
db = SQLAlchemy(app)

# Userモデルの定義
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

# テスト用ユーザーを登録する関数
def create_test_user():
    with app.app_context():
        db.create_all()
        test_user = User(username="testuser", password="testpassword")
        db.session.add(test_user)
        db.session.commit()
        print("Test user created successfully!")

if __name__ == "__main__":
    create_test_user()
