import React from 'react';
import { User, ViewState, AppAccount } from '../types';
import { ARTICLES } from '../data/articles';
import { AdUnit } from '../components/AdUnit';

interface HomeViewProps {
  currentUser: User | null;
  accounts: AppAccount[];
  onNavigate: (view: ViewState) => void;
}

export const HomeView: React.FC<HomeViewProps> = ({
  currentUser,
  accounts,
  onNavigate,
}) => {
  const recentArticles = ARTICLES.slice(0, 3);

  // If logged in
  if (currentUser) {
    const appCount = accounts.filter(a => a.userId === currentUser.id && a.accountType === 'تطبيق').length;
    const emailCount = accounts.filter(a => a.userId === currentUser.id && a.accountType === 'بريد').length;
    const siteCount = accounts.filter(a => a.userId === currentUser.id && a.accountType === 'موقع').length;

    return (
      <main className="wrap">
        <header style={{ marginBottom: '24px' }}>
          <h1 style={{ fontSize: '24px', color: 'var(--heading)', fontWeight: 800 }}>
            مرحباً، {currentUser.username} 👋
          </h1>
          <p style={{ fontSize: '14px', color: 'var(--muted)' }}>
            اختر قسماً لإدارة حساباتك وكلمات مرورك المشفرة
          </p>
        </header>

        <div className="feat-grid" style={{ marginBottom: '32px' }}>
          <div
            className="feat-card"
            onClick={() => onNavigate({ view: 'category', category: 'تطبيق' })}
          >
            <div className="feat-icon">📱</div>
            <h3>التطبيقات والمنصات</h3>
            <p>إدارة حسابات التطبيقات والخدمات ({appCount} حساب)</p>
          </div>

          <div
            className="feat-card"
            onClick={() => onNavigate({ view: 'category', category: 'بريد' })}
          >
            <div className="feat-icon">📧</div>
            <h3>البريد الإلكتروني</h3>
            <p>إدارة جميع حسابات البريد الإلكتروني ({emailCount} حساب)</p>
          </div>

          <div
            className="feat-card"
            onClick={() => onNavigate({ view: 'category', category: 'موقع' })}
          >
            <div className="feat-icon">🌐</div>
            <h3>المواقع الإلكترونية</h3>
            <p>إدارة حسابات المواقع والروابط ({siteCount} حساب)</p>
          </div>
        </div>

        <section>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h2 style={{ fontSize: '18px', color: 'var(--heading)', fontWeight: 700 }}>
              📖 آخر مقالات الأمن الرقمي
            </h2>
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              onClick={() => onNavigate({ view: 'blog' })}
            >
              عرض جميع المقالات
            </button>
          </div>
          <div className="blog-grid">
            {recentArticles.map(art => (
              <div
                key={art.slug}
                className="blog-card"
                onClick={() => onNavigate({ view: 'article', slug: art.slug })}
              >
                <div className="blog-cat">{art.cat}</div>
                <h2>{art.title}</h2>
                <p>{art.desc}</p>
                <span className="blog-link">اقرأ المقال ◀</span>
              </div>
            ))}
          </div>
        </section>
      </main>
    );
  }

  // If guest (logged out)
  return (
    <main>
      {/* Hero */}
      <section className="hero">
        <span className="badge">إدارة حساباتك في مكان واحد</span>
        <h1>كلمات مرورك، تحت سيطرتك الكاملة</h1>
        <p>
          نظّم بيانات حساباتك في مكان واحد، مع تشفير كلمات المرور المخزنة وإمكانية استعادتها عند الحاجة.
        </p>
      </section>

      <div className="wrap" style={{ paddingTop: 0 }}>
        <AdUnit slot="top" />

        {/* Welcome */}
        <section className="card welcome-panel" aria-labelledby="intro-title">
          <span className="badge">مرحباً بك</span>
          <h2 id="intro-title">👋 أهلاً بك في مدير الحسابات الشامل</h2>
          <p>
            هذا الموقع يساعدك على تنظيم بيانات حساباتك المختلفة في مكان واحد، مثل حسابات التطبيقات والبريد الإلكتروني والمواقع. تعرّف على طريقة الاستخدام، ثم اقرأ أحدث مقالاتنا من هنا.
          </p>
        </section>

        {/* Articles */}
        <section className="blog-section" aria-labelledby="blog-title">
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              gap: '12px',
              flexWrap: 'wrap',
              marginBottom: '18px',
            }}
          >
            <h2 id="blog-title" style={{ fontSize: '20px', color: 'var(--heading)', fontWeight: 800 }}>
              ✍️ مقالات الأمن الرقمي
            </h2>
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              onClick={() => onNavigate({ view: 'blog' })}
            >
              اقرأ جميع المقالات
            </button>
          </div>
          <div className="blog-grid">
            {recentArticles.map(art => (
              <div
                key={art.slug}
                className="blog-card"
                onClick={() => onNavigate({ view: 'article', slug: art.slug })}
              >
                <div className="blog-cat">{art.cat}</div>
                <h2>{art.title}</h2>
                <p>{art.desc}</p>
                <div className="blog-meta">🕐 {art.readTime} · {art.date}</div>
                <span className="blog-link">اقرأ المقال ◀</span>
              </div>
            ))}
          </div>
        </section>

        {/* Guide grid */}
        <div className="guide-grid">
          <section className="card" aria-labelledby="how-title">
            <h2 id="how-title" className="card-title">📖 طريقة استخدام الموقع</h2>
            <ol className="guide-list">
              <li>اضغط «دخول / تسجيل» من الشريط العلوي.</li>
              <li>أنشئ حساباً باسم مستخدم وكلمة مرور، أو سجّل الدخول بحسابك الحالي.</li>
              <li>اختر القسم المناسب وأضف بيانات الحساب الذي تريد تنظيمه.</li>
              <li>ارجع إلى حساباتك لإدارتها أو تعديلها أو حذفها.</li>
            </ol>
          </section>

          <section className="card" aria-labelledby="privacy-info-title">
            <h2 id="privacy-info-title" className="card-title">🛡️ الأمان والخصوصية</h2>
            <div className="privacy-note">
              <p>
                يشفّر الموقع كلمات المرور المحفوظة باستخدام خوارزمية تشفير متقدمة. تسجيل الحساب والدخول يعتمدان على اسم المستخدم وكلمة المرور فقط، ولا يُطلب بريد إلكتروني للحساب.
              </p>
              <p>
                استخدم كلمة مرور قوية وفريدة، واحمِ جهازك وبيانات دخولك.
              </p>
              <div>
                <button
                  type="button"
                  onClick={() => onNavigate({ view: 'privacy' })}
                  style={{ color: '#60a5fa', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
                >
                  سياسة الخصوصية
                </button>
                {' · '}
                <button
                  type="button"
                  onClick={() => onNavigate({ view: 'terms' })}
                  style={{ color: '#60a5fa', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
                >
                  شروط الاستخدام
                </button>
              </div>
            </div>
          </section>
        </div>

        {/* Features */}
        <section aria-labelledby="feat-title" style={{ marginBottom: '48px' }}>
          <div style={{ textAlign: 'center', marginBottom: '20px' }}>
            <span className="badge">المميزات</span>
            <h2 id="feat-title" style={{ fontSize: '22px', color: 'var(--heading)', fontWeight: 800, marginTop: '8px' }}>
              لماذا مدير الحسابات الشامل؟
            </h2>
          </div>
          <div className="feat-grid">
            <div className="feat-card">
              <div className="feat-icon">🔒</div>
              <h3>تشفير قوي</h3>
              <p>جميع كلمات مرورك مشفرة بخوارزمية AES المتقدمة.</p>
            </div>
            <div className="feat-card">
              <div className="feat-icon">👤</div>
              <h3>دخول مباشر</h3>
              <p>أنشئ حسابك وسجّل الدخول باسم مستخدم وكلمة مرور.</p>
            </div>
            <div className="feat-card">
              <div className="feat-icon">📱</div>
              <h3>متوافق الجوال</h3>
              <p>تصميم متجاوب يعمل بسلاسة على أي جهاز.</p>
            </div>
            <div className="feat-card">
              <div className="feat-icon">🛡️</div>
              <h3>خصوصية تامة</h3>
              <p>لا تتبع، لا بيع بيانات، لا إعلانات مخصصة من طرفنا.</p>
            </div>
            <div className="feat-card">
              <div className="feat-icon">⚡</div>
              <h3>سريع وبسيط</h3>
              <p>إضافة وإدارة حساباتك في ثوانٍ بواجهة سهلة.</p>
            </div>
            <div className="feat-card">
              <div className="feat-icon">☁️</div>
              <h3>سحابي آمن</h3>
              <p>وصول لحساباتك من أي مكان وأي وقت.</p>
            </div>
          </div>
        </section>

        <AdUnit slot="mid" />

        {/* FAQ */}
        <section className="card" aria-labelledby="faq-title">
          <h2 id="faq-title" className="card-title">❓ الأسئلة الشائعة</h2>
          <div style={{ display: 'grid', gap: '18px' }}>
            <div>
              <h3 style={{ color: 'var(--heading)', fontSize: '15px', marginBottom: '6px' }}>
                هل بياناتي آمنة تماماً؟
              </h3>
              <p style={{ fontSize: '14px', lineHeight: 1.8 }}>
                نعم. كلمات المرور مشفرة بخوارزمية متقدمة قبل التخزين، ولا يمكن لأحد قراءتها بدون فك التشفير المصرح به.
              </p>
            </div>
            <div>
              <h3 style={{ color: 'var(--heading)', fontSize: '15px', marginBottom: '6px' }}>
                هل الخدمة مجانية؟
              </h3>
              <p style={{ fontSize: '14px', lineHeight: 1.8 }}>
                نعم، الخدمة الأساسية مجانية بالكامل دون أي رسوم مخفية.
              </p>
            </div>
            <div>
              <h3 style={{ color: 'var(--heading)', fontSize: '15px', marginBottom: '6px' }}>
                ماذا لو نسيت كلمة المرور؟
              </h3>
              <p style={{ fontSize: '14px', lineHeight: 1.8 }}>
                إذا كنت مسجلاً للدخول، يمكنك تغييرها من صفحة الإعدادات؛ واحرص على تذكر كلمة مرورك الرئيسية لضمان الوصول لحساباتك.
              </p>
            </div>
            <div>
              <h3 style={{ color: 'var(--heading)', fontSize: '15px', marginBottom: '6px' }}>
                هل يدعم الأجهزة المحمولة؟
              </h3>
              <p style={{ fontSize: '14px', lineHeight: 1.8 }}>
                نعم، الموقع متجاوب بالكامل ويعمل على الهاتف والحاسوب والتابلت.
              </p>
            </div>
          </div>
        </section>

        <AdUnit slot="bottom" />
      </div>
    </main>
  );
};
