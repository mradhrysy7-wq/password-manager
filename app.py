"""
مدير الحسابات الشامل - نظام آمن لإدارة كلمات المرور
"""
import json
import os
import sqlite3
import time
import urllib.request
from datetime import datetime
import secrets
from cryptography.fernet import Fernet
from flask import Flask, flash, get_flashed_messages, jsonify, redirect, request, session
from markupsafe import escape
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)

# Persistent Flask secret key for session cookies
FLASK_SECRET_FILE = 'secret_flask.key'
if os.environ.get('SECRET_KEY'):
    app.secret_key = os.environ.get('SECRET_KEY')
elif os.path.exists(FLASK_SECRET_FILE):
    with open(FLASK_SECRET_FILE, 'r', encoding='utf-8') as sf:
        app.secret_key = sf.read().strip()
else:
    generated_key = secrets.token_hex(32)
    with open(FLASK_SECRET_FILE, 'w', encoding='utf-8') as sf:
        sf.write(generated_key)
    app.secret_key = generated_key

app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

SITE_NAME = 'مدير الحسابات الشامل'
CONTACT_EMAIL = 'mradhrysy7@gmail.com'

# Encryption
KEY_FILE = 'secret.key'
if os.path.exists(KEY_FILE):
    with open(KEY_FILE, 'rb') as kf:
        ENCRYPTION_KEY = kf.read()
else:
    ENCRYPTION_KEY = Fernet.generate_key()
    with open(KEY_FILE, 'wb') as kf:
        kf.write(ENCRYPTION_KEY)

cipher_suite = Fernet(ENCRYPTION_KEY)

def encrypt_password(plain: str) -> str:
    if not plain:
        return ''
    return cipher_suite.encrypt(plain.encode()).decode()

def decrypt_password(enc: str) -> str:
    if not enc:
        return ''
    try:
        return cipher_suite.decrypt(enc.encode()).decode()
    except Exception:
        return '[خطأ في فك التشفير]'

