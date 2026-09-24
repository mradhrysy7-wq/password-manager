import sqlite3
from flask import Flask, request, render_template_string, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "super_secret_key_morad_dev"

# --- 1. تهيئة قاعدة البيانات والجداول ---
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            account_data TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- 2. قوالب HTML تصميم عصري ومرتب ---

AUTH_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>مدير الحسابات - تسجيل الدخول</title>
    <style>
        * { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background-color: #f3f4f6; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; color: #1f2937; }
        .card { background: #ffffff; padding: 32px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03); width: 100%; max-width: 360px; }
        h2 { margin: 0 0 24px 0; font-size: 20px; font-weight: 700; text-align: center; color: #111827; }
        h4 { margin: 16px 0 12px 0; font-size: 14px; color: #6b7280; font-weight: 500; }
        input { width: 100%; padding: 10px 14px; margin-bottom: 12px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 14px; outline: none; background: #f9fafb; }
        input:focus { border-color: #2563eb; background: #fff; box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1); }
        button { width: 100%; padding: 10px; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 14px; transition: background 0.2s; }
        .btn-primary { background: #2563eb; color: #ffffff; }
        .btn-primary:hover { background: #1d4ed8; }
        .btn-outline { background: #ffffff; border: 1px solid #d1d5db; color: #374151; }
        .btn-outline:hover { background: #f3f4f6; }
        hr { border: none; border-top: 1px solid #e5e7eb; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="card">
        <h2>مدير الحسابات الآمن</h2>
        <form action="/login" method="POST">
            <input type="text" name="username" placeholder="اسم المستخدم" required>
            <input type="password" name="password" placeholder="كلمة السر" required>
            <button type="submit" class="btn-primary">تسجيل الدخول</button>
        </form>
        <hr>
        <form action="/register" method="POST">
            <h4>ليس لديك حساب؟</h4>
            <input type="text" name="username" placeholder="اسم مستخدم جديد" required>
            <input type="password" name="password" placeholder="كلمة السر" required>
            <button type="submit" class="btn-outline">إنشاء حساب جديد</button>
        </form>
    </div>
</body>
</html>
"""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>لوحة التحكم</title>
    <style>
        * { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background-color: #f8fafc; margin: 0; padding: 24px; color: #334155; }
        .main-wrapper { max-width: 800px; margin: 0 auto; }
        
        /* Navbar / Header */
        .header { display: flex; justify-content: space-between; align-items: center; background: #ffffff; padding: 16px 24px; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 20px; }
        .header h2 { margin: 0; font-size: 18px; color: #0f172a; font-weight: 600; }
        .logout { color: #ef4444; text-decoration: none; font-size: 14px; font-weight: 500; padding: 6px 12px; border-radius: 6px; background: #fef2f2; }
        .logout:hover { background: #fee2e2; }

        /* Content Card */
        .card { background: #ffffff; padding: 24px; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 20px; }
        .card-title { margin: 0 0 16px 0; font-size: 15px; font-weight: 600; color: #475569; }

        /* Form Row (مصفوفة بجانب بعض) */
        .form-row { display: flex; gap: 10px; align-items: center; }
        .form-row select { padding: 10px 14px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 14px; background: #ffffff; color: #334155; outline: none; }
        .form-row input { flex: 1; padding: 10px 14px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 14px; outline: none; background: #ffffff; }
        .form-row input:focus, .form-row select:focus { border-color: #2563eb; }
        .form-row button { background: #2563eb; color: #ffffff; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 600; white-space: nowrap; }
        .form-row button:hover { background: #1d4ed8; }

        /* Table */
        table { width: 100%; border-collapse: separate; border-spacing: 0; margin-top: 8px; }
        th { background: #f8fafc; color: #64748b; font-weight: 600; font-size: 13px; padding: 12px 16px; text-align: center; border-bottom: 1px solid #e2e8f0; }
        td { padding: 14px 16px; text-align: center; border-bottom: 1px solid #f1f5f9; font-size: 14px; color: #1e293b; }
        tr:last-child td { border-bottom: none; }
        
        .tag { padding: 4px 10px; border-radius: 6px; font-size: 12px; font-weight: 500; display: inline-block; }
        .tag-email { background: #eff6ff; color: #1d4ed8; }
        .tag-app { background: #fefce8; color: #a16207; }
        .tag-gen { background: #f1f5f9; color: #475569; }
    </style>
</head>
<body>
    <div class="main-wrapper">
        <div class="header">
            <h2>مرحباً، {{ username }} 👋</h2>
            <a href="/logout" class="logout">تسجيل الخروج</a>
        </div>

        <div class="card">
            <div class="card-title">حفظ بيانات جديدة</div>
            <form action="/add_account" method="POST" class="form-row">
                <select name="category" required>
                    <option value="إيميل">إيميل</option>
                    <option value="تطبيق">تطبيق</option>
                    <option value="حساب عام">عام</option>
                </select>
                <input type="text" name="account_data" placeholder="البيانات أو كلمة السر..." required>
                <button type="submit">حفظ الحساب</button>
            </form>
        </div>

        <div class="card">
            <div class="card-title">حساباتك المحفوظة</div>
            <table>
                <thead>
                    <tr>
                        <th style="width: 60px;">#</th>
                        <th style="width: 120px;">النوع</th>
                        <th>البيانات المحفوظة</th>
                    </tr>
                </thead>
                <tbody>
                    {% for row in accounts %}
                    <tr>
                        <td style="color: #94a3b8;">{{ loop.index }}</td>
                        <td>
                            {% if row[0] == 'إيميل' %}
                                <span class="tag tag-email">إيميل</span>
                            {% elif row[0] == 'تطبيق' %}
                                <span class="tag tag-app">تطبيق</span>
                            {% else %}
                                <span class="tag tag-gen">عام</span>
                            {% endif %}
                        </td>
                        <td style="font-weight: 500;">{{ row[1] }}</td>
                    </tr>
                    {% else %}
                    <tr>
                        <td colspan="3" style="color: #94a3b8; padding: 24px;">لا توجد حسابات محفوظة حتى الآن.</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""

# --- 3. المسارات (Routes) ---

@app.route("/")
def index():
    if "user_id" in session:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute("SELECT category, account_data FROM user_accounts WHERE user_id = ?", (session["user_id"],))
        accounts = cursor.fetchall()
        conn.close()
        return render_template_string(DASHBOARD_HTML, username=session["username"], accounts=accounts)
    
    return render_template_string(AUTH_HTML)

@app.route("/register", methods=["POST"])
def register():
    username = request.form.get("username")
    password = request.form.get("password")
    hashed_password = generate_password_hash(password)
    
    try:
        conn = sqlite3.connect("database.db")
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
    
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    
    if user and check_password_hash(user[1], password):
        session["user_id"] = user[0]
        session["username"] = username
        return redirect("/")
    else:
        return "<script>alert('اسم المستخدم أو كلمة السر غير صحيحة!'); window.location.href='/';</script>"

@app.route("/add_account", methods=["POST"])
def add_account():
    if "user_id" not in session:
        return redirect("/")
        
    category = request.form.get("category")
    account_data = request.form.get("account_data")
    
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO user_accounts (user_id, category, account_data) VALUES (?, ?, ?)", 
                   (session["user_id"], category, account_data))
    conn.commit()
    conn.close()
    
    return redirect("/")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)