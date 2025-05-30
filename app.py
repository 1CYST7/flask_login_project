from datetime import datetime  # 匯入處理時間的模組
from flask import Flask, render_template, request, redirect, session, url_for  # 匯入 Flask 相關功能
from werkzeug.security import generate_password_hash, check_password_hash  # 密碼雜湊與驗證函式
from werkzeug.utils import secure_filename  # 取得安全的檔案名稱
import os  # 作業系統相關操作模組

app = Flask(__name__)  # 建立 Flask 應用程式實例
app.secret_key = os.urandom(24)  # 設定 session 的密鑰，使用隨機亂數增強安全性

# 設定圖片上傳資料夾與允許的副檔名
UPLOAD_FOLDER = 'static/uploads'  # 圖片存放的資料夾路徑
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}  # 允許的圖片副檔名集合
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER  # 將上傳資料夾路徑設定到 Flask 配置

# 模擬資料存放區（實務應使用資料庫）
users = {}  # 字典：username -> hashed password (使用者資料)
diaries = []  # 日記列表，每筆日記為字典，包括用戶、內容、是否公開、圖片、留言等
notifications = []  # 通知列表，每筆通知為字典，包含擁有者、發起者、訊息等


def allowed_file(filename):
    # 確認檔名有「.」且副檔名在允許清單內（忽略大小寫）
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# 根目錄路由，直接轉址到登入頁面
@app.route('/')
def home():
    return redirect('/login')


# 註冊頁面，可處理 GET 與 POST 請求
@app.route('/register', methods=['GET', 'POST'])
def register():
    msg = ""  # 初始化訊息字串
    if request.method == 'POST':  # 若使用者送出註冊表單
        username = request.form['username']  # 取得輸入帳號
        password = request.form['password']  # 取得輸入密碼

        if username in users:  # 帳號已存在
            msg = "此帳號已被使用"
        elif not username.isalnum():  # 帳號格式非英數字
            msg = "帳號只能用英文和數字"
        else:
            # 密碼雜湊並存入使用者資料字典
            users[username] = generate_password_hash(password)
            return redirect('/login')  # 註冊成功導向登入頁
    # GET 請求或註冊失敗時呈現註冊頁並帶入訊息
    return render_template('register.html', msg=msg)


# 登入頁面，可處理 GET 與 POST 請求
@app.route('/login', methods=['GET', 'POST'])
def login():
    msg = ""  # 初始化訊息字串
    if request.method == 'POST':  # 使用者送出登入表單
        username = request.form['username']  # 取得輸入帳號
        password = request.form['password']  # 取得輸入密碼

        # 檢查帳號是否存在且密碼正確
        if username in users and check_password_hash(users[username], password):
            session['username'] = username  # 登入成功將帳號寫入 session
            return redirect('/my_diary')  # 導向「我的日記」頁面
        else:
            msg = "帳號或密碼錯誤"  # 登入失敗訊息
    # GET 請求或登入失敗時呈現登入頁並帶入訊息
    return render_template('login.html', msg=msg)


# 撰寫日記頁面，可處理 GET 與 POST
@app.route('/write', methods=['GET', 'POST'])
def write():
    if 'username' not in session:  # 若未登入，導向登入頁
        return redirect('/login')

    msg = ""  # 初始化訊息字串
    if request.method == 'POST':  # 使用者送出日記表單
        content = request.form['content']  # 取得日記內容文字
        is_public = 'is_public' in request.form  # 判斷是否公開（日記 checkbox）
        image_file = request.files.get('image')  # 取得圖片檔案物件（若有）
        image_filename = None  # 初始化圖片檔名為 None

        # 若有上傳圖片且格式允許
        if image_file and allowed_file(image_file.filename):
            image_filename = secure_filename(image_file.filename)  # 取得安全檔名
            # 將圖片存入指定上傳資料夾
            image_file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

        # 將新日記加入日記清單
        diaries.append({
            'user': session['username'],  # 日記作者
            'content': content,  # 內容文字
            'is_public': is_public,  # 是否公開
            'image': image_filename,  # 圖片檔名（若有）
            'comments': [],  # 留言列表，初始為空
            'created_at': datetime.now(),  # 建立時間，使用現在時間
            'forward_from': None  # 預設為 None，表示非轉發日記
        })
        msg = "發表成功"  # 成功訊息

    # GET 請求或發表成功時渲染撰寫日記頁面並帶訊息
    return render_template('write.html', msg=msg)


# 顯示「我的日記」頁面
@app.route('/my_diary')
def my_diary():
    if 'username' not in session:  # 未登入導向登入頁
        return redirect('/login')

    # 從日記清單篩選出屬於該使用者的日記
    my = [d for d in diaries if d['user'] == session['username']]
    return render_template('my_diary.html', diaries=my)  # 傳入使用者的日記


