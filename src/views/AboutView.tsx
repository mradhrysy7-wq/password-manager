import React from 'react';
import { ViewState } from '../types';

interface AboutViewProps {
  onNavigate: (view: ViewState) => void;
}

export const AboutView: React.FC<AboutViewProps> = ({ onNavigate }) => {
  return (
    <main className="wrap-narrow">
      <nav className="breadcrumb">
        <button type="button" onClick={() => onNavigate({ view: 'home' })}>
          الرئيسية
        </button>{' '}
        › <span>عن الموقع</span>
      </nav>

      <article className="card">
        <h1 className="card-title">🛡️ عن مدير الحسابات الشامل</h1>
        <div className="article-body">
          <p>
            <strong>مدير الحسابات الشامل</strong> هو تطبيق ويب متخصص يهدف إلى مساعدة الأفراد والمؤسسات على إدارة كلمات المرور والحسابات الرقمية بأعلى درجات الأمان والتنظيم. صمّمناه بعناية فائقة ليكون بسيطاً في الاستخدام دون أي تنازل عن الأمان.
          </p>

          <h2>🎯 رسالتنا</h2>
          <p>
            نؤمن بأن الأمن الرقمي حق أساسي لكل مستخدم، وليس رفاهية حكراً على المتخصصين. لذلك بنينا هذه المنصة لتكون في متناول الجميع، بواجهة عربية سهلة وتقنية تشفير متقدمة.
          </p>

          <h2>🔐 معايير الأمان المعتمدة</h2>
          <ul>
            <li>تشفير كلمات المرور بخوارزمية <strong>AES-GCM (مع تشفير متماثل وفحص سلامة التشفير)</strong></li>
            <li>تجزئة كلمات المرور الرئيسية وتأمينها عبر خوارزميات <strong>SHA-256 / PBKDF2</strong> المشددة</li>
            <li>انتهاء الجلسة تلقائياً بعد <strong>15 دقيقة</strong> من عدم النشاط لحماية حسابك في حال ترك الجهاز مفتوحاً</li>
            <li>تخزين محلي معزول ومشفّر لا يعتمد على خوادم خارجية غير موثوقة</li>
            <li>الدخول المباشر باسم مستخدم وكلمة مرور، دون تعقيدات أو تتبع شخصي</li>
          </ul>

          <h2>📧 تواصل معنا</h2>
          <p>
            لأي استفسار أو اقتراح أو إبلاغ عن ثغرة أمنية، يرجى التواصل عبر{' '}
            <button
              type="button"
              onClick={() => onNavigate({ view: 'contact' })}
              style={{ color: '#60a5fa', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
            >
              صفحة التواصل
            </button>
            {' أو مباشرة عبر البريد الإلكتروني: '}
            <a href="mailto:mradhrysy7@gmail.com" style={{ color: '#60a5fa' }}>mradhrysy7@gmail.com</a>.
          </p>
        </div>
      </article>
    </main>
  );
};
