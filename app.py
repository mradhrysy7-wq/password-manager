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

# 1. صفحة المصادقة والترحيب المحدثة بجميع الأقسام المقترحة
AUTH_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>مدير الحسابات الشامل - أمانك وخصوصيتك أولاً</title>
    <style>
        :root {
            --bg-color: #0d1117; 
            --card-bg: rgba(22, 27, 34, 0.85); 
            --card-border: #30363d;
            --text-color: #c9d1d9; 
            --text-heading: #ffffff;
            --text-muted: #8b949e; 
            --input-bg: #161b22; 
            --input-border: #30363d;
            --input-text: #ffffff; 
            --btn-bg: #238636; 
            --btn-hover: #2ea043;
            --btn-outline-bg: #21262d; 
            --accent-blue: #2f81f7;
            --accent-red: #f85149;
        }
        .light-theme {
            --bg-color: #f6f8fa; 
            --card-bg: #ffffff; 
            --card-border: #d0d7de;
            --text-color: #24292f; 
            --text-heading: #0f172a;
            --text-muted: #57606a; 
            --input-bg: #ffffff; 
            --input-border: #d0d7de;
            --input-text: #1f2937; 
            --btn-bg: #2da44e; 
            --btn-hover: #2c974b;
            --btn-outline-bg: #f3f4f6; 
            --accent-blue: #0969da;
            --accent-red: #cf222e;
        }
        * { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; scroll-behavior: smooth; }
        body { background-color: var(--bg-color); margin: 0; padding: 0; color: var(--text-color); transition: background-color 0.3s ease; }
        
        .navbar { display: flex; justify-content: space-between; align-items: center; padding: 16px 24px; background: var(--card-bg); border-bottom: 1px solid var(--card-border); position: sticky; top: 0; z-index: 100; backdrop-filter: blur(10px); }
        .navbar h2 { margin: 0; font-size: 18px; color: var(--text-heading); display: flex; align-items: center; gap: 8px; }
        #themeToggle { background: none; border: 1px solid var(--card-border); color: var(--text-color); border-radius: 8px; padding: 6px 12px; cursor: pointer; font-size: 14px; }
        
        .container { max-width: 900px; margin: 0 auto; padding: 32px 20px; }
        
        .badge { display: inline-block; padding: 4px 12px; border-radius: 20px; background: rgba(47, 129, 247, 0.15); color: var(--accent-blue); font-size: 12px; font-weight: 600; margin-bottom: 12px; }
        .hero { text-align: center; margin-bottom: 40px; }
        .hero h1 { font-size: 32px; color: var(--text-heading); margin: 0 0 12px 0; font-weight: 800; }
        .hero p { font-size: 15px; color: var(--text-muted); max-width: 600px; margin: 0 auto 24px auto; line-height: 1.6; }
        
        .auth-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 24px; margin-bottom: 48px; }
        .card { background: var(--card-bg); padding: 24px; border-radius: 12px; border: 1px solid var(--card-border); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
        .card h3 { margin-top: 0; color: var(--text-heading); font-size: 16px; border-bottom: 1px solid var(--card-border); padding-bottom: 10px; }
        
        input { width: 100%; padding: 10px 14px; margin-bottom: 12px; border: 1px solid var(--input-border); border-radius: 8px; font-size: 14px; outline: none; background: var(--input-bg); color: var(--input-text); }
        button.action-btn { width: 100%; padding: 10px; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 14px; transition: 0.2s; }
        .btn-primary { background: var(--btn-bg); color: #ffffff; }
        .btn-primary:hover { background: var(--btn-hover); }
        .btn-outline { background: var(--btn-outline-bg); border: 1px solid var(--input-border); color: var(--text-color); }
        
        .section-title { text-align: center; margin: 48px 0 24px 0; }
        .section-title h2 { font-size: 24px; color: var(--text-heading); margin: 0 0 8px 0; }
        .section-title p { font-size: 14px; color: var(--text-muted); margin: 0; }
        
        .features-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; }
        .feature-item { background: var(--card-bg); border: 1px solid var(--card-border); padding: 20px; border-radius: 10px; text-align: center; }
        .feature-item .icon { font-size: 28px; margin-bottom: 10px; }
        .feature-item h4 { margin: 0 0 6px 0; color: var(--text-heading); font-size: 15px; }
        .feature-item p { margin: 0; font-size: 12px; color: var(--text-muted); line-height: 1.5; }
        
        .steps-wrapper { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; }
        .step-card { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 10px; padding: 20px; position: relative; }
        .step-num { width: 28px; height: 28px; background: var(--accent-blue); color: #white; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 13px; margin-bottom: 12px; }
        .step-card h4 { margin: 0 0 6px 0; color: var(--text-heading); font-size: 14px; }
        .step-card p { margin: 0; font-size: 12px; color: var(--text-muted); line-height: 1.5; }
        
        .compare-table { width: 100%; border-collapse: collapse; background: var(--card-bg); border-radius: 10px; overflow: hidden; border: 1px solid var(--card-border); }
        .compare-table th, .compare-table td { padding: 14px; text-align: center; border-bottom: 1px solid var(--card-border); font-size: 13px; }
        .compare-table th { background: rgba(255,255,255,0.03); color: var(--text-heading); }
        .check { color: #39d353; font-weight: bold; }
        .cross { color: var(--accent-red); font-weight: bold; }
        
        .faq-item { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 8px; margin-bottom: 10px; padding: 14px 18px; cursor: pointer; }
        .faq-title { font-weight: 600; font-size: 14px; color: var(--text-heading); display: flex; justify-content: space-between; align-items: center; }
        .faq-desc { font-size: 12px; color: var(--text-muted); margin-top: 8px; display: none; line-height: 1.6; border-top: 1px solid var(--card-border); padding-top: 8px; }
        
        .footer { text-align: center; border-top: 1px solid var(--card-border); margin-top: 60px; padding: 24px; color: var(--text-muted); font-size: 12px; }
        .footer a { color: var(--accent-blue); text-decoration: none; }
    </style>
</head>
<body>
    <div class="navbar">
        <h2>🔒 مدير الحسابات</h2>
        <button id="themeToggle">☀️ / 🌙</button>
    </div>

    <div class="container">
        <div class="hero">
            <span class="badge">أمان وخصوصية</span>
            <h1>كلمات مرورك، تحت سيطرتك</h1>
            <p>احفظ حساباتك بأمان وسهولة وأدر جميع اشتراكاتك وتطبيقاتك في مكان واحد بدون تعقيد وبأعلى درجات التشفير.</p>
        </div>

        <div class="auth-grid">
            <div class="card">
                <h3>🔑 تسجيل الدخول</h3>
                <form action="/login" method="POST">
                    <input type="text" name="username" placeholder="اسم المستخدم للنظام" required>
                    <input type="password" name="password" placeholder="كلمة السر للنظام" required>
                    <button type="submit" class="action-btn btn-primary">تسجيل الدخول</button>
                </form>
            </div>
            <div class="card">
                <h3>✨ إنشاء حساب جديد</h3>
                <form action="/register" method="POST">
                    <input type="text" name="username" placeholder="اسم مستخدم جديد" required>
                    <input type="password" name="password" placeholder="كلمة السر (6 أحرف على الأقل)" minlength="6" required>
                    <button type="submit" class="action-btn btn-outline">إنشاء حساب جديد</button>
                </form>
            </div>
        </div>

        <!-- قسم المميزات -->
        <div class="section-title">
            <span class="badge">المميزات</span>
            <h2>لماذا تختار مدير الحسابات؟</h2>
            <p>نقدم لك تجربة آمنة وبسيطة لإدارة جميع حساباتك في مكان واحد</p>
        </div>
        <div class="features-grid">
            <div class="feature-item">
                <div class="icon">🔐</div>
                <h4>تشفير قوي</h4>
                <p>جميع بياناتك مشفرة بتقنيات Fernet المتقدمة قبل التخزين.</p>
            </div>
            <div class="feature-item">
                <div class="icon">🛡️</div>
                <h4>خصوصية تامة</h4>
                <p>لا نشارك بياناتك مع أي طرف ثالث ولا نستخدم أدوات تتبع.</p>
            </div>
            <div class="feature-item">
                <div class="icon">⚡</div>
                <h4>سهل الاستخدام</h4>
                <p>واجهة بسيطة وواضحة تناسب الجميع بدون خطوات معقدة.</p>
            </div>
            <div class="feature-item">
                <div class="icon">📱</div>
                <h4>دعم لجميع الأجهزة</h4>
                <p>استخدمه بسهولة من الجوال، الأيباد، أو الكمبيوتر.</p>
            </div>
        </div>

        <!-- قسم طريقة الاستخدام -->
        <div class="section-title">
            <span class="badge">طريقة الاستخدام</span>
            <h2>كيف تستخدم الموقع؟</h2>
            <p>خطوات بسيطة يمكنك البدء بها في دقائق</p>
        </div>
        <div class="steps-wrapper">
            <div class="step-card">
                <div class="step-num">1</div>
                <h4>إنشاء حساب</h4>
                <p>سجل حسابك الجديد بكلمة مرور رئيسية فريدة وقوية.</p>
            </div>
            <div class="step-card">
                <div class="step-num">2</div>
                <h4>إضافة الحسابات</h4>
                <p>أضف حساباتك المختلفة (تطبيقات، إيميلات، مواقع) مع بيانات الدخول.</p>
            </div>
            <div class="step-card">
                <div class="step-num">3</div>
                <h4>تنظيم الحسابات</h4>
                <p>رتب وزع حساباتك في مكان واحد حسب احتياجك اليومي.</p>
            </div>
            <div class="step-card">
                <div class="step-num">4</div>
                <h4>الوصول السريع</h4>
                <p>استعرض واكشف كلمات المرور عند الحاجة بضغطة زر آمنة.</p>
            </div>
        </div>

        <!-- قسم المقارنة مع جوجل -->
        <div class="section-title">
            <span class="badge">مقارنة</span>
            <h2>لماذا مدير الحسابات بدلاً من Google؟</h2>
            <p>إليك الفرق الجوهري في إدارة خصوصيتك</p>
        </div>
        <table class="compare-table">
            <thead>
                <tr>
                    <th>المعيار</th>
                    <th>مدير الحسابات 🛡️</th>
                    <th>Google Password Manager 🌐</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td>الخصوصية والتشفير</td>
                    <td class="check">تشفير خاص ولا يُقرأ من السيرفرات</td>
                    <td class="cross">مرتبط بحساب جوجل الموحد</td>
                </tr>
                <tr>
                    <td>تتبع البيانات والإعلانات</td>
                    <td class="check">بدون تتبع أو إعلانات تماماً</td>
                    <td class="cross">يتم جمع البيانات لتحسين الإعلانات</td>
                </tr>
                <tr>
                    <td>التحكم والملكية</td>
                    <td class="check">تحكم كامل في قاعدة بياناتك الخاصة</td>
                    <td class="cross">مخزن في سحابة جوجل المركزية</td>
                </tr>
                <tr>
                    <td>التصنيف والتنظيم</td>
                    <td class="check">مخصص للتطبيقات والإيميلات والمواقع</td>
                    <td class="cross">خيارات تنظيميّة محدودة للروابط فقط</td>
                </tr>
            </tbody>
        </table>

        <!-- قسم الأسئلة الشائعة -->
        <div class="section-title">
            <span class="badge">الأسئلة الشائعة</span>
            <h2>أسئلة يتكرر طرحها</h2>
        </div>
        <div class="faq-item" onclick="toggleFaq(this)">
            <div class="faq-title"><span>هل الموقع مجاني؟</span><span>+</span></div>
            <div class="faq-desc">نعم، الموقع مجاني بالكامل ومصمم ليقدم خدمة آمنة وسريعة للمستخدمين.</div>
        </div>
        <div class="faq-item" onclick="toggleFaq(this)">
            <div class="faq-title"><span>كيف يتم حماية كلمات المرور الخاصة بي؟</span><span>+</span></div>
            <div class="faq-desc">تتم حماية كلمات مرورك بتشفير Fernet المتقدم قبل أن تدخل قاعدة البيانات، ولا يتم حفظها بنص واضح أبداً.</div>
        </div>
        <div class="faq-item" onclick="toggleFaq(this)">
            <div class="faq-title"><span>هل يمكنني حذف حسابي وجميع بياناتي؟</span><span>+</span></div>
            <div class="faq-desc">نعم، يمكنك الذهاب لصفحة الإعدادات وحذف الحساب نهائياً، وسيتم مسح جميع بياناتك دون إمكانية استرجاعها.</div>
        </div>

        <div class="footer">
            <p>© 2026 مدير الحسابات - جميع الحقوق محفوظة | <a href="/about">عن المشروع وسياسة الأمان</a></p>
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

        function toggleFaq(elem) {
            const desc = elem.querySelector('.faq-desc');
            const span = elem.querySelector('.faq-title span:last-child');
            if (desc.style.display === 'block') {
                desc.style.display = 'none';
                span.textContent = '+';
            } else {
                desc.style.display = 'block';
                span.textContent = '-';
            }
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

# 4. صفحة الإعدادات والأمان (/settings)
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

# 5. صفحة عن الموقع وسياسة الأمان (/about)
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
