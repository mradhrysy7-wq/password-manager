"""
مدير الحسابات الشامل - نظام آمن لإدارة كلمات المرور
"""
import os
import sqlite3
import time
from datetime import datetime
from cryptography.fernet import Fernet
from flask import Flask, flash, get_flashed_messages, jsonify, redirect, request, session
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'morad_super_secure_key_2026')

SITE_NAME = 'مدير الحسابات الشامل'
CONTACT_EMAIL = 'mradhrysy7@gmail.com'

# مفتاح التشفير
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

# قاعدة البيانات
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
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;min-height:100vh;line-height:1.6;direction:rtl;}
a{color:inherit;text-decoration:none}
.site-nav{background:var(--card);border-bottom:1px solid var(--brd);padding:0 20px;display:flex;align-items:center;justify-content:space-between;height:60px;position:sticky;top:0;z-index:200;}
.nav-logo{font-size:18px;font-weight:800;color:var(--heading);display:flex;align-items:center;gap:8px}
.nav-links{display:flex;gap:8px;align-items:center;}
.nav-links a,.nav-links button{font-size:13px;color:var(--text);padding:7px 13px;border-radius:7px;border:none;background:none;cursor:pointer;}
.nav-cta{background:var(--btn)!important;color:#fff!important;font-weight:700}
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
.hero{text-align:center;padding:50px 18px 30px}
.hero h1{font-size:clamp(24px,5vw,36px);color:var(--heading);font-weight:900;margin-bottom:12px}
.badge{display:inline-block;padding:4px 14px;border-radius:20px;font-size:12px;font-weight:700;background:rgba(59,130,246,.15);color:#60a5fa;margin-bottom:12px}
.feat-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:16px;margin:20px 0}
.feat-card{background:var(--card);border:1px solid var(--brd);border-radius:12px;padding:22px 16px;text-align:center;cursor:pointer;text-decoration:none;}
.feat-icon{font-size:30px;margin-bottom:8px}
footer.site-footer{background:var(--card);border-top:1px solid var(--brd);margin-top:50px;padding:25px 20px;text-align:center;font-size:13px;color:var(--muted);}
.footer-links{display:flex;gap:16px;justify-content:center;flex-wrap:wrap;margin-bottom:10px}
.pwd-gen-box{background:var(--ibg);border:1px solid var(--ibr);border-radius:8px;padding:14px;margin:12px 0;}
</style>
"""

# أداة توليد كلمات المرور الآمنة
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
}
</script>
"""

def page(content: str, title: str = SITE_NAME, logged_in: bool = False, username: str = ''):
    msgs = get_flashed_messages(with_categories=True)
    flash_html = ''.join(f'<div class="alert alert-{c}">{m}</div>' for c, m in msgs)
    if flash_html:
        flash_html = f'<div class="flash-wrap">{flash_html}</div>'

    if logged_in:
        nav_right = f"""
            <a href="/category/تطبيق">📱 التطبيقات</a>
            <a href="/category/بريد">📧 البريد</a>
            <a href="/category/موقع">🌐 المواقع</a>
            <a href="/settings">⚙️ الإعدادات</a>
            <a href="/logout" class="btn btn-sm btn-danger">خروج</a>
        """
    else:
        nav_right = """
            <a href="/about">عن الموقع</a>
            <a href="/contact">تواصل معنا</a>
            <a href="/auth" class="nav-cta btn btn-sm">دخول / تسجيل</a>
        """

    return f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} | {SITE_NAME}</title>
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
        uname = user[0] if user else 'مستخدم'
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
    <main class="wrap">
        <section class="hero">
            <span class="badge">إدارة حساباتك في مكان واحد</span>
            <h1>كلمات مرورك، تحت سيطرتك الكاملة</h1>
            <p>نظّم بيانات حساباتك مع تشفير Fernet المتقدم ومولّد كلمات مرور قوي وعشوائي.</p>
            <div style="margin-top:20px;">
                <a href="/auth" class="btn btn-primary" style="font-size:16px;">ابدأ الآن مجاناً 🚀</a>
            </div>
        </section>
    </main>"""
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
            <td>{r[1] or '-'}</td>
            <td>{r[2] or '-'}</td>
            <td>{r[3] or '-'}</td>
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
            <h1 class="card-title">➕ إضافة حساب في قسم {cat_type}</h1>
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
                <!-- أداة توليد كلمة المرور -->
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
    if request.method == 'POST':
        raw_pwd = request.form.get('password', '')
        conn.execute('UPDATE app_accounts SET app_name=?,app_username=?,email=?,password=? WHERE id=? AND user_id=?',
                     (request.form.get('app_name'), request.form.get('app_username'), request.form.get('email'),
                      encrypt_password(raw_pwd), item_id, session['user_id']))
        conn.commit()
        row = conn.execute('SELECT account_type FROM app_accounts WHERE id=?', (item_id,)).fetchone()
        conn.close()
        flash('تم تحديث البيانات بنجاح. ✅', 'success')
        return redirect(f'/category/{row[0]}')

    acc = conn.execute('SELECT * FROM app_accounts WHERE id=? AND user_id=?', (item_id, session['user_id'])).fetchone()
    conn.close()
    if not acc:
        return redirect('/')

    content = f"""
    <main class="wrap" style="display:flex;justify-content:center;">
        <div class="card" style="width:min(460px,100%);">
            <h1 class="card-title">✏️ تعديل الحساب</h1>
            <form method="POST">
                <div class="fg"><label>اسم الخدمة</label><input type="text" name="app_name" value="{acc[2] or ''}" required></div>
                <div class="fg"><label>البريد الإلكتروني</label><input type="email" name="email" value="{acc[5] or ''}"></div>
                <div class="fg"><label>اسم المستخدم</label><input type="text" name="app_username" value="{acc[4] or ''}"></div>
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

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        flash(f'تم إرسال رسالتك بنجاح إلى {CONTACT_EMAIL}! سنرد عليك قريباً. ✅', 'success')
        return redirect('/contact')
    content = f"""
    <main class="wrap-narrow">
        <div class="card">
            <h1 class="card-title">📬 تواصل معنا</h1>
            <p style="margin-bottom:16px;">البريد الإلكتروني المعتمد: <a href="mailto:{CONTACT_EMAIL}" style="color:#60a5fa;font-weight:700;">{CONTACT_EMAIL}</a></p>
            <form method="POST">
                <div class="fg"><label>الاسم</label><input type="text" name="name" required></div>
                <div class="fg"><label>البريد الإلكتروني</label><input type="email" name="email" required></div>
                <div class="fg"><label>الموضوع</label><input type="text" name="subject" required></div>
                <div class="fg"><label>الرسالة</label><textarea name="message" required></textarea></div>
                <button type="submit" class="btn btn-primary btn-block">إرسال الرسالة إلى {CONTACT_EMAIL} ✉️</button>
            </form>
        </div>
    </main>"""
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

if __name__ == '__main__':
    app.run(debug=True)
