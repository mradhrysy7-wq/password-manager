import sqlite3
import os
import time
from flask import Flask, request, render_template_string, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.fernet import Fernet

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "morad_super_secure_adsense_key_2026")

KEY_FILE = "secret.key"
if os.path.exists(KEY_FILE):
    with open(KEY_FILE, "rb") as key_file:
        ENCRYPTION_KEY = key_file.read()
else:
    ENCRYPTION_KEY = Fernet.generate_key()
    with open(KEY_FILE, "wb") as key_file:
        key_file.write(ENCRYPTION_KEY)

cipher_suite = Fernet(ENCRYPTION_KEY)

def encrypt_password(plain_password):
    if not plain_password:
        return ""
    return cipher_suite.encrypt(plain_password.encode()).decode()

def decrypt_password(encrypted_password):
    if not encrypted_password:
        return ""
    try:
        return cipher_suite.decrypt(encrypted_password.encode()).decode()
    except Exception:
        return "[خطأ في فك التشفير]"

DB_PATH = os.path.join(os.getcwd(), "database_app_details.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db():
    conn = get_db_connection()
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
            account_type TEXT,
            app_username TEXT,      
            email TEXT,             
            password TEXT,          
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.before_request
def check_session_timeout():
    if "user_id" in session:
        now = time.time()
        last_active = session.get("last_active", now)
        if now - last_active > 900:
            session.clear()
            return redirect("/")
        session["last_active"] = now

# 1. صفحة المصادقة والترحيب بالزوار (Landing & Auth)
AUTH_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="google-site-verification" content="xfoF9HVlynNHlY9YLc-6XRs1XJcEd5BbxK8-U_dHq0g" />
    <title>مدير الحسابات الشامل - بوابة الأمان</title>
    <style>
        :root {
            --bg-color: #121212; --card-bg: rgba(30, 30, 30, 0.85); --text-color: #ffffff;
            --text-muted: #a0a0a0; --input-bg: rgba(50, 50, 50, 0.6); --input-border: #444444;
            --input-text: #ffffff; --border-color: #333333; --btn-bg: #2563eb; --btn-outline-bg: #2a2a2a;
            --guide-bg: rgba(37, 99, 235, 0.08); --guide-border: rgba(37, 99, 235, 0.25);
            --why-bg: rgba(16, 185, 129, 0.08); --why-border: rgba(16, 185, 129, 0.25);
        }
        .light-theme {
            --bg-color: #f3f4f6; --card-bg: #ffffff; --text-color: #1f2937; --text-muted: #6b7280;
            --input-bg: #f9fafb; --input-border: #d1d5db; --input-text: #1f2937; --border-color: #e5e7eb;
            --btn-bg: #2563eb; --btn-outline-bg: #ffffff;
            --guide-bg: #eff6ff; --guide-border: #bfdbfe;
            --why-bg: #ecfdf5; --why-border: #a7f3d0;
        }
        * { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background-color: var(--bg-color); display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; color: var(--text-color); transition: background-color 0.3s ease; padding: 20px; }
        .card { background: var(--card-bg); padding: 32px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); width: 100%; max-width: 480px; backdrop-filter: blur(10px); border: 1px solid var(--border-color); }
        .header-section { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
        #themeToggle { background: none; border: none; cursor: pointer; font-size: 20px; padding: 0; }
        h2 { margin: 0; font-size: 20px; font-weight: 700; color: var(--text-color); }
        h4 { margin: 16px 0 12px 0; font-size: 14px; color: var(--text-muted); font-weight: 500; }
        p.desc { font-size: 13px; color: var(--text-muted); margin-bottom: 16px; line-height: 1.5; }
        
        /* صناديق المعلومات الإرشادية والمقارنة */
        .info-box { border-radius: 8px; padding: 12px 14px; margin-bottom: 12px; font-size: 12px; line-height: 1.6; }
        
        .guide-box { background: var(--guide-bg); border: 1px solid var(--guide-border); }
        .guide-box h3 { margin: 0 0 6px 0; font-size: 13px; color: #60a5fa; display: flex; align-items: center; gap: 6px; }
        .light-theme .guide-box h3 { color: #2563eb; }

        .why-box { background: var(--why-bg); border: 1px solid var(--why-border); }
        .why-box h3 { margin: 0 0 6px 0; font-size: 13px; color: #34d399; display: flex; align-items: center; gap: 6px; }
        .light-theme .why-box h3 { color: #059669; }

        .info-box ul { margin: 0; padding-right: 18px; color: var(--text-color); }
        .info-box li { margin-bottom: 4px; }

        input { width: 100%; padding: 10px 14px; margin-bottom: 12px; border: 1px solid var(--input-border); border-radius: 8px; font-size: 14px; outline: none; background: var(--input-bg); color: var(--input-text); }
        button.action-btn { width: 100%; padding: 10px; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 14px; }
        .btn-primary { background: var(--btn-bg); color: #ffffff; }
        .btn-outline { background: var(--btn-outline-bg); border: 1px solid var(--input-border); color: var(--text-color); }
        hr { border: none; border-top: 1px solid var(--border-color); margin: 20px 0; }
        .links-footer { text-align: center; margin-top: 15px; }
        .links-footer a { color: var(--btn-bg); font-size: 13px; text-decoration: none; }
    </style>
</head>
<body>
    <div class="card">
        <div class="header-section">
            <button id="themeToggle" title="تبديل الثيم">☀️</button>
            <h2>مدير الحسابات الشامل</h2>
        </div>
        <p class="desc">منصة آمنة ومشفرة بالكامل لحفظ كلمات مرورك وتطبيقاتك في مكان واحد بكل ثقة.</p>
        
        <!-- 1. قسم طريقة الاستخدام -->
        <div class="info-box guide-box">
            <h3>📖 طريقة استخدام الموقع:</h3>
            <ul>
                <li><strong>إنشاء حساب:</strong> قم بإنشاء حسابك الخاص بكلمة مرور رئيسية فريدة.</li>
                <li><strong>تنظيم البيانات:</strong> اختر القسم المناسب (تطبيقات، بريد، مواقع) وأضف حساباتك.</li>
                <li><strong>العرض والنسخ:</strong> اضغط "إظهار" لاستعراض كلمة المرور المشفرة عند الحاجة.</li>
                <li><strong>حماية أوتوماتيكية:</strong> يُسجل النظام خروجك تلقائياً بعد 15 دقيقة خمول.</li>
            </ul>
        </div>

        <!-- 2. قسم لماذا تختار موقعنا بدل قوقل -->
        <div class="info-box why-box">
            <h3>💡 لماذا تختار موقعنا بدلاً من Google؟</h3>
            <ul>
                <li><strong>تشفير قوي وخاص (Fernet):</strong> كلمات مرورك تشفر بمفتاح خاص بك وليس مشافرة بسحابة شركة كبرى.</li>
                <li><strong>خصوصية وسرية 100%:</strong> لا يوجد تتبع للبيانات، لا إعلانات موجهة، ولا مشاركة لسلوكك.</li>
                <li><strong>ملكية كاملة للبيانات:</strong> بياناتك مخزنة في قاعدة بياناتك الخاصة تحت سيطرتك التامة.</li>
                <li><strong>إدارة مخصصة وسريعة:</strong> واجهة بسيطة بدون تعقيدات حسابات قوقل أو قيود المتصفح.</li>
            </ul>
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
            <input type="password" name="password" placeholder="كلمة السر الجديدة (6 أحرف على الأقل)" minlength="6" required>
            <button type="submit" class="action-btn btn-outline">إنشاء حساب جديد</button>
        </form>
        <div class="links-footer">
            <a href="/about">عن المشروع وسياسة الأمان</a>
        </div>
    </div>
    <script>
        const themeToggleBtn = document.getElementById('themeToggle');
        themeToggleBtn.addEventListener('click', () => {
            document.body.classList.toggle('light-theme');
            localStorage.setItem('theme', document.body.classList.contains('light-theme') ? 'light' : 'dark');
            themeToggleBtn.textContent = document.body.classList.contains('light-theme') ? '🌙' : '☀️';
        });
        if (localStorage.getItem('theme') === 'light') {
            document.body.classList.add('light-theme');
            themeToggleBtn.textContent = '🌙';
        }
    </script>
</body>
</html>
"""

# 2. الصفحة الرئيسية للمستخدم المسجل (Home / Dashboard)
HOME_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>الرئيسية - لوحة التحكم</title>
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-XXXXXXXXXXXXXXXX" crossorigin="anonymous"></script>
    <style>
        :root {
            --bg-color: #121212; --card-bg: #1e1e1e; --text-color: #cbd5e1; --text-heading: #f8fafc;
            --border-color: #333333; --logout-bg: #451a03; --logout-text: #f87171;
        }
        .light-theme {
            --bg-color: #f8fafc; --card-bg: #ffffff; --text-color: #334155; --text-heading: #0f172a;
            --border-color: #e2e8f0; --logout-bg: #fef2f2; --logout-text: #ef4444;
        }
        * { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background-color: var(--bg-color); margin: 0; padding: 24px; color: var(--text-color); transition: background-color 0.3s ease; }
        .main-wrapper { max-width: 800px; margin: 0 auto; }
        .header { display: flex; justify-content: space-between; align-items: center; background: var(--card-bg); padding: 16px 24px; border-radius: 12px; margin-bottom: 24px; border: 1px solid var(--border-color); flex-wrap: wrap; gap: 10px; }
        .header h2 { margin: 0; font-size: 18px; color: var(--text-heading); }
        .header-actions { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
        #themeToggle { background: none; border: 1px solid var(--border-color); color: var(--text-color); padding: 6px 10px; border-radius: 6px; cursor: pointer; }
        .btn-nav { text-decoration: none; color: var(--text-color); font-size: 13px; font-weight: 500; padding: 6px 12px; border-radius: 6px; background: var(--border-color); }
        .logout { color: var(--logout-text); text-decoration: none; font-size: 14px; font-weight: 500; padding: 6px 12px; border-radius: 6px; background: var(--logout-bg); }
        .grid-sections { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 24px; }
        .section-card { background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 12px; padding: 24px; text-align: center; text-decoration: none; color: var(--text-heading); transition: transform 0.2s, border-color 0.2s; }
        .section-card:hover { transform: translateY(-3px); border-color: #2563eb; }
        .section-card h3 { margin: 0 0 8px 0; font-size: 18px; }
        .section-card p { margin: 0; font-size: 13px; color: #94a3b8; }
    </style>
</head>
<body>
    <div class="main-wrapper">
        <div class="header">
            <h2>مرحباً، {{ username }} 👋 - لوحة التحكم</h2>
            <div class="header-actions">
                <a href="/settings" class="btn-nav">⚙️ الإعدادات</a>
                <a href="/about" class="btn-nav">ℹ️ عن الموقع</a>
                {% if username == 'morad' or username == 'admin' %}
                <a href="/admin/users" class="btn-nav" style="background: #1e3a8a; color: white;">👥 لوحة المشرف</a>
                {% endif %}
                <button id="themeToggle" title="تبديل الثيم">🌙 / ☀️</button>
                <a href="/logout" class="logout">تسجيل الخروج</a>
            </div>
        </div>
        <div class="grid-sections">
            <a href="/category/تطبيق" class="section-card">
                <h3>📱 التطبيقات والمنصات</h3>
                <p>إدارة حسابات التطبيقات</p>
            </a>
            <a href="/category/بريد" class="section-card">
                <h3>📧 البريد الإلكتروني</h3>
                <p>إدارة الإيميلات</p>
            </a>
            <a href="/category/موقع" class="section-card">
                <h3>🌐 المواقع الإلكترونية</h3>
                <p>إدارة حسابات المواقع والروابط</p>
            </a>
        </div>
    </div>
    <script>
        const themeToggleBtn = document.getElementById('themeToggle');
        themeToggleBtn.addEventListener('click', () => {
            document.body.classList.toggle('light-theme');
            localStorage.setItem('theme', document.body.classList.contains('light-theme') ? 'light' : 'dark');
        });
        if (localStorage.getItem('theme') === 'light') {
            document.body.classList.add('light-theme');
        }
    </script>
</body>
</html>
"""

# 3. صفحة إدارة الأقسام وتخزين الحسابات
CATEGORY_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>إدارة {{ cat_name }}</title>
    <style>
        :root {
            --bg-color: #121212; --card-bg: #1e1e1e; --text-color: #cbd5e1; --text-heading: #f8fafc;
            --text-muted: #94a3b8; --border-color: #333333; --table-header-bg: #252525; --row-border: #2a2a2a;
            --input-bg: #2a2a2a; --input-border: #444444; --input-text: #ffffff; --back-bg: #2a2a2a;
        }
        .light-theme {
            --bg-color: #f8fafc; --card-bg: #ffffff; --text-color: #334155; --text-heading: #0f172a;
            --text-muted: #64748b; --border-color: #e2e8f0; --table-header-bg: #f8fafc; --row-border: #f1f5f9;
            --input-bg: #ffffff; --input-border: #cbd5e1; --input-text: #1e293b; --back-bg: #e2e8f0;
        }
        * { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background-color: var(--bg-color); margin: 0; padding: 24px; color: var(--text-color); transition: background-color 0.3s ease; }
        .main-wrapper { max-width: 950px; margin: 0 auto; }
        .header { display: flex; justify-content: space-between; align-items: center; background: var(--card-bg); padding: 16px 24px; border-radius: 12px; margin-bottom: 20px; border: 1px solid var(--border-color); }
        .back-btn { text-decoration: none; color: var(--text-color); background: var(--back-bg); padding: 6px 14px; border-radius: 6px; font-size: 13px; font-weight: 500; }
        .card { background: var(--card-bg); padding: 24px; border-radius: 12px; margin-bottom: 20px; border: 1px solid var(--border-color); }
        .card-title { margin: 0 0 16px 0; font-size: 16px; font-weight: 600; color: var(--text-heading); border-bottom: 2px solid var(--border-color); padding-bottom: 8px; }
        .form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin-bottom: 15px; }
        .form-group label { display: block; font-size: 12px; font-weight: 600; color: var(--text-muted); margin-bottom: 6px; }
        .form-group input { width: 100%; padding: 10px 14px; border: 1px solid var(--input-border); border-radius: 8px; font-size: 14px; outline: none; background: var(--input-bg); color: var(--input-text); }
        .btn-submit { background: #2563eb; color: #ffffff; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 600; width: 100%; }
        .btn-submit:hover { background: #1d4ed8; }
        table { width: 100%; border-collapse: separate; border-spacing: 0; margin-top: 12px; }
        th { background: var(--table-header-bg); color: var(--text-muted); font-weight: 600; font-size: 13px; padding: 12px 14px; text-align: center; border-bottom: 1px solid var(--border-color); }
        td { padding: 14px 14px; text-align: center; border-bottom: 1px solid var(--row-border); font-size: 14px; color: var(--text-color); }
        .actions-cell { display: flex; gap: 8px; justify-content: center; }
        .btn-edit { background: #0284c7; color: white; padding: 5px 10px; border-radius: 6px; text-decoration: none; font-size: 12px; font-weight: 500; }
        .btn-delete { background: #dc2626; color: white; padding: 5px 10px; border-radius: 6px; text-decoration: none; font-size: 12px; font-weight: 500; }
        .pwd-container { display: flex; align-items: center; justify-content: center; gap: 6px; }
        .btn-reveal { background: #475569; color: white; border: none; padding: 3px 8px; border-radius: 4px; font-size: 11px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="main-wrapper">
        <div class="header">
            <h2 style="margin:0; font-size: 18px; color: var(--text-heading);">إدارة قسم: {{ cat_name }}</h2>
            <a href="/" class="back-btn">← العودة للرئيسية</a>
        </div>
        <div class="card">
            <div class="card-title">➕ إضافة حساب جديد في {{ cat_name }}</div>
            <form action="/add_item" method="POST">
                <input type="hidden" name="account_type" value="{{ cat_slug }}">
                <div class="form-grid">
                    {% if cat_slug == 'بريد' %}
                    <div class="form-group">
                        <label>البريد الإلكتروني</label>
                        <input type="email" name="email" placeholder="example@mail.com" required>
                    </div>
                    <div class="form-group">
                        <label>كلمة المرور (Password)</label>
                        <input type="text" name="password" placeholder="كلمة المرور" required>
                    </div>
                    {% elif cat_slug == 'تطبيق' %}
                    <div class="form-group">
                        <label>اسم التطبيق / الخدمة</label>
                        <input type="text" name="app_name" placeholder="مثال: تيليجرام..." required>
                    </div>
                    <div class="form-group">
                        <label>البريد الإلكتروني</label>
                        <input type="email" name="email" placeholder="example@mail.com">
                    </div>
                    <div class="form-group">
                        <label>اسم المستخدم (Username)</label>
                        <input type="text" name="app_username" placeholder="اسم المستخدم" required>
                    </div>
                    <div class="form-group">
                        <label>كلمة المرور (Password)</label>
                        <input type="text" name="password" placeholder="كلمة المرور" required>
                    </div>
                    {% else %}
                    <div class="form-group">
                        <label>اسم الموقع / الخدمة</label>
                        <input type="text" name="app_name" placeholder="مثال: جيت هب..." required>
                    </div>
                    <div class="form-group">
                        <label>البريد الإلكتروني</label>
                        <input type="email" name="email" placeholder="example@mail.com">
                    </div>
                    <div class="form-group">
                        <label>اسم المستخدم (Username)</label>
                        <input type="text" name="app_username" placeholder="اسم المستخدم">
                    </div>
                    <div class="form-group">
                        <label>كلمة المرور (Password)</label>
                        <input type="text" name="password" placeholder="كلمة المرور" required>
                    </div>
                    {% endif %}
                </div>
                <button type="submit" class="btn-submit">حفظ البيانات</button>
            </form>
            <table>
                <thead>
                    <tr>
                        <th style="width: 40px;">#</th>
                        {% if cat_slug == 'بريد' %}
                        <th>البريد الإلكتروني</th>
                        <th>كلمة المرور</th>
                        {% elif cat_slug == 'تطبيق' %}
                        <th>اسم التطبيق / الخدمة</th>
                        <th>البريد الإلكتروني</th>
                        <th>اسم المستخدم</th>
                        <th>كلمة المرور</th>
                        {% else %}
                        <th>اسم الموقع / الخدمة</th>
                        <th>البريد الإلكتروني</th>
                        <th>اسم المستخدم</th>
                        <th>كلمة المرور</th>
                        {% endif %}
                        <th style="width: 120px;">الإجراءات</th>
                    </tr>
                </thead>
                <tbody>
                    {% for row in accounts %}
                    <tr>
                        <td style="color: var(--text-muted);">{{ loop.index }}</td>
                        {% if cat_slug == 'بريد' %}
                        <td style="font-weight: 600; color: var(--text-heading);">{{ row[2] if row[2] else '-' }}</td>
                        <td>
                            <div class="pwd-container">
                                <span id="pwd-text-{{ row[0] }}">••••••••</span>
                                <button type="button" class="btn-reveal" onclick="togglePassword('{{ row[0] }}', this)">إظهار</button>
                            </div>
                        </td>
                        {% else %}
                        <td style="font-weight: 600; color: var(--text-heading);">{{ row[1] if row[1] else '-' }}</td>
                        <td style="color: var(--text-muted);">{{ row[2] if row[2] else '-' }}</td>
                        <td>{{ row[3] if row[3] else '-' }}</td>
                        <td>
                            <div class="pwd-container">
                                <span id="pwd-text-{{ row[0] }}">••••••••</span>
                                <button type="button" class="btn-reveal" onclick="togglePassword('{{ row[0] }}', this)">إظهار</button>
                            </div>
                        </td>
                        {% endif %}
                        <td class="actions-cell">
                            <a href="/edit/{{ row[0] }}" class="btn-edit">تعديل</a>
                            <a href="/delete/{{ row[0] }}" class="btn-delete" onclick="return confirm('هل أنت متأكد من الحذف؟');">حذف</a>
                        </td>
                    </tr>
                    {% else %}
                    <tr><td colspan="{{ 3 if cat_slug == 'بريد' else 6 }}" style="color: var(--text-muted); padding: 20px;">لا توجد حسابات مسجلة في هذا القسم.</td></tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    <script>
        function togglePassword(id, btn) {
            const span = document.getElementById('pwd-text-' + id);
            if (span.textContent === '••••••••') {
                fetch('/get_password/' + id)
                    .then(response => response.json())
                    .then(data => {
                        span.textContent = data.password;
                        btn.textContent = 'إخفاء';
                    });
            } else {
                span.textContent = '••••••••';
                btn.textContent = 'إظهار';
            }
        }
    </script>
</body>
</html>
"""

# صفحة تعديل العنصر
EDIT_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تعديل الحساب</title>
    <style>
        :root {
            --bg-color: #121212; --card-bg: #1e1e1e; --text-color: #cbd5e1; --text-heading: #f8fafc;
            --text-muted: #94a3b8; --border-color: #333333; --input-bg: #2a2a2a; --input-border: #444444; --input-text: #ffffff;
        }
        .light-theme {
            --bg-color: #f8fafc; --card-bg: #ffffff; --text-color: #334155; --text-heading: #0f172a;
            --text-muted: #64748b; --border-color: #e2e8f0; --input-bg: #ffffff; --input-border: #cbd5e1; --input-text: #1e293b;
        }
        * { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background-color: var(--bg-color); margin: 0; padding: 24px; color: var(--text-color); display: flex; justify-content: center; align-items: center; min-height: 100vh; }
        .card { background: var(--card-bg); padding: 32px; border-radius: 12px; width: 100%; max-width: 450px; border: 1px solid var(--border-color); }
        h2 { margin: 0 0 20px 0; font-size: 18px; color: var(--text-heading); border-bottom: 2px solid var(--border-color); padding-bottom: 8px; }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; font-size: 12px; font-weight: 600; color: var(--text-muted); margin-bottom: 6px; }
        .form-group input { width: 100%; padding: 10px 14px; border: 1px solid var(--input-border); border-radius: 8px; font-size: 14px; outline: none; background: var(--input-bg); color: var(--input-text); }
        .btn-submit { background: #2563eb; color: #ffffff; border: none; padding: 10px; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 600; width: 100%; margin-top: 10px; }
        .btn-cancel { display: block; text-align: center; margin-top: 10px; color: var(--text-muted); text-decoration: none; font-size: 13px; }
    </style>
</head>
<body>
    <div class="card">
        <h2>تعديل البيانات</h2>
        <form method="POST">
            {% if account[3] != 'بريد' %}
            <div class="form-group">
                <label>اسم التطبيق / الموقع</label>
                <input type="text" name="app_name" value="{{ account[2] or '' }}" required>
            </div>
            <div class="form-group">
                <label>البريد الإلكتروني</label>
                <input type="email" name="email" value="{{ account[5] or '' }}">
            </div>
            <div class="form-group">
                <label>اسم المستخدم</label>
                <input type="text" name="app_username" value="{{ account[4] or '' }}">
            </div>
            {% else %}
            <div class="form-group">
                <label>البريد الإلكتروني</label>
                <input type="email" name="email" value="{{ account[5] or '' }}" required>
            </div>
            {% endif %}
            <div class="form-group">
                <label>كلمة المرور الجديدة</label>
                <input type="text" name="password" placeholder="أدخل كلمة المرور الجديدة" required>
            </div>
            <button type="submit" class="btn-submit">حفظ التعديلات</button>
        </form>
        <a href="/category/{{ account[3] }}" class="btn-cancel">إلغاء والعودة</a>
    </div>
</body>
</html>
"""

# 4. صفحة الإعدادات والأمان الجديدة (/settings)
SETTINGS_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>إعدادات الحساب والأمان</title>
    <style>
        :root {
            --bg-color: #121212; --card-bg: #1e1e1e; --text-color: #cbd5e1; --text-heading: #f8fafc;
            --text-muted: #94a3b8; --border-color: #333333; --input-bg: #2a2a2a; --input-border: #444444; --input-text: #ffffff;
        }
        .light-theme {
            --bg-color: #f8fafc; --card-bg: #ffffff; --text-color: #334155; --text-heading: #0f172a;
            --text-muted: #64748b; --border-color: #e2e8f0; --input-bg: #ffffff; --input-border: #cbd5e1; --input-text: #1e293b;
        }
        * { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background-color: var(--bg-color); margin: 0; padding: 24px; color: var(--text-color); }
        .main-wrapper { max-width: 600px; margin: 0 auto; }
        .header { display: flex; justify-content: space-between; align-items: center; background: var(--card-bg); padding: 16px 24px; border-radius: 12px; margin-bottom: 20px; border: 1px solid var(--border-color); }
        .back-btn { text-decoration: none; color: var(--text-color); background: var(--border-color); padding: 6px 14px; border-radius: 6px; font-size: 13px; font-weight: 500; }
        .card { background: var(--card-bg); padding: 24px; border-radius: 12px; margin-bottom: 20px; border: 1px solid var(--border-color); }
        .card-title { margin: 0 0 16px 0; font-size: 16px; font-weight: 600; color: var(--text-heading); border-bottom: 2px solid var(--border-color); padding-bottom: 8px; }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; font-size: 12px; font-weight: 600; color: var(--text-muted); margin-bottom: 6px; }
        .form-group input { width: 100%; padding: 10px 14px; border: 1px solid var(--input-border); border-radius: 8px; font-size: 14px; outline: none; background: var(--input-bg); color: var(--input-text); }
        .btn-submit { background: #2563eb; color: #ffffff; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 600; width: 100%; }
        .btn-danger { background: #dc2626; color: #ffffff; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 600; width: 100%; }
    </style>
</head>
<body>
    <div class="main-wrapper">
        <div class="header">
            <h2 style="margin:0; font-size: 18px; color: var(--text-heading);">إعدادات الحساب والأمان</h2>
            <a href="/" class="back-btn">← العودة للرئيسية</a>
        </div>
        <div class="card">
            <div class="card-title">🔒 تغيير كلمة المرور الرئيسية</div>
            <form action="/update_credentials" method="POST">
                <div class="form-group">
                    <label>اسم المستخدم الحالي</label>
                    <input type="text" value="{{ username }}" disabled style="opacity: 0.7;">
                </div>
                <div class="form-group">
                    <label>كلمة المرور الجديدة للنظام</label>
                    <input type="password" name="new_password" placeholder="أدخل كلمة المرور الجديدة" required>
                </div>
                <button type="submit" class="btn-submit">تحديث كلمة المرور</button>
            </form>
        </div>
        <div class="card" style="border-color: #7f1d1d;">
            <div class="card-title" style="color: #f87171;">⚠️ منطقة الخطر - حذف الحساب</div>
            <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 15px;">حذف الحساب سيؤدي إلى مسح جميع حساباتك وكلمات المرور المخزنة نهائياً بشكل لا يمكن استرجاعه.</p>
            <form action="/delete_account" method="POST" onsubmit="return confirm('هل أنت متأكد تماماً من حذف حسابك وكل بياناتك نهائياً؟');">
                <button type="submit" class="btn-danger">حذف حسابي نهائياً</button>
            </form>
        </div>
    </div>
</body>
</html>
"""

# 5. صفحة عن الموقع وسياسة الأمان الجديدة (/about)
ABOUT_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>عن المشروع وسياسة الأمان</title>
    <style>
        :root {
            --bg-color: #121212; --card-bg: #1e1e1e; --text-color: #cbd5e1; --text-heading: #f8fafc;
            --text-muted: #94a3b8; --border-color: #333333;
        }
        .light-theme {
            --bg-color: #f8fafc; --card-bg: #ffffff; --text-color: #334155; --text-heading: #0f172a;
            --text-muted: #64748b; --border-color: #e2e8f0;
        }
        * { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background-color: var(--bg-color); margin: 0; padding: 24px; color: var(--text-color); }
        .main-wrapper { max-width: 700px; margin: 0 auto; }
        .header { display: flex; justify-content: space-between; align-items: center; background: var(--card-bg); padding: 16px 24px; border-radius: 12px; margin-bottom: 20px; border: 1px solid var(--border-color); }
        .back-btn { text-decoration: none; color: var(--text-color); background: var(--border-color); padding: 6px 14px; border-radius: 6px; font-size: 13px; font-weight: 500; }
        .card { background: var(--card-bg); padding: 28px; border-radius: 12px; margin-bottom: 20px; border: 1px solid var(--border-color); line-height: 1.7; }
        .card h3 { margin-top: 0; color: var(--text-heading); font-size: 18px; border-bottom: 2px solid var(--border-color); padding-bottom: 8px; }
        .card p { font-size: 14px; color: var(--text-color); }
    </style>
</head>
<body>
    <div class="main-wrapper">
        <div class="header">
            <h2 style="margin:0; font-size: 18px; color: var(--text-heading);">عن مدير الحسابات الشامل</h2>
            <a href="/" class="back-btn">← العودة للرئيسية</a>
        </div>
        <div class="card">
            <h3>🛡️ الخصوصية والأمان المتقدم</h3>
            <p>تم تصميم هذا النظام ليكون خيارك الآمن والموثوق لإدارة جميع كلمات المرور والتطبيقات والبريد الإلكتروني في مكان واحد. يعتمد الموقع على تقنيات تشفير قوية جداً باستخدام خوارزمية <strong>Fernet (Cryptographic Symmetric Encryption)</strong>، مما يضمن أن كلمات المرور الخاصة بك مشفرة تماماً داخل قاعدة البيانات ولا يمكن لأحد قراءتها سواك.</p>
        </div>
        <div class="card">
            <h3>🚀 رؤية المشروع</h3>
            <p>هدفنا هو تقديم أداة برمجية نظيفة، سريعة، وخالية من تتبع الإعلانات المزعجة، مصممة بأعلى معايير هندسة البرمجيات لتوفير تجربة مستخدم سلسلة وآمنة على السحابة.</p>
        </div>
    </div>
</body>
</html>
"""

# 6. لوحة تحكم المشرف (/admin/users)
ADMIN_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>لوحة تحكم المشرف</title>
    <style>
        :root {
            --bg-color: #121212; --card-bg: #1e1e1e; --text-color: #cbd5e1; --text-heading: #f8fafc;
            --text-muted: #94a3b8; --border-color: #333333; --table-header-bg: #252525; --row-border: #2a2a2a;
        }
        .light-theme {
            --bg-color: #f8fafc; --card-bg: #ffffff; --text-color: #334155; --text-heading: #0f172a;
            --text-muted: #64748b; --border-color: #e2e8f0; --table-header-bg: #f8fafc; --row-border: #f1f5f9;
        }
        * { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background-color: var(--bg-color); margin: 0; padding: 24px; color: var(--text-color); }
        .main-wrapper { max-width: 850px; margin: 0 auto; }
        .header { display: flex; justify-content: space-between; align-items: center; background: var(--card-bg); padding: 16px 24px; border-radius: 12px; margin-bottom: 20px; border: 1px solid var(--border-color); }
        .back-btn { text-decoration: none; color: var(--text-color); background: var(--border-color); padding: 6px 14px; border-radius: 6px; font-size: 13px; font-weight: 500; }
        .card { background: var(--card-bg); padding: 24px; border-radius: 12px; border: 1px solid var(--border-color); }
        table { width: 100%; border-collapse: separate; border-spacing: 0; margin-top: 12px; }
        th { background: var(--table-header-bg); color: var(--text-muted); font-weight: 600; font-size: 13px; padding: 12px 14px; text-align: center; border-bottom: 1px solid var(--border-color); }
        td { padding: 14px 14px; text-align: center; border-bottom: 1px solid var(--row-border); font-size: 14px; color: var(--text-color); }
    </style>
</head>
<body>
    <div class="main-wrapper">
        <div class="header">
            <h2 style="margin:0; font-size: 18px; color: var(--text-heading);">👥 لوحة تحكم المشرف (إدارة المستخدمين)</h2>
            <a href="/" class="back-btn">← العودة للرئيسية</a>
        </div>
        <div class="card">
            <table>
                <thead>
                    <tr>
                        <th>معرف المستخدم (ID)</th>
                        <th>اسم المستخدم</th>
                        <th>عدد الحسابات المحفوظة</th>
                    </tr>
                </thead>
                <tbody>
                    {% for u in users_data %}
                    <tr>
                        <td>{{ u[0] }}</td>
                        <td style="font-weight: 600; color: var(--text-heading);">{{ u[1] }}</td>
                        <td>{{ u[2] }} حسابات</td>
                    </tr>
                    {% else %}
                    <tr><td colspan="3" style="color: var(--text-muted); padding: 20px;">لا توجد حسابات مسجلة في النظام.</td></tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""

@app.route("/")
def index():
    if "user_id" in session:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE id = ?", (session["user_id"],))
        user_row = cursor.fetchone()
        conn.close()
        username = user_row[0] if user_row else "مستخدم"
        return render_template_string(HOME_HTML, username=username)
    return render_template_string(AUTH_HTML)

@app.route("/category/<cat_slug>")
def category_view(cat_slug):
    if "user_id" not in session: return redirect("/")
    cat_names = {"تطبيق": "التطبيقات والمنصات", "بريد": "البريد الإلكتروني", "موقع": "المواقع الإلكترونية"}
    cat_name = cat_names.get(cat_slug, "الحسابات")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, app_name, email, app_username, password FROM app_accounts WHERE user_id = ? AND account_type = ?", (session["user_id"], cat_slug))
    accounts = cursor.fetchall()
    conn.close()
    return render_template_string(CATEGORY_HTML, cat_name=cat_name, cat_slug=cat_slug, accounts=accounts)

@app.route("/get_password/<int:item_id>")
def get_password(item_id):
    if "user_id" not in session: return {"password": "Unauthorized"}, 403
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM app_accounts WHERE id = ? AND user_id = ?", (item_id, session["user_id"]))
    row = cursor.fetchone()
    conn.close()
    if row:
        decrypted = decrypt_password(row[0])
        return {"password": decrypted}
    return {"password": "Not Found"}, 404

@app.route("/add_item", methods=["POST"])
def add_item():
    current_user_id = session.get("user_id")
    if not current_user_id:
        return redirect("/")
        
    account_type = request.form.get("account_type")
    if account_type == "بريد":
        app_name, email, app_username = None, request.form.get("email"), None
    else:
        app_name, email, app_username = request.form.get("app_name"), request.form.get("email"), request.form.get("app_username")
    
    raw_password = request.form.get("password")
    encrypted_pwd = encrypt_password(raw_password)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    cursor.execute("INSERT INTO app_accounts (user_id, account_type, app_name, app_username, email, password) VALUES (?, ?, ?, ?, ?, ?)", 
                   (current_user_id, account_type, app_name, app_username, email, encrypted_pwd))
    conn.commit()
    conn.close()
    return redirect(f"/category/{account_type}")

@app.route("/edit/<int:item_id>", methods=["GET", "POST"])
def edit_item(item_id):
    if "user_id" not in session: return redirect("/")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == "POST":
        raw_password = request.form.get("password")
        encrypted_pwd = encrypt_password(raw_password)
        email, app_name, app_username = request.form.get("email"), request.form.get("app_name"), request.form.get("app_username")
        
        cursor.execute("UPDATE app_accounts SET app_name = ?, app_username = ?, email = ?, password = ? WHERE id = ? AND user_id = ?",
                       (app_name, app_username, email, encrypted_pwd, item_id, session["user_id"]))
        conn.commit()
        cursor.execute("SELECT account_type FROM app_accounts WHERE id = ?", (item_id,))
        acc_type = cursor.fetchone()[0]
        conn.close()
        return redirect(f"/category/{acc_type}")
        
    cursor.execute("SELECT * FROM app_accounts WHERE id = ? AND user_id = ?", (item_id, session["user_id"]))
    account = cursor.fetchone()
    conn.close()
    if not account: return "العنصر غير موجود أو لا تملك صلاحية الوصول إليه."
    return render_template_string(EDIT_HTML, account=account)

@app.route("/delete/<int:item_id>")
def delete_item(item_id):
    if "user_id" not in session: return redirect("/")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT account_type FROM app_accounts WHERE id = ? AND user_id = ?", (item_id, session["user_id"]))
    row = cursor.fetchone()
    if row:
        acc_type = row[0]
        cursor.execute("DELETE FROM app_accounts WHERE id = ? AND user_id = ?", (item_id, session["user_id"]))
        conn.commit()
        conn.close()
        return redirect(f"/category/{acc_type}")
    conn.close()
    return redirect("/")

@app.route("/settings", methods=["GET"])
def settings_page():
    if "user_id" not in session: return redirect("/")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE id = ?", (session["user_id"],))
    user_row = cursor.fetchone()
    conn.close()
    username = user_row[0] if user_row else ""
    return render_template_string(SETTINGS_HTML, username=username)

@app.route("/update_credentials", methods=["POST"])
def update_credentials():
    if "user_id" not in session: return redirect("/")
    new_password = request.form.get("new_password", "").strip()
    if not new_password: return "<script>alert('يرجى ادخال كلمة المرور الجديدة!'); window.location.href='/settings';</script>"
    
    hashed_password = generate_password_hash(new_password)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hashed_password, session["user_id"]))
    conn.commit()
    conn.close()
    return "<script>alert('تم تحديث كلمة المرور بنجاح!'); window.location.href='/settings';</script>"

@app.route("/delete_account", methods=["POST"])
def delete_account():
    if "user_id" not in session: return redirect("/")
    user_id = session["user_id"]
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM app_accounts WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    session.clear()
    return redirect("/")

@app.route("/about")
def about_page():
    return render_template_string(ABOUT_HTML)

@app.route("/admin/users")
def admin_users():
    if "user_id" not in session: return redirect("/")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE id = ?", (session["user_id"],))
    user_row = cursor.fetchone()
    if not user_row or user_row[0] not in ['morad', 'admin']:
        conn.close()
        return "غير مسموح لك بالوصول لهذه الصفحة.", 403
    
    cursor.execute('''
        SELECT users.id, users.username, COUNT(app_accounts.id) 
        FROM users 
        LEFT JOIN app_accounts ON users.id = app_accounts.user_id 
        GROUP BY users.id
    ''')
    users_data = cursor.fetchall()
    conn.close()
    return render_template_string(ADMIN_HTML, users_data=users_data)

@app.route("/register", methods=["POST"])
def register():
    username, password = request.form.get("username", "").strip(), request.form.get("password", "").strip()
    if not username or not password: return "<script>alert('يرجى تعبئة جميع الحقول!'); window.location.href='/';</script>"
    hashed_password = generate_password_hash(password)
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        conn.close()
        return "<script>alert('تم إنشاء الحساب بنجاح!'); window.location.href='/';</script>"
    except sqlite3.IntegrityError:
        return "<script>alert('اسم المستخدم موجود بالفعل!'); window.location.href='/';</script>"

@app.route("/login", methods=["POST"])
def login():
    username, password = request.form.get("username", "").strip(), request.form.get("password", "").strip()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, password_hash FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    if user and check_password_hash(user[1], password):
        session["user_id"] = user[0]
        session["last_active"] = time.time()
        return redirect("/")
    else:
        return "<script>alert('اسم المستخدم أو كلمة السر غير صحيحة!'); window.location.href='/';</script>"

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