# 公開日記頁面與留言功能
@app.route('/public_diary', methods=['GET', 'POST'])
def public_diary():
    if 'username' not in session:  # 未登入導向登入頁
        return redirect('/login')

    if request.method == 'POST':  # 有留言送出
        idx = int(request.form['diary_index'])  # 取得留言的日記索引
        comment = request.form['comment']  # 取得留言文字

        diary = diaries[idx]  # 取得該篇日記物件
        comment_data = {
            'user': session['username'],  # 留言使用者
            'text': comment,  # 留言內容
            'created_at': datetime.now()  # 留言時間
        }
        diary['comments'].append(comment_data)  # 將留言加入該日記留言列表

        # 若留言者不是日記作者，新增通知
        if diary['user'] != session['username']:
            notifications.append({
                'owner': diary['user'],  # 通知擁有者（日記作者）
                'from_user': session['username'],  # 留言者
                'message': f"在你的日記留言：{comment}",  # 通知訊息
                'diary_index': idx,  # 日記索引
                'created_at': datetime.now(),  # 通知時間
                'forward_from': None  # 通知欄位，預設 None
            })

        return redirect('/public_diary')  # 留言後刷新公開日記頁

    # GET 請求時，篩選所有公開日記並附上索引
    public = [(i, d) for i, d in enumerate(diaries) if d['is_public']]
    # 依建立時間由新到舊排序
    public.sort(key=lambda x: x[1]['created_at'], reverse=True)
    
    return render_template('public_diary.html', diaries=public)  # 傳入公開日記列表


# 查看單篇日記並留言（URL 帶日記索引）
@app.route('/view_diary/<int:index>', methods=['GET', 'POST'])
def view_diary(index):
    if 'username' not in session:  # 未登入導向登入頁
        return redirect('/login')

    # 確認日記索引有效
    if index < 0 or index >= len(diaries):
        return "找不到這篇日記", 404  # 索引無效回傳 404 錯誤

    diary = diaries[index]  # 取得指定日記

    if request.method == 'POST':  # 使用者留言送出
        comment = request.form['comment'].strip()  # 取得留言內容並去除空白
        if comment:
            comment_data = {
                'user': session['username'],  # 留言使用者
                'text': comment,  # 留言內容
                'created_at': datetime.now()  # 留言時間
            }
            diary['comments'].append(comment_data)  # 加入留言列表

            # 若留言者非日記作者，新增通知
            if diary['user'] != session['username']:
                notifications.append({
                    'owner': diary['user'],  # 通知擁有者（日記作者）
                    'from_user': session['username'],  # 留言者
                    'message': f"在你的日記留言：{comment}",  # 通知訊息
                    'diary_index': index  # 日記索引
                })

        # 留言後刷新該篇日記頁面
        return redirect(url_for('view_diary', index=index))

    # GET 請求，呈現該篇日記頁面並帶入日記內容和索引
    return render_template('view_diary.html', diary=diary, index=index)


# 轉發日記功能 (POST)
@app.route('/forward_diary', methods=['POST'])
def forward_diary():
    if 'username' not in session:  # 未登入導向登入頁
        return redirect('/login')

    idx = int(request.form['diary_index'])  # 取得轉發的日記索引
    original = diaries[idx]  # 取得原始日記內容

    # 新增一筆轉發日記，內容與圖片皆複製，並標示轉發來源
    diaries.append({
        'user': session['username'],  # 轉發者為當前使用者
        'content': original['content'],  # 原文內容
        'is_public': True,  # 轉發日記必為公開
        'image': original['image'],  # 複製圖片檔名
        'comments': [],  # 留言清空
        'created_at': datetime.now(),  # 轉發時間
        'forward_from': original['user']  # 記錄原作者 username
    })

    # 若轉發者不是原作者，通知原作者有人轉發
    if original['user'] != session['username']:
        notifications.append({
            'owner': original['user'],  # 通知擁有者（原作者）
            'from_user': session['username'],  # 轉發者
            'message': f"轉發了你的日記：{original['content'][:20]}"  # 通知訊息，顯示前20字
        })

    return redirect('/public_diary')  # 轉發後回公開日記頁


# 通知中心頁面
@app.route('/notifications')
def notify():
    if 'username' not in session:  # 未登入導向登入頁
        return redirect('/login')

    # 取得屬於當前使用者的所有通知
    my_notify = [n for n in notifications if n['owner'] == session['username']]
    return render_template('notification.html', notifications=my_notify)  # 傳入通知列表


# 登出路由，清除 session
@app.route('/logout')
def logout():
    session.pop('username', None)  # 移除 session 中的 username (若存在)
    return redirect('/login')  # 導回登入頁