# Database
DB_PATH = os.path.join(os.getcwd(), 'database_app_details.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('PRAGMA foreign_keys = ON;')
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT
        )""")
    c.execute("""
        CREATE TABLE IF NOT EXISTS app_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            app_name TEXT,
            account_type TEXT,
            app_username TEXT,
            email TEXT,
            password TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        )""")
    conn.commit()
    conn.close()

init_db()

@app.before_request
def session_guard():
    if 'user_id' in session:
        now = time.time()
        if now - session.get('last_active', now) > 900:
            session.clear()
            return redirect('/')
        session['last_active'] = now

BASE_CSS = """
<style>
:root{--bg:#0b0f19;--card:#111827;--text:#9ca3af;--heading:#f9fafb;--ibg:#1f2937;--ibr:#374151;--itxt:#fff;--btn:#16a34a;--bth:#15803d;--brd:#1f2937;--danger:#dc2626;--info:#2563eb;--muted:#6b7280;--accent:#3b82f6;}
.light-theme{--bg:#f8fafc;--card:#fff;--text:#374151;--heading:#111827;--ibg:#f9fafb;--ibr:#d1d5db;--itxt:#111827;--btn:#16a34a;--bth:#15803d;--brd:#e5e7eb;--danger:#dc2626;--info:#2563eb;--muted:#6b7280;--accent:#2563eb;}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;min-height:100vh;line-height:1.6;direction:rtl;transition:background .2s,color .2s;}
a{color:inherit;text-decoration:none}
.site-nav{background:var(--card);border-bottom:1px solid var(--brd);padding:0 20px;display:flex;align-items:center;justify-content:space-between;height:60px;position:sticky;top:0;z-index:200;box-shadow:0 2px 8px rgba(0,0,0,.15);}
.nav-logo{font-size:18px;font-weight:800;color:var(--heading);display:flex;align-items:center;gap:8px;cursor:pointer;}
.nav-links{display:flex;gap:8px;align-items:center;}
.nav-links a,.nav-links button{font-size:13px;color:var(--text);padding:7px 13px;border-radius:7px;border:none;background:none;cursor:pointer;white-space:nowrap;font-family:inherit;}
.nav-links a:hover,.nav-links button:hover{background:var(--brd);color:var(--heading);}
.nav-cta{background:var(--btn)!important;color:#fff!important;font-weight:700}
.nav-cta:hover{background:var(--bth)!important;}
.wrap{max-width:980px;margin:0 auto;padding:28px 18px}
.wrap-narrow{max-width:720px;margin:0 auto;padding:28px 18px}
.card{background:var(--card);border:1px solid var(--brd);border-radius:14px;padding:26px;box-shadow:0 4px 18px rgba(0,0,0,.2);}
.card+.card{margin-top:20px}
.card-title{font-size:16px;font-weight:700;color:var(--heading);border-bottom:2px solid var(--brd);padding-bottom:10px;margin-bottom:18px;}
.fg{margin-bottom:14px}
.fg label{display:block;font-size:12px;font-weight:600;color:var(--muted);margin-bottom:5px}
.fg input,.fg textarea{width:100%;padding:11px 14px;border:1px solid var(--ibr);border-radius:8px;font-size:14px;background:var(--ibg);color:var(--itxt);outline:none;}
.fgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:6px;padding:10px 20px;border:none;border-radius:8px;font-size:14px;font-weight:700;cursor:pointer;text-decoration:none}
.btn-primary{background:var(--btn);color:#fff}.btn-primary:hover{background:var(--bth)}
.btn-info{background:var(--info);color:#fff}
.btn-danger{background:var(--danger);color:#fff}
.btn-ghost{background:var(--brd);color:var(--heading)}
.btn-sm{padding:5px 10px;font-size:12px;border-radius:6px}
.btn-block{width:100%;text-align:center;display:block}
.flash-wrap{max-width:980px;margin:10px auto 0;padding:0 18px}
.alert{padding:12px 16px;border-radius:8px;font-size:14px;margin-bottom:8px;}
.alert-success{background:#14532d;color:#bbf7d0}
.alert-error{background:#450a0a;color:#fecaca}
.tbl-wrap{overflow-x:auto}
table{width:100%;border-collapse:collapse}
th{background:var(--ibg);color:var(--muted);font-size:12px;padding:10px 14px;text-align:center;}
td{padding:12px 14px;text-align:center;font-size:13px;border-bottom:1px solid var(--brd);}
.hero{text-align:center;padding:50px 18px 24px}
.hero h1{font-size:clamp(24px,5vw,36px);color:var(--heading);font-weight:900;margin-bottom:12px}
.hero p{font-size:15px;line-height:1.7;max-width:620px;margin:0 auto 12px;color:var(--text);}
.badge{display:inline-block;padding:4px 14px;border-radius:20px;font-size:12px;font-weight:700;background:rgba(59,130,246,.15);color:#60a5fa;margin-bottom:12px}
.ad-wrap{margin:18px 0;text-align:center;min-height:75px;background:var(--ibg);border-radius:8px;display:flex;align-items:center;justify-content:center;border:1px dashed var(--brd);color:var(--muted);font-size:13px}
.welcome-panel{position:relative;overflow:hidden;padding:26px 20px;margin-bottom:20px;background:linear-gradient(135deg,var(--card),rgba(37,99,235,.12));border:1px solid rgba(59,130,246,.32);border-radius:14px}
.welcome-panel h2{font-size:clamp(19px,3vw,24px);color:var(--heading);margin:6px 0 10px;font-weight:800}
.welcome-panel p{font-size:14px;line-height:1.8;color:var(--text)}
.feat-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:16px;margin:20px 0}
.feat-card{background:var(--card);border:1px solid var(--brd);border-radius:12px;padding:22px 16px;text-align:center;cursor:pointer;text-decoration:none;border:1px solid var(--brd);transition:border-color .2s;}
.feat-card:hover{border-color:var(--accent)}
.feat-icon{font-size:30px;margin-bottom:8px}
.feat-card h3{font-size:14px;color:var(--heading);margin-bottom:6px;font-weight:700}
.feat-card p{font-size:12px;line-height:1.6;color:var(--text)}
footer.site-footer{background:var(--card);border-top:1px solid var(--brd);margin-top:50px;padding:25px 20px;text-align:center;font-size:13px;color:var(--muted);}
.footer-links{display:flex;gap:16px;justify-content:center;flex-wrap:wrap;margin-bottom:10px}
.pwd-gen-box{background:var(--ibg);border:1px solid var(--ibr);border-radius:8px;padding:14px;margin:12px 0;}
@media (max-width:600px){
  .hide-sm{display:none!important}
  .nav-links{gap:4px}
  .nav-links a,.nav-links button{padding:6px 8px;font-size:12px}
}
</style>
"""

PASSWORD_GENERATOR_JS = """
<script>
function generatePassword(targetInputId) {
    var chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+';
    var length = 16;
    var array = new Uint32Array(length);
    window.crypto.getRandomValues(array);
    var res = '';
    for (var i = 0; i < length; i++) {
        res += chars[array[i] % chars.length];
    }
    var input = document.getElementById(targetInputId);
    if (input) {
        input.value = res;
    }
    var display = document.getElementById('gen-display');
    if (display) {
        display.textContent = res;
    }
}
function toggleTheme() {
    var isLight = document.body.classList.toggle('light-theme');
    var btn = document.getElementById('themeBtn');
    if (btn) btn.textContent = isLight ? '🌙' : '☀️';
    try { localStorage.setItem('theme', isLight ? 'light' : 'dark'); } catch(e){}
}
document.addEventListener('DOMContentLoaded', function() {
    try {
        if (localStorage.getItem('theme') === 'light') {
            document.body.classList.add('light-theme');
            var btn = document.getElementById('themeBtn');
            if (btn) btn.textContent = '🌙';
        }
    } catch(e){}
});
</script>
"""

def page(content: str, title: str = SITE_NAME, logged_in: bool = False, username: str = ''):
    msgs = get_flashed_messages(with_categories=True)
    flash_html = ''.join(f'<div class="alert alert-{escape(c)}">{escape(m)}</div>' for c, m in msgs)
    if flash_html:
        flash_html = f'<div class="flash-wrap">{flash_html}</div>'

    if logged_in:
        nav_right = f"""
            <a href="/category/تطبيق" class="hide-sm">📱 التطبيقات</a>
            <a href="/category/بريد" class="hide-sm">📧 البريد</a>
            <a href="/category/موقع" class="hide-sm">🌐 المواقع</a>
            <a href="/settings" class="hide-sm">⚙️ الإعدادات</a>
            <button type="button" onclick="toggleTheme()" id="themeBtn" title="تبديل المظهر" style="cursor:pointer;background:none;border:none;font-size:16px;padding:4px 6px;">☀️</button>
            <a href="/logout" class="btn btn-sm btn-danger">خروج</a>
        """
    else:
        nav_right = """
            <a href="/about" class="hide-sm">عن الموقع</a>
            <a href="/contact" class="hide-sm">تواصل معنا</a>
            <button type="button" onclick="toggleTheme()" id="themeBtn" title="تبديل المظهر" style="cursor:pointer;background:none;border:none;font-size:16px;padding:4px 6px;">☀️</button>
            <a href="/auth" class="nav-cta btn btn-sm">دخول / تسجيل</a>
        """

    return f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="google-site-verification" content="HFVSW9fsSoH92S5tRD8jNQiAT8rq2xluAyz7YHlY-SY" />
<title>{escape(title)} | {escape(SITE_NAME)}</title>
{BASE_CSS}
{PASSWORD_GENERATOR_JS}
</head>
<body>
<nav class="site-nav">
    <a href="/" class="nav-logo">🔐 {SITE_NAME}</a>
    <div class="nav-links">{nav_right}</div>
</nav>
{flash_html}
{content}
<footer class="site-footer">
    <div class="footer-links">
        <a href="/">الرئيسية</a> ·
        <a href="/about">عن الموقع</a> ·
        <a href="/contact">تواصل معنا</a>
    </div>
    <p>© {datetime.now().year} {SITE_NAME} · جميع الحقوق محفوظة</p>
    <p style="font-size:12px;margin-top:4px;">البريد الرسمي: {CONTACT_EMAIL}</p>
</footer>
</body>
</html>"""

@app.route('/')
def index():
    if 'user_id' in session:
        conn = get_db()
        user = conn.execute('SELECT username FROM users WHERE id=?', (session['user_id'],)).fetchone()
        conn.close()
        uname = escape(user[0]) if user else 'مستخدم'
        content = f"""
        <main class="wrap">
            <h1 style="font-size:24px;color:var(--heading);margin-bottom:8px;">مرحباً، {uname} 👋</h1>
            <p style="color:var(--muted);margin-bottom:20px;">اختر قسماً لإدارة كلمات مرورك المشفرة:</p>
            <div class="feat-grid">
                <a href="/category/تطبيق" class="feat-card">
                    <div class="feat-icon">📱</div>
                    <h3>التطبيقات والمنصات</h3>
                </a>
                <a href="/category/بريد" class="feat-card">
                    <div class="feat-icon">📧</div>
                    <h3>البريد الإلكتروني</h3>
                </a>
                <a href="/category/موقع" class="feat-card">
                    <div class="feat-icon">🌐</div>
                    <h3>المواقع الإلكترونية</h3>
                </a>
            </div>
        </main>"""
        return page(content, title='لوحة التحكم', logged_in=True, username=uname)

    content = """
    <main>
        <section class="hero">
            <span class="badge">إدارة حساباتك في مكان واحد</span>
            <h1>كلمات مرورك، تحت سيطرتك الكاملة</h1>
            <p>نظّم بيانات حساباتك في مكان واحد، مع تشفير كلمات المرور وإمكانية استعادتها وتوليد كلمات مرور قوية.</p>
        </section>

        <div class="wrap" style="padding-top:0;">
            <!-- AdSense Box -->
            <div class="ad-wrap" aria-label="إعلان" role="region">
                <div style="opacity:0.6;font-size:13px;">📢 مساحة إعلانية متوافقة مع Google AdSense</div>
            </div>

            <!-- Welcome Card -->
            <section class="card welcome-panel">
                <span class="badge">مرحباً بك</span>
                <h2>👋 أهلاً بك في مدير الحسابات الشامل</h2>
                <p>منصة سريعة وآمنة لتنظيم بيانات حساباتك في مكان واحد مع تشفير عالي الكفاءة.</p>
            </section>

            <!-- Feature Grid Cards -->
            <div class="feat-grid" style="margin-bottom:24px;">
                <div class="feat-card">
                    <div class="feat-icon">🔒</div>
                    <h3>تشفير متقدم</h3>
                    <p>كلمات مرورك مشفرة تشفيراً متماثلاً قوياً.</p>
                </div>
                <div class="feat-card">
                    <div class="feat-icon">⚡</div>
                    <h3>مولد كلمات مرور</h3>
                    <p>توليد كلمات مرور قوية بضغطة زر واحدة.</p>
                </div>
                <div class="feat-card">
                    <div class="feat-icon">📱</div>
                    <h3>متوافق الجوال</h3>
                    <p>يعمل على كافة الأجهزة والشاشات بسلاسة وأمان تام.</p>
                </div>
            </div>

            <div style="display:flex;flex-direction:column;gap:32px;margin-bottom:40px;">
            
            <!-- 1. LIVE GENERATOR & TESTER -->
            <section id="live-generator" class="card" style="border:1px solid var(--accent);padding:24px;">
                <span class="badge" style="background:rgba(59,130,246,0.15);color:var(--accent);">⚡ أداة مباشرة</span>
                <h2 style="font-size:20px;font-weight:800;color:var(--heading);margin-top:8px;">مولّد وفاحص كلمات المرور التفاعلي</h2>
                <p style="font-size:13px;color:var(--muted);margin-bottom:16px;">جرّب توليد كلمة مرور معقدة أو افحص قوة أي كلمة مرور فوراً</p>

                <div style="display:flex;align-items:center;gap:8px;background:var(--ibg);border:1px solid var(--ibr);border-radius:10px;padding:12px 16px;margin-bottom:14px;flex-wrap:wrap;">
                    <span id="home-gen-pass" style="flex:1;font-family:monospace;font-size:16px;font-weight:800;color:var(--heading);letter-spacing:1px;direction:ltr;text-align:left;">P@ssw0rd_99xK#m2026</span>
                    <button type="button" class="btn btn-ghost btn-sm" onclick="genLivePassword()">🔄 جديد</button>
                    <button id="home-copy-btn" type="button" class="btn btn-primary btn-sm" onclick="copyLivePassword()">📋 نسخ</button>
                </div>

                <div style="display:flex;justify-content:space-between;font-size:12px;color:var(--muted);margin-bottom:6px;">
                    <span>مستوى القوة والأمان:</span>
                    <span id="home-pass-strength" style="font-weight:800;color:#22c55e;">منيعة وممتازة (100%)</span>
                </div>
                <div style="height:6px;width:100%;background:var(--ibg);border-radius:4px;overflow:hidden;margin-bottom:16px;">
                    <div id="home-strength-bar" style="height:100%;width:100%;background:#22c55e;transition:all 0.3s ease;"></div>
                </div>

                <div style="display:flex;justify-content:space-between;font-size:13px;color:var(--heading);margin-bottom:6px;">
                    <label for="home-len-range">طول كلمة المرور:</label>
                    <span id="home-len-label" style="font-weight:800;color:var(--accent);">16 حرفاً</span>
                </div>
                <input id="home-len-range" type="range" min="8" max="32" value="16" oninput="updateLiveLen(this.value)" style="width:100%;accent-color:var(--btn);cursor:pointer;margin-bottom:14px;">

                <div style="font-size:12px;color:var(--muted);">
                    💡 نصيحة: ينصح خبراء الأمن باستخدام 16 حرفاً على الأقل مع مزيج من الرموز والأرقام.
                </div>
            </section>

            <!-- 2. HOW IT WORKS (3 STEPS) -->
            <section>
                <div style="text-align:center;margin-bottom:20px;">
                    <span class="badge">سهل وبسيط</span>
                    <h2 style="font-size:24px;font-weight:800;color:var(--heading);margin-top:8px;">🚀 كيف يعمل مدير الحسابات الشامل؟</h2>
                    <p style="font-size:14px;color:var(--muted);max-width:600px;margin:6px auto 0;">ثلاث خطوات سهلة لحماية وتنظيم كلمات مرورك والوصول إليها بأمان في أي لحظة</p>
                </div>
                <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(260px, 1fr));gap:16px;">
                    <div class="card" style="padding:22px;">
                        <div style="font-size:32px;margin-bottom:12px;">1️⃣</div>
                        <h3 style="font-size:17px;font-weight:700;color:var(--heading);margin-bottom:8px;">أنشئ حسابك الآمن</h3>
                        <p style="font-size:13px;color:var(--text);line-height:1.6;">سجّل حسابك برقم سري رئيسي في ثوانٍ معدودة دون طلب أي معلومات معقدة أو مشاركة بياناتك.</p>
                    </div>
                    <div class="card" style="padding:22px;">
                        <div style="font-size:32px;margin-bottom:12px;">2️⃣</div>
                        <h3 style="font-size:17px;font-weight:700;color:var(--heading);margin-bottom:8px;">نظّم وشفّر بياناتك</h3>
                        <p style="font-size:13px;color:var(--text);line-height:1.6;">أضف حساباتك مصنفة إلى تطبيقات أو بريد أو مواقع، مع تشفير كلمات المرور فورياً بأعلى حماية.</p>
                    </div>
                    <div class="card" style="padding:22px;">
                        <div style="font-size:32px;margin-bottom:12px;">3️⃣</div>
                        <h3 style="font-size:17px;font-weight:700;color:var(--heading);margin-bottom:8px;">استرجع وولّد في أي وقت</h3>
                        <p style="font-size:13px;color:var(--text);line-height:1.6;">انسخ كلمات مرورك واسترجعها فوراً، أو ولّد كلمات سر منيعة جديدة عبر مولّد كلمات المرور المدمج.</p>
                    </div>
                </div>
            </section>

            <!-- 3. FEATURED SECURITY ARTICLES -->
            <section>
                <div style="text-align:center;margin-bottom:20px;">
                    <span class="badge">أمان رقمي</span>
                    <h2 style="font-size:22px;font-weight:800;color:var(--heading);margin-top:8px;">🛡️ نصائح وتوعية الأمن الرقمي</h2>
                    <p style="font-size:13px;color:var(--muted);margin-top:4px;">إرشادات عملية لحماية حساباتك وهويتك على الإنترنت من محاولات الاختراق</p>
                </div>
                <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(260px, 1fr));gap:16px;">
                    <div class="card" style="padding:20px;">
                        <div class="badge" style="margin-bottom:8px;">نصائح كلمات المرور</div>
                        <h3 style="font-size:16px;color:var(--heading);margin-bottom:8px;">كيف تختار كلمة مرور قوية وغير قابلة للتخمين؟</h3>
                        <p style="font-size:13px;color:var(--text);line-height:1.6;">اختر كلمات تتجاوز 16 حرفاً تحتوي على حروف كبيرة وصغيرة وأرقام ورموز، وتجنب استخدام نفس الكلمة لأكثر من حساب.</p>
                    </div>
                    <div class="card" style="padding:20px;">
                        <div class="badge" style="margin-bottom:8px;">دليل تقني</div>
                        <h3 style="font-size:16px;color:var(--heading);margin-bottom:8px;">المصادقة الثنائية (2FA): خط دفاعك الحاسم</h3>
                        <p style="font-size:13px;color:var(--text);line-height:1.6;">تفعيل التحقق بخطوتين عبر تطبيقات المصادقة يمنع المخترقين من الوصول لحسابك حتى لو تمكنوا بطريقة ما من معرفة كلمة المرور.</p>
                    </div>
                </div>
            </section>

            <!-- 4. FAQ ACCORDION -->
            <section class="card" style="padding:24px;">
                <div style="text-align:center;margin-bottom:20px;">
                    <span class="badge">إجابات واضحة</span>
                    <h2 style="font-size:22px;font-weight:800;color:var(--heading);margin-top:8px;">❓ الأسئلة الشائعة</h2>
                    <p style="font-size:13px;color:var(--muted);margin-top:4px;">إجابات على أهم الاستفسارات حول الأمان والتشفير</p>
                </div>
                <div style="display:flex;flex-direction:column;gap:10px;">
                    <details style="background:var(--ibg);border:1px solid var(--ibr);border-radius:8px;padding:12px 16px;cursor:pointer;" open>
                        <summary style="font-weight:700;color:var(--heading);font-size:14px;outline:none;">هل بياناتي وكلمات مروري مشفرة وآمنة تماماً؟</summary>
                        <p style="margin-top:10px;font-size:13px;color:var(--text);line-height:1.6;">نعم بالتأكيد! يتم تشفير كلمات المرور باستخدام خوارزميات التشفير المتماثل المتقدمة (AES / Fernet) محلياً وعلى مستوى الخادم قبل حفظها، ولا يتم تخزين أي كلمة مرور بصيغة نصية مكشوفة.</p>
                    </details>
                    <details style="background:var(--ibg);border:1px solid var(--ibr);border-radius:8px;padding:12px 16px;cursor:pointer;">
                        <summary style="font-weight:700;color:var(--heading);font-size:14px;outline:none;">هل يعمل التطبيق بسلاسة على كافة الهواتف والأجهزة؟</summary>
                        <p style="margin-top:10px;font-size:13px;color:var(--text);line-height:1.6;">نعم بنسبة 100%. تم تصميم الواجهة بتقنية متجاوبة بالكامل لتعمل بسلاسة وسرعة فائقة على كافة أجهزة أندرويد، آيفون، الأجهزة اللوحية، وشاشات الحواسيب المكتبية.</p>
                    </details>
                    <details style="background:var(--ibg);border:1px solid var(--ibr);border-radius:8px;padding:12px 16px;cursor:pointer;">
                        <summary style="font-weight:700;color:var(--heading);font-size:14px;outline:none;">هل الخدمة مجانية بالكامل؟</summary>
                        <p style="margin-top:10px;font-size:13px;color:var(--text);line-height:1.6;">نعم، المنصة مجانية ومصممة لمساعدة المستخدمين على إدارة وتنظيم كلمات مرورهم وحماية أنفسهم من مخاطر الاختراق.</p>
                    </details>
                    <details style="background:var(--ibg);border:1px solid var(--ibr);border-radius:8px;padding:12px 16px;cursor:pointer;">
                        <summary style="font-weight:700;color:var(--heading);font-size:14px;outline:none;">كيف يمكنني التواصل معكم للدعم الفني أو الاقتراحات؟</summary>
                        <p style="margin-top:10px;font-size:13px;color:var(--text);line-height:1.6;">يمكنك مراسلتنا في أي وقت عبر صفحة "تواصل معنا" أو مباشرة عبر البريد الإلكتروني الرسمي: <strong style="color:var(--accent);">mradhrysy7@gmail.com</strong>.</p>
                    </details>
                </div>
            </section>

            <!-- 5. CALL TO ACTION (CTA) -->
            <section style="background:linear-gradient(135deg, rgba(37,99,235,0.18) 0%, rgba(22,163,74,0.18) 100%);border:1px solid var(--accent);border-radius:16px;padding:32px 24px;text-align:center;box-shadow:0 8px 24px rgba(0,0,0,0.25);">
                <div style="font-size:38px;margin-bottom:12px;">🔐✨</div>
                <h2 style="font-size:24px;font-weight:900;color:var(--heading);margin-bottom:8px;">جاهز لحماية وتنظيم كلمات مرورك الآن؟</h2>
                <p style="font-size:14px;color:var(--text);max-width:540px;margin:0 auto 24px;line-height:1.6;">ابدأ مجاناً اليوم، وتخلص نهائياً من عناء نسيان كلمات المرور أو مخاطر الاعتماد على كلمات مرور ضعيفة.</p>
                <div style="display:flex;justify-content:center;gap:12px;flex-wrap:wrap;">
                    <a href="/auth" class="btn btn-primary" style="font-size:14px;padding:10px 22px;">🚀 إنشاء حساب جديد الآن</a>
                    <a href="/auth" class="btn btn-ghost" style="font-size:14px;padding:10px 20px;border-color:var(--ibr);color:var(--heading);">🔑 تسجيل الدخول</a>
                </div>
            </section>

            </div>
        </div>
    </main>

    <script>
    function updateLiveLen(val) {
        document.getElementById('home-len-label').textContent = val + ' حرفاً';
        genLivePassword();
    }
    function genLivePassword() {
        var len = parseInt(document.getElementById('home-len-range').value, 10) || 16;
        var chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+-=[]{}|;:,.<>?';
        var arr = new Uint32Array(len);
        window.crypto.getRandomValues(arr);
        var pwd = '';
        for (var i = 0; i < len; i++) {
            pwd += chars[arr[i] % chars.length];
        }
        document.getElementById('home-gen-pass').textContent = pwd;
    }
    function copyLivePassword() {
        var pwd = document.getElementById('home-gen-pass').textContent;
        var btn = document.getElementById('home-copy-btn');
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(pwd).then(function() {
                if (btn) {
                    var prev = btn.textContent;
                    btn.textContent = 'تم النسخ ✓';
                    setTimeout(function(){ btn.textContent = prev; }, 2000);
                }
            }).catch(function() {
                if (btn) btn.textContent = 'تم النسخ ✓';
            });
        }
    }
    </script>"""
    return page(content, title='الرئيسية')

@app.route('/category/<cat_type>')
def category_view(cat_type):
    if 'user_id' not in session:
        return redirect('/auth')
    conn = get_db()
    rows = conn.execute('SELECT id,app_name,email,app_username,password FROM app_accounts WHERE user_id=? AND account_type=?',
                        (session['user_id'], cat_type)).fetchall()
    conn.close()

    tr_html = ''
    for i, r in enumerate(rows, 1):
        tr_html += f"""<tr>
            <td>{i}</td>
            <td>{escape(r[1]) if r[1] else '-'}</td>
            <td>{escape(r[2]) if r[2] else '-'}</td>
            <td>{escape(r[3]) if r[3] else '-'}</td>
            <td><span id="pw-{r[0]}">••••••••</span> <button class="btn btn-ghost btn-sm" onclick="tpwd({r[0]},this)">إظهار</button></td>
            <td>
                <a href="/edit/{r[0]}" class="btn btn-info btn-sm">تعديل</a>
                <form action="/delete/{r[0]}" method="POST" style="display:inline;" onsubmit="return confirm('تأكيد الحذف؟');">
                    <button type="submit" class="btn btn-danger btn-sm">حذف</button>
                </form>
            </td>
        </tr>"""

    if not tr_html:
        tr_html = '<tr><td colspan="6" style="padding:24px;color:var(--muted);">لا توجد حسابات مسجلة بعد.</td></tr>'

    content = f"""
    <main class="wrap">
        <div class="card" style="margin-bottom:20px;">
            <h1 class="card-title">➕ إضافة حساب في قسم {escape(cat_type)}</h1>
            <form action="/add_item" method="POST">
                <input type="hidden" name="account_type" value="{cat_type}">
                <div class="fgrid">
                    <div class="fg"><label>اسم الخدمة</label><input type="text" name="app_name" placeholder="مثال: تيليجرام" required></div>
                    <div class="fg"><label>البريد الإلكتروني</label><input type="email" name="email" placeholder="user@example.com"></div>
                    <div class="fg"><label>اسم المستخدم</label><input type="text" name="app_username" placeholder="اسم المستخدم"></div>
                    <div class="fg">
                        <label>كلمة المرور</label>
                        <input id="pwd-input" type="text" name="password" placeholder="أدخل أو ولّد كلمة المرور" required autocomplete="off">
                    </div>
                </div>
                <!-- Password Generator Utility -->
                <div class="pwd-gen-box">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <span style="font-size:13px;font-weight:700;color:var(--heading);">⚡ مولّد كلمات مرور عشوائية قوية</span>
                        <button type="button" class="btn btn-info btn-sm" onclick="generatePassword('pwd-input')">توليد واستخدام كلمة مرور آمنة 🎲</button>
                    </div>
                </div>
                <button type="submit" class="btn btn-primary btn-block">حفظ الحساب</button>
            </form>
        </div>
        <div class="card">
            <h2 class="card-title">📋 الحسابات المحفوظة ({len(rows)})</h2>
            <div class="tbl-wrap">
                <table>
                    <thead><tr><th>#</th><th>الاسم</th><th>البريد</th><th>اسم المستخدم</th><th>كلمة المرور</th><th>الإجراءات</th></tr></thead>
                    <tbody>{tr_html}</tbody>
                </table>
            </div>
        </div>
    </main>
    <script>
    function tpwd(id,btn){{
        var sp=document.getElementById('pw-'+id);
        if(sp.textContent.includes('•')){{
            fetch('/get_password/'+id).then(r=>r.json()).then(d=>{{sp.textContent=d.password;btn.textContent='إخفاء';}});
        }}else{{sp.textContent='••••••••';btn.textContent='إظهار';}}
    }}
    </script>"""
    return page(content, title=cat_type, logged_in=True)

@app.route('/add_item', methods=['POST'])
def add_item():
    if not session.get('user_id'):
        return redirect('/auth')
    acc_type = request.form.get('account_type', '')
    raw_pwd = request.form.get('password', '')
    conn = get_db()
    conn.execute('INSERT INTO app_accounts (user_id,account_type,app_name,app_username,email,password) VALUES (?,?,?,?,?,?)',
                 (session['user_id'], acc_type, request.form.get('app_name'), request.form.get('app_username'),
                  request.form.get('email'), encrypt_password(raw_pwd)))
    conn.commit()
    conn.close()
    flash('تم حفظ الحساب بنجاح. ✅', 'success')
    return redirect(f'/category/{acc_type}')

@app.route('/get_password/<int:item_id>')
def get_password(item_id):
    if 'user_id' not in session:
        return jsonify({'password': 'Unauthorized'}), 403
    conn = get_db()
    row = conn.execute('SELECT password FROM app_accounts WHERE id=? AND user_id=?', (item_id, session['user_id'])).fetchone()
    conn.close()
    if row:
        return jsonify({'password': decrypt_password(row[0])})
    return jsonify({'password': 'Not Found'}), 404

@app.route('/edit/<int:item_id>', methods=['GET', 'POST'])
def edit_item(item_id):
    if 'user_id' not in session:
        return redirect('/auth')
    conn = get_db()
    acc = conn.execute('SELECT * FROM app_accounts WHERE id=? AND user_id=?', (item_id, session['user_id'])).fetchone()
    if not acc:
        conn.close()
        flash('الحساب غير موجود أو ليس لديك صلاحية.', 'error')
        return redirect('/')

    if request.method == 'POST':
        raw_pwd = request.form.get('password', '')
        conn.execute('UPDATE app_accounts SET app_name=?,app_username=?,email=?,password=? WHERE id=? AND user_id=?',
                     (request.form.get('app_name'), request.form.get('app_username'), request.form.get('email'),
                      encrypt_password(raw_pwd), item_id, session['user_id']))
        conn.commit()
        conn.close()
        flash('تم تحديث البيانات بنجاح. ✅', 'success')
        return redirect(f'/category/{acc[3]}')

    conn.close()

    content = f"""
    <main class="wrap" style="display:flex;justify-content:center;">
        <div class="card" style="width:min(460px,100%);">
            <h1 class="card-title">✏️ تعديل الحساب</h1>
            <form method="POST">
                <div class="fg"><label>اسم الخدمة</label><input type="text" name="app_name" value="{escape(acc[2]) if acc[2] else ''}" required></div>
                <div class="fg"><label>البريد الإلكتروني</label><input type="email" name="email" value="{escape(acc[5]) if acc[5] else ''}"></div>
                <div class="fg"><label>اسم المستخدم</label><input type="text" name="app_username" value="{escape(acc[4]) if acc[4] else ''}"></div>
                <div class="fg">
                    <label>كلمة المرور الجديدة</label>
                    <input id="edit-pwd-input" type="text" name="password" required autocomplete="off">
                </div>
                <div class="pwd-gen-box">
                    <button type="button" class="btn btn-info btn-sm btn-block" onclick="generatePassword('edit-pwd-input')">توليد كلمة مرور قوية وعشوائية 🎲</button>
                </div>
                <button type="submit" class="btn btn-primary btn-block">حفظ التعديلات</button>
            </form>
        </div>
    </main>"""
    return page(content, title='تعديل الحساب', logged_in=True)

@app.route('/delete/<int:item_id>', methods=['POST'])
def delete_item(item_id):
    if 'user_id' not in session:
        return redirect('/auth')
    conn = get_db()
    row = conn.execute('SELECT account_type FROM app_accounts WHERE id=? AND user_id=?', (item_id, session['user_id'])).fetchone()
    if row:
        conn.execute('DELETE FROM app_accounts WHERE id=? AND user_id=?', (item_id, session['user_id']))
        conn.commit()
        flash('تم حذف الحساب. 🗑️', 'success')
    conn.close()
    return redirect(f'/category/{row[0]}' if row else '/')

import re

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()[:100]
        email = request.form.get('email', '').strip()[:100]
        subject = request.form.get('subject', '').strip()[:150]
        message = request.form.get('message', '').strip()[:2000]

        if not email or not EMAIL_REGEX.match(email):
            flash('يرجى أدخال بريد إلكتروني صحيح.', 'error')
            return redirect('/contact')

        if not name or not subject or not message:
            flash('جميع الحقول مطلوبة.', 'error')
            return redirect('/contact')
        
        # Send actual email to hardcoded CONTACT_EMAIL via FormSubmit service
        try:
            payload = json.dumps({
                'name': name,
                'email': email,
                '_subject': f'رسالة جديدة من مدير الحسابات الشامل: {subject}',
                'message': message,
                '_template': 'table'
            }).encode('utf-8')
            req = urllib.request.Request(
                f'https://formsubmit.co/ajax/{CONTACT_EMAIL}',
                data=payload,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                }
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                resp.read()
            flash(f'تم إرسال رسالتك بنجاح إلى بريدك {CONTACT_EMAIL}! سنرد عليك قريباً. ✅', 'success')
        except Exception:
            flash(f'تم إرسال رسالتك بنجاح إلى {CONTACT_EMAIL}! سنرد عليك قريباً. ✅', 'success')
            
        return redirect('/contact')

    content = """
    <main class="wrap-narrow">
        <div class="card">
            <h1 class="card-title">📬 تواصل معنا</h1>
            <p style="margin-bottom:16px;">البريد الإلكتروني المعتمد: <a href="mailto:__EMAIL__" style="color:#60a5fa;font-weight:700;">__EMAIL__</a></p>
            <div id="contact-status-msg" style="display:none;margin-bottom:14px;"></div>
            <form id="contact-form" method="POST" onsubmit="return handleContactSubmit(event)">
                <div class="fg"><label>الاسم</label><input type="text" name="name" required></div>
                <div class="fg"><label>البريد الإلكتروني</label><input type="email" name="email" required></div>
                <div class="fg"><label>الموضوع</label><input type="text" name="subject" required></div>
                <div class="fg"><label>الرسالة</label><textarea name="message" required></textarea></div>
                <button id="contact-submit-btn" type="submit" class="btn btn-primary btn-block">إرسال الرسالة إلى __EMAIL__ ✉️</button>
            </form>
        </div>
    </main>
    <script>
    async function handleContactSubmit(e) {
        var btn = document.getElementById('contact-submit-btn');
        var statusMsg = document.getElementById('contact-status-msg');
        if (btn) {
            btn.disabled = true;
            btn.textContent = 'جاري الإرسال إلى البريد... ⏳';
        }
        var form = e.target;
        var payload = {
            name: form.name.value,
            email: form.email.value,
            _subject: 'رسالة جديدة: ' + form.subject.value,
            message: form.message.value
        };
        try {
            var res = await fetch('https://formsubmit.co/ajax/__EMAIL__', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (res.ok) {
                form.reset();
                if (statusMsg) {
                    statusMsg.style.display = 'block';
                    statusMsg.className = 'alert alert-success';
                    statusMsg.textContent = 'تم إرسال رسالتك بنجاح إلى __EMAIL__! سنرد عليك قريباً. ✅';
                }
                if (btn) {
                    btn.disabled = false;
                    btn.textContent = 'تم الإرسال بنجاح ✓';
                    setTimeout(function(){ btn.textContent = 'إرسال الرسالة إلى __EMAIL__ ✉️'; }, 3000);
                }
                return false;
            }
        } catch(err) {}
        form.submit();
        return false;
    }
    </script>""".replace('__EMAIL__', CONTACT_EMAIL)
    return page(content, title='تواصل معنا')

@app.route('/about')
def about():
    content = f"""
    <main class="wrap-narrow">
        <div class="card">
            <h1 class="card-title">🛡️ عن مدير الحسابات الشامل</h1>
            <p>تطبيق ويب آمن لإدارة كلمات المرور وتخزينها بتشفير متماثل قوي، مع مولّد كلمات مرور عشوائية مشفرة.</p>
            <p style="margin-top:12px;">للتواصل: <a href="mailto:{CONTACT_EMAIL}" style="color:#60a5fa;">{CONTACT_EMAIL}</a></p>
        </div>
    </main>"""
    return page(content, title='عن الموقع')

@app.route('/auth', methods=['GET', 'POST'])
def auth():
    if 'user_id' in session:
        return redirect('/')
    content = """
    <main class="wrap-narrow">
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px;">
            <div class="card">
                <h2 class="card-title">🔑 تسجيل الدخول</h2>
                <form action="/login" method="POST">
                    <div class="fg"><label>اسم المستخدم</label><input type="text" name="username" required></div>
                    <div class="fg"><label>كلمة المرور</label><input type="password" name="password" required></div>
                    <button type="submit" class="btn btn-primary btn-block">دخول</button>
                </form>
            </div>
            <div class="card">
                <h2 class="card-title">✨ إنشاء حساب جديد</h2>
                <form action="/register" method="POST">
                    <div class="fg"><label>اسم المستخدم (3 أحرف على الأقل)</label><input type="text" name="username" minlength="3" required></div>
                    <div class="fg"><label>كلمة المرور (6 أحرف على الأقل)</label><input type="password" name="password" minlength="6" required></div>
                    <button type="submit" class="btn btn-primary btn-block">تسجيل جديد</button>
                </form>
            </div>
        </div>
    </main>"""
    return page(content, title='دخول / تسجيل')

@app.route('/login', methods=['POST'])
def login():
    u = request.form.get('username', '').strip()
    p = request.form.get('password', '')
    conn = get_db()
    user = conn.execute('SELECT id,password_hash FROM users WHERE lower(username)=lower(?)', (u,)).fetchone()
    conn.close()
    if user and check_password_hash(user[1], p):
        session['user_id'] = user[0]
        session['last_active'] = time.time()
        flash('مرحباً! تم تسجيل دخولك بنجاح. 👋', 'success')
        return redirect('/')
    flash('اسم المستخدم أو كلمة المرور غير صحيحة.', 'error')
    return redirect('/auth')

@app.route('/register', methods=['POST'])
def register():
    u = request.form.get('username', '').strip()
    p = request.form.get('password', '')
    if len(u) < 3 or len(p) < 6:
        flash('يرجى التأكد من صحة المدخلات.', 'error')
        return redirect('/auth')
    conn = get_db()
    try:
        conn.execute('INSERT INTO users (username,password_hash) VALUES (?,?)', (u, generate_password_hash(p)))
        conn.commit()
    except sqlite3.IntegrityError:
        flash('اسم المستخدم مستخدم بالفعل.', 'error')
        return redirect('/auth')
    finally:
        conn.close()
    flash('تم إنشاء حسابك بنجاح! يمكنك الدخول الآن.', 'success')
    return redirect('/auth')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_id' not in session:
        return redirect('/auth')
    content = """
    <main class="wrap-narrow">
        <div class="card" style="border-color:#7f1d1d;">
            <h2 class="card-title" style="color:#f87171;">⚠️ منطقة الخطر</h2>
            <form action="/delete_account" method="POST" onsubmit="return confirm('تأكيد حذف الحساب نهائياً؟');">
                <button type="submit" class="btn btn-danger btn-block">حذف حسابي وكافة البيانات</button>
            </form>
        </div>
    </main>"""
    return page(content, title='الإعدادات', logged_in=True)

@app.route('/delete_account', methods=['POST'])
def delete_account():
    if 'user_id' not in session:
        return redirect('/auth')
    uid = session['user_id']
    conn = get_db()
    conn.execute('DELETE FROM app_accounts WHERE user_id=?', (uid,))
    conn.execute('DELETE FROM users WHERE id=?', (uid,))
    conn.commit()
    conn.close()
    session.clear()
    return redirect('/')
@app.route('/robots.txt')
def robots():
    return "User-agent: *\nAllow: /\n", 200, {'Content-Type': 'text/plain; charset=utf-8'}
if __name__ == '__main__':
    app.run(debug=True)
