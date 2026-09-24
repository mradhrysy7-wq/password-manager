import sqlite3
from flask import Flask, request, render_template_string, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "super_secret_key_morad_fixed"

# --- 1. تهيئة قاعدة البيانات ---
def init_db():
    conn = sqlite3.connect("database_app_details.db")
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS app_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            app_name TEXT,          
            email TEXT,             
            app_username TEXT,      
            password TEXT,          
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

init_db()

# --- 2. قوالب HTML ---

AUTH_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تسجيل الدخول - مدير الحسابات الشامل</title>
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6038377293496140" crossorigin="anonymous"></script>
    <style>
        :root {
            --bg-color: #121212;
            --card-bg: rgba(30, 30, 30, 0.85);
            --text-color: #ffffff;
            --text-muted: #a0a0a0;
            --input-bg: rgba(50, 50, 50, 0.6);
            --input-border: #444444;
            --input-text: #ffffff;
            --border-color: #333333;
            --btn-bg: #2563eb;
            --btn-hover: #1d4ed8;
            --btn-outline-bg: #2a2a2a;
        }

        .light-theme {
            --bg-color: #f3f4f6;
            --card-bg: #ffffff;
            --text-color: #1f2937;
            --text-muted: #6b7280;
            --input-bg: #f9fafb;
            --input-border: #d1d5db;
            --input-text: #1f2937;
            --border-color: #e5e7eb;
            --btn-bg: #2563eb;
            --btn-hover: #1d4ed8;
            --btn-outline-bg: #ffffff;
        }

        * { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background-color: var(--bg-color); display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; color: var(--text-color); transition: background-color 0.3s ease; }
        
        .card { background: var(--card-bg); padding: 32px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); width: 100%; max-width: 380px; backdrop-filter: blur(10px); transition: background-color 0.3s ease; }
        
        /* تنسيق الجزء العلوي (أيقونة الليل والنهار والعنوان) */
        .header-section { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
        
        #themeToggle { background: none; border: none; cursor: pointer; font-size: 20px; padding: 0; transition: transform 0.2s; }
        #themeToggle:hover { transform: scale(1.1); }
        
        h2 { margin: 0; font-size: 20px; font-weight: 700; color: var(--text-color); }
        h4 { margin: 16px 0 12px 0; font-size: 14px; color: var(--text-muted); font-weight: 500; }
        
        input { width: 100%; padding: 10px 14px; margin-bottom: 12px; border: 1px solid var(--input-border); border-radius: 8px; font-size: 14px; outline: none; background: var(--input-bg); color: var(--input-text); transition: border-color 0.2s; }
        input:focus { border-color: var(--btn-bg); }
        
        button.action-btn { width: 100%; padding: 10px; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 14px; transition: background-color 0.2s; }
        .btn-primary { background: var(--btn-bg); color: #ffffff; }
        .btn-primary:hover { background: var(--btn-hover); }
        .btn-outline { background: var(--btn-outline-bg); border: 1px solid var(--input-border); color: var(--text-color); }
        
        hr { border: none; border-top: 1px solid var(--border-color); margin: 20px 0; }
    </style>
</head>
<body>
    <div class="card">
        <!-- الجزء العلوي: الأيقونة في الأعلى بجانب العنوان -->
        <div class="header-section">
            <button id="themeToggle" title="تبديل الثيم">☀️</button>
            <h2>مدير الحسابات الشامل</h2>
        </div>

        <form action="/login" method="POST">
            <input type="text" name="username" placeholder="اسم المستخدم للنظام" required>
            <input type="password" name="password" placeholder="كلمة السر للنظام" required>
            <button type="submit" class="action-btn btn-primary">تسجيل الدخول</button>
        </form>
        <hr>
        <form action="/register" method="POST">
            <h4>ليس لديك حساب؟</h4>
            <input type="text" name="username" placeholder="اسم مستخدم جديد" required>
            <input type="password" name="password" placeholder="كلمة السر الجديدة" required>
            <button type="submit" class="action-btn btn-outline">إنشاء حساب جديد</button>
        </form>
    </div>
    <script>
        const themeToggleBtn = document.getElementById('themeToggle');
        
        themeToggleBtn.addEventListener('click', () => {
            document.body.classList.toggle('light-theme');
            if (document.body.classList.contains('light-theme')) {
                themeToggleBtn.textContent = '🌙';
                localStorage.setItem('theme', 'light');
            } else {
                themeToggleBtn.textContent = '☀️';
                localStorage.setItem('theme', 'dark');
            }
        });

        // استعادة الثيم المحفوظ
        if (localStorage.getItem('theme') === 'light') {
            document.body.classList.add('light-theme');
            themeToggleBtn.textContent = '🌙';
        }
    </script>
</body>
</html>
"""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>لوحة التحكم - تفاصيل حسابات التطبيقات</title>
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-6038377293496140" crossorigin="anonymous"></script>
    <style>
        :root {
            --bg-color: #121212; --card-bg: #1e1e1e; --text-color: #cbd5e1; --text-heading: #f8fafc;
            --text-muted: #94a3b8; --border-color: #333333; --table-header-bg: #252525; --row-border: #2a2a2a;
            --input-bg: #2a2a2a; --input-border: #444444; --input-text: #ffffff; --tag-bg: #1e3a8a;
            --tag-text: #93c5fd; --logout-bg: #451a03; --logout-text: #f87171;
        }

        .light-theme {
            --bg-color: #f8fafc; --card-bg: #ffffff; --text-color: #334155; --text-heading: #0f172a;
            --text-muted: #64748b; --border-color: #e2e8f0; --table-header-bg: #f8fafc; --row-border: #f1f5f9;
            --input-bg: #ffffff; --input-border: #cbd5e1; --input-text: #1e293b; --tag-bg: #eff6ff;
            --tag-text: #1d4ed8; --logout-bg: #fef2f2; --logout-text: #ef4444;
        }

        * { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background-color: var(--bg-color); margin: 0; padding: 24px; color: var(--text-color); transition: background-color 0.3s ease; }
        .main-wrapper { max-width: 950px; margin: 0 auto; }
        
        .header { display: flex; justify-content: space-between; align-items: center; background: var(--card-bg); padding: 16px 24px; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 20px; border: 1px solid var(--border-color); }
        .header h2 { margin: 0; font-size: 18px; color: var(--text-heading); }
        .header-actions { display: flex; gap: 12px; align-items: center; }
        
        #themeToggle { background: none; border: 1px solid var(--input-border); color: var(--text-color); padding: 6px 10px; border-radius: 6px; cursor: pointer; font-size: 14px; }
        .logout { color: var(--logout-text); text-decoration: none; font-size: 14px; font-weight: 500; padding: 6px 12px; border-radius: 6px; background: var(--logout-bg); }

        .card { background: var(--card-bg); padding: 24px; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 20px; border: 1px solid var(--border-color); }
        .card-title { margin: 0 0 16px 0; font-size: 16px; font-weight: 600; color: var(--text-heading); border-bottom: 2px solid var(--border-color); padding-bottom: 8px; }

        .form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin-bottom: 15px; }
        .form-group label { display: block; font-size: 12px; font-weight: 600; color: var(--text-muted); margin-bottom: 6px; }
        .form-group input { width: 100%; padding: 10px 14px; border: 1px solid var(--input-border); border-radius: 8px; font-size: 14px; outline: none; background: var(--input-bg); color: var(--input-text); }
        .form-group input:focus { border-color: #2563eb; }
        
        .btn-submit { background: #2563eb; color: #ffffff; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 600; width: 100%; }
        .btn-submit:hover { background: #1d4ed8; }

        table { width: 100%; border-collapse: separate; border-spacing: 0; margin-top: 12px; }
        th { background: var(--table-header-bg); color: var(--text-muted); font-weight: 600; font-size: 13px; padding: 12px 14px; text-align: center; border-bottom: 1px solid var(--border-color); }
        td { padding: 14px 14px; text-align: center; border-bottom: 1px solid var(--row-border); font-size: 14px; color: var(--text-color); }
        tr:last-child td { border-bottom: none; }
        .tag { padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 500; display: inline-block; background: var(--tag-bg); color: var(--tag-text); }
    </style>
</head>
<body>
    <div class="main-wrapper">
        <div class="header">
            <h2>مرحباً، مراد 👋</h2>
            <div class="header-actions">
                <button id="themeToggle" title="تبديل الثيم">🌙 / ☀️</button>
                <a href="/logout" class="logout">تسجيل الخروج</a>
            </div>
        </div>

        <div class="card">
            <div class="card-title">📱 إضافة بيانات تطبيق (تويتر، انستغرام، وغيرها)</div>
            <form action="/add_app_account" method="POST">
                <div class="form-grid">
                    <div class="form-group">
                        <label>اسم التطبيق / الموقع</label>
                        <input type="text" name="app_name" placeholder="مثال: تويتر">
                    </div>
                    <div class="form-group">
                        <label>البريد الإلكتروني المرتبط</label>
                        <input type="email" name="email" placeholder="example@mail.com">
                    </div>
                    <div class="form-group">
                        <label>اسم المستخدم (Username)</label>
                        <input type="text" name="app_username" placeholder="@username">
                    </div>
                    <div class="form-group">
                        <label>كلمة المرور (Password)</label>
                        <input type="text" name="password" placeholder="كلمة المرور الخاصة بالتطبيق" required>
                    </div>
                </div>
                <button type="submit" class="btn-submit">حفظ بيانات التطبيق</button>
            </form>

            <table>
                <thead>
                    <tr>
                        <th style="width: 50px;">#</th>
                        <th>التطبيق / الموقع</th>
                        <th>البريد الإلكتروني</th>
                        <th>اسم المستخدم</th>
                        <th>كلمة المرور</th>
                    </tr>
                </thead>
                <tbody>
                    {% for row in accounts %}
                    <tr>
                        <td style="color: var(--text-muted);">{{ loop.index }}</td>
                        <td><span class="tag">{{ row[0] if row[0] else '-' }}</span></td>
                        <td style="color: var(--text-muted);">{{ row[1] if row[1] else '-' }}</td>
                        <td style="font-weight: 500; color: var(--text-heading);">{{ row[2] if row[2] else '-' }}</td>
                        <td style="font-family: monospace; font-weight: 600;">{{ row[3] }}</td>
                    </tr>
                    {% else %}
                    <tr><td colspan="5" style="color: var(--text-muted); padding: 20px;">لا توجد حسابات تطبيقات محفوظة بعد.</td></tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    <script>
        const themeToggleBtn = document.getElementById('themeToggle');
        
        themeToggleBtn.addEventListener('click', () => {
            document.body.classList.toggle('light-theme');
            if (document.body.classList.contains('light-theme')) {
                localStorage.setItem('theme', 'light');
            } else {
                localStorage.setItem('theme', 'dark');
            }
        });

        if (localStorage.getItem('theme') === 'light') {
            document.body.classList.add('light-theme');
        }
    </script>
</body>
</html>
"""

# --- 3. المسارات (Routes) ---

@app.route("/")
def index():
    if "user_id" in session:
        conn = sqlite3.connect("database_app_details.db")
        cursor = conn.cursor()
        cursor.execute("SELECT app_name, email, app_username, password FROM app_accounts WHERE user_id = ?", (session["user_id"],))
        accounts = cursor.fetchall()
        conn.close()
        return render_template_string(DASHBOARD_HTML, accounts=accounts)
    
    return render_template_string(AUTH_HTML)

@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username")
    password = request.form.get("password")
    hashed_password = generate_password_hash(password)
    
    try:
        conn = sqlite3.connect("database_app_details.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        conn.close()
        return "<script>alert('تم إنشاء الحساب بنجاح!'); window.location.href='/';</script>"
    except sqlite3.IntegrityError:
        return "<script>alert('اسم المستخدم موجود بالفعل!'); window.location.href='/';</script>"

@app.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")
    
    conn = sqlite3.connect("database_app_details.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    
    if user and check_password_hash(user[1], password):
        session["user_id"] = user[0]
        return redirect("/")
    else:
        return "<script>alert('اسم المستخدم أو كلمة السر غير صحيحة!'); window.location.href='/';</script>"

@app.route("/add_app_account", methods=["POST"])
def add_app_account():
    if "user_id" not in session: return redirect("/")
    app_name = request.form.get("app_name")
    email = request.form.get("email")
    app_username = request.form.get("app_username")
    password = request.form.get("password")
    
    conn = sqlite3.connect("database_app_details.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO app_accounts (user_id, app_name, email, app_username, password) VALUES (?, ?, ?, ?, ?)", 
                   (session["user_id"], app_name, email, app_username, password))
    conn.commit()
    conn.close()
    return redirect("/")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
