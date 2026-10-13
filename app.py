import hashlib
import os
import secrets
import smtplib
import sqlite3
import time
from datetime import datetime
from email.message import EmailMessage

from cryptography.fernet import Fernet
from flask import (
    Flask,
    flash,
    redirect,
    render_template_string,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get(
    'SECRET_KEY', 'morad_super_secure_adsense_key_2026'
)

KEY_FILE = 'secret.key'
if os.path.exists(KEY_FILE):
  with open(KEY_FILE, 'rb') as key_file:
    ENCRYPTION_KEY = key_file.read()
else:
  ENCRYPTION_KEY = Fernet.generate_key()
  with open(KEY_FILE, 'wb') as key_file:
    key_file.write(ENCRYPTION_KEY)

cipher_suite = Fernet(ENCRYPTION_KEY)


def encrypt_password(plain_password):
  if not plain_password:
    return ''
  return cipher_suite.encrypt(plain_password.encode()).decode()


def decrypt_password(encrypted_password):
  if not encrypted_password:
    return ''
  try:
    return cipher_suite.decrypt(encrypted_password.encode()).decode()
  except Exception:
    return '[خطأ في فك التشفير]'


DB_PATH = os.path.join(os.getcwd(), 'database_app_details.db')


def get_db_connection():
  conn = sqlite3.connect(DB_PATH)
  conn.execute('PRAGMA foreign_keys = ON;')
  return conn


def init_db():
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT
        )
    """)
  # ترقية قواعد البيانات القديمة دون حذف الحسابات أو كلمات المرور المحفوظة.
  user_columns = {
      row[1] for row in cursor.execute('PRAGMA table_info(users)').fetchall()
  }
  if 'email' not in user_columns:
    cursor.execute('ALTER TABLE users ADD COLUMN email TEXT')
  cursor.execute(
      'CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_unique ON'
      ' users(email COLLATE NOCASE) WHERE email IS NOT NULL AND email != ""'
  )
  cursor.execute("""
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
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS auth_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            purpose TEXT NOT NULL,
            code_hash TEXT NOT NULL,
            payload TEXT,
            expires_at REAL NOT NULL,
            attempts INTEGER NOT NULL DEFAULT 0
        )
    """)
  conn.commit()
  conn.close()


init_db()


@app.before_request
def check_session_timeout():
  if 'user_id' in session:
    now = time.time()
    last_active = session.get('last_active', now)
    if now - last_active > 900:
      session.clear()
      return redirect('/')
    session['last_active'] = now


# 1. صفحة المصادقة والترحيب بالزوار (Landing & Auth - الواجهة الحديثة)
AUTH_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="google-site-verification" content="xfoF9HVlynNHlY9YLc-6XRs1XJcEd5BbxK8-U_dHq0g" />
    <title>مدير الحسابات الشامل | أمان وخصوصية كلمات المرور</title>
    <style>
        :root {
            --bg-color: #0b0f19; --card-bg: #111827; --text-color: #9ca3af; --text-heading: #f9fafc;
            --input-bg: #1f2937; --input-border: #374151; --input-text: #ffffff;
            --btn-bg: #16a34a; --btn-hover: #15803d; --border-color: #1f2937;
        }
        .light-theme {
            --bg-color: #f3f4f6; --card-bg: #ffffff; --text-color: #4b5563; --text-heading: #111827;
            --input-bg: #f9fafb; --input-border: #d1d5db; --input-text: #111827;
            --btn-bg: #16a34a; --btn-hover: #15803d; --border-color: #e5e7eb;
        }
        * { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background-color: var(--bg-color); margin: 0; padding: 20px; color: var(--text-color); min-height: 100vh; transition: background-color 0.3s; }
        .top-bar { display: flex; justify-content: space-between; align-items: center; max-width: 1000px; margin: 0 auto 30px auto; }
        .logo { font-size: 20px; font-weight: 700; color: var(--text-heading); display: flex; align-items: center; gap: 8px; }
        #themeToggle { background: none; border: 1px solid var(--border-color); color: var(--text-heading); padding: 6px 12px; border-radius: 8px; cursor: pointer; }
        
        .hero { text-align: center; max-width: 700px; margin: 0 auto 40px auto; }
        .badge { background: rgba(37, 99, 235, 0.1); color: #3b82f6; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; display: inline-block; margin-bottom: 12px; }
        .hero h1 { font-size: 32px; color: var(--text-heading); margin: 0 0 12px 0; font-weight: 800; }
        .hero p { font-size: 15px; line-height: 1.6; margin: 0; }

        .auth-container { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; max-width: 850px; margin: 0 auto 50px auto; }
        .auth-card { background: var(--card-bg); border: 1px solid var(--border-color); padding: 28px; border-radius: 16px; box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3); }
        .auth-card h3 { margin: 0 0 20px 0; font-size: 18px; color: var(--text-heading); display: flex; align-items: center; justify-content: center; gap: 8px; }
        
        input { width: 100%; padding: 12px 14px; margin-bottom: 14px; border: 1px solid var(--input-border); border-radius: 8px; font-size: 14px; outline: none; background: var(--input-bg); color: var(--input-text); text-align: right; }
        button.action-btn { width: 100%; padding: 12px; border: none; border-radius: 8px; font-weight: 700; cursor: pointer; font-size: 14px; background: var(--btn-bg); color: #ffffff; transition: background 0.2s; }
        button.action-btn:hover { background: var(--btn-hover); }

        .features-section { max-width: 950px; margin: 0 auto; text-align: center; }
        .features-title { font-size: 20px; color: var(--text-heading); margin-bottom: 24px; font-weight: 700; }
        .features-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; }
        .feature-item { background: var(--card-bg); border: 1px solid var(--border-color); padding: 20px; border-radius: 12px; }
        .feature-icon { font-size: 24px; margin-bottom: 8px; }
        .feature-item h4 { margin: 0 0 6px 0; color: var(--text-heading); font-size: 15px; }
        .feature-item p { margin: 0; font-size: 12px; line-height: 1.5; }
        
        footer { text-align: center; margin-top: 50px; padding-bottom: 20px; font-size: 13px; }
        footer a { color: #3b82f6; text-decoration: none; }
    </style>
</head>
<body>
    <div class="top-bar">
        <div class="logo">🔐 مدير الحسابات</div>
        <button id="themeToggle">🌙 / ☀️</button>
    </div>

    <div class="hero">
        <span class="badge">أمان وخصوصية</span>
        <h1>كلمات مرورك، تحت سيطرتك</h1>
        <p>احفظ حساباتك بأمان وسهولة وأدر جميع اشتراكاتك وتطبيقاتك في مكان واحد وبأعلى درجات التشفير.</p>
    </div>

    <div class="auth-container">
        <!-- كرت تسجيل الدخول -->
        <div class="auth-card">
            <h3>🔑 تسجيل الدخول</h3>
            <form action="/login" method="POST">
                <input type="email" name="email" placeholder="البريد الإلكتروني" autocomplete="email" required>
                <input type="password" name="password" placeholder="كلمة المرور" required>
                <button type="submit" class="action-btn">متابعة وإرسال رمز التحقق</button>
            </form>
            <p style="text-align:center"><a href="/forgot-password" style="color:#60a5fa">نسيت كلمة المرور؟</a></p>
        </div>

        <!-- كرت إنشاء حساب جديد -->
        <div class="auth-card">
            <h3>✨ إنشاء حساب جديد</h3>
            <form action="/register" method="POST">
                <input type="email" name="email" placeholder="بريدك الإلكتروني" autocomplete="email" required>
                <input type="password" name="password" placeholder="كلمة المرور (6 أحرف على الأقل)" minlength="6" required>
                <button type="submit" class="action-btn">إنشاء حساب جديد</button>
            </form>
        </div>
    </div>

    <div class="features-section">
        <div class="badge">المميزات</div>
        <h2 class="features-title">لماذا تختار مدير الحسابات؟</h2>
        <div class="features-grid">
            <div class="feature-item">
                <div class="feature-icon">🔒</div>
                <h4>تشفير قوي</h4>
                <p>بياناتك مشفرة بتقنيات Fernet المتقدمة.</p>
            </div>
            <div class="feature-item">
                <div class="feature-icon">🛡️</div>
                <h4>خصوصية تامة</h4>
                <p>لا نشارك بياناتك ولا نستخدم أدوات تتبع.</p>
            </div>
            <div class="feature-item">
                <div class="feature-icon">⚡</div>
                <h4>سهل الاستخدام</h4>
                <p>واجهة بسيطة وواضحة تناسب الحسابات اليومية.</p>
            </div>
            <div class="feature-item">
                <div class="feature-icon">📱</div>
                <h4>دعم الأجهزة</h4>
                <p>استخدمه بسهولة من الجوال أو اللابتوب.</p>
            </div>
        </div>
    </div>

    <footer>
        <a href="/about">عن المشروع وسياسة الأمان</a>
    </footer>

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

# 2. الصفحة الرئيسية للمستخدم المسجل (Home / Dashboard)
HOME_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>الرئيسية - لوحة التحكم</title>
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
                btn.textContent = 'إخفاء';
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


@app.route('/')
def index():
  if 'user_id' in session:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        'SELECT username FROM users WHERE id = ?', (session['user_id'],)
    )
    user_row = cursor.fetchone()
    conn.close()
    username = user_row[0] if user_row else 'مستخدم'
    return render_template_string(HOME_HTML, username=username)
  return render_template_string(AUTH_HTML)


@app.route('/category/<cat_slug>')
def category_view(cat_slug):
  if 'user_id' not in session:
    return redirect('/')
  cat_names = {
      'تطبيق': 'التطبيقات والمنصات',
      'بريد': 'البريد الإلكتروني',
      'موقع': 'المواقع الإلكترونية',
  }
  cat_name = cat_names.get(cat_slug, 'الحسابات')

  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
      'SELECT id, app_name, email, app_username, password FROM app_accounts'
      ' WHERE user_id = ? AND account_type = ?',
      (session['user_id'], cat_slug),
  )
  accounts = cursor.fetchall()
  conn.close()
  return render_template_string(
      CATEGORY_HTML, cat_name=cat_name, cat_slug=cat_slug, accounts=accounts
  )


@app.route('/get_password/<int:item_id>')
def get_password(item_id):
  if 'user_id' not in session:
    return {'password': 'Unauthorized'}, 403
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
      'SELECT password FROM app_accounts WHERE id = ? AND user_id = ?',
      (item_id, session['user_id']),
  )
  row = cursor.fetchone()
  conn.close()
  if row:
    decrypted = decrypt_password(row[0])
    return {'password': decrypted}
  return {'password': 'Not Found'}, 404


@app.route('/add_item', methods=['POST'])
def add_item():
  current_user_id = session.get('user_id')
  if not current_user_id:
    return redirect('/')

  account_type = request.form.get('account_type')
  if account_type == 'بريد':
    app_name, email, app_username = None, request.form.get('email'), None
  else:
    app_name, email, app_username = (
        request.form.get('app_name'),
        request.form.get('email'),
        request.form.get('app_username'),
    )

  raw_password = request.form.get('password')
  encrypted_pwd = encrypt_password(raw_password)

  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute('PRAGMA foreign_keys = ON;')
  cursor.execute(
      'INSERT INTO app_accounts (user_id, account_type, app_name,'
      ' app_username, email, password) VALUES (?, ?, ?, ?, ?, ?)',
      (
          current_user_id,
          account_type,
          app_name,
          app_username,
          email,
          encrypted_pwd,
      ),
  )
  conn.commit()
  conn.close()
  return redirect(f'/category/{account_type}')


@app.route('/edit/<int:item_id>', methods=['GET', 'POST'])
def edit_item(item_id):
  if 'user_id' not in session:
    return redirect('/')
  conn = get_db_connection()
  cursor = conn.cursor()

  if request.method == 'POST':
    raw_password = request.form.get('password')
    encrypted_pwd = encrypt_password(raw_password)
    email, app_name, app_username = (
        request.form.get('email'),
        request.form.get('app_name'),
        request.form.get('app_username'),
    )

    cursor.execute(
        'UPDATE app_accounts SET app_name = ?, app_username = ?, email = ?,'
        ' password = ? WHERE id = ? AND user_id = ?',
        (
            app_name,
            app_username,
            email,
            encrypted_pwd,
            item_id,
            session['user_id'],
        ),
    )
    conn.commit()
    cursor.execute(
        'SELECT account_type FROM app_accounts WHERE id = ?', (item_id,)
    )
    acc_type = cursor.fetchone()[0]
    conn.close()
    return redirect(f'/category/{acc_type}')

  cursor.execute(
      'SELECT * FROM app_accounts WHERE id = ? AND user_id = ?',
      (item_id, session['user_id']),
  )
  account = cursor.fetchone()
  conn.close()
  if not account:
    return 'العنصر غير موجود أو لا تملك صلاحية الوصول إليه.'
  return render_template_string(EDIT_HTML, account=account)


@app.route('/delete/<int:item_id>')
def delete_item(item_id):
  if 'user_id' not in session:
    return redirect('/')
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
      'SELECT account_type FROM app_accounts WHERE id = ? AND user_id = ?',
      (item_id, session['user_id']),
  )
  row = cursor.fetchone()
  if row:
    acc_type = row[0]
    cursor.execute(
        'DELETE FROM app_accounts WHERE id = ? AND user_id = ?',
        (item_id, session['user_id']),
    )
    conn.commit()
    conn.close()
    return redirect(f'/category/{acc_type}')
  conn.close()
  return redirect('/')


@app.route('/settings', methods=['GET'])
def settings_page():
  if 'user_id' not in session:
    return redirect('/')
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
      'SELECT username FROM users WHERE id = ?', (session['user_id'],)
  )
  user_row = cursor.fetchone()
  conn.close()
  username = user_row[0] if user_row else ''
  return render_template_string(SETTINGS_HTML, username=username)


@app.route('/update_credentials', methods=['POST'])
def update_credentials():
  if 'user_id' not in session:
    return redirect('/')
  new_password = request.form.get('new_password', '').strip()
  if not new_password:
    return (
        '<script>alert("يرجى ادخال كلمة المرور الجديدة!");'
        ' window.location.href="/settings";</script>'
    )

  hashed_password = generate_password_hash(new_password)
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
      'UPDATE users SET password_hash = ? WHERE id = ?',
      (hashed_password, session['user_id']),
  )
  conn.commit()
  conn.close()
  return (
      '<script>alert("تم تحديث كلمة المرور بنجاح!");'
      ' window.location.href="/settings";</script>'
  )


@app.route('/delete_account', methods=['POST'])
def delete_account():
  if 'user_id' not in session:
    return redirect('/')
  user_id = session['user_id']
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute('DELETE FROM app_accounts WHERE user_id = ?', (user_id,))
  cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
  conn.commit()
  conn.close()
  session.clear()
  return redirect('/')


@app.route('/about')
def about_page():
  return render_template_string(ABOUT_HTML)


@app.route('/admin/users')
def admin_users():
  if 'user_id' not in session:
    return redirect('/')
  conn = get_db_connection()
  cursor = conn.cursor()
  cursor.execute(
      'SELECT username FROM users WHERE id = ?', (session['user_id'],)
  )
  user_row = cursor.fetchone()
  if not user_row or user_row[0] not in ['morad', 'admin']:
    conn.close()
    return 'غير مسموح لك بالوصول لهذه الصفحة.', 403

  cursor.execute("""
        SELECT users.id, users.username, COUNT(app_accounts.id) 
        FROM users 
        LEFT JOIN app_accounts ON users.id = app_accounts.user_id 
        GROUP BY users.id
    """)
  users_data = cursor.fetchall()
  conn.close()
  return render_template_string(ADMIN_HTML, users_data=users_data)


def send_email_code(to_email, code, purpose):
  """Send a one-time code using SMTP environment settings."""
  smtp_host = os.environ.get('SMTP_HOST', 'smtp.gmail.com').strip()
  smtp_port = int(os.environ.get('SMTP_PORT', '465'))
  smtp_user = os.environ.get('SMTP_USER', '').strip()
  smtp_password = os.environ.get('SMTP_PASSWORD', '')
  smtp_from = os.environ.get('SMTP_FROM', smtp_user).strip()
  if not all([smtp_host, smtp_user, smtp_password, smtp_from]):
    raise RuntimeError(
        'إعدادات البريد غير مكتملة: SMTP_HOST وSMTP_PORT وSMTP_USER'
        ' وSMTP_PASSWORD وSMTP_FROM'
    )
  msg = EmailMessage()
  msg['Subject'] = 'رمز التحقق - مدير الحسابات'
  msg['From'] = smtp_from
  msg['To'] = to_email
  msg.set_content(
      f'مرحبًا،\n\nرمز التحقق الخاص بك هو: {code}\n'
      'صلاحية الرمز 10 دقائق. لا تشارك الرمز مع أي شخص.\n\n'
      'إذا لم تطلب هذا الرمز، فتجاهل الرسالة.'
  )
  # التعديل الرئيسي: استخدام SMTP_SSL بدلاً من SMTP مع starttls لدعم المنفذ 465
  with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=20) as server:
    server.login(smtp_user, smtp_password)
    server.send_message(msg)


def create_email_code(email, purpose, payload=None):
  code = f'{secrets.randbelow(1000000):06d}'
  code_hash = hashlib.sha256(code.encode()).hexdigest()
  conn = get_db_connection()
  try:
    conn.execute(
        'DELETE FROM auth_codes WHERE email = ? AND purpose = ?',
        (email, purpose),
    )
    conn.execute(
        'INSERT INTO auth_codes (email, purpose, code_hash, payload,'
        ' expires_at, attempts) VALUES (?, ?, ?, ?, ?, 0)',
        (email, purpose, code_hash, payload, time.time() + 600),
    )
    conn.commit()
  finally:
    conn.close()
  send_email_code(email, code, purpose)


def verify_email_code(email, purpose, code):
  conn = get_db_connection()
  try:
    row = conn.execute(
        'SELECT id, code_hash, payload, expires_at, attempts FROM auth_codes '
        'WHERE email = ? AND purpose = ? ORDER BY id DESC LIMIT 1',
        (email, purpose),
    ).fetchone()
    if not row or row[3] < time.time() or row[4] >= 5:
      return None
    conn.execute(
        'UPDATE auth_codes SET attempts = attempts + 1 WHERE id = ?', (row[0],)
    )
    conn.commit()
    if secrets.compare_digest(
        row[1], hashlib.sha256(code.strip().encode()).hexdigest()
    ):
      conn.execute(
          'DELETE FROM auth_codes WHERE email = ? AND purpose = ?',
          (email, purpose),
      )
      conn.commit()
      return row[2]
    return False
  finally:
    conn.close()


OTP_HTML = """
<!doctype html><html lang="ar" dir="rtl"><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ title }}</title>
<style>
body{margin:0;background:#0b0f19;color:#f9fafb;font-family:Arial,sans-serif;display:grid;place-items:center;min-height:100vh;padding:18px;box-sizing:border-box}
.card{width:min(420px,100%);background:#111827;border:1px solid #374151;border-radius:16px;padding:26px;box-sizing:border-box}
p{color:#cbd5e1;line-height:1.7}input{width:100%;box-sizing:border-box;padding:13px;margin:8px 0 16px;background:#1f2937;color:white;border:1px solid #4b5563;border-radius:8px}
button{width:100%;padding:13px;border:0;border-radius:8px;background:#16a34a;color:white;font-weight:bold;cursor:pointer}
a{color:#93c5fd} .error{color:#fca5a5}
</style><div class="card"><h2>{{ title }}</h2><p>{{ message }}</p>
{% if error %}<p class="error">{{ error }}</p>{% endif %}
<form method="post"><input type="hidden" name="email" value="{{ email }}">
{% if mode == 'code' %}<label>رمز التحقق المرسل إلى بريدك</label><input name="code" inputmode="numeric" pattern="[0-9]{6}" maxlength="6" placeholder="000000" required>
{% elif mode == 'new_password' %}<label>كلمة المرور الجديدة</label><input type="password" name="password" minlength="6" placeholder="6 أحرف على الأقل" required>
{% endif %}<button type="submit">{{ button }}</button></form><p><a href="/">العودة إلى الصفحة الرئيسية</a></p></div></html>
"""


@app.route('/verify-registration', methods=['GET', 'POST'])
def verify_registration():
  email = session.get('pending_registration_email', '')
  if not email:
    return redirect('/')
  error = ''
  if request.method == 'POST':
    payload = verify_email_code(email, 'register', request.form.get('code', ''))
    if payload is not False and payload is not None:
      # Pending data is kept in the signed session, not in the URL.
      password_hash = session.get('pending_registration_password_hash')
      if not password_hash:
        session.pop('pending_registration_email', None)
        return redirect('/')
      conn = get_db_connection()
      try:
        conn.execute(
            'INSERT INTO users (username, password_hash, email) VALUES (?, ?,'
            ' ?)',
            (email, password_hash, email),
        )
        conn.commit()
      except sqlite3.IntegrityError:
        error = 'هذا البريد مسجل بالفعل. جرّب تسجيل الدخول.'
      finally:
        conn.close()
      if not error:
        session.pop('pending_registration_email', None)
        session.pop('pending_registration_password_hash', None)
        return (
            '<script>alert("تم التحقق وإنشاء الحساب بنجاح. سجّل الدخول'
            ' الآن."); location.href="/";</script>'
        )
    else:
      error = 'الرمز غير صحيح أو انتهت صلاحيته. حاول طلب رمز جديد.'
  return render_template_string(
      OTP_HTML,
      title='تأكيد البريد الإلكتروني',
      message=f'أرسلنا رمز تحقق إلى {email}. أدخل الرمز خلال 10 دقائق.',
      mode='code',
      email=email,
      button='تأكيد البريد',
      error=error,
  )


@app.route('/verify-login', methods=['GET', 'POST'])
def verify_login():
  email = session.get('pending_login_email', '')
  if not email:
    return redirect('/')
  error = ''
  if request.method == 'POST':
    result = verify_email_code(email, 'login', request.form.get('code', ''))
    if result is not False and result is not None:
      user_id = session.get('pending_login_user_id')
      session.pop('pending_login_email', None)
      session.pop('pending_login_user_id', None)
      session['user_id'] = user_id
      session['last_active'] = time.time()
      return redirect('/')
    error = 'الرمز غير صحيح أو انتهت صلاحيته. حاول مرة أخرى.'
  return render_template_string(
      OTP_HTML,
      title='رمز تسجيل الدخول',
      message=f'أرسلنا رمزًا إلى {email}. أدخل الرمز لإكمال تسجيل الدخول.',
      mode='code',
      email=email,
      button='تأكيد وتسجيل الدخول',
      error=error,
  )


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
  error = ''
  if request.method == 'POST':
    email = request.form.get('email', '').strip().lower()
    conn = get_db_connection()
    user = conn.execute(
        'SELECT id FROM users WHERE lower(email) = ?', (email,)
    ).fetchone()
    conn.close()
    if user:
      try:
        create_email_code(email, 'reset')
        session['pending_reset_email'] = email
        return redirect('/reset-password')
      except Exception:
        app.logger.exception('Email delivery failed for password reset')
        error = 'تعذر إرسال الرمز. إعدادات البريد تحتاج إلى ضبط.'
    else:
      # Avoid disclosing whether an account exists.
      error = (
          'إذا كان البريد مسجلًا، فستصلك رسالة. تحقق من البريد أو جرّب مرة'
          ' أخرى.'
      )
  return render_template_string(
      """
    <!doctype html><html lang="ar" dir="rtl"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <style>body{background:#0b0f19;color:white;font-family:Arial;display:grid;place-items:center;min-height:100vh;padding:18px}.card{background:#111827;padding:26px;border-radius:14px;width:min(420px,100%);box-sizing:border-box}input,button{box-sizing:border-box;width:100%;padding:13px;margin:10px 0;border-radius:8px}input{background:#1f2937;color:white;border:1px solid #374151}button{background:#16a34a;color:white;border:0;font-weight:bold}.err{color:#fca5a5}a{color:#93c5fd}</style>
    <div class="card"><h2>استعادة كلمة المرور</h2><p>اكتب بريدك الإلكتروني لنرسل لك رمز إعادة التعيين.</p>{% if error %}<p class="err">{{ error }}</p>{% endif %}
    <form method="post"><input type="email" name="email" placeholder="البريد الإلكتروني" required><button>إرسال رمز التحقق</button></form><a href="/">العودة لتسجيل الدخول</a></div></html>
    """,
      error=error,
  )


@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
  email = session.get('pending_reset_email', '')
  if not email:
    return redirect('/forgot-password')
  error = ''
  if request.method == 'POST':
    code = request.form.get('code', '')
    result = verify_email_code(email, 'reset', code)
    if result is not False and result is not None:
      session['reset_code_verified_email'] = email
      return redirect('/choose-new-password')
    error = 'الرمز غير صحيح أو انتهت صلاحيته.'
  return render_template_string(
      OTP_HTML,
      title='التحقق لاستعادة الحساب',
      message=f'أرسلنا رمز استعادة إلى {email}. أدخل الرمز خلال 10 دقائق.',
      mode='code',
      email=email,
      button='التحقق من الرمز',
      error=error,
  )


@app.route('/choose-new-password', methods=['GET', 'POST'])
def choose_new_password():
  email = session.get('reset_code_verified_email', '')
  if not email:
    return redirect('/forgot-password')
  error = ''
  if request.method == 'POST':
    password = request.form.get('password', '')
    if len(password) < 6:
      error = 'كلمة المرور يجب أن تكون 6 أحرف على الأقل.'
    else:
      conn = get_db_connection()
      conn.execute(
          'UPDATE users SET password_hash = ? WHERE lower(email) = ?',
          (generate_password_hash(password), email),
      )
      conn.commit()
      conn.close()
      session.pop('pending_reset_email', None)
      session.pop('reset_code_verified_email', None)
      return (
          '<script>alert("تم تغيير كلمة المرور بنجاح. يمكنك تسجيل'
          ' الدخول."); location.href="/";</script>'
      )
  return render_template_string(
      OTP_HTML,
      title='إنشاء كلمة مرور جديدة',
      message='اكتب كلمة المرور الجديدة. استخدم 6 أحرف على الأقل.',
      mode='new_password',
      email=email,
      button='حفظ كلمة المرور الجديدة',
      error=error,
  )


@app.route('/register', methods=['POST'])
def register():
  email = request.form.get('email', '').strip().lower()
  password = request.form.get('password', '')
  if not email or '@' not in email or '.' not in email.rsplit('@', 1)[-1]:
    return (
        '<script>alert("يرجى إدخال بريد إلكتروني صحيح.");'
        ' location.href="/";</script>'
    )
  if len(password) < 6:
    return (
        '<script>alert("كلمة المرور يجب أن تكون 6 أحرف على الأقل.");'
        ' location.href="/";</script>'
    )
  conn = get_db_connection()
  exists = conn.execute(
      'SELECT 1 FROM users WHERE lower(email) = ? OR lower(username) = ?',
      (email, email),
  ).fetchone()
  conn.close()
  if exists:
    return (
        '<script>alert("هذا البريد مسجل بالفعل. جرّب تسجيل الدخول.");'
        ' location.href="/";</script>'
    )
  session['pending_registration_email'] = email
  session['pending_registration_password_hash'] = generate_password_hash(
      password
  )
  try:
    create_email_code(email, 'register')
    return redirect('/verify-registration')
  except Exception:
    app.logger.exception('Email delivery failed during registration')
    session.pop('pending_registration_email', None)
    session.pop('pending_registration_password_hash', None)
    return (
        '<script>alert("تعذر إرسال رمز التحقق. يجب ضبط إعدادات البريد'
        ' أولًا."); location.href="/";</script>'
    )


@app.route('/login', methods=['POST'])
def login():
  email = request.form.get('email', '').strip().lower()
  password = request.form.get('password', '')
  conn = get_db_connection()
  user = conn.execute(
      'SELECT id, password_hash, email FROM users WHERE lower(email) = ? OR'
      ' lower(username) = ? LIMIT 1',
      (email, email),
  ).fetchone()
  conn.close()
  if user and check_password_hash(user[1], password):
    verified_email = user[2] or (email if '@' in email else '')
    if not verified_email or '@' not in verified_email:
      return (
          '<script>alert("هذا الحساب القديم لا يملك بريدًا موثقًا. أضف بريدًا'
          ' إلكترونيًا أولًا."); location.href="/";</script>'
      )
    session['pending_login_email'] = verified_email
    session['pending_login_user_id'] = user[0]
    try:
      create_email_code(verified_email, 'login')
      return redirect('/verify-login')
    except Exception:
      app.logger.exception('Email delivery failed during login')
      session.pop('pending_login_email', None)
      session.pop('pending_login_user_id', None)
      return (
          '<script>alert("تعذر إرسال رمز الدخول. إعدادات البريد تحتاج إلى'
          ' ضبط."); location.href="/";</script>'
      )
  return (
      '<script>alert("البريد الإلكتروني أو كلمة المرور غير صحيحة.");'
      ' location.href="/";</script>'
  )


@app.route('/logout')
def logout():
  session.clear()
  return redirect('/')


if __name__ == '__main__':
  app.run(debug=True)
