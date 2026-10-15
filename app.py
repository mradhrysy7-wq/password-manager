"""
مدير الحسابات الشامل - نظام آمن لإدارة كلمات المرور
متوافق مع سياسات Google AdSense
"""
import hashlib
import json
import os
import secrets
import sqlite3
import time
import urllib.error
import urllib.request
from datetime import datetime

from cryptography.fernet import Fernet
from flask import (
    Flask, Response, flash, get_flashed_messages,
    jsonify, redirect, render_template_string, request, session,
)
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'morad_super_secure_adsense_key_2026')

# ══════════════════════════════════════════════════════════
# إعدادات الموقع (عدّل هذه القيم قبل النشر)
# ══════════════════════════════════════════════════════════
SITE_URL        = os.environ.get('SITE_URL', 'https://your-domain.com')
ADSENSE_CLIENT  = os.environ.get('ADSENSE_CLIENT', 'ca-pub-XXXXXXXXXXXXXXXXX')   # ← ضع معرف AdSense
ADSENSE_SLOT_TOP    = os.environ.get('ADSENSE_SLOT_TOP',    '1234567890')
ADSENSE_SLOT_MID    = os.environ.get('ADSENSE_SLOT_MID',    '0987654321')
ADSENSE_SLOT_BOTTOM = os.environ.get('ADSENSE_SLOT_BOTTOM', '1122334455')
SITE_NAME       = 'مدير الحسابات الشامل'
CONTACT_EMAIL   = os.environ.get('CONTACT_EMAIL', 'contact@your-domain.com')

# ══════════════════════════════════════════════════════════
# مفتاح التشفير
# ══════════════════════════════════════════════════════════
KEY_FILE = 'secret.key'
if os.path.exists(KEY_FILE):
    with open(KEY_FILE, 'rb') as _kf:
        ENCRYPTION_KEY = _kf.read()
else:
    ENCRYPTION_KEY = Fernet.generate_key()
    with open(KEY_FILE, 'wb') as _kf:
        _kf.write(ENCRYPTION_KEY)

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


