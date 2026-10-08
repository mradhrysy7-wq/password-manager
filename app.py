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
    if not plain_password: return ""
    return cipher_suite.encrypt(plain_password.encode()).decode()

def decrypt_password(encrypted_password):
    if not encrypted_password: return ""
    try: return cipher_suite.decrypt(encrypted_password.encode()).decode()
    except Exception: return "[خطأ في فك التشفير]"

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

# 1. الواجهة الرئيسية للزوار (صفحة الدخول والتسجيل)
AUTH_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>مدير الحسابات الشامل</title>
    <style>
        :root {
            --bg: #0d1117; --card: #161b22; --border: #30363d;
            --text: #c9d1d9; --heading: #ffffff; --muted: #8b949e;
            --input-bg: #0d1117; --btn-bg: #238636; --btn-hover: #2ea043;
            --blue: #2f81f7; --red: #f85149;
        }
        .light-theme {
            --bg: #f6f8fa; --card: #ffffff; --border: #d0d7de;
            --text: #24292f; --heading: #0f172a; --muted: #57606a;
            --input-bg: #ffffff; --btn-bg: #2da44e; --btn-hover: #2c974b;
            --blue: #0969da; --red: #cf222e;
        }
        * { box-sizing: border-box; font-family: system-ui, sans-serif; scroll-behavior: smooth; }
        body { background: var(--bg); margin: 0; padding: 0; color: var(--text); transition: 0.3s; }
        .nav { display: flex; justify-content: space-between; align-items: center; padding: 14px 20px; background: var(--card); border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 10; }
        .nav h2 { margin: 0; font-size: 18px; color: var(--heading); }
        #themeToggle { background: none; border: 1px solid var(--border); color: var(--text); border-radius: 6px; padding: 6px 12px; cursor: pointer; }
        .container { max-width: 850px; margin: 0 auto; padding: 24px 16px; }
        .badge { display: inline-block; padding: 4px 12px; border-radius: 20px; background: rgba(47,129,247,0.15); color: var(--blue); font-size: 12px; font-weight: 600; margin-bottom: 10px; }
        .hero { text-align: center; margin-bottom: 32px; }
        .hero h1 { font-size: 28px; color: var(--heading); margin: 0 0 10px 0; }
        .hero p { font-size: 14px; color: var(--muted); margin: 0; line-height: 1.5; }
        .auth-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; margin-bottom: 40px; }
        .card { background: var(--card); padding: 20px; border-radius: 10px; border: 1px solid var(--border); }
        .card h3 { margin: 0 0 14px 0; color: var(--heading); font-size: 16px; border-bottom: 1px solid var(--border); padding-bottom: 8px; }
        input { width: 100%; padding: 10px; margin-bottom: 10px; border: 1px solid var(--border); border-radius: 6px; background: var(--input-bg); color: var(--text); outline: none; }
        button.btn { width: 100%; padding: 10px; border: none; border-radius: 6px; font-weight: 600; cursor: pointer; background: var(--btn-bg); color: #fff; }
        button.btn:hover { background: var(--btn-hover); }
        .btn-outline { background: transparent; border: 1px solid var(--border); color: var(--text); }
        .section-title { text-align: center; margin: 40px 0 20px 0; }
        .section-title h2 { font-size: 22px; color: var(--heading); margin: 0; }
        .grid-4 { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }
        .box { background: var(--card); border: 1px solid var(--border); padding: 16px; border-radius: 8px; text-align: center; }
        .box h4 { margin: 8px 0 4px 0; color: var(--heading); font-size: 14px; }
        .box p { margin: 0; font-size: 12px; color: var(--muted); line-height: 1.4; }
        .num { width: 24px; height: 24px; background: var(--blue); color: #fff; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: bold; margin: 0 auto 8px auto; }
        table { width: 100%; border-collapse: collapse; background: var(--card); border-radius: 8px; overflow: hidden; border: 1px solid var(--border); }
        th, td { padding: 12px; text-align: center; border-bottom: 1px solid var(--border); font-size: 13px; }
        th { background: rgba(255,255,255,0.02); color: var(--heading); }
        .check { color: #39d353; font-weight: bold; }
        .cross { color: var(--red); font-weight: bold; }
        .faq { background: var(--card); border: 1px solid var(--border); border-radius: 6px; margin-bottom: 8px; padding: 12px 16px; cursor: pointer; }
        .faq-title { font-weight: 600; font-size: 13px; color: var(--heading); display: flex; justify-content: space-between; }
        .faq-desc { font-size: 12px; color: var(--muted); margin-top: 8px; display: none; border-top: 1px solid var(--border); padding-top: 8px; }
        .footer { text-align: center; border-top: 1px solid var(--border); margin-top: 40px; padding: 20px; color: var(--muted); font-size: 12px; }
        .footer a { color: var(--blue); text-decoration: none; }
    </style>
</head>
<body>
    <div class="nav">
        <h2>🔒 مدير الحسابات</h2>
        <button id="themeToggle">☀️ / 🌙</button>
    </div>
    <div class="container">
        <div class="hero">
            <span class="badge">أمان وخصوصية</span>
            <h1>كلمات مرورك، تحت سيطرتك</h1>
            <p>احفظ حساباتك بأمان وسهولة وأدر جميع اشتراكاتك وتطبيقاتك في مكان واحد وبأعلى درجات التشفير.</p>
        </div>

        <div class="auth-grid">
            <div class="card">
                <h3>🔑 تسجيل الدخول</h3>
                <form action="/login" method="POST">
                    <input type="text" name="username" placeholder="اسم المستخدم للنظام" required>
                    <input type="password" name="password" placeholder="كلمة السر للنظام" required>
                    <button type="submit" class="btn">تسجيل الدخول</button>
                </form>
            </div>
            <div class="card">
                <h3>✨ إنشاء حساب جديد</h3>
                <form action="/register" method="POST">
                    <input type="text" name="username" placeholder="اسم مستخدم جديد" required>
                    <input type="password" name="password" placeholder="كلمة السر (6 أحرف على الأقل)" minlength="6" required>
                    <button type="submit" class="btn btn-outline">إنشاء حساب جديد</button>
                </form>
            </div>
        </div>

        <div class="section-title">
            <span class="badge">المميزات</span>
            <h2>لماذا تختار مدير الحسابات؟</h2>
        </div>
        <div class="grid-4">
            <div class="box"><div>🔐</div><h4>تشفير قوي</h4><p>بياناتك مشفرة بتقنيات Fernet المتقدمة.</p></div>
            <div class="box"><div>🛡️</div><h4>خصوصية تامة</h4><p>لا نشارك بياناتك ولا نستخدم أدوات تتبع.</p></div>
            <div class="box"><div>⚡</div><h4>سهل الاستخدام</h4><p>واجهة بسيطة وواضحة تناسب الجميع.</p></div>
            <div class="box"><div>📱</div><h4>دعم الأجهزة</h4><p>استخدمه بسهولة من الجوال أو الكمبيوتر.</p></div>
        </div>

        <div class="section-title">
            <span class="badge">طريقة الاستخدام</span>
            <h2>كيف تستخدم الموقع؟</h2>
        </div>
        <div class="grid-4">
            <div class="box"><div class="num">1</div><h4>إنشاء حساب</h4><p>سجل حسابك بكلمة مرور رئيسية فريدة.</p></div>
            <div class="box"><div class="num">2</div><h4>إضافة الحسابات</h4><p>أضف حساباتك واشتراكاتك بمرونة.</p></div>
            <div class="box"><div class="num">3</div><h4>تنظيم الحسابات</h4><p>رتب بياناتك في أقسام واضحة.</p></div>
            <div class="box"><div class="num">4</div><h4>الوصول السريع</h4><p>اكشف كلمات المرور بضغطة زر آمنة.</p></div>
        </div>

        <div class="section-title">
            <span class="badge">مقارنة</span>
            <h2>لماذا موقعنا بدلاً من Google؟</h2>
        </div>
        <table>
            <thead>
                <tr><th>المعيار</th><th>مدير الحسابات 🛡️</th><th>Google Manager 🌐</th></tr>
            </thead>
            <tbody>
                <tr><td>التشفير والسرية</td><td class="check">مفتاح تشفير خاص بك</td><td class="cross">مرتبط بحساب جوجل المركزى</td></tr>
                <tr><td>تتبع الإعلانات</td><td class="check">بدون تتبع نهائياً</td><td class="cross">يتم تحليله للإعلانات</td></tr>
                <tr><td>الملكية والسيطرة</td><td class="check">تحكم كامل بقاعدة البيانات</td><td class="cross">مخزن في سحابة جوجل</td></tr>
            </tbody>
        </table>

        <div class="section-title">
            <span class="badge">الأسئلة الشائعة</span>
            <h2>أسئلة مكررة</h2>
        </div>
        <div class="faq" onclick="toggleFaq(this)">
            <div class="faq-title"><span>هل الموقع مجاني؟</span><span>+</span></div>
            <div class="faq-desc">نعم، الموقع مجاني بالكامل ومصمم لأمان وحفظ بياناتك.</div>
        </div>
        <div class="faq" onclick="toggleFaq(this)">
            <div class="faq-title"><span>كيف يتم حماية كلمات المرور؟</span><span>+</span></div>
            <div class="faq-desc">تتم حمايتها بتشفير Fernet قبل الدخول لقاعدة البيانات.</div>
        </div>

        <div class="footer">
            <p>© 2026 مدير الحسابات | <a href="/about">عن المشروع وسياسة الأمان</a></p>
        </div>
    </div>
    <script>
        const themeToggleBtn = document.getElementById('themeToggle');
        themeToggleBtn.addEventListener('click', () => {
            document.body.classList.toggle('light-theme');
            localStorage.setItem('theme', document.body.classList.contains('light-theme') ? 'light' : 'dark');
        });
        if (localStorage.getItem('theme') === 'light') document.body.classList.add('light-theme');
        function toggleFaq(elem) {
            const desc = elem.querySelector('.faq-desc');
            const span = elem.querySelector('.faq-title span:last-child');
            if (desc.style.display === 'block') { desc.style.display = 'none'; span.textContent = '+'; }
            else { desc.style.display = 'block'; span.textContent = '-'; }
        }
    </script>
</body>
</html>
"""

# 2. لوحة التحكم الداخلية
HOME_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>لوحة التحكم - مدير الحسابات</title>
    <style>
        :root {
            --bg: #0d1117; --card: #161b22; --border: #30363d;
            --text: #c9d1d9; --heading: #ffffff; --muted: #8b949e;
            --blue: #2f81f7; --red: #f85149; --card-hover: #1c2128;
        }
        * { box-sizing: border-box; font-family: system-ui, -apple-system, sans-serif; }
        body { background: var(--bg); margin: 0; padding: 0; color: var(--text); }
        
        .top-nav { display: flex; justify-content: space-between; align-items: center; padding: 14px 24px; background: var(--card); border-bottom: 1px solid var(--border); }
        .logo-area { display: flex; align-items: center; gap: 10px; }
        .logo-icon { width: 34px; height: 34px; background: var(--blue); color: #fff; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 18px; }
        .logo-text h3 { margin: 0; font-size: 15px; color: var(--heading); }
        .logo-text span { font-size: 11px; color: var(--muted); }
        
        .user-nav { display: flex; align-items: center; gap: 12px; }
        .nav-link { color: var(--text); text-decoration: none; font-size: 13px; display: flex; align-items: center; gap: 4px; padding: 6px 10px; border-radius: 6px; border: 1px solid var(--border); background: var(--bg); }
        .logout-link { color: var(--red); border-color: rgba(248,81,73,0.3); background: rgba(248,81,73,0.05); }

        .container { max-width: 900px; margin: 0 auto; padding: 24px 16px; }

        .welcome-card { background: linear-gradient(135deg, rgba(47,129,247,0.12) 0%, var(--card) 100%); border: 1px solid var(--border); border-radius: 12px; padding: 24px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .welcome-info h2 { margin: 0 0 6px 0; font-size: 22px; color: var(--heading); }
        .welcome-info h4 { margin: 0 0 6px 0; font-size: 14px; color: var(--blue); font-weight: 500; }
        .welcome-info p { margin: 0; font-size: 12px; color: var(--muted); }
        .shield-badge { font-size: 42px; background: rgba(47,129,247,0.1); padding: 12px; border-radius: 50%; border: 1px solid rgba(47,129,247,0.2); }

        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 12px; margin-bottom: 28px; }
        .stat-box { background: var(--card); border: 1px solid var(--border); border-radius: 10px; padding: 16px; text-align: center; }
        .stat-icon { font-size: 20px; margin-bottom: 4px; opacity: 0.8; }
        .stat-val { font-size: 20px; font-weight: bold; color: var(--heading); margin-bottom: 2px; }
        .stat-lbl { font-size: 11px; color: var(--muted); }

        .sec-header { margin-bottom: 14px; }
        .sec-header h3 { margin: 0 0 4px 0; font-size: 16px; color: var(--heading); display: flex; align-items: center; gap: 6px; }
        .sec-header p { margin: 0; font-size: 12px; color: var(--muted); }

        .cat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 16px; margin-bottom: 28px; }
        .cat-card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; position: relative; transition: 0.2s; text-decoration: none; color: inherit; display: flex; flex-direction: column; justify-content: space-between; }
        .cat-card:hover { border-color: var(--blue); background: var(--card-hover); }
        .cat-top { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; }
        .cat-icon { width: 40px; height: 40px; border-radius: 10px; background: rgba(47,129,247,0.1); display: flex; align-items: center; justify-content: center; font-size: 20px; }
        .cat-title { margin: 0; font-size: 15px; color: var(--heading); font-weight: 600; }
        .cat-desc { font-size: 12px; color: var(--muted); margin: 0 0 16px 0; line-height: 1.5; }
        .cat-btn { display: inline-flex; align-items: center; gap: 6px; background: rgba(47,129,247,0.15); color: var(--blue); border: none; padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 600; width: fit-content; }

        .tips-box { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 16px; }
        .tips-content { flex: 1; }
        .tips-content h4 { margin: 0 0 10px 0; font-size: 14px; color: var(--heading); display: flex; align-items: center; gap: 6px; }
        .tips-content ul { margin: 0; padding-right: 18px; font-size: 12px; color: var(--muted); line-height: 1.8; }
        .tips-badge { font-size: 13px; font-weight: bold; color: var(--blue); background: rgba(47,129,247,0.1); padding: 8px 14px; border-radius: 8px; border: 1px solid rgba(47,129,247,0.2); }

        .footer { text-align: center; margin-top: 32px; padding-top: 16px; border-top: 1px solid var(--border); font-size: 11px; color: var(--muted); }
        .footer-links { display: flex; justify-content: center; gap: 16px; margin-bottom: 8px; }
        .footer-links a { color: var(--muted); text-decoration: none; }
        .footer-links a:hover { color: var(--blue); }
    </style>
</head>
<body>
    <div class="top-nav">
        <div class="logo-area">
            <div class="logo-icon">🔒</div>
            <div class="logo-text">
                <h3>مدير الحسابات</h3>
                <span>كلمات مرورك.. تحت سيطرتك</span>
            </div>
        </div>
        <div class="user-nav">
            <span style="font-size: 13px; color: var(--heading); font-weight: 500;">👤 {{ username }}</span>
            <a href="/settings" class="nav-link">⚙️ الإعدادات</a>
            <a href="/about" class="nav-link">ℹ️ عن الموقع</a>
            {% if username in ['morad', 'admin'] %}
            <a href="/admin/users" class="nav-link" style="background:#1e3a8a; color:#fff;">👥 المشرف</a>
            {% endif %}
            <a href="/logout" class="nav-link logout-link">تسجيل الخروج</a>
        </div>
    </div>

    <div class="container">
        <div class="welcome-card">
            <div class="welcome-info">
                <h2>مرحباً، {{ username }} 👋</h2>
                <h4>لوحة التحكم الخاصة بك في مدير الحسابات</h4>
                <p>احفظ بياناتك بشكل آمن، وأدر حساباتك بكل سهولة.</p>
            </div>
            <div class="shield-badge">🛡️</div>
        </div>

        <div class="stats-grid">
            <div class="stat-box">
                <div class="stat-icon">🕒</div>
                <div class="stat-val">اليوم</div>
                <div class="stat-lbl">آخر دخول</div>
            </div>
            <div class="stat-box">
                <div class="stat-icon">🔒</div>
                <div class="stat-val">100%</div>
                <div class="stat-lbl">تسجيلات آمنة</div>
            </div>
            <div class="stat-box">
                <div class="stat-icon">📂</div>
                <div class="stat-val">3</div>
                <div class="stat-lbl">الفئات</div>
            </div>
            <div class="stat-box">
                <div class="stat-icon">🛡️</div>
                <div class="stat-val">{{ total_accounts }}</div>
                <div class="stat-lbl">حسابات محفوظة</div>
            </div>
        </div>

        <div class="sec-header">
            <h3>📱 أقسام الموقع</h3>
            <p>اختر القسم الذي تريد الوصول إليه وإدارته</p>
        </div>

        <div class="cat-grid">
            <a href="/category/تطبيق" class="cat-card">
                <div>
                    <div class="cat-top">
                        <div class="cat-icon">📱</div>
                        <h4 class="cat-title">التطبيقات والمنصات</h4>
                    </div>
                    <p class="cat-desc">حفظ وإدارة بيانات حساباتك في التطبيقات والمنصات المختلفة.</p>
                </div>
                <div class="cat-btn">الدخول الآن ➔</div>
            </a>

            <a href="/category/بريد" class="cat-card">
                <div>
                    <div class="cat-top">
                        <div class="cat-icon">📧</div>
                        <h4 class="cat-title">البريد الإلكتروني</h4>
                    </div>
                    <p class="cat-desc">إدارة وحفظ أرقامك السرية وحسابات البريد الإلكتروني.</p>
                </div>
                <div class="cat-btn">الدخول الآن ➔</div>
            </a>

            <a href="/category/موقع" class="cat-card">
                <div>
                    <div class="cat-top">
                        <div class="cat-icon">🌐</div>
                        <h4 class="cat-title">المواقع الإلكترونية</h4>
                    </div>
                    <p class="cat-desc">إدارة حساباتك وبيانات دخولك للمواقع الإلكترونية بكل سهولة.</p>
                </div>
                <div class="cat-btn">الدخول الآن ➔</div>
            </a>
        </div>

        <div class="tips-box">
            <div class="tips-content">
                <h4>💡 نصائح سريعة الأمان</h4>
                <ul>
                    <li>استخدم كلمات مرور قوية وفريدة لكل حساب.</li>
                    <li>قم بتفعيل التحقق الثنائي متى كان متاحاً.</li>
                    <li>قم بعمل نسخة احتياطية من بياناتك بشكل دوري.</li>
                </ul>
            </div>
            <div class="tips-badge">أمانك أولويتنا</div>
        </div>

        <div class="footer">
            <div class="footer-links">
                <a href="/about">سياسة الخصوصية</a>
                <a href="/about">شروط الاستخدام</a>
                <a href="/about">تواصل معنا</a>
            </div>
            <p>© 2026 مدير الحسابات - جميع الحقوق محفوظة</p>
        </div>
    </div>
</body>
</html>
"""

# 3. صفحة إدارة الأقسام المحدثة المماثلة للصورة (CATEGORY_HTML)
CATEGORY_HTML = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>إدارة {{ cat_name }} - مدير الحسابات</title>
    <style>
        :root {
            --bg: #0d1117; --card: #161b22; --border: #30363d;
            --text: #c9d1d9; --heading: #ffffff; --muted: #8b949e;
            --blue: #2f81f7; --red: #f85149; --green: #238636;
            --green-hover: #2ea043; --card-hover: #1c2128;
        }
        * { box-sizing: border-box; font-family: system-ui, -apple-system, sans-serif; }
        body { background: var(--bg); margin: 0; padding: 0; color: var(--text); }
        
        .top-nav { display: flex; justify-content: space-between; align-items: center; padding: 14px 20px; background: var(--card); border-bottom: 1px solid var(--border); }
        .nav-link { color: var(--text); text-decoration: none; font-size: 13px; display: inline-flex; align-items: center; gap: 6px; padding: 6px 12px; border-radius: 6px; border: 1px solid var(--border); background: var(--bg); }

        .container { max-width: 900px; margin: 0 auto; padding: 24px 16px; }

        /* البنر العلوي للقسم */
        .hero-banner { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 24px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .hero-info h2 { margin: 0 0 8px 0; font-size: 20px; color: var(--heading); display: flex; align-items: center; gap: 8px; }
        .hero-info p { margin: 0; font-size: 13px; color: var(--muted); line-height: 1.5; }
        .hero-icon { font-size: 38px; background: rgba(47,129,247,0.1); padding: 14px; border-radius: 12px; border: 1px solid rgba(47,129,247,0.2); }

        /* شريط البحث وزر إضافة حساب */
        .action-bar { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }
        .search-box { flex: 1; min-width: 220px; }
        .search-box input { width: 100%; padding: 10px 14px; background: var(--card); border: 1px solid var(--border); border-radius: 8px; color: var(--text); font-size: 13px; outline: none; }
        .btn-add { background: var(--green); color: #fff; border: none; padding: 10px 18px; border-radius: 8px; font-weight: 600; font-size: 13px; cursor: pointer; display: inline-flex; align-items: center; gap: 6px; transition: 0.2s; }
        .btn-add:hover { background: var(--green-hover); }

        /* نموذج إضافة حساب */
        .add-form-card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 20px; display: none; }
        .add-form-card.active { display: block; }
        .form-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-bottom: 14px; }
        .form-grid input { width: 100%; padding: 10px; background: var(--bg); border: 1px solid var(--border); border-radius: 6px; color: var(--heading); font-size: 13px; outline: none; }

        /* قائمة الحسابات بتصميم الكروت مثل الصورة */
        .account-card { background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 16px 20px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; gap: 16px; transition: 0.2s; }
        .account-card:hover { border-color: var(--blue); }
        .acc-right { display: flex; align-items: center; gap: 14px; }
        .acc-icon { width: 44px; height: 44px; border-radius: 10px; background: rgba(47,129,247,0.1); display: flex; align-items: center; justify-content: center; font-size: 22px; flex-shrink: 0; }
        .acc-details h4 { margin: 0 0 4px 0; font-size: 15px; color: var(--heading); }
        .acc-details p { margin: 0 0 6px 0; font-size: 12px; color: var(--muted); }
        .acc-badge { display: inline-block; background: rgba(255,255,255,0.05); border: 1px solid var(--border); padding: 2px 8px; border-radius: 6px; font-size: 11px; color: var(--blue); }

        .acc-left { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
        .btn-action { padding: 6px 12px; border-radius: 6px; font-size: 12px; text-decoration: none; font-weight: 500; cursor: pointer; border: 1px solid var(--border); display: inline-flex; align-items: center; gap: 4px; }
        .btn-pwd { background: rgba(47,129,247,0.1); color: var(--blue); border-color: rgba(47,129,247,0.3); }
        .btn-edit { background: rgba(255,255,255,0.05); color: var(--text); }
        .btn-del { background: rgba(248,81,73,0.1); color: var(--red); border-color: rgba(248,81,73,0.3); }

        .empty-box { text-align: center; padding: 40px 20px; background: var(--card); border: 1px solid var(--border); border-radius: 12px; color: var(--muted); font-size: 13px; }

        /* شريط التنبيه السفلي */
        .info-alert { background: var(--card); border: 1px solid var(--border); border-radius: 8px; padding: 12px 16px; display: flex; align-items: center; gap: 10px; font-size: 12px; color: var(--muted); margin-top: 20px; }
        .info-alert-icon { color: var(--blue); font-size: 16px; }
    </style>
</head>
<body>
    <div class="top-nav">
        <a href="/" class="nav-link">➔ العودة للرئيسية</a>
        <span style="font-size: 14px; font-weight: bold; color: var(--heading);">مدير الحسابات</span>
    </div>

    <div class="container">
        <div class="hero-banner">
            <div class="hero-info">
                <h2>📁 {{ cat_name }}</h2>
                <p>قم بتنظيم حساباتك في قسم {{ cat_name }} لتسهيل الوصول إليها وإدارتها بطريقة أفضل وأكثر أماناً.</p>
            </div>
            <div class="hero-icon">
                {% if cat_slug == 'تطبيق' %}📱{% elif cat_slug == 'بريد' %}📧{% else %}🌐{% endif %}
            </div>
        </div>

        <div class="action-bar">
            <div class="search-box">
                <input type="text" id="searchInput" onkeyup="filterAccounts()" placeholder="🔍 ابحث في حسابات {{ cat_name }}...">
            </div>
            <button class="btn-add" onclick="toggleForm()">➕ إضافة حساب جديد</button>
        </div>

        <div class="add-form-card" id="addForm">
            <h3 style="margin: 0 0 14px 0; font-size: 15px; color: var(--heading);">إضافة حساب جديد إلى {{ cat_name }}</h3>
            <form action="/add_item" method="POST">
                <input type="hidden" name="account_type" value="{{ cat_slug }}">
                <div class="form-grid">
                    {% if cat_slug != 'بريد' %}
                    <input type="text" name="app_name" placeholder="اسم الخدمة/التطبيق (مثال: Netflix)" required>
                    <input type="text" name="app_username" placeholder="اسم المستخدم">
                    {% endif %}
                    <input type="email" name="email" placeholder="البريد الإلكتروني">
                    <input type="text" name="password" placeholder="كلمة المرور" required>
                </div>
                <button type="submit" class="btn-add" style="width: 100%; justify-content: center;">حفظ الحساب</button>
            </form>
        </div>

        <div id="accountsList">
            {% for row in accounts %}
            <div class="account-card item-row">
                <div class="acc-right">
                    <div class="acc-icon">
                        {% if cat_slug == 'تطبيق' %}📱{% elif cat_slug == 'بريد' %}📧{% else %}🌐{% endif %}
                    </div>
                    <div class="acc-details">
                        <h4 class="item-title">
                            {% if cat_slug == 'بريد' %}
                                {{ row[2] or 'حساب بريد إلكتروني' }}
                            {% else %}
                                {{ row[1] or 'خدمة غير معنونة' }}
                            {% endif %}
                        </h4>
                        <p class="item-sub">
                            {% if cat_slug != 'بريد' and row[3] %}المستخدم: {{ row[3] }} | {% endif %}
                            {% if row[2] and cat_slug != 'بريد' %}البريد: {{ row[2] }}{% endif %}
                        </p>
                        <span class="acc-badge" id="pwd-{{ row[0] }}">كلمة المرور: ••••••••</span>
                    </div>
                </div>
                <div class="acc-left">
                    <button class="btn-action btn-pwd" onclick="togglePwd('{{ row[0] }}', this)">👁️ إظهار</button>
                    <a href="/edit/{{ row[0] }}" class="btn-action btn-edit">✏️ تعديل</a>
                    <a href="/delete/{{ row[0] }}" class="btn-action btn-del" onclick="return confirm('هل أنت متأكد من الحذف؟')">🗑️ حذف</a>
                </div>
            </div>
            {% else %}
            <div class="empty-box">
                لا توجد حسابات مسجلة في هذا القسم حتى الآن. اضغط على "إضافة حساب جديد" للبدء.
            </div>
            {% endfor %}
        </div>

        <div class="info-alert">
            <span class="info-alert-icon">ℹ️</span>
            <span>يمكنك تعديل أو حذف أي حساب في أي وقت حسب رغبتك بكل أمان وخصوصية.</span>
        </div>
    </div>

    <script>
        function toggleForm() {
            const form = document.getElementById('addForm');
            form.classList.toggle('active');
        }
        function togglePwd(id, btn) {
            const badge = document.getElementById('pwd-' + id);
            if (badge.textContent.includes('••••••••')) {
                fetch('/get_password/' + id).then(r => r.json()).then(d => { 
                    badge.textContent = 'كلمة المرور: ' + d.password; 
                    btn.textContent = '🙈 إخفاء'; 
                });
            } else { 
                badge.textContent = 'كلمة المرور: ••••••••'; 
                btn.textContent = '👁️ إظهار'; 
            }
        }
        function filterAccounts() {
            const query = document.getElementById('searchInput').value.toLowerCase();
            const items = document.querySelectorAll('.item-row');
            items.forEach(item => {
                const text = item.textContent.toLowerCase();
                item.style.display = text.includes(query) ? 'flex' : 'none';
            });
        }
    </script>
</body>
</html>
"""

# 4. باقي الأقسام والصفحات الداخلية
EDIT_HTML = """
<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="UTF-8"><title>تعديل الحساب</title>
<style>body{background:#0d1117; color:#c9d1d9; font-family:system-ui; display:flex; justify-content:center; align-items:center; min-height:100vh; margin:0;}
.card{background:#161b22; padding:24px; border-radius:10px; width:100%; max-width:400px; border:1px solid #30363d;}
input{width:100%; padding:10px; margin-bottom:10px; border-radius:6px; border:1px solid #30363d; background:#0d1117; color:#fff; box-sizing:border-box;}
button{width:100%; padding:10px; background:#2f81f7; color:#fff; border:none; border-radius:6px; font-weight:bold; cursor:pointer;}
a{display:block; text-align:center; margin-top:10px; color:#8b949e; text-decoration:none;}
</style></head><body><div class="card"><h2>تعديل البيانات</h2><form method="POST">
{% if account[3] != 'بريد' %}<input type="text" name="app_name" value="{{ account[2] or '' }}" required>
<input type="text" name="app_username" value="{{ account[4] or '' }}">{% endif %}
<input type="email" name="email" value="{{ account[5] or '' }}">
<input type="text" name="password" placeholder="كلمة المرور الجديدة" required>
<button type="submit">حفظ التعديل</button></form><a href="/category/{{ account[3] }}">إلغاء والعودة</a></div></body></html>
"""

SETTINGS_HTML = """
<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="UTF-8"><title>الإعدادات</title>
<style>body{background:#0d1117; color:#c9d1d9; font-family:system-ui; padding:20px;} .wrapper{max-width:500px; margin:0 auto;}
.card{background:#161b22; padding:20px; border-radius:10px; border:1px solid #30363d; margin-bottom:20px;}
input{width:100%; padding:10px; margin-bottom:10px; border-radius:6px; border:1px solid #30363d; background:#0d1117; color:#fff; box-sizing:border-box;}
button{width:100%; padding:10px; border:none; border-radius:6px; font-weight:bold; cursor:pointer;}
.btn-blue{background:#238636; color:#fff;} .btn-red{background:#f85149; color:#fff;}
</style></head><body><div class="wrapper">
<div class="card"><h3>🔒 تغيير كلمة المرور الرئيسية</h3><form action="/update_credentials" method="POST">
<input type="password" name="new_password" placeholder="كلمة المرور الجديدة" required>
<button type="submit" class="btn-blue">تحديث كلمة المرور</button></form></div>
<div class="card" style="border-color:#7f1d1d;"><h3 style="color:#f85149;">⚠️ منطقة الخطر - حذف الحساب</h3>
<form action="/delete_account" method="POST" onsubmit="return confirm('هل أنت متأكد من الحذف النهائي؟');">
<button type="submit" class="btn-red">حذف حسابي نهائياً</button></form></div>
<a href="/" style="color:#8b949e; text-decoration:none;">← العودة للرئيسية</a></div></body></html>
"""

ABOUT_HTML = """
<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="UTF-8"><title>عن الموقع</title>
<style>body{background:#0d1117; color:#c9d1d9; font-family:system-ui; padding:20px;} .wrapper{max-width:600px; margin:0 auto;}
.card{background:#161b22; padding:20px; border-radius:10px; border:1px solid #30363d; line-height:1.6;}
</style></head><body><div class="wrapper"><div class="card">
<h2>🛡️ الخصوصية والأمان المتقدم</h2>
<p>نظام تشفير قوي يعتمد خوارزمية Fernet لتأمين كلمات المرور الخاصة بك محلية ومباشرة بدون تتبع أو مشاركة للبيانات.</p>
<a href="/" style="color:#2f81f7; text-decoration:none;">← العودة للرئيسية</a></div></div></body></html>
"""

ADMIN_HTML = """
<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="UTF-8"><title>لوحة المشرف</title>
<style>body{background:#0d1117; color:#c9d1d9; font-family:system-ui; padding:20px;} .wrapper{max-width:700px; margin:0 auto;}
table{width:100%; border-collapse:collapse; background:#161b22; border-radius:8px; overflow:hidden;}
th,td{padding:12px; text-align:center; border-bottom:1px solid #30363d;} th{background:rgba(255,255,255,0.02);}
</style></head><body><div class="wrapper"><h2>👥 لوحة تحكم المشرف</h2>
<table><thead><tr><th>ID</th><th>اسم المستخدم</th><th>عدد الحسابات المحفوظة</th></tr></thead><tbody>
{% for u in users_data %}<tr><td>{{ u[0] }}</td><td>{{ u[1] }}</td><td>{{ u[2] }} حسابات</td></tr>{% endfor %}
</tbody></table><br><a href="/" style="color:#2f81f7; text-decoration:none;">← العودة للرئيسية</a></div></body></html>
"""

# 5. التوجيهات والأوامر (Routes)
@app.route("/")
def index():
    if "user_id" in session:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE id = ?", (session["user_id"],))
        user_row = cursor.fetchone()
        
        cursor.execute("SELECT COUNT(*) FROM app_accounts WHERE user_id = ?", (session["user_id"],))
        total_accounts = cursor.fetchone()[0]
        conn.close()
        
        username = user_row[0] if user_row else "مستخدم"
        return render_template_string(HOME_HTML, username=username, total_accounts=total_accounts)
    return render_template_string(AUTH_HTML)

@app.route("/category/<cat_slug>")
def category_view(cat_slug):
    if "user_id" not in session: return redirect("/")
    cat_names = {"تطبيق": "التطبيقات والمنصات", "بريد": "البريد الإلكتروني", "موقع": "المواقع الإلكترونية"}
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, app_name, email, app_username, password FROM app_accounts WHERE user_id = ? AND account_type = ?", (session["user_id"], cat_slug))
    accounts = cursor.fetchall()
    conn.close()
    return render_template_string(CATEGORY_HTML, cat_name=cat_names.get(cat_slug, "الحسابات"), cat_slug=cat_slug, accounts=accounts)

@app.route("/get_password/<int:item_id>")
def get_password(item_id):
    if "user_id" not in session: return {"password": "Unauthorized"}, 403
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM app_accounts WHERE id = ? AND user_id = ?", (item_id, session["user_id"]))
    row = cursor.fetchone()
    conn.close()
    return {"password": decrypt_password(row[0])} if row else ({"password": "Not Found"}, 404)

@app.route("/add_item", methods=["POST"])
def add_item():
    if "user_id" not in session: return redirect("/")
    account_type = request.form.get("account_type")
    app_name = None if account_type == "بريد" else request.form.get("app_name")
    app_username = None if account_type == "بريد" else request.form.get("app_username")
    email = request.form.get("email")
    encrypted_pwd = encrypt_password(request.form.get("password"))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO app_accounts (user_id, account_type, app_name, app_username, email, password) VALUES (?, ?, ?, ?, ?, ?)", 
                   (session["user_id"], account_type, app_name, app_username, email, encrypted_pwd))
    conn.commit()
    conn.close()
    return redirect(f"/category/{account_type}")

@app.route("/edit/<int:item_id>", methods=["GET", "POST"])
def edit_item(item_id):
    if "user_id" not in session: return redirect("/")
    conn = get_db_connection()
    cursor = conn.cursor()
    if request.method == "POST":
        encrypted_pwd = encrypt_password(request.form.get("password"))
        cursor.execute("UPDATE app_accounts SET app_name = ?, app_username = ?, email = ?, password = ? WHERE id = ? AND user_id = ?",
                       (request.form.get("app_name"), request.form.get("app_username"), request.form.get("email"), encrypted_pwd, item_id, session["user_id"]))
        conn.commit()
        cursor.execute("SELECT account_type FROM app_accounts WHERE id = ?", (item_id,))
        acc_type = cursor.fetchone()[0]
        conn.close()
        return redirect(f"/category/{acc_type}")
    cursor.execute("SELECT * FROM app_accounts WHERE id = ? AND user_id = ?", (item_id, session["user_id"]))
    account = cursor.fetchone()
    conn.close()
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

@app.route("/settings")
def settings_page():
    if "user_id" not in session: return redirect("/")
    return render_template_string(SETTINGS_HTML)

@app.route("/update_credentials", methods=["POST"])
def update_credentials():
    if "user_id" not in session: return redirect("/")
    new_password = request.form.get("new_password", "").strip()
    if new_password:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (generate_password_hash(new_password), session["user_id"]))
        conn.commit()
        conn.close()
    return "<script>alert('تم تحديث كلمة المرور!'); window.location.href='/settings';</script>"

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
def about_page(): return render_template_string(ABOUT_HTML)

@app.route("/admin/users")
def admin_users():
    if "user_id" not in session: return redirect("/")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users WHERE id = ?", (session["user_id"],))
    user_row = cursor.fetchone()
    if not user_row or user_row[0] not in ['morad', 'admin']:
        conn.close()
        return "غير مسموح لك بالوصول.", 403
    cursor.execute("SELECT users.id, users.username, COUNT(app_accounts.id) FROM users LEFT JOIN app_accounts ON users.id = app_accounts.user_id GROUP BY users.id")
    users_data = cursor.fetchall()
    conn.close()
    return render_template_string(ADMIN_HTML, users_data=users_data)

@app.route("/register", methods=["POST"])
def register():
    username, password = request.form.get("username", "").strip(), request.form.get("password", "").strip()
    if not username or not password: return "<script>alert('يرجى تعبئة جميع الحقول!'); window.location.href='/';</script>"
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, generate_password_hash(password)))
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
    return "<script>alert('اسم المستخدم أو كلمة السر غير صحيحة!'); window.location.href='/';</script>"

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
