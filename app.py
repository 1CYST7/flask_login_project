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

# 模擬資料
users = {}  # username -> hashed password
diaries = []  # 每筆字典：user, content, is_public, image, comments:[]
notifications = []  # 每筆字典：owner, from_user, message

# 檢查副檔名是否合法
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return redirect('/login')

# 註冊
@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username in users:
            msg = "此帳號已被使用"
        elif not username.isalnum():
            msg = "帳號只能用英文和數字"
        else:
            users[username] = generate_password_hash(password)
            return redirect('/login')
    return render_template('register.html', msg=msg)


# 登入
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
            msg = "帳號或密碼錯誤"
    return render_template('login.html', msg=msg)



# 發表日記
@app.route('/write', methods=['GET', 'POST'])
def write():
    if 'username' not in session:
        return redirect('/login')
    msg = ""
    if request.method == 'POST':
        content = request.form['content']
        is_public = 'is_public' in request.form
        image_file = request.files.get('image')
        image_filename = None
        if image_file and allowed_file(image_file.filename):
            image_filename = secure_filename(image_file.filename)
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
        diaries.append({
            'user': session['username'],
            'content': content,
            'is_public': is_public,
            'image': image_filename,
            'comments': []
        })
        msg = "發表成功"
    return render_template('write.html', msg=msg)


# 我的日記
@app.route('/my_diary')
def my_diary():
    if 'username' not in session:
        return redirect('/login')
    my = [d for d in diaries if d['user'] == session['username']]
    return render_template('my_diary.html', diaries=my)

@app.route('/public_diary', methods=['GET', 'POST'])
def public_diary():
    if 'username' not in session:
        return redirect('/login')

    if request.method == 'POST':
        idx = int(request.form['diary_index'])
        comment = request.form['comment']
        diary = diaries[idx]
        comment_data = {
            'user': session['username'],
            'text': comment
        }
        diary['comments'].append(comment_data)

        # 加入通知
        if diary['user'] != session['username']:
            notifications.append({
                'owner': diary['user'],
                'from_user': session['username'],
                'message': f"在你的日記留言：{comment}"
            })
        return redirect('/public_diary')

    public = [(i, d) for i, d in enumerate(diaries) if d['is_public']]
    return render_template('public_diary.html', diaries=public)

# 通知頁面
@app.route('/notifications')
def notify():
    if 'username' not in session:
        return redirect('/login')
    my_notify = [n for n in notifications if n['owner'] == session['username']]
    return render_template('notification.html', notifications=my_notify)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/login')