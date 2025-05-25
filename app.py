from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename # 用於安全的檔案上傳
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)
# 儲存圖片的路徑
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 暫時用記憶體模擬儲存使用者與日記（正式應使用資料庫）
users = {}     # 儲存帳號密碼
diaries = []   # 儲存日記，每筆是 dict，包含 user, content, is_public

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return redirect('/login')

@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in users:
            msg = "此帳號已經註冊！請改用其他帳號。"
        elif not username.isalnum():
            msg = "帳號只能使用英文與數字。"
        else:
            hashed = generate_password_hash(password)
            users[username] = hashed
            msg = "註冊成功，請登入！"
            return redirect(url_for('login'))
    return render_template('register.html', msg=msg)


@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in users and check_password_hash(users[username], password):
            session['username'] = username
            return redirect('/my_diary')
        else:
            msg = "登入失敗，請檢查帳號或密碼。"
    return render_template('login.html', msg=msg)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/login')

@app.route('/write', methods=['GET', 'POST'])
def write_diary():
    if 'username' not in session:
        return redirect('/login')
    msg = ""
    if request.method == 'POST':
        content = request.form['content']
        is_public = 'is_public' in request.form

        # 🖼️ 圖片處理
        image = request.files.get('image')
        image_filename = None
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_filename = filename

        # 儲存日記內容
        diaries.append({
            'user': session['username'],
            'content': content,
            'is_public': is_public,
            'image': image_filename  # 儲存圖片檔名（如果有）
        })
        msg = "日記已成功儲存！"
    return render_template('write.html', msg=msg)


@app.route('/my_diary')
def my_diary():
    if 'username' not in session:
        return redirect('/login')
    my_entries = [d for d in diaries if d['user'] == session['username']]
    return render_template('my_diary.html', diaries=my_entries)

@app.route('/public_diary')
def public_diary():
    public_entries = [d for d in diaries if d['is_public']]
    return render_template('public_diary.html', diaries=public_entries)
