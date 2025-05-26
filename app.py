from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# 設定圖片上傳資料夾與允許格式
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 模擬資料
users = {}  # username -> hashed password
diaries = []  # 每筆日記：user, content, is_public, image, comments:[]
notifications = []  # 每筆通知：owner, from_user, message, diary_index

# 副檔名檢查

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


# 公開日記 + 留言功能
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

        # 留言通知
        if diary['user'] != session['username']:
            notifications.append({
                'owner': diary['user'],
                'from_user': session['username'],
                'message': f"在你的日記留言：{comment}",
                'diary_index': idx,
                'forward_from': None  # 預設為 None，如果是轉發則儲存原始作者的 username
            })

        return redirect('/public_diary')

    public = [(i, d) for i, d in enumerate(diaries) if d['is_public']]
    return render_template('public_diary.html', diaries=public)



#查看原文時也能留言
@app.route('/view_diary/<int:index>', methods=['GET', 'POST'])
def view_diary(index):
    if 'username' not in session:
        return redirect('/login')

    # 確認 index 是否有效
    if index < 0 or index >= len(diaries):
        return "找不到這篇日記", 404

    diary = diaries[index]

    if request.method == 'POST':
        comment = request.form['comment'].strip()
        if comment:
            comment_data = {
                'user': session['username'],
                'text': comment
            }
            diary['comments'].append(comment_data)

            # 新增通知
            if diary['user'] != session['username']:
                notifications.append({
                    'owner': diary['user'],
                    'from_user': session['username'],
                    'message': f"在你的日記留言：{comment}",
                    'diary_index': index
                   
                })

        return redirect(url_for('view_diary', index=index))

    return render_template('view_diary.html', diary=diary, index=index)
# 轉發日記
@app.route('/forward_diary', methods=['POST'])
def forward_diary():
    if 'username' not in session:
        return redirect('/login')

    idx = int(request.form['diary_index'])
    original = diaries[idx]

    # 新增轉發日記
    diaries.append({
        'user': session['username'],
        'content': original['content'],
        'is_public': True,
        'image': original['image'],
        'comments': [],
        'forward_from': original['user']  # 標記原作者
    })

    # 新增通知給原作者
    if original['user'] != session['username']:
        notifications.append({
            'owner': original['user'],
            'from_user': session['username'],
            'message': f"轉發了你的日記：{original['content'][:20]}"
        })

    return redirect('/public_diary')



# 通知中心
@app.route('/notifications')
def notify():
    if 'username' not in session:
        return redirect('/login')

    my_notify = [n for n in notifications if n['owner'] == session['username']]
    return render_template('notification.html', notifications=my_notify)


# 登出
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect('/login')