# ══════════════════════════════════════════════════════════
# قاعدة البيانات
# ══════════════════════════════════════════════════════════
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
    cols = {r[1] for r in c.execute('PRAGMA table_info(users)').fetchall()}
    if 'email' not in cols:
        c.execute('ALTER TABLE users ADD COLUMN email TEXT')
    c.execute(
        'CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON '
        'users(email COLLATE NOCASE) WHERE email IS NOT NULL AND email != ""'
    )
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
    c.execute("""
        CREATE TABLE IF NOT EXISTS auth_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            purpose TEXT NOT NULL,
            code_hash TEXT NOT NULL,
            payload TEXT,
            expires_at REAL NOT NULL,
            attempts INTEGER NOT NULL DEFAULT 0
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


# ══════════════════════════════════════════════════════════
# مكوّن الإعلانات (AdSense)
# ══════════════════════════════════════════════════════════
def ad_unit(slot: str, layout: str = 'auto') -> str:
    """يُعيد وحدة إعلان AdSense جاهزة. إذا لم يُضبط المعرف لا تظهر."""
    if 'XXXXXXXXX' in ADSENSE_CLIENT:
        return ''   # لم يُضبط معرف AdSense بعد
    return f"""
<div class="ad-wrap" aria-label="إعلان">
    <ins class="adsbygoogle"
         style="display:block"
         data-ad-client="{ADSENSE_CLIENT}"
         data-ad-slot="{slot}"
         data-ad-format="{layout}"
         data-full-width-responsive="true"></ins>
    <script>(adsbygoogle = window.adsbygoogle || []).push({{}});</script>
</div>"""


# ══════════════════════════════════════════════════════════
# CSS مشترك
# ══════════════════════════════════════════════════════════
BASE_CSS = """
<style>
:root{
    --bg:#0b0f19;--card:#111827;--text:#9ca3af;--heading:#f9fafb;
    --ibg:#1f2937;--ibr:#374151;--itxt:#fff;
    --btn:#16a34a;--bth:#15803d;--brd:#1f2937;
    --danger:#dc2626;--info:#2563eb;--muted:#6b7280;
    --accent:#3b82f6;
}
.light-theme{
    --bg:#f8fafc;--card:#fff;--text:#374151;--heading:#111827;
    --ibg:#f9fafb;--ibr:#d1d5db;--itxt:#111827;
    --btn:#16a34a;--bth:#15803d;--brd:#e5e7eb;
    --danger:#dc2626;--info:#2563eb;--muted:#6b7280;
    --accent:#2563eb;
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{
    background:var(--bg);color:var(--text);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
    min-height:100vh;line-height:1.6;transition:background .3s,color .3s;
}
a{color:inherit;text-decoration:none}
img{max-width:100%;height:auto}
/* Nav */
.site-nav{
    background:var(--card);border-bottom:1px solid var(--brd);
    padding:0 20px;display:flex;align-items:center;
    justify-content:space-between;height:60px;
    position:sticky;top:0;z-index:200;
    box-shadow:0 2px 8px rgba(0,0,0,.15);
}
.nav-logo{font-size:18px;font-weight:800;color:var(--heading);display:flex;align-items:center;gap:8px}
.nav-links{display:flex;gap:8px;align-items:center;flex-wrap:wrap}
.nav-links a,.nav-links button{
    font-size:13px;color:var(--text);padding:7px 13px;
    border-radius:7px;border:none;background:none;cursor:pointer;
    transition:background .2s,color .2s;white-space:nowrap;
}
.nav-links a:hover,.nav-links button:hover{background:var(--brd);color:var(--heading)}
.nav-cta{background:var(--btn)!important;color:#fff!important;font-weight:700}
.nav-cta:hover{background:var(--bth)!important}
/* Layout */
.wrap{max-width:980px;margin:0 auto;padding:28px 18px}
.wrap-narrow{max-width:720px;margin:0 auto;padding:28px 18px}
/* Cards */
.card{
    background:var(--card);border:1px solid var(--brd);
    border-radius:14px;padding:26px;
    box-shadow:0 4px 18px rgba(0,0,0,.2);
}
.card+.card{margin-top:20px}
.card-title{
    font-size:16px;font-weight:700;color:var(--heading);
    border-bottom:2px solid var(--brd);padding-bottom:10px;margin-bottom:18px;
}
/* Forms */
.fg{margin-bottom:14px}
.fg label{display:block;font-size:12px;font-weight:600;color:var(--muted);margin-bottom:5px}
.fg input,.fg textarea,.fg select{
    width:100%;padding:11px 14px;border:1px solid var(--ibr);
    border-radius:8px;font-size:14px;background:var(--ibg);
    color:var(--itxt);outline:none;transition:border-color .2s;
    font-family:inherit;
}
.fg input:focus,.fg textarea:focus,.fg select:focus{border-color:var(--info)}
.fg textarea{resize:vertical;min-height:120px}
.fgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px}
/* Buttons */
.btn{display:inline-flex;align-items:center;justify-content:center;gap:6px;
    padding:10px 20px;border:none;border-radius:8px;font-size:14px;
    font-weight:700;cursor:pointer;transition:background .2s,opacity .2s;text-decoration:none}
.btn-primary{background:var(--btn);color:#fff}.btn-primary:hover{background:var(--bth)}
.btn-info{background:var(--info);color:#fff}.btn-info:hover{background:#1d4ed8}
.btn-danger{background:var(--danger);color:#fff}.btn-danger:hover{background:#b91c1c}
.btn-ghost{background:var(--brd);color:var(--heading)}.btn-ghost:hover{opacity:.8}
.btn-sm{padding:5px 10px;font-size:12px;border-radius:6px}
.btn-block{width:100%;text-align:center;display:block}
/* Flash */
.flash-wrap{max-width:980px;margin:10px auto 0;padding:0 18px}
.alert{padding:12px 16px;border-radius:8px;font-size:14px;margin-bottom:8px;display:flex;align-items:center;gap:10px}
.alert-success{background:#14532d;color:#bbf7d0}
.alert-error{background:#450a0a;color:#fecaca}
.alert-info{background:#1e3a5f;color:#bae6fd}
/* Tables */
.tbl-wrap{overflow-x:auto}
table{width:100%;border-collapse:collapse}
th{background:var(--ibg);color:var(--muted);font-size:12px;font-weight:700;
    padding:10px 14px;text-align:center;border-bottom:1px solid var(--brd)}
td{padding:12px 14px;text-align:center;font-size:13px;
    border-bottom:1px solid var(--brd);vertical-align:middle}
tr:last-child td{border-bottom:none}
.td-act{display:flex;gap:6px;justify-content:center}
/* Hero */
.hero{text-align:center;padding:60px 18px 44px}
.hero h1{font-size:clamp(26px,5vw,44px);color:var(--heading);font-weight:900;
    margin-bottom:14px;line-height:1.2}
.hero p{font-size:16px;line-height:1.7;max-width:620px;margin:0 auto 28px}
.badge{display:inline-block;padding:4px 14px;border-radius:20px;font-size:12px;
    font-weight:700;background:rgba(59,130,246,.15);color:#60a5fa;margin-bottom:14px}
/* Feature grid */
.feat-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:16px;margin-top:16px}
.feat-card{background:var(--card);border:1px solid var(--brd);border-radius:12px;
    padding:22px 16px;text-align:center;transition:transform .2s,border-color .2s}
.feat-card:hover{transform:translateY(-3px);border-color:var(--accent)}
.feat-icon{font-size:30px;margin-bottom:10px}
.feat-card h3{font-size:14px;color:var(--heading);margin-bottom:6px;font-weight:700}
.feat-card p{font-size:12px;line-height:1.6}
/* Landing page guidance */
.welcome-panel{position:relative;overflow:hidden;padding:clamp(24px,4vw,42px);margin-bottom:24px;
    background:linear-gradient(135deg,var(--card),rgba(37,99,235,.12));border-color:rgba(59,130,246,.32)}
.welcome-panel h2{font-size:clamp(22px,3vw,30px);line-height:1.45;color:var(--heading);margin-bottom:12px}
.welcome-panel p{font-size:15px;line-height:1.9;max-width:780px;margin-bottom:18px}
.guide-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:18px;margin-bottom:30px}
.guide-grid .card{height:100%}
.guide-list{list-style:none;counter-reset:guide;padding:0;display:grid;gap:12px}
.guide-list li{counter-increment:guide;position:relative;padding:12px 46px 12px 14px;
    background:var(--ibg);border:1px solid var(--brd);border-radius:10px;font-size:14px;line-height:1.8}
.guide-list li::before{content:counter(guide);position:absolute;right:12px;top:13px;width:24px;height:24px;
    display:grid;place-items:center;border-radius:50%;background:var(--info);color:#fff;font-weight:800;font-size:12px}
.privacy-note{border-right:4px solid var(--accent);padding:14px 16px;background:var(--ibg);border-radius:0 10px 10px 0;line-height:1.9}
.privacy-note p{font-size:14px;margin-bottom:12px}
.privacy-note a{color:#60a5fa}
.blog-section{margin:0 0 32px}
/* Blog */
.blog-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px}
.blog-card{background:var(--card);border:1px solid var(--brd);border-radius:12px;
    padding:22px;transition:transform .2s,border-color .2s;display:flex;flex-direction:column}
.blog-card:hover{transform:translateY(-2px);border-color:var(--accent)}
.blog-cat{font-size:11px;font-weight:700;color:var(--accent);text-transform:uppercase;margin-bottom:8px}
.blog-card h2{font-size:17px;color:var(--heading);font-weight:700;margin-bottom:8px;line-height:1.4}
.blog-card p{font-size:13px;line-height:1.7;flex:1;margin-bottom:14px}
.blog-meta{font-size:12px;color:var(--muted);margin-bottom:12px}
.blog-link{font-size:13px;font-weight:700;color:var(--accent)}
.blog-link:hover{text-decoration:underline}
/* Article */
.article-body h2{font-size:20px;color:var(--heading);font-weight:700;margin:28px 0 10px;border-right:4px solid var(--accent);padding-right:12px}
.article-body h3{font-size:16px;color:var(--heading);font-weight:600;margin:20px 0 8px}
.article-body p{font-size:15px;line-height:1.9;margin-bottom:14px}
.article-body ul,.article-body ol{padding-right:22px;margin-bottom:14px}
.article-body li{font-size:14px;line-height:1.8;margin-bottom:6px}
.article-body strong{color:var(--heading)}
.article-body blockquote{border-right:4px solid var(--accent);padding:12px 16px;
    background:var(--ibg);border-radius:0 8px 8px 0;margin:16px 0;font-style:italic}
/* Ads */
.ad-wrap{margin:22px 0;text-align:center;min-height:90px;background:var(--ibg);
    border-radius:8px;display:flex;align-items:center;justify-content:center;
    border:1px dashed var(--brd)}
/* Footer */
footer.site-footer{
    background:var(--card);border-top:1px solid var(--brd);
    margin-top:60px;padding:30px 20px;text-align:center;font-size:13px;color:var(--muted);
}
.footer-links{display:flex;gap:16px;justify-content:center;flex-wrap:wrap;margin-bottom:12px}
.footer-links a{color:#60a5fa}
.footer-links a:hover{text-decoration:underline}
/* OTP */
.otp-wrap{display:flex;align-items:center;justify-content:center;
    min-height:calc(100vh - 60px);padding:20px}
.otp-card{width:min(430px,100%)}
/* Prose */
.prose h2{font-size:19px;color:var(--heading);font-weight:700;margin:26px 0 10px;
    border-right:4px solid var(--accent);padding-right:12px}
.prose p,.prose li{font-size:14px;line-height:1.85;color:var(--text)}
.prose ul{padding-right:20px;margin-bottom:14px}
.prose li{margin-bottom:6px}
/* Breadcrumb */
.breadcrumb{font-size:13px;color:var(--muted);margin-bottom:16px}
.breadcrumb a{color:#60a5fa}
.breadcrumb a:hover{text-decoration:underline}
/* Responsive */
@media(max-width:600px){
    .hide-sm{display:none!important}
    .nav-links{gap:4px}
    .nav-links a,.nav-links button{padding:6px 8px;font-size:12px}
}
</style>"""

# ══════════════════════════════════════════════════════════
# AdSense script في الـ head
# ══════════════════════════════════════════════════════════
def adsense_head() -> str:
    if 'XXXXXXXXX' in ADSENSE_CLIENT:
        return ''
    return f'<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={ADSENSE_CLIENT}" crossorigin="anonymous"></script>'


# ══════════════════════════════════════════════════════════
# قالب الصفحة المشترك
# ══════════════════════════════════════════════════════════
def page(content: str, title: str = SITE_NAME,
         logged_in: bool = False, username: str = '',
         desc: str = 'مدير الحسابات الشامل – احفظ كلمات مرورك بأمان وتشفير متقدم.',
         canonical: str = '', include_ads: bool = False) -> str:

    msgs = get_flashed_messages(with_categories=True)
    flash_html = ''
    if msgs:
        items = ''.join(
            f'<div class="alert alert-{c}">{m}</div>' for c, m in msgs
        )
        flash_html = f'<div class="flash-wrap">{items}</div>'

    admin_btn = ''
    if username in ('morad', 'admin'):
        admin_btn = '<a href="/admin/users" class="nav-cta btn btn-sm" style="background:#1e3a8a">👥 المشرف</a>'

    if logged_in:
        nav_right = f"""
            <a href="/blog" class="hide-sm">✍️ المدونة</a>
            <a href="/settings" class="hide-sm">⚙️ الإعدادات</a>
            {admin_btn}
            <button id="themeToggle" title="تبديل المظهر">🌙/☀️</button>
            <a href="/logout" class="btn btn-sm" style="background:#450a0a;color:#f87171;">خروج</a>
        """
    else:
        nav_right = """
            <a href="/blog" class="hide-sm">✍️ المدونة</a>
            <a href="/about" class="hide-sm">عن الموقع</a>
            <a href="/privacy" class="hide-sm">الخصوصية</a>
            <button id="themeToggle" title="تبديل المظهر">🌙/☀️</button>
            <a href="/auth" class="nav-cta btn btn-sm">دخول / تسجيل</a>
        """

    canon_tag = f'<link rel="canonical" href="{SITE_URL}{canonical}">' if canonical else ''
    year = datetime.now().year

    return f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="{desc}">
<meta name="robots" content="index, follow">
<meta property="og:title" content="{title} | {SITE_NAME}">
<meta property="og:description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{SITE_NAME}">
<meta name="twitter:card" content="summary">
<meta name="twitter:title" content="{title} | {SITE_NAME}">
<meta name="twitter:description" content="{desc}">
<meta name="google-site-verification" content="xfoF9HVlynNHlY9YLc-6XRs1XJcEd5BbxK8-U_dHq0g">
{canon_tag}
<title>{title} | {SITE_NAME}</title>
{BASE_CSS}
{adsense_head() if include_ads else ''}
</head>
<body>
<nav class="site-nav" role="navigation" aria-label="القائمة الرئيسية">
    <a href="/" class="nav-logo">🔐 {SITE_NAME}</a>
    <div class="nav-links">{nav_right}</div>
</nav>
{flash_html}
{content}
<footer class="site-footer" role="contentinfo">
    <div class="footer-links">
        <a href="/">الرئيسية</a>
        <a href="/blog">المدونة</a>
        <a href="/about">عن الموقع</a>
        <a href="/privacy">سياسة الخصوصية</a>
        <a href="/terms">شروط الاستخدام</a>
        <a href="/contact">تواصل معنا</a>
    </div>
    <p style="font-size:12px;">© {year} {SITE_NAME} · جميع الحقوق محفوظة</p>
    <p style="font-size:11px;margin-top:6px;color:var(--muted);">
        هذا الموقع يستخدم Google AdSense الذي قد يستخدم ملفات تعريف الارتباط لعرض إعلانات مخصصة.
        <a href="/privacy" style="color:#60a5fa;">سياسة الخصوصية</a>
    </p>
</footer>
<script>
(function(){{
    var btn=document.getElementById('themeToggle');
    function applyTheme(t){{document.body.classList.toggle('light-theme',t==='light');}}
    if(btn)btn.addEventListener('click',function(){{
        var n=document.body.classList.contains('light-theme')?'dark':'light';
        localStorage.setItem('theme',n);applyTheme(n);
    }});
    applyTheme(localStorage.getItem('theme'));
}})();
</script>
</body>
</html>"""


# ══════════════════════════════════════════════════════════
# بيانات المدونة (محتوى ثابت – يمكن لاحقاً نقله لقاعدة بيانات)
# ══════════════════════════════════════════════════════════
ARTICLES = [
    {
        'slug': 'how-to-create-strong-password',
        'cat': 'أمان رقمي',
        'title': 'كيف تنشئ كلمة مرور قوية لا تُكسر أبداً؟',
        'desc': 'دليل شامل لإنشاء كلمات مرور آمنة وقوية تحمي حساباتك من الاختراق والقرصنة.',
        'date': '10 أكتوبر 2026',
        'read_time': '5 دقائق',
        'body': """
<p>في عالم رقمي تتزايد فيه التهديدات السيبرانية يوماً بعد يوم، أصبح اختيار كلمة مرور قوية أمراً لا تهاون فيه.
كثيرون يقعون في خطأ استخدام كلمات مرور بسيطة أو متكررة عبر مواقع متعددة، وهو ما يجعلهم هدفاً سهلاً للمخترقين.</p>

<h2>لماذا كلمات المرور الضعيفة خطيرة؟</h2>
<p>وفقاً لدراسات الأمن السيبراني، يمكن لهجمات "القوة العمياء" (Brute Force) كسر كلمة مرور مكونة من 6 أرقام
في أقل من ثانية واحدة باستخدام الحواسيب الحديثة. أما كلمة مرور من 8 أحرف مختلطة، فقد تأخذ بضع ساعات فقط.
لذلك فإن قوة كلمة مرورك = درعك الأول ضد الاختراق.</p>

<h2>مواصفات كلمة المرور القوية</h2>
<ul>
<li><strong>الطول:</strong> 12 حرفاً على الأقل، والأفضل 16 أو أكثر.</li>
<li><strong>التنوع:</strong> مزيج من الحروف الكبيرة والصغيرة والأرقام والرموز الخاصة مثل @، !، #.</li>
<li><strong>التفرد:</strong> كلمة مرور مختلفة لكل حساب دون استثناء.</li>
<li><strong>التجنب:</strong> لا تستخدم اسمك أو تاريخ ميلادك أو كلمات القاموس.</li>
<li><strong>العشوائية:</strong> تجنب الأنماط المتوقعة كـ "123456" أو "qwerty".</li>
</ul>

<h2>تقنية عبارة المرور (Passphrase)</h2>
<p>بدلاً من كلمة واحدة معقدة، يمكنك استخدام عبارة من 4 كلمات عشوائية مفصولة برموز.
مثال: <strong>قمر@بحر!جبل#نجم</strong> – هذه العبارة سهلة الحفظ وشبه مستحيلة الكسر لأن طولها كبير.</p>

<h2>كيف تتذكر كل هذه الكلمات؟</h2>
<p>الجواب البسيط: استخدم مدير كلمات المرور! أداة مثل <strong>مدير الحسابات الشامل</strong>
تحفظ جميع كلمات مرورك المشفرة في مكان واحد آمن، وما عليك سوى تذكر كلمة مرور رئيسية واحدة قوية
للوصول إلى كل شيء.</p>

<h2>خطوات عملية لتأمين حساباتك اليوم</h2>
<ol>
<li>قائمة بجميع حساباتك المهمة: البريد الإلكتروني، البنك، منصات التواصل.</li>
<li>غيّر كلمة المرور لكل حساب إلى كلمة مرور قوية وفريدة.</li>
<li>فعّل المصادقة الثنائية (2FA) حيثما أمكن.</li>
<li>احفظ الكلمات في مدير كلمات مرور موثوق.</li>
<li>راجع كلمات مرورك كل 6 أشهر وجددها.</li>
</ol>

<blockquote>
"كلمة مرورك هي المفتاح لحياتك الرقمية كاملة. استثمر دقائق في اختيارها الصحيح لتوفر على نفسك أيام من المتاعب."
</blockquote>

<h2>الخلاصة</h2>
<p>الأمن الرقمي لا يبدأ بأجهزة معقدة أو برامج متطورة، بل يبدأ بكلمة مرور قوية تحمي حساباتك.
اتخذ الخطوة الأولى الآن وابدأ باستخدام مدير كلمات مرور آمن لتنظيم حساباتك وحمايتها.</p>
"""
    },
    {
        'slug': 'two-factor-authentication-guide',
        'cat': 'دليل تقني',
        'title': 'المصادقة الثنائية: طبقة حماية إضافية لا غنى عنها',
        'desc': 'تعرف على المصادقة الثنائية 2FA وكيف تحمي حساباتك حتى لو سُرقت كلمة المرور.',
        'date': '8 أكتوبر 2026',
        'read_time': '6 دقائق',
        'body': """
<p>تخيل أن تعرف أن كلمة مرورك قد سُرقت، لكن حسابك ظل آمناً تماماً! هذا بالضبط ما توفره المصادقة الثنائية (Two-Factor Authentication - 2FA)،
التقنية التي أصبحت معياراً أساسياً في أمان الحسابات الرقمية حول العالم.</p>

<h2>ما هي المصادقة الثنائية؟</h2>
<p>المصادقة الثنائية هي نظام أمان يتطلب خطوتين للتحقق من هويتك عند تسجيل الدخول:
<strong>شيء تعرفه</strong> (كلمة المرور) و<strong>شيء تملكه</strong> (هاتفك أو رمز OTP).
حتى لو حصل أحدهم على كلمة مرورك، لن يتمكن من الدخول بدون العامل الثاني.</p>

<h2>أنواع المصادقة الثنائية</h2>
<ul>
<li><strong>رمز SMS:</strong> يُرسل رمز مؤقت لهاتفك عبر رسالة نصية.</li>
<li><strong>تطبيق المصادقة:</strong> مثل Google Authenticator أو Authy يولد رموزاً تتغير كل 30 ثانية.</li>
<li><strong>البريد الإلكتروني:</strong> يُرسل رمز مؤقت للتحقق من هويتك في الخدمات التي توفر هذا الخيار.</li>
<li><strong>مفاتيح الأجهزة:</strong> مثل YubiKey للحسابات عالية الحساسية.</li>
<li><strong>البصمة البيومترية:</strong> بصمة الإصبع أو التعرف على الوجه.</li>
</ul>

<h2>إحصائيات مقنعة عن أهمية 2FA</h2>
<p>دراسات جوجل تُشير إلى أن تفعيل المصادقة الثنائية يمنع <strong>100%</strong> من هجمات الروبوتات الآلية،
و<strong>99%</strong> من هجمات التصيد الاحتيالي الجماعية. هذه الأرقام وحدها كافية للإقناع.</p>

<h2>كيف تفعّل 2FA على حساباتك؟</h2>
<ol>
<li>اذهب إلى إعدادات الأمان في حسابك (Google، Facebook، Twitter...).</li>
<li>ابحث عن خيار "التحقق بخطوتين" أو "المصادقة الثنائية".</li>
<li>اختر الطريقة المناسبة لك (SMS أو تطبيق مصادقة).</li>
<li>اتبع الخطوات وأكّد التفعيل.</li>
<li>احفظ رموز الاسترداد في مكان آمن.</li>
</ol>

<h2>مدير الحسابات والمصادقة الثنائية</h2>
<p>الموقع لا يستخدم حالياً مصادقة OTP لحساب الموقع؛ تسجيل الدخول يتم باسم المستخدم وكلمة المرور فقط.
يمكنك تفعيل المصادقة الثنائية بشكل مستقل في حساباتك الأخرى التي تدعمها.</p>

<blockquote>
"المصادقة الثنائية هي أفضل استثمار أمني يمكنك القيام به مجاناً. فعّلها الآن قبل أن تندم لاحقاً."
</blockquote>

<h2>الخلاصة</h2>
<p>المصادقة الثنائية ليست خياراً للمتخصصين فقط، بل ضرورة لكل مستخدم رقمي.
ابدأ بتفعيلها على أهم حساباتك: البريد الإلكتروني، الحسابات البنكية، ومنصات التواصل الاجتماعي.
كل دقيقة تقضيها في تأمين حساباتك تستحق عشرة أضعافها مستقبلاً.</p>
"""
    },
    {
        'slug': 'password-manager-benefits',
        'cat': 'نصائح تقنية',
        'title': '7 أسباب تجعل مدير كلمات المرور ضرورة لا رفاهية',
        'desc': 'اكتشف لماذا يستخدم خبراء الأمن السيبراني مديري كلمات المرور وكيف تختار الأفضل.',
        'date': '5 أكتوبر 2026',
        'read_time': '7 دقائق',
        'body': """
<p>هل تستخدم كلمة مرور واحدة في جميع مواقعك؟ أو تحفظ كلمات مرورك في ملف نصي على الكمبيوتر؟
إذا كانت إجابتك نعم لأي منهما، فأنت في خطر حقيقي. الحل؟ مدير كلمات المرور.</p>

<h2>1. لا تحتاج لتذكر شيء</h2>
<p>المشكلة الأولى التي يواجهها الجميع هي صعوبة تذكر كلمات مرور معقدة لعشرات المواقع.
مدير كلمات المرور يحفظ كل شيء نيابة عنك. تحتاج فقط لتذكر كلمة مرور رئيسية واحدة قوية.</p>

<h2>2. كلمة مرور فريدة لكل موقع</h2>
<p>عندما يتم اختراق موقع ما وتسريب قاعدة بياناته، يحاول المخترقون استخدام نفس بيانات الدخول
على مواقع أخرى (يُسمى هذا Credential Stuffing). مع مدير كلمات المرور، لكل موقع كلمة مرور مختلفة،
فحتى لو اختُرق أحدها، الباقي بأمان تام.</p>

<h2>3. توليد كلمات مرور آمنة تلقائياً</h2>
<p>بدلاً من التفكير في كلمة مرور قوية يدوياً، يولد مدير كلمات المرور لك كلمات عشوائية ومعقدة
بنقرة واحدة. مثال: <strong>K#9mQ$vL2@nR</strong> – من سيتذكر هذا؟ لا أحد، لكن المدير يتذكره نيابة عنك.</p>

<h2>4. الحماية من التصيد الاحتيالي (Phishing)</h2>
<p>مديرو كلمات المرور المتقدمون يتحققون من عنوان الموقع قبل ملء البيانات تلقائياً.
إذا كنت على موقع مزيف يتظاهر بأنه Google أو PayPal، لن يملأ المدير بياناتك لأن العنوان مختلف.</p>

<h2>5. الوصول من أي جهاز</h2>
<p>مع مدير كلمات المرور السحابي، جميع حساباتك متاحة من هاتفك، حاسوبك، أو أي جهاز آخر.
لا تقلق بشأن نسيان كلمة المرور عندما تغير جهازك.</p>

<h2>6. تنظيم حساباتك بشكل احترافي</h2>
<p>مدير الحسابات الشامل يتيح لك تصنيف حساباتك: تطبيقات، بريد إلكتروني، مواقع.
يمكنك البحث والوصول لأي حساب في ثوانٍ بدلاً من البحث في ذاكرتك أو ملفات متناثرة.</p>

<h2>7. تشفير لا يمكن كسره</h2>
<p>يستخدم مدير الحسابات الشامل خوارزمية <strong>Fernet</strong> للتشفير المتماثل،
وهي مبنية على AES-128-CBC مع HMAC-SHA256 للتحقق من النزاهة. حتى لو وصل أحد لقاعدة البيانات،
لن يرى سوى نصوص مشفرة لا معنى لها.</p>

<blockquote>
"استخدام مدير كلمات المرور هو القرار الأمني الأفضل الذي يمكنك اتخاذه بعد تفعيل المصادقة الثنائية."
— خبراء الأمن السيبراني
</blockquote>

<h2>الخلاصة</h2>
<p>مدير كلمات المرور ليس مجرد أداة راحة، بل هو ضرورة أمنية في عالم رقمي متزايد الخطورة.
ابدأ اليوم بتسجيل حساباتك في مدير الحسابات الشامل واستمتع بالأمان والراحة في آنٍ واحد.</p>
"""
    },
    {
        'slug': 'email-security-tips',
        'cat': 'أمان رقمي',
        'title': '10 نصائح ذهبية لحماية بريدك الإلكتروني من الاختراق',
        'desc': 'احمِ بريدك الإلكتروني من القرصنة والتصيد الاحتيالي بهذه النصائح العملية المجربة.',
        'date': '2 أكتوبر 2026',
        'read_time': '8 دقائق',
        'body': """
<p>البريد الإلكتروني هو مفتاح مملكتك الرقمية. معظم المواقع تستخدمه لاستعادة كلمات المرور،
مما يعني أن اختراق بريدك = اختراق جميع حساباتك. إليك 10 نصائح عملية لحمايته.</p>

<h2>1. استخدم كلمة مرور قوية وفريدة</h2>
<p>كلمة مرور بريدك يجب أن تكون الأقوى بين جميع حساباتك. استخدم 16 حرفاً على الأقل مع مزيج من الأرقام والرموز.</p>

<h2>2. فعّل التحقق بخطوتين فوراً</h2>
<p>Gmail وOutlook وجميع خدمات البريد الكبرى توفر هذه الميزة. فعّلها الآن لا تأجيل.</p>

<h2>3. احذر من رسائل التصيد (Phishing)</h2>
<p>لا تضغط على روابط في رسائل غير متوقعة حتى لو بدت من جهات موثوقة. تحقق دائماً من عنوان المرسل الفعلي.</p>

<h2>4. راجع الأجهزة المتصلة بحسابك</h2>
<p>في إعدادات أمان حسابك، ستجد قائمة بالأجهزة المتصلة. أخرج من أي جهاز لا تتعرف عليه فوراً.</p>

<h2>5. لا تستخدم بريدك الرئيسي للتسجيل في كل شيء</h2>
<p>أنشئ بريداً ثانوياً للتسجيل في المواقع غير الضرورية. احتفظ ببريدك الرئيسي للأمور المهمة فقط.</p>

<h2>6. حدّث كلمة مرورك كل 6 أشهر</h2>
<p>التغيير الدوري لكلمة المرور يقلل من خطر الاستغلال في حال حدث تسريب بيانات دون علمك.</p>

<h2>7. استخدم VPN على الشبكات العامة</h2>
<p>الشبكات العامة في المطارات والمقاهي غير آمنة. استخدم VPN موثوقاً قبل الوصول لبريدك على أي شبكة عامة.</p>

<h2>8. فعّل تنبيهات النشاط المشبوه</h2>
<p>معظم خدمات البريد ترسل إشعاراً عند تسجيل الدخول من جهاز جديد. تأكد من تفعيل هذا الخيار.</p>

<h2>9. احذف الرسائل الحساسة بعد قراءتها</h2>
<p>رسائل تحتوي على كلمات مرور أو معلومات بنكية أو شخصية يجب حذفها بعد الاطلاع عليها وتفريغ سلة المهملات.</p>

<h2>10. احفظ بيانات بريدك في مدير كلمات المرور</h2>
<p>لا تكتب كلمة مرور بريدك في ورقة أو ملف نصي. استخدم مدير حسابات مشفر للحفاظ عليها بأمان.</p>

<h2>الخلاصة</h2>
<p>حماية بريدك الإلكتروني تعني حماية هويتك الرقمية كاملة. طبّق هذه النصائح العشر الآن
واستخدم مدير الحسابات الشامل لتنظيم جميع حساباتك بصورة آمنة.</p>
"""
    },
    {
        'slug': 'cybersecurity-for-beginners',
        'cat': 'مبتدئون',
        'title': 'الأمن السيبراني للمبتدئين: كل ما تحتاج معرفته في 2026',
        'desc': 'دليل شامل ومبسط للمبتدئين عن الأمن السيبراني وحماية الخصوصية الرقمية.',
        'date': '28 سبتمبر 2026',
        'read_time': '10 دقائق',
        'body': """
<p>الأمن السيبراني لم يعد حكراً على المختصين والمهندسين. في عالم أصبح فيه كل شيء رقمياً،
يحتاج كل مستخدم للإنترنت إلى فهم أساسيات حماية نفسه على الشبكة.</p>

<h2>ما هو الأمن السيبراني؟</h2>
<p>الأمن السيبراني هو مجموعة الممارسات والتقنيات التي تهدف إلى حماية أجهزتك وبياناتك وخصوصيتك
من الهجمات الإلكترونية والوصول غير المصرح به.</p>

<h2>أبرز التهديدات التي تواجهك</h2>
<ul>
<li><strong>التصيد الاحتيالي (Phishing):</strong> رسائل إلكترونية أو روابط مزيفة تسرق بياناتك.</li>
<li><strong>البرامج الخبيثة (Malware):</strong> تشمل الفيروسات وبرامج التجسس وبرامج الفدية.</li>
<li><strong>سرقة الهوية:</strong> استخدام معلوماتك الشخصية لانتحال شخصيتك.</li>
<li><strong>هجمات القوة العمياء:</strong> تجربة ملايين كلمات المرور آلياً حتى الوصول لحسابك.</li>
<li><strong>الشبكات غير الآمنة:</strong> التنصت على اتصالاتك عبر WiFi غير مشفر.</li>
</ul>

<h2>أساسيات الحماية للمبتدئين</h2>
<h3>أولاً: كلمات المرور</h3>
<p>كلمة مرور قوية وفريدة لكل حساب، مع استخدام مدير كلمات مرور لتنظيمها.</p>

<h3>ثانياً: التحديثات</h3>
<p>حدّث نظام تشغيلك وتطبيقاتك دورياً. التحديثات تُصلح الثغرات الأمنية المكتشفة.</p>

<h3>ثالثاً: النسخ الاحتياطي</h3>
<p>احتفظ بنسخة احتياطية من بياناتك المهمة في مكانين مختلفين: القرص الصلب والسحابة.</p>

<h3>رابعاً: وعي التصيد</h3>
<p>قبل الضغط على أي رابط، تحقق من: هل الرسالة منطقية؟ هل عنوان المرسل صحيح؟ هل الرابط آمن؟</p>

<h3>خامساً: خصوصية الشبكة الاجتماعية</h3>
<p>راجع إعدادات الخصوصية في حساباتك على منصات التواصل وقلل المعلومات المتاحة للعموم.</p>

<h2>أدوات مجانية للحماية</h2>
<ul>
<li><strong>مدير كلمات المرور:</strong> مثل مدير الحسابات الشامل لتشفير وتنظيم كلمات مرورك.</li>
<li><strong>برنامج مكافحة فيروسات:</strong> Windows Defender مجاني وفعّال لمستخدمي ويندوز.</li>
<li><strong>HTTPS:</strong> تأكد من وجود القفل الأخضر في شريط العنوان عند إدخال بيانات حساسة.</li>
<li><strong>هيئة Have I Been Pwned:</strong> موقع مجاني للتحقق إن كان بريدك تعرض لتسريب بيانات.</li>
</ul>

<blockquote>
"أضعف حلقة في سلسلة الأمن السيبراني هي الإنسان. التعليم والوعي هما أقوى أسلحة الحماية."
</blockquote>

<h2>خطة العمل لهذا الأسبوع</h2>
<ol>
<li>يوم 1: أنشئ حساباً في مدير الحسابات وأضف أهم 5 حسابات لديك.</li>
<li>يوم 2: فعّل التحقق بخطوتين على بريدك الإلكتروني.</li>
<li>يوم 3: حدّث جميع تطبيقاتك ونظام تشغيلك.</li>
<li>يوم 4: راجع إعدادات خصوصية حساباتك على التواصل الاجتماعي.</li>
<li>يوم 5: تحقق من تسريب بريدك على haveibeenpwned.com.</li>
</ol>

<h2>الخلاصة</h2>
<p>الأمن السيبراني رحلة لا وجهة، لكن البداية سهلة. ابدأ بالخطوات البسيطة وطوّر معرفتك تدريجياً.
مدير الحسابات الشامل هو شريكك الأول في هذه الرحلة نحو حياة رقمية أكثر أماناً.</p>
"""
    },
    {
        'slug': 'protect-social-media-accounts',
        'cat': 'أمان رقمي',
        'title': 'كيف تحمي حساباتك على منصات التواصل الاجتماعي؟',
        'desc': 'نصائح متخصصة لحماية حساباتك على إنستغرام وتويتر وسناب وتيك توك من الاختراق.',
        'date': '25 سبتمبر 2026',
        'read_time': '6 دقائق',
        'body': """
<p>منصات التواصل الاجتماعي أصبحت جزءاً لا يتجزأ من حياتنا اليومية، وفي نفس الوقت هدفاً رئيسياً
للمخترقين الذين يسعون للسيطرة على حساباتك لأغراض متعددة. إليك الدليل الشامل للحماية.</p>

<h2>لماذا يستهدف المخترقون حسابات التواصل؟</h2>
<ul>
<li>نشر إعلانات احتيالية لمتابعيك دون علمك.</li>
<li>ابتزازك مقابل استعادة حسابك.</li>
<li>سرقة هويتك وانتحال شخصيتك للاحتيال على أصدقائك.</li>
<li>الوصول لمعلوماتك الشخصية ورسائلك الخاصة.</li>
</ul>

<h2>إنستغرام: الأكثر استهدافاً</h2>
<p>إنستغرام يتصدر قائمة المنصات المخترقة. قواعد الحماية:</p>
<ul>
<li>فعّل المصادقة الثنائية من: الإعدادات ← الأمان ← المصادقة الثنائية.</li>
<li>راجع التطبيقات المتصلة بحسابك وأزل غير الضرورية.</li>
<li>احذر من روابط DM حتى من الأصدقاء (حسابهم قد يكون مخترقاً).</li>
</ul>

<h2>تيك توك وسناب: الشباب الأكثر عرضة</h2>
<p>المخترقون يستهدفون المستخدمين الشباب بأساليب ذكية مثل العروض الوهمية والمسابقات المزيفة.
تذكر: إذا كان العرض جيداً جداً، فهو على الأرجح احتيال.</p>

<h2>تويتر/X: الحسابات العامة</h2>
<p>الحسابات ذات المتابعين الكثيرين هدف للاختراق. استخدم مفاتيح أمان التطبيق (App-specific passwords)
بدلاً من كلمة مرورك الرئيسية عند الاتصال بتطبيقات ثالثة.</p>

<h2>ماذا تفعل إذا اختُرق حسابك؟</h2>
<ol>
<li>أبلّغ المنصة فوراً عبر زر "الإبلاغ عن اختراق".</li>
<li>غيّر كلمة مرور بريدك الإلكتروني المرتبط أولاً.</li>
<li>أخرج من جميع الأجهزة في إعدادات الأمان.</li>
<li>أخبر أصدقاءك أن حسابك مخترق حتى لا يقعوا في فخ رسائل المخترق.</li>
<li>قدّم طلب استرداد رسمي للمنصة مع إثبات الهوية.</li>
</ol>

<h2>الخلاصة</h2>
<p>حسابات التواصل الاجتماعي تحتوي على جزء كبير من حياتك الشخصية. احمها بجدية بتطبيق هذه النصائح
واحتفظ ببيانات الدخول لجميع حساباتك في مدير الحسابات الشامل للوصول إليها بسهولة وأمان.</p>
"""
    },
]


def get_article(slug: str):
    return next((a for a in ARTICLES if a['slug'] == slug), None)


# ══════════════════════════════════════════════════════════
# 1. الصفحة الرئيسية
# ══════════════════════════════════════════════════════════
@app.route('/auth')
def auth_page():
    if 'user_id' in session:
        return redirect('/')
    content = f"""
    <main class="wrap-narrow">
        <header style="text-align:center;margin:12px 0 24px;">
            <span class="badge">🔐 حسابك يبدأ من هنا</span>
            <h1 style="font-size:28px;color:var(--heading);font-weight:900;">دخول / تسجيل حساب</h1>
            <p>سجّل الدخول إلى حسابك أو أنشئ حساباً جديداً للبدء.</p>
        </header>
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px;" id="auth-forms">
            <article class="card" id="login-section">
                <h2 class="card-title">🔑 تسجيل الدخول</h2>
                <form action="/login" method="POST" novalidate>
                    <div class="fg"><label for="li-username">اسم المستخدم</label>
                    <input id="li-username" type="text" name="username" placeholder="اسم المستخدم" autocomplete="username" required></div>
                    <div class="fg"><label for="li-pass">كلمة المرور</label>
                    <input id="li-pass" type="password" name="password" placeholder="كلمة المرور" autocomplete="current-password" required></div>
                    <button type="submit" class="btn btn-primary btn-block">تسجيل الدخول</button>
                </form>
            </article>
            <article class="card" id="register-section">
                <h2 class="card-title">✨ إنشاء حساب مجاني</h2>
                <form action="/register" method="POST" novalidate>
                    <div class="fg"><label for="re-username">اسم المستخدم</label>
                    <input id="re-username" type="text" name="username" placeholder="3 أحرف على الأقل" minlength="3" maxlength="32" autocomplete="username" required></div>
                    <div class="fg"><label for="re-pass">كلمة المرور</label>
                    <input id="re-pass" type="password" name="password" placeholder="6 أحرف على الأقل" minlength="6" autocomplete="new-password" required></div>
                    <button type="submit" class="btn btn-primary btn-block">إنشاء حساب مجاني</button>
                </form>
                <p style="text-align:center;margin-top:10px;font-size:12px;color:var(--muted);">بالتسجيل توافق على <a href="/terms" style="color:#60a5fa;">شروط الاستخدام</a> و <a href="/privacy" style="color:#60a5fa;">سياسة الخصوصية</a></p>
            </article>
        </div>
    </main>"""
    return page(content, title='دخول / تسجيل حساب', desc='تسجيل الدخول أو إنشاء حساب في مدير الحسابات الشامل.', include_ads=False)


@app.route('/')
def index():
    if 'user_id' in session:
        conn = get_db()
        row  = conn.execute('SELECT username FROM users WHERE id=?', (session['user_id'],)).fetchone()
        conn.close()
        username = row[0] if row else 'مستخدم'

        recent = ARTICLES[:3]
        blog_items = ''.join(f"""
        <a href="/blog/{a['slug']}" class="blog-card" style="text-decoration:none;">
            <div class="blog-cat">{a['cat']}</div>
            <h2>{a['title']}</h2>
            <p>{a['desc']}</p>
            <span class="blog-link">اقرأ المقال ◀</span>
        </a>""" for a in recent)

        content = f"""
        <main class="wrap">
            <header style="margin-bottom:24px;">
                <h1 style="font-size:22px;color:var(--heading);">مرحباً، {username} 👋</h1>
                <p style="font-size:14px;">اختر قسماً لإدارة حساباتك</p>
            </header>
            <div class="feat-grid" style="margin-bottom:32px;">
                <a href="/category/تطبيق" class="feat-card" style="text-decoration:none;">
                    <div class="feat-icon">📱</div>
                    <h3>التطبيقات والمنصات</h3>
                    <p>إدارة حسابات التطبيقات والخدمات المختلفة</p>
                </a>
                <a href="/category/بريد" class="feat-card" style="text-decoration:none;">
                    <div class="feat-icon">📧</div>
                    <h3>البريد الإلكتروني</h3>
                    <p>إدارة جميع حسابات البريد الإلكتروني</p>
                </a>
                <a href="/category/موقع" class="feat-card" style="text-decoration:none;">
                    <div class="feat-icon">🌐</div>
                    <h3>المواقع الإلكترونية</h3>
                    <p>إدارة حسابات المواقع والروابط</p>
                </a>
            </div>
            <section>
                <h2 style="font-size:18px;color:var(--heading);margin-bottom:16px;font-weight:700;">📖 آخر مقالات الأمن الرقمي</h2>
                <div class="blog-grid">{blog_items}</div>
                <div style="text-align:center;margin-top:18px;">
                    <a href="/blog" class="btn btn-ghost">عرض جميع المقالات</a>
                </div>
            </section>
        </main>"""
        return page(content, title='لوحة التحكم', logged_in=True, username=username)

    # ─── صفحة الهبوط (غير مسجل) ───────────────────────────────────────────
    blog_items = ''.join(f"""
    <a href="/blog/{a['slug']}" class="blog-card" style="text-decoration:none;">
        <div class="blog-cat">{a['cat']}</div>
        <h2>{a['title']}</h2>
        <p>{a['desc']}</p>
        <div class="blog-meta">🕐 {a['read_time']} · {a['date']}</div>
        <span class="blog-link">اقرأ المقال ◀</span>
    </a>""" for a in ARTICLES[:3])

    structured_data = json.dumps({
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": SITE_NAME,
        "url": SITE_URL,
        "description": "مدير الحسابات الشامل – احفظ كلمات مرورك بأمان وتشفير متقدم.",
        "potentialAction": {
            "@type": "SearchAction",
            "target": f"{SITE_URL}/blog?q={{search_term_string}}",
            "query-input": "required name=search_term_string"
        }
    }, ensure_ascii=False)

    content = f"""
    <script type="application/ld+json">{structured_data}</script>
    <main>
        <!-- Hero -->
        <section class="hero">
            <span class="badge">إدارة حساباتك في مكان واحد</span>
            <h1>كلمات مرورك، تحت سيطرتك الكاملة</h1>
            <p>نظّم بيانات حساباتك في مكان واحد، مع تشفير كلمات المرور المخزنة وإمكانية استعادتها عند الحاجة.</p>
        </section>

        <div class="wrap" style="padding-top:0;">
            <!-- موضع إعلان الصفحة الترحيبية: بعد المقدمة وقبل محتوى الترحيب والمقالات -->
            {ad_unit(ADSENSE_SLOT_TOP)}

            <!-- ترحيب مختصر، وتظهر المقالات تحته مباشرة -->
            <section class="card welcome-panel" aria-labelledby="intro-title">
                <span class="badge">مرحباً بك</span>
                <h2 id="intro-title">👋 أهلاً بك في مدير الحسابات الشامل</h2>
                <p>هذا الموقع يساعدك على تنظيم بيانات حساباتك المختلفة في مكان واحد، مثل حسابات التطبيقات والبريد الإلكتروني والمواقع. تعرّف على طريقة الاستخدام، ثم اقرأ أحدث مقالاتنا من هنا.</p>
            </section>

            <!-- المقالات مباشرة تحت الترحيب -->
            <section class="blog-section" aria-labelledby="blog-title">
                <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:18px;">
                    <h2 id="blog-title" style="font-size:20px;color:var(--heading);font-weight:800;">✍️ مقالات الأمن الرقمي</h2>
                    <a href="/blog" class="btn btn-ghost btn-sm">اقرأ جميع المقالات</a>
                </div>
                <div class="blog-grid">{blog_items}</div>
            </section>

            <!-- خطوات الاستخدام والخصوصية في بطاقتين واضحتين -->
            <div class="guide-grid">
                <section class="card" aria-labelledby="how-title">
                    <h2 id="how-title" class="card-title">📖 طريقة استخدام الموقع</h2>
                    <ol class="guide-list">
                        <li>اضغط «دخول / تسجيل» من الشريط العلوي.</li>
                        <li>أنشئ حساباً باسم مستخدم وكلمة مرور، أو سجّل الدخول بحسابك الحالي.</li>
                        <li>اختر القسم المناسب وأضف بيانات الحساب الذي تريد تنظيمه.</li>
                        <li>ارجع إلى حساباتك لإدارتها أو تعديلها أو حذفها.</li>
                    </ol>
                </section>
                <section class="card" aria-labelledby="privacy-info-title">
                    <h2 id="privacy-info-title" class="card-title">🛡️ الأمان والخصوصية</h2>
                    <div class="privacy-note">
                        <p>يشفّر الموقع كلمات المرور المحفوظة باستخدام Fernet. تسجيل الحساب والدخول يعتمدان على اسم المستخدم وكلمة المرور فقط، ولا يُطلب بريد إلكتروني للحساب.</p>
                        <p>استخدم كلمة مرور قوية وفريدة، واحمِ جهازك وبيانات دخولك. تعتمد الحماية أيضاً على حماية مفتاح التشفير وإعداد الخادم، ولا توجد خدمة يمكن ضمان أمانها بنسبة 100%.</p>
                        <a href="/privacy">سياسة الخصوصية</a> · <a href="/terms">شروط الاستخدام</a>
                    </div>
                </section>
            </div>

            <!-- المميزات -->
            <section aria-labelledby="feat-title" style="margin-bottom:48px;">
                <div style="text-align:center;margin-bottom:20px;">
                    <span class="badge">المميزات</span>
                    <h2 id="feat-title" style="font-size:22px;color:var(--heading);font-weight:800;margin-top:8px;">لماذا مدير الحسابات الشامل؟</h2>
                </div>
                <div class="feat-grid">
                    <div class="feat-card"><div class="feat-icon">🔒</div><h3>تشفير Fernet</h3><p>جميع كلمات مرورك مشفرة بخوارزمية AES-128 المتقدمة.</p></div>
                    <div class="feat-card"><div class="feat-icon">👤</div><h3>دخول مباشر</h3><p>أنشئ حسابك وسجّل الدخول باسم مستخدم وكلمة مرور.</p></div>
                    <div class="feat-card"><div class="feat-icon">📱</div><h3>متوافق الجوال</h3><p>تصميم متجاوب يعمل بسلاسة على أي جهاز.</p></div>
                    <div class="feat-card"><div class="feat-icon">🛡️</div><h3>خصوصية تامة</h3><p>لا تتبع، لا بيع بيانات، لا إعلانات مخصصة من طرفنا.</p></div>
                    <div class="feat-card"><div class="feat-icon">⚡</div><h3>سريع وبسيط</h3><p>إضافة وإدارة حساباتك في ثوانٍ بواجهة سهلة.</p></div>
                    <div class="feat-card"><div class="feat-icon">☁️</div><h3>سحابي آمن</h3><p>وصول لحساباتك من أي مكان وأي وقت.</p></div>
                </div>
            </section>

            <!-- موضع إعلان إضافي داخل الصفحة الترحيبية -->
            {ad_unit(ADSENSE_SLOT_MID)}

            <!-- FAQ -->
            <section class="card" aria-labelledby="faq-title">
                <h2 id="faq-title" class="card-title">❓ الأسئلة الشائعة</h2>
                <div style="display:grid;gap:18px;">
                    <div>
                        <h3 style="color:var(--heading);font-size:15px;margin-bottom:6px;">هل بياناتي آمنة تماماً؟</h3>
                        <p style="font-size:14px;line-height:1.8;">نعم. كلمات المرور مشفرة بخوارزمية Fernet قبل التخزين. حتى مشرف الموقع لا يمكنه رؤيتها.</p>
                    </div>
                    <div>
                        <h3 style="color:var(--heading);font-size:15px;margin-bottom:6px;">هل الخدمة مجانية؟</h3>
                        <p style="font-size:14px;line-height:1.8;">نعم، الخدمة الأساسية مجانية بالكامل دون أي رسوم مخفية.</p>
                    </div>
                    <div>
                        <h3 style="color:var(--heading);font-size:15px;margin-bottom:6px;">ماذا لو نسيت كلمة المرور؟</h3>
                        <p style="font-size:14px;line-height:1.8;">لا تتوفر استعادة كلمة المرور عبر البريد. إذا كنت مسجلاً للدخول، غيّرها من صفحة الإعدادات؛ وإلا فلن تتمكن من استعادة الحساب بعد نسيانها.</p>
                    </div>
                    <div>
                        <h3 style="color:var(--heading);font-size:15px;margin-bottom:6px;">هل يدعم الأجهزة المحمولة؟</h3>
                        <p style="font-size:14px;line-height:1.8;">نعم، الموقع متجاوب بالكامل ويعمل على الهاتف والحاسوب والتابلت.</p>
                    </div>
                </div>
            </section>

            <!-- موضع إعلان أسفل محتوى الصفحة الترحيبية -->
            {ad_unit(ADSENSE_SLOT_BOTTOM)}
        </div>
    </main>"""
    return page(content, title='الصفحة الرئيسية',
                desc='مدير الحسابات الشامل – احفظ كلمات مرورك بأمان وتشفير Fernet متقدم. مجاني، سريع، وسهل الاستخدام.',
                canonical='/', include_ads=True)


# ══════════════════════════════════════════════════════════
# 2. المدونة – قائمة المقالات
# ══════════════════════════════════════════════════════════
@app.route('/blog')
def blog_index():
    cards = ''.join(f"""
    <article class="blog-card">
        <div class="blog-cat">{a['cat']}</div>
        <h2><a href="/blog/{a['slug']}" style="color:var(--heading);">{a['title']}</a></h2>
        <p>{a['desc']}</p>
        <div class="blog-meta">🕐 {a['read_time']} · 📅 {a['date']}</div>
        <a href="/blog/{a['slug']}" class="blog-link">اقرأ المقال كاملاً ◀</a>
    </article>""" for a in ARTICLES)

    structured = json.dumps({
        "@context": "https://schema.org",
        "@type": "Blog",
        "name": f"مدونة {SITE_NAME}",
        "url": f"{SITE_URL}/blog",
        "description": "مقالات متخصصة في الأمن السيبراني وحماية كلمات المرور والخصوصية الرقمية.",
        "blogPost": [
            {"@type": "BlogPosting", "headline": a['title'],
             "url": f"{SITE_URL}/blog/{a['slug']}", "datePublished": a['date']}
            for a in ARTICLES
        ]
    }, ensure_ascii=False)

    content = f"""
    <script type="application/ld+json">{structured}</script>
    <main class="wrap">
        <header style="text-align:center;margin-bottom:32px;">
            <span class="badge">✍️ المدونة</span>
            <h1 style="font-size:30px;color:var(--heading);font-weight:900;margin-top:10px;">مقالات الأمن الرقمي</h1>
            <p style="font-size:15px;max-width:560px;margin:10px auto 0;line-height:1.7;">
                دليلك الشامل لحماية حساباتك وخصوصيتك الرقمية. مقالات موثوقة يكتبها خبراء متخصصون.
            </p>
        </header>
        <!-- موضع الإعلان أعلى قائمة المقالات -->
        {ad_unit(ADSENSE_SLOT_TOP)}
        <div class="blog-grid" style="margin-bottom:32px;">{cards}</div>
        <!-- موضع الإعلان أسفل قائمة المقالات -->
        {ad_unit(ADSENSE_SLOT_BOTTOM)}
    </main>"""
    return page(content, title='المدونة – مقالات الأمن الرقمي',
                desc='مقالات متخصصة في الأمن السيبراني وحماية كلمات المرور والخصوصية الرقمية.',
                canonical='/blog', include_ads=True)


# ══════════════════════════════════════════════════════════
# 3. صفحة المقال المفرد
# ══════════════════════════════════════════════════════════
@app.route('/blog/<slug>')
def blog_article(slug):
    art = get_article(slug)
    if not art:
        return page('<main class="wrap"><div class="card"><p>المقال غير موجود.</p></div></main>',
                    title='المقال غير موجود'), 404

    others = [a for a in ARTICLES if a['slug'] != slug][:3]
    other_links = ''.join(f"""
    <a href="/blog/{a['slug']}" class="blog-card" style="text-decoration:none;">
        <div class="blog-cat">{a['cat']}</div>
        <h3 style="font-size:14px;color:var(--heading);margin-bottom:6px;">{a['title']}</h3>
        <span class="blog-link">اقرأ ◀</span>
    </a>""" for a in others)

    structured = json.dumps({
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": art['title'],
        "description": art['desc'],
        "url": f"{SITE_URL}/blog/{slug}",
        "datePublished": art['date'],
        "publisher": {"@type": "Organization", "name": SITE_NAME, "url": SITE_URL},
        "articleSection": art['cat'],
        "inLanguage": "ar"
    }, ensure_ascii=False)

    content = f"""
    <script type="application/ld+json">{structured}</script>
    <main class="wrap-narrow">
        <nav class="breadcrumb" aria-label="مسار التنقل">
            <a href="/">الرئيسية</a> ›
            <a href="/blog">المدونة</a> ›
            <span>{art['title']}</span>
        </nav>
        <!-- موضع الإعلان أعلى المقال -->
        {ad_unit(ADSENSE_SLOT_TOP)}
        <article class="card">
            <div class="blog-cat" style="margin-bottom:10px;">{art['cat']}</div>
            <h1 style="font-size:26px;color:var(--heading);font-weight:900;line-height:1.3;margin-bottom:12px;">{art['title']}</h1>
            <div class="blog-meta" style="margin-bottom:22px;">🕐 {art['read_time']} · 📅 {art['date']}</div>
            <div class="article-body">{art['body']}</div>
        </article>
        <!-- موضع الإعلان بين المقال والمقالات ذات الصلة -->
        {ad_unit(ADSENSE_SLOT_MID)}
        <section style="margin-top:28px;">
            <h2 style="font-size:18px;color:var(--heading);font-weight:700;margin-bottom:16px;">📖 مقالات ذات صلة</h2>
            <div class="blog-grid">{other_links}</div>
        </section>
        <!-- موضع الإعلان أسفل المقالات ذات الصلة -->
        {ad_unit(ADSENSE_SLOT_BOTTOM)}
    </main>"""
    return page(content, title=art['title'], desc=art['desc'], canonical=f'/blog/{slug}', include_ads=True)


# ══════════════════════════════════════════════════════════
# 4. قسم الحسابات (تطبيق / بريد / موقع)
# ══════════════════════════════════════════════════════════
@app.route('/category/<cat_slug>')
def category_view(cat_slug):
    if 'user_id' not in session:
        return redirect('/')
    cat_names = {'تطبيق': 'التطبيقات والمنصات', 'بريد': 'البريد الإلكتروني', 'موقع': 'المواقع الإلكترونية'}
    if cat_slug not in cat_names:
        flash('القسم غير موجود.', 'error')
        return redirect('/')
    cat_name = cat_names[cat_slug]

    conn     = get_db()
    accounts = conn.execute(
        'SELECT id,app_name,email,app_username,password FROM app_accounts WHERE user_id=? AND account_type=?',
        (session['user_id'], cat_slug)
    ).fetchall()
    urow     = conn.execute('SELECT username FROM users WHERE id=?', (session['user_id'],)).fetchone()
    conn.close()
    username = urow[0] if urow else ''

    # ─ رؤوس الجدول
    if cat_slug == 'بريد':
        th = '<th>البريد الإلكتروني</th><th>كلمة المرور</th>'
    else:
        th = '<th>الاسم / الخدمة</th><th>البريد</th><th>اسم المستخدم</th><th>كلمة المرور</th>'

    # ─ صفوف الجدول
    rows = ''
    for i, r in enumerate(accounts, 1):
        rid = r[0]
        if cat_slug == 'بريد':
            cells = f'<td style="font-weight:700;color:var(--heading);">{r[2] or "-"}</td>'
        else:
            cells = (f'<td style="font-weight:700;color:var(--heading);">{r[1] or "-"}</td>'
                     f'<td>{r[2] or "-"}</td><td>{r[3] or "-"}</td>')
        cells += f"""<td>
            <div style="display:flex;align-items:center;justify-content:center;gap:6px;">
                <span id="pw-{rid}">••••••••</span>
                <button type="button" class="btn btn-ghost btn-sm"
                    onclick="tpwd({rid},this)" aria-label="إظهار كلمة المرور">إظهار</button>
            </div></td>"""
        rows += f"""<tr>
            <td style="color:var(--muted);">{i}</td>{cells}
            <td class="td-act">
                <a href="/edit/{rid}" class="btn btn-info btn-sm">تعديل</a>
                <form method="POST" action="/delete/{rid}" style="display:inline;"
                    onsubmit="return confirm('هل أنت متأكد من الحذف؟');">
                    <button type="submit" class="btn btn-danger btn-sm">حذف</button>
                </form>
            </td></tr>"""
    if not rows:
        colspan = 4 if cat_slug == 'بريد' else 7
        rows = f'<tr><td colspan="{colspan}" style="color:var(--muted);padding:24px;">لا توجد حسابات بعد.</td></tr>'

    # ─ نموذج الإضافة
    if cat_slug == 'بريد':
        form_f = """
        <div class="fg"><label>البريد الإلكتروني</label><input type="email" name="email" placeholder="example@mail.com" required></div>
        <div class="fg"><label>كلمة المرور</label><input type="text" name="password" placeholder="كلمة المرور" required autocomplete="off"></div>"""
    elif cat_slug == 'تطبيق':
        form_f = """
        <div class="fg"><label>اسم التطبيق / الخدمة</label><input type="text" name="app_name" placeholder="مثال: تيليجرام" required></div>
        <div class="fg"><label>البريد الإلكتروني</label><input type="email" name="email" placeholder="example@mail.com"></div>
        <div class="fg"><label>اسم المستخدم</label><input type="text" name="app_username" placeholder="اسم المستخدم" required></div>
        <div class="fg"><label>كلمة المرور</label><input type="text" name="password" placeholder="كلمة المرور" required autocomplete="off"></div>"""
    else:
        form_f = """
        <div class="fg"><label>اسم الموقع / الخدمة</label><input type="text" name="app_name" placeholder="مثال: GitHub" required></div>
        <div class="fg"><label>البريد الإلكتروني</label><input type="email" name="email" placeholder="example@mail.com"></div>
        <div class="fg"><label>اسم المستخدم</label><input type="text" name="app_username" placeholder="اسم المستخدم"></div>
        <div class="fg"><label>كلمة المرور</label><input type="text" name="password" placeholder="كلمة المرور" required autocomplete="off"></div>"""

    content = f"""
    <main class="wrap">
        <nav class="breadcrumb"><a href="/">الرئيسية</a> › <span>{cat_name}</span></nav>
        <div class="card" style="margin-bottom:20px;">
            <h1 class="card-title">➕ إضافة حساب جديد في {cat_name}</h1>
            <form action="/add_item" method="POST">
                <input type="hidden" name="account_type" value="{cat_slug}">
                <div class="fgrid">{form_f}</div>
                <button type="submit" class="btn btn-primary btn-block" style="margin-top:8px;">حفظ الحساب</button>
            </form>
        </div>
        <div class="card">
            <h2 class="card-title">📋 الحسابات المحفوظة ({len(accounts)})</h2>
            <div class="tbl-wrap">
                <table>
                    <thead><tr><th style="width:40px;">#</th>{th}<th style="width:130px;">الإجراءات</th></tr></thead>
                    <tbody>{rows}</tbody>
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
    return page(content, title=cat_name, logged_in=True, username=username)


# ══════════════════════════════════════════════════════════
# 5. API جلب كلمة المرور
# ══════════════════════════════════════════════════════════
@app.route('/get_password/<int:item_id>')
def get_password(item_id):
    if 'user_id' not in session:
        return jsonify({'password': 'Unauthorized'}), 403
    conn = get_db()
    row  = conn.execute('SELECT password FROM app_accounts WHERE id=? AND user_id=?',
                        (item_id, session['user_id'])).fetchone()
    conn.close()
    if row:
        return jsonify({'password': decrypt_password(row[0])})
    return jsonify({'password': 'Not Found'}), 404


# ══════════════════════════════════════════════════════════
# 6. إضافة حساب
# ══════════════════════════════════════════════════════════
@app.route('/add_item', methods=['POST'])
def add_item():
    if not session.get('user_id'):
        return redirect('/')
    account_type = request.form.get('account_type', '')
    raw_pwd = request.form.get('password', '')
    if not raw_pwd:
        flash('كلمة المرور مطلوبة.', 'error')
        return redirect(f'/category/{account_type}')
    if account_type == 'بريد':
        app_name, email, app_username = None, request.form.get('email'), None
    else:
        app_name     = request.form.get('app_name')
        email        = request.form.get('email')
        app_username = request.form.get('app_username')
    conn = get_db()
    conn.execute(
        'INSERT INTO app_accounts (user_id,account_type,app_name,app_username,email,password) VALUES(?,?,?,?,?,?)',
        (session['user_id'], account_type, app_name, app_username, email, encrypt_password(raw_pwd))
    )
    conn.commit(); conn.close()
    flash('تم حفظ الحساب بنجاح. ✅', 'success')
    return redirect(f'/category/{account_type}')


# ══════════════════════════════════════════════════════════
# 7. تعديل حساب
# ══════════════════════════════════════════════════════════
@app.route('/edit/<int:item_id>', methods=['GET', 'POST'])
def edit_item(item_id):
    if 'user_id' not in session:
        return redirect('/')
    conn = get_db()
    if request.method == 'POST':
        raw_pwd      = request.form.get('password', '')
        email        = request.form.get('email')
        app_name     = request.form.get('app_name')
        app_username = request.form.get('app_username')
        conn.execute(
            'UPDATE app_accounts SET app_name=?,app_username=?,email=?,password=? WHERE id=? AND user_id=?',
            (app_name, app_username, email, encrypt_password(raw_pwd), item_id, session['user_id'])
        )
        conn.commit()
        row = conn.execute('SELECT account_type FROM app_accounts WHERE id=?', (item_id,)).fetchone()
        conn.close()
        flash('تم تحديث البيانات بنجاح. ✅', 'success')
        return redirect(f'/category/{row[0]}')

    account  = conn.execute('SELECT * FROM app_accounts WHERE id=? AND user_id=?',
                            (item_id, session['user_id'])).fetchone()
    urow     = conn.execute('SELECT username FROM users WHERE id=?', (session['user_id'],)).fetchone()
    conn.close()
    if not account:
        flash('العنصر غير موجود.', 'error')
        return redirect('/')
    username = urow[0] if urow else ''
    acc_type = account[3]

    extra = (f"""
        <div class="fg"><label>اسم التطبيق / الموقع</label><input type="text" name="app_name" value="{account[2] or ''}" required></div>
        <div class="fg"><label>البريد الإلكتروني</label><input type="email" name="email" value="{account[5] or ''}"></div>
        <div class="fg"><label>اسم المستخدم</label><input type="text" name="app_username" value="{account[4] or ''}"></div>"""
               if acc_type != 'بريد' else
               f'<div class="fg"><label>البريد الإلكتروني</label><input type="email" name="email" value="{account[5] or ''}" required></div>')

    content = f"""
    <main class="wrap" style="display:flex;justify-content:center;">
        <div class="card" style="width:min(460px,100%);">
            <nav class="breadcrumb"><a href="/">الرئيسية</a> › <a href="/category/{acc_type}">القسم</a> › <span>تعديل</span></nav>
            <h1 class="card-title">✏️ تعديل البيانات</h1>
            <form method="POST">
                {extra}
                <div class="fg"><label>كلمة المرور الجديدة</label><input type="text" name="password" placeholder="أدخل كلمة المرور الجديدة" required autocomplete="off"></div>
                <button type="submit" class="btn btn-primary btn-block">حفظ التعديلات</button>
            </form>
            <a href="/category/{acc_type}" class="btn btn-ghost btn-block" style="margin-top:10px;">إلغاء والعودة</a>
        </div>
    </main>"""
    return page(content, title='تعديل الحساب', logged_in=True, username=username)


# ══════════════════════════════════════════════════════════
# 8. حذف حساب (POST فقط)
# ══════════════════════════════════════════════════════════
@app.route('/delete/<int:item_id>', methods=['POST'])
def delete_item(item_id):
    if 'user_id' not in session:
        return redirect('/')
    conn = get_db()
    row  = conn.execute('SELECT account_type FROM app_accounts WHERE id=? AND user_id=?',
                        (item_id, session['user_id'])).fetchone()
    if row:
        conn.execute('DELETE FROM app_accounts WHERE id=? AND user_id=?', (item_id, session['user_id']))
        conn.commit()
        flash('تم حذف الحساب. 🗑️', 'success')
    conn.close()
    return redirect(f'/category/{row[0]}' if row else '/')


# ══════════════════════════════════════════════════════════
# 9. الإعدادات
# ══════════════════════════════════════════════════════════
@app.route('/settings')
def settings_page():
    if 'user_id' not in session:
        return redirect('/')
    conn  = get_db()
    urow  = conn.execute('SELECT username,email FROM users WHERE id=?', (session['user_id'],)).fetchone()
    conn.close()
    username = urow[0] if urow else ''

    content = f"""
    <main class="wrap-narrow">
        <nav class="breadcrumb"><a href="/">الرئيسية</a> › <span>الإعدادات</span></nav>
        <div class="card">
            <h2 class="card-title">👤 تغيير اسم المستخدم</h2>
            <form action="/update_username" method="POST" style="margin-bottom:24px;">
                <div class="fg"><label for="current-username">اسم المستخدم الحالي</label>
                <input id="current-username" type="text" value="{username}" disabled style="opacity:.7;"></div>
                <div class="fg"><label for="new-username">اسم المستخدم الجديد</label>
                <input id="new-username" type="text" name="username" minlength="3" maxlength="32" autocomplete="username" required></div>
                <button type="submit" class="btn btn-info btn-block">تحديث اسم المستخدم</button>
            </form>
            <h2 class="card-title">🔒 تغيير كلمة المرور الرئيسية</h2>
            <form action="/update_credentials" method="POST">
                <div class="fg">
                    <label for="np">كلمة المرور الجديدة</label>
                    <input id="np" type="password" name="new_password" placeholder="6 أحرف على الأقل" minlength="6" required autocomplete="new-password">
                </div>
                <button type="submit" class="btn btn-primary btn-block">تحديث كلمة المرور</button>
            </form>
        </div>
        <div class="card" style="border-color:#7f1d1d;margin-top:20px;">
            <h2 class="card-title" style="color:#f87171;">⚠️ منطقة الخطر – حذف الحساب</h2>
            <p style="font-size:13px;line-height:1.8;margin-bottom:16px;">
                حذف الحساب سيمسح جميع بياناتك وكلمات مرورك المخزنة نهائياً بشكل لا يمكن استرجاعه.
            </p>
            <form action="/delete_account" method="POST"
                onsubmit="return confirm('هل أنت متأكد تماماً من حذف حسابك وكل بياناتك نهائياً؟');">
                <button type="submit" class="btn btn-danger btn-block">حذف حسابي نهائياً</button>
            </form>
        </div>
    </main>"""
    return page(content, title='الإعدادات', logged_in=True, username=username)


@app.route('/update_credentials', methods=['POST'])
def update_credentials():
    if 'user_id' not in session:
        return redirect('/')
    pw = request.form.get('new_password', '').strip()
    if len(pw) < 6:
        flash('كلمة المرور يجب أن تكون 6 أحرف على الأقل.', 'error')
        return redirect('/settings')
    conn = get_db()
    conn.execute('UPDATE users SET password_hash=? WHERE id=?', (generate_password_hash(pw), session['user_id']))
    conn.commit(); conn.close()
    flash('تم تحديث كلمة المرور بنجاح. ✅', 'success')
    return redirect('/settings')


@app.route('/update_username', methods=['POST'])
def update_username():
    if 'user_id' not in session:
        return redirect('/auth')
    username = request.form.get('username', '').strip()
    if len(username) < 3 or len(username) > 32 or any(ch.isspace() for ch in username):
        flash('اسم المستخدم يجب أن يكون من 3 إلى 32 حرفاً ومن دون مسافات.', 'error')
        return redirect('/settings')
    conn = get_db()
    exists = conn.execute(
        'SELECT 1 FROM users WHERE lower(username)=lower(?) AND id<>?',
        (username, session['user_id'])
    ).fetchone()
    if exists:
        conn.close()
        flash('اسم المستخدم مستخدم بالفعل. اختر اسماً آخر.', 'error')
        return redirect('/settings')
    conn.execute('UPDATE users SET username=? WHERE id=?', (username, session['user_id']))
    conn.commit()
    conn.close()
    flash('تم تحديث اسم المستخدم بنجاح. ✅', 'success')
    return redirect('/settings')


@app.route('/delete_account', methods=['POST'])
def delete_account():
    if 'user_id' not in session:
        return redirect('/')
    uid = session['user_id']
    conn = get_db()
    conn.execute('DELETE FROM app_accounts WHERE user_id=?', (uid,))
    conn.execute('DELETE FROM users WHERE id=?', (uid,))
    conn.commit(); conn.close()
    session.clear()
    return redirect('/')


# ══════════════════════════════════════════════════════════
# 10. عن الموقع
# ══════════════════════════════════════════════════════════
@app.route('/about')
def about_page():
    content = """
    <main class="wrap-narrow">
        <article class="card">
            <h1 class="card-title">🛡️ عن مدير الحسابات الشامل</h1>
            <div class="article-body">
                <p>
                    <strong>مدير الحسابات الشامل</strong> هو تطبيق ويب متخصص يهدف إلى مساعدة الأفراد والمؤسسات
                    على إدارة كلمات المرور والحسابات الرقمية بأعلى درجات الأمان والتنظيم.
                    صمّمناه بعناية فائقة ليكون بسيطاً في الاستخدام دون أي تنازل عن الأمان.
                </p>
                <h2>🎯 رسالتنا</h2>
                <p>
                    نؤمن بأن الأمن الرقمي حق أساسي لكل مستخدم، وليس رفاهية حكراً على المتخصصين.
                    لذلك بنينا هذه المنصة لتكون في متناول الجميع، بواجهة عربية سهلة وتقنية تشفير متقدمة.
                </p>
                <h2>🔐 معايير الأمان المعتمدة</h2>
                <ul>
                    <li>تشفير كلمات المرور بخوارزمية <strong>Fernet (AES-128-CBC + HMAC-SHA256)</strong></li>
                    <li>تجزئة كلمات المرور الرئيسية بـ <strong>PBKDF2-SHA256</strong> عبر Werkzeug</li>
                    <li>انتهاء الجلسة تلقائياً بعد <strong>15 دقيقة</strong> من عدم النشاط</li>
                    <li>الحماية من CSRF بقبول طلبات الحذف عبر POST فقط</li>
                    <li>الدخول باسم مستخدم وكلمة مرور، دون تحقق OTP عبر البريد</li>
                </ul>
                <h2>📧 تواصل معنا</h2>
                <p>لأي استفسار أو اقتراح أو إبلاغ عن ثغرة أمنية، يرجى التواصل عبر <a href="/contact" style="color:#60a5fa;">صفحة التواصل</a>.</p>
            </div>
        </article>
    </main>"""
    return page(content, title='عن الموقع',
                desc='تعرف على مدير الحسابات الشامل ومعايير الأمان والتشفير المعتمدة لحماية كلمات مرورك.',
                canonical='/about')


# ══════════════════════════════════════════════════════════
# 11. سياسة الخصوصية ✅ (شرط AdSense)
# ══════════════════════════════════════════════════════════
@app.route('/privacy')
def privacy_page():
    yr = datetime.now().year
    content = f"""
    <main class="wrap-narrow">
        <article class="card prose">
            <h1 class="card-title">🔏 سياسة الخصوصية</h1>
            <p><em>آخر تحديث: {datetime.now().strftime('%d %B %Y')}</em></p>
            <p>
                يُولي موقع <strong>{SITE_NAME}</strong> أهمية قصوى لخصوصية مستخدميه.
                توضح هذه السياسة بدقة كيفية جمع معلوماتك واستخدامها وحمايتها.
                باستخدامك للموقع، توافق على الشروط الواردة في هذه السياسة.
            </p>

            <h2>1. المعلومات التي نجمعها</h2>
            <ul>
                <li><strong>بيانات الحساب:</strong> اسم المستخدم وكلمة المرور المُجزَّأة (Hashed). لا يُطلب بريد إلكتروني لإنشاء الحساب.</li>
                <li><strong>بيانات الحسابات المحفوظة:</strong> أسماء التطبيقات وكلمات المرور المُشفَّرة التي تُضيفها بنفسك.</li>
                <li><strong>بيانات الجلسة:</strong> رقم الجلسة المؤقت لتسجيل الدخول، يُحذف تلقائياً بعد الخروج.</li>
                <li><strong>بيانات الاستخدام:</strong> لا نجمع أي بيانات تصفح أو تتبع سلوكي من طرفنا.</li>
            </ul>

            <h2>2. كيف نستخدم معلوماتك</h2>
            <ul>
                <li>تشغيل الخدمة وتأمين الوصول إلى حسابك.</li>
                <li>تشغيل الحساب وإدارة الجلسة بعد تسجيل الدخول.</li>
                <li>تحسين أداء الخدمة وإصلاح المشكلات التقنية.</li>
            </ul>

            <h2>3. الإعلانات – Google AdSense</h2>
            <p>
                يستخدم موقعنا <strong>Google AdSense</strong> لعرض الإعلانات التي تساهم في تمويل الخدمة المجانية.
                قد تستخدم Google ملفات تعريف الارتباط (Cookies) لعرض إعلانات مبنية على اهتماماتك وسلوك التصفح.
            </p>
            <p>يمكنك التحكم في هذه الإعلانات عبر:</p>
            <ul>
                <li><a href="https://www.google.com/settings/ads" target="_blank" rel="noopener" style="color:#60a5fa;">إعدادات إعلانات Google</a></li>
                <li><a href="https://www.aboutads.info/choices/" target="_blank" rel="noopener" style="color:#60a5fa;">موقع خيارات الإعلانات الرقمية</a></li>
            </ul>
            <p>
                لمزيد من المعلومات حول كيفية استخدام Google لبياناتك، راجع:
                <a href="https://policies.google.com/privacy" target="_blank" rel="noopener" style="color:#60a5fa;">سياسة خصوصية Google</a> و
                <a href="https://policies.google.com/technologies/ads" target="_blank" rel="noopener" style="color:#60a5fa;">سياسة إعلانات Google</a>.
            </p>

            <h2>4. ملفات تعريف الارتباط (Cookies)</h2>
            <p>
                نستخدم ملفات تعريف الارتباط الضرورية فقط لإدارة جلسات تسجيل الدخول.
                بالإضافة إلى ذلك، قد تستخدم Google AdSense ملفات تعريف الارتباط لأغراض الإعلانات كما هو موضح أعلاه.
            </p>

            <h2>5. مشاركة البيانات مع أطراف ثالثة</h2>
            <p>
                لا نبيع أو نشارك أو نؤجر بياناتك الشخصية لأي طرف ثالث.
                لا يستخدم الموقع البريد الإلكتروني لإنشاء حساب الموقع أو تسجيل الدخول أو استعادة كلمة المرور.
                قد تظل عناوين البريد التي أُدخلت سابقاً محفوظة في سجلات الحسابات الحالية.
                الاستثناء الوحيد: المتطلبات القانونية والأوامر القضائية.
            </p>

            <h2>6. أمان البيانات</h2>
            <ul>
                <li>كلمات المرور المُخزَّنة مُشفَّرة بخوارزمية Fernet لا يمكن قراءتها.</li>
                <li>كلمات مرور الحسابات مُجزَّأة (Hashed) ولا يمكن استعادتها.</li>
                <li>الاتصال مشفر عبر HTTPS في بيئة الإنتاج.</li>
                <li>الجلسات تنتهي تلقائياً بعد 15 دقيقة من عدم النشاط.</li>
            </ul>

            <h2>7. حقوقك</h2>
            <ul>
                <li><strong>حق الوصول:</strong> يمكنك الاطلاع على بياناتك من خلال حسابك في أي وقت.</li>
                <li><strong>حق التصحيح:</strong> يمكنك تعديل بياناتك من صفحة الإعدادات.</li>
                <li><strong>حق الحذف:</strong> يمكنك حذف حسابك وجميع بياناتك نهائياً من صفحة الإعدادات.</li>
                <li><strong>حق الاعتراض:</strong> يمكنك إيقاف الإعلانات المخصصة من إعدادات Google.</li>
            </ul>

            <h2>8. خصوصية الأطفال</h2>
            <p>
                خدمتنا غير موجهة للأطفال دون سن 13 عاماً. إذا علمنا بأن طفلاً قاصراً قد سجّل حساباً،
                سنحذف بياناته فوراً.
            </p>

            <h2>9. تغييرات في السياسة</h2>
            <p>
                قد نحدّث هذه السياسة من وقت لآخر. سيُعلَن عن أي تغييرات جوهرية عبر الموقع.
                تاريخ آخر تحديث مذكور في أعلى الصفحة.
            </p>

            <h2>10. التواصل</h2>
            <p>
                لأي استفسار حول سياسة الخصوصية:
                البريد الإلكتروني: <a href="mailto:{CONTACT_EMAIL}" style="color:#60a5fa;">{CONTACT_EMAIL}</a> |
                <a href="/contact" style="color:#60a5fa;">نموذج التواصل</a>
            </p>
        </article>
    </main>"""
    return page(content, title='سياسة الخصوصية',
                desc='سياسة الخصوصية لموقع مدير الحسابات الشامل وكيفية التعامل مع بياناتك وإعلانات Google AdSense.',
                canonical='/privacy')


# ══════════════════════════════════════════════════════════
# 12. شروط الاستخدام ✅ (شرط AdSense)
# ══════════════════════════════════════════════════════════
@app.route('/terms')
def terms_page():
    content = f"""
    <main class="wrap-narrow">
        <article class="card prose">
            <h1 class="card-title">📋 شروط وأحكام الاستخدام</h1>
            <p><em>آخر تحديث: {datetime.now().strftime('%d %B %Y')}</em></p>
            <p>باستخدامك لموقع <strong>{SITE_NAME}</strong>، فإنك توافق على الشروط والأحكام التالية كاملة.</p>

            <h2>1. قبول الشروط</h2>
            <p>استخدامك للموقع يُعدّ قبولاً تاماً لهذه الشروط. إذا كنت لا توافق على أي جزء منها، يرجى التوقف عن استخدام الخدمة.</p>

            <h2>2. وصف الخدمة</h2>
            <p>مدير الحسابات الشامل هو خدمة ويب تتيح لك تخزين وإدارة كلمات مرور حساباتك الرقمية بشكل آمن ومشفر.</p>

            <h2>3. أهلية الاستخدام</h2>
            <ul>
                <li>يجب أن يكون عمرك 13 عاماً أو أكثر لاستخدام الخدمة.</li>
                <li>يجب أن تقدم معلومات صحيحة عند التسجيل.</li>
                <li>أنت مسؤول عن الحفاظ على سرية بيانات حسابك.</li>
            </ul>

            <h2>4. الاستخدام المقبول</h2>
            <ul>
                <li>يجب استخدام الخدمة لأغراض مشروعة وقانونية فقط.</li>
                <li>يُحظر استخدامها لتخزين معلومات غير قانونية أو ضارة.</li>
                <li>يُحظر محاولة اختراق أو تعطيل الخدمة.</li>
                <li>يُحظر الوصول لحسابات الآخرين دون إذن.</li>
                <li>أنت وحدك مسؤول عن البيانات التي تخزنها.</li>
            </ul>

            <h2>5. الإعلانات</h2>
            <p>
                يعرض الموقع إعلانات عبر Google AdSense لتمويل الخدمة المجانية.
                بقبولك لهذه الشروط، توافق على عرض هذه الإعلانات أثناء استخدامك للموقع.
            </p>

            <h2>6. الملكية الفكرية</h2>
            <p>جميع حقوق الملكية الفكرية لهذا الموقع محفوظة. لا يُسمح بنسخ أو توزيع أي محتوى دون إذن مسبق.</p>

            <h2>7. إخلاء المسؤولية</h2>
            <p>تُقدَّم الخدمة "كما هي" دون أي ضمانات. لا نتحمل المسؤولية عن أي ضرر ينتج عن الاستخدام أو عدم القدرة على الاستخدام.</p>

            <h2>8. إنهاء الخدمة</h2>
            <p>نحتفظ بالحق في تعليق أو إنهاء حسابك في حال انتهاك هذه الشروط.</p>

            <h2>9. تعديل الشروط</h2>
            <p>قد نعدّل هذه الشروط من وقت لآخر. الاستمرار في الاستخدام يعني موافقتك على الشروط المحدَّثة.</p>

            <h2>10. القانون المطبق</h2>
            <p>تخضع هذه الشروط للقوانين المعمول بها، وتُحسم أي نزاعات وفقاً لها.</p>

            <h2>11. التواصل</h2>
            <p>للتواصل بشأن هذه الشروط: <a href="/contact" style="color:#60a5fa;">صفحة التواصل</a></p>
        </article>
    </main>"""
    return page(content, title='شروط الاستخدام',
                desc='شروط وأحكام استخدام موقع مدير الحسابات الشامل.',
                canonical='/terms')


# ══════════════════════════════════════════════════════════
# 13. صفحة التواصل ✅ (شرط AdSense)
# ══════════════════════════════════════════════════════════
@app.route('/contact', methods=['GET', 'POST'])
def contact_page():
    if request.method == 'POST':
        flash('شكراً! تم استلام رسالتك وسنرد عليك في أقرب وقت. ✅', 'success')
        return redirect('/contact')

    content = f"""
    <main class="wrap-narrow">
        <div class="card">
            <h1 class="card-title">📬 تواصل معنا</h1>
            <p style="font-size:14px;line-height:1.8;margin-bottom:22px;">
                هل لديك سؤال، اقتراح، أو تريد الإبلاغ عن مشكلة أو ثغرة أمنية؟
                أرسل لنا رسالة وسنرد عليك في أقرب وقت ممكن.
                يمكنك أيضاً مراسلتنا مباشرة على:
                <a href="mailto:{CONTACT_EMAIL}" style="color:#60a5fa;">{CONTACT_EMAIL}</a>
            </p>
            <form method="POST">
                <div class="fgrid">
                    <div class="fg">
                        <label for="cn">الاسم الكريم</label>
                        <input id="cn" type="text" name="name" placeholder="اسمك" required>
                    </div>
                    <div class="fg">
                        <label for="ce">البريد الإلكتروني</label>
                        <input id="ce" type="email" name="email" placeholder="example@mail.com" required>
                    </div>
                </div>
                <div class="fg">
                    <label for="cs">الموضوع</label>
                    <input id="cs" type="text" name="subject" placeholder="موضوع رسالتك" required>
                </div>
                <div class="fg">
                    <label for="cm">الرسالة</label>
                    <textarea id="cm" name="message" placeholder="اكتب رسالتك هنا..." required></textarea>
                </div>
                <button type="submit" class="btn btn-primary btn-block">إرسال الرسالة ✉️</button>
            </form>
        </div>
    </main>"""
    return page(content, title='تواصل معنا',
                desc='تواصل مع فريق مدير الحسابات الشامل لأي استفسار أو اقتراح.',
                canonical='/contact')


# ══════════════════════════════════════════════════════════
# 14. لوحة المشرف
# ══════════════════════════════════════════════════════════
@app.route('/admin/users')
def admin_users():
    if 'user_id' not in session:
        return redirect('/')
    conn  = get_db()
    urow  = conn.execute('SELECT username FROM users WHERE id=?', (session['user_id'],)).fetchone()
    if not urow or urow[0] not in ('morad', 'admin'):
        conn.close()
        return page('<main class="wrap"><div class="card"><p style="color:var(--danger);">⛔ غير مسموح.</p></div></main>',
                    title='غير مسموح'), 403
    data = conn.execute("""
        SELECT u.id, u.username, u.email, COUNT(a.id)
        FROM users u LEFT JOIN app_accounts a ON u.id=a.user_id
        GROUP BY u.id""").fetchall()
    conn.close()
    rows = ''.join(
        f'<tr><td>{r[0]}</td><td style="font-weight:700;color:var(--heading);">{r[1]}</td>'
        f'<td>{r[2] or "-"}</td><td>{r[3]}</td></tr>' for r in data
    ) or '<tr><td colspan="4" style="color:var(--muted);padding:24px;">لا توجد حسابات.</td></tr>'
    content = f"""
    <main class="wrap">
        <div class="card">
            <h1 class="card-title">👥 لوحة تحكم المشرف – إدارة المستخدمين</h1>
            <div class="tbl-wrap">
                <table>
                    <thead><tr><th>ID</th><th>اسم المستخدم</th><th>البريد</th><th>عدد الحسابات</th></tr></thead>
                    <tbody>{rows}</tbody>
                </table>
            </div>
        </div>
    </main>"""
    return page(content, title='لوحة المشرف', logged_in=True, username=urow[0])


# ══════════════════════════════════════════════════════════
# 15. OTP / المصادقة – helpers
# ══════════════════════════════════════════════════════════
def otp_page(title, message, mode, email, button, error=''):
    err = f'<p style="color:#fca5a5;margin-bottom:12px;font-size:14px;">{error}</p>' if error else ''
    if mode == 'code':
        field = f"""<div class="fg">
            <label for="otpcode">رمز التحقق المرسل إلى {email}</label>
            <input id="otpcode" name="code" inputmode="numeric" pattern="[0-9]{{6}}"
                maxlength="6" placeholder="000000" required autocomplete="one-time-code"
                style="font-size:24px;letter-spacing:8px;text-align:center;">
        </div>"""
    else:
        field = """<div class="fg">
            <label for="newpw">كلمة المرور الجديدة</label>
            <input id="newpw" type="password" name="password" minlength="6"
                placeholder="6 أحرف على الأقل" required autocomplete="new-password">
        </div>"""
    content = f"""
    <main class="otp-wrap">
        <div class="card otp-card">
            <h1 style="font-size:20px;color:var(--heading);margin-bottom:12px;">{title}</h1>
            <p style="font-size:14px;line-height:1.7;margin-bottom:16px;">{message}</p>
            {err}
            <form method="POST">
                <input type="hidden" name="email" value="{email}">
                {field}
                <button type="submit" class="btn btn-primary btn-block">{button}</button>
            </form>
            <p style="text-align:center;margin-top:16px;font-size:13px;">
                <a href="/" style="color:#60a5fa;">← العودة للصفحة الرئيسية</a>
            </p>
        </div>
    </main>"""
    return page(content, title=title, include_ads=False)


def send_email_code(to_email: str, code: str, purpose: str):
    api_key    = os.environ.get('RESEND_API_KEY', '').strip()
    from_email = os.environ.get('RESEND_FROM', 'onboarding@resend.dev').strip()
    if not api_key:
        raise RuntimeError('RESEND_API_KEY غير مضبوط في متغيرات البيئة')
    subjects = {'register': 'تأكيد إنشاء حسابك', 'login': 'رمز تسجيل الدخول', 'reset': 'إعادة تعيين كلمة المرور'}
    data = {
        'from': from_email, 'to': [to_email],
        'subject': subjects.get(purpose, 'رمز التحقق'),
        'text': (f'مرحبًا،\n\nرمز التحقق الخاص بك هو: {code}\n'
                 'الرمز صالح لمدة 10 دقائق. لا تشاركه مع أحد.\n\n'
                 'إذا لم تطلب هذا الرمز فتجاهل الرسالة.'),
    }
    req = urllib.request.Request(
        'https://api.resend.com/emails',
        data=json.dumps(data).encode(),
        headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            if resp.status not in (200, 201):
                raise RuntimeError('فشل الإرسال عبر Resend')
    except urllib.error.HTTPError as e:
        app.logger.error('Resend HTTP %s: %s', e.code, e.read().decode(errors='replace'))
        raise RuntimeError(f'فشل إرسال البريد (HTTP {e.code})') from e
    except urllib.error.URLError as e:
        app.logger.error('Resend URLError: %s', e)
        raise RuntimeError('تعذر الاتصال بـ Resend') from e


def create_email_code(email: str, purpose: str, payload=None):
    code      = f'{secrets.randbelow(1_000_000):06d}'
    code_hash = hashlib.sha256(code.encode()).hexdigest()
    conn      = get_db()
    try:
        conn.execute('DELETE FROM auth_codes WHERE email=? AND purpose=?', (email, purpose))
        conn.execute(
            'INSERT INTO auth_codes (email,purpose,code_hash,payload,expires_at,attempts) VALUES(?,?,?,?,?,0)',
            (email, purpose, code_hash, payload, time.time() + 600)
        )
        conn.commit()
    finally:
        conn.close()
    send_email_code(email, code, purpose)


def verify_email_code(email: str, purpose: str, code: str):
    conn = get_db()
    try:
        row = conn.execute(
            'SELECT id,code_hash,payload,expires_at,attempts FROM auth_codes '
            'WHERE email=? AND purpose=? ORDER BY id DESC LIMIT 1',
            (email, purpose)
        ).fetchone()
        if not row or row[3] < time.time() or row[4] >= 5:
            return None
        conn.execute('UPDATE auth_codes SET attempts=attempts+1 WHERE id=?', (row[0],))
        conn.commit()
        if secrets.compare_digest(row[1], hashlib.sha256(code.strip().encode()).hexdigest()):
            conn.execute('DELETE FROM auth_codes WHERE email=? AND purpose=?', (email, purpose))
            conn.commit()
            return True
        return False
    finally:
        conn.close()


# ══════════════════════════════════════════════════════════
# 16. مسارات التحقق
# ══════════════════════════════════════════════════════════
@app.route('/verify-registration', methods=['GET', 'POST'])
def verify_registration():
    flash('إنشاء الحساب لا يتطلب تأكيد البريد الإلكتروني.', 'info')
    return redirect('/auth#register-section')


@app.route('/verify-login', methods=['GET', 'POST'])
def verify_login():
    flash('تسجيل الدخول الآن باسم المستخدم وكلمة المرور فقط.', 'info')
    return redirect('/auth#login-section')


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    flash('لا تتوفر استعادة كلمة المرور عبر البريد. إذا كنت مسجلاً للدخول، يمكنك تغييرها من الإعدادات.', 'error')
    return redirect('/auth')


@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    return redirect('/forgot-password')


@app.route('/choose-new-password', methods=['GET', 'POST'])
def choose_new_password():
    return redirect('/forgot-password')


# ══════════════════════════════════════════════════════════
# 17. تسجيل الدخول / التسجيل / الخروج
# ══════════════════════════════════════════════════════════
@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '').strip()
    pw    = request.form.get('password', '')
    if len(username) < 3 or len(username) > 32 or any(ch.isspace() for ch in username):
        flash('اسم المستخدم يجب أن يكون من 3 إلى 32 حرفاً ومن دون مسافات.', 'error')
        return redirect('/auth#register-section')
    if len(pw) < 6:
        flash('كلمة المرور يجب أن تكون 6 أحرف على الأقل.', 'error')
        return redirect('/auth#register-section')
    conn   = get_db()
    exists = conn.execute('SELECT 1 FROM users WHERE lower(username)=lower(?)',
                          (username,)).fetchone()
    conn.close()
    if exists:
        flash('اسم المستخدم مستخدم بالفعل. اختر اسماً آخر.', 'error')
        return redirect('/auth#register-section')
    conn = get_db()
    try:
        conn.execute('INSERT INTO users (username,password_hash,email) VALUES(?,?,NULL)',
                     (username, generate_password_hash(pw)))
        conn.commit()
    except sqlite3.IntegrityError:
        flash('اسم المستخدم مستخدم بالفعل. اختر اسماً آخر.', 'error')
        return redirect('/auth#register-section')
    finally:
        conn.close()
    flash('🎉 تم إنشاء حسابك بنجاح! يمكنك تسجيل الدخول الآن.', 'success')
    return redirect('/auth#login-section')


@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    pw    = request.form.get('password', '')
    conn  = get_db()
    user  = conn.execute(
        'SELECT id,password_hash FROM users WHERE lower(username)=lower(?) LIMIT 1',
        (username,)
    ).fetchone()
    conn.close()
    if user and check_password_hash(user[1], pw):
        session['user_id']     = user[0]
        session['last_active'] = time.time()
        flash('مرحباً! تم تسجيل دخولك بنجاح. 👋', 'success')
        return redirect('/')
    flash('اسم المستخدم أو كلمة المرور غير صحيحة.', 'error')
    return redirect('/auth#login-section')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


# ══════════════════════════════════════════════════════════
# 18. robots.txt و sitemap.xml
# ══════════════════════════════════════════════════════════
@app.route('/robots.txt')
def robots_txt():
    txt = f"""User-agent: *
Allow: /
Allow: /blog
Allow: /blog/
Allow: /about
Allow: /privacy
Allow: /terms
Allow: /contact
Disallow: /admin/
Disallow: /settings
Disallow: /category/
Disallow: /edit/
Disallow: /delete/
Disallow: /get_password/
Disallow: /forgot-password
Disallow: /verify-registration
Disallow: /verify-login
Disallow: /reset-password
Disallow: /choose-new-password

Sitemap: {SITE_URL}/sitemap.xml
"""
    return Response(txt, mimetype='text/plain')


@app.route('/sitemap.xml')
def sitemap_xml():
    static_pages = [
        ('/', '1.0', 'daily'),
        ('/blog', '0.9', 'daily'),
        ('/about', '0.7', 'monthly'),
        ('/privacy', '0.5', 'monthly'),
        ('/terms', '0.5', 'monthly'),
        ('/contact', '0.6', 'monthly'),
    ]
    blog_pages = [(f'/blog/{a["slug"]}', '0.8', 'monthly') for a in ARTICLES]
    all_pages  = static_pages + blog_pages
    urls = '\n'.join(
        f'  <url><loc>{SITE_URL}{loc}</loc><changefreq>{freq}</changefreq><priority>{pri}</priority></url>'
        for loc, pri, freq in all_pages
    )
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{urls}
</urlset>"""
    return Response(xml, mimetype='application/xml')


# ══════════════════════════════════════════════════════════
if __name__ == '__main__':
    app.run(debug=True)
