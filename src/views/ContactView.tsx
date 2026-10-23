import React, { useState } from 'react';
import { ViewState } from '../types';

interface ContactViewProps {
  onNavigate: (view: ViewState) => void;
  onSendMessage: (data: { name: string; email: string; subject: string; message: string }) => void;
}

const DESTINATION_EMAIL = 'mradhrysy7@gmail.com';

export const ContactView: React.FC<ContactViewProps> = ({ onNavigate, onSendMessage }) => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [subject, setSubject] = useState('');
  const [message, setMessage] = useState('');
  const [isSending, setIsSending] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [copiedEmail, setCopiedEmail] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !email.trim() || !subject.trim() || !message.trim()) return;

    setIsSending(true);

    try {
      // Send directly to destination email via formsubmit.co ajax endpoint
      await fetch(`https://formsubmit.co/ajax/${DESTINATION_EMAIL}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: JSON.stringify({
          name: name.trim(),
          email: email.trim(),
          _subject: `[مدير الحسابات الشامل] ${subject.trim()}`,
          message: message.trim(),
          _replyto: email.trim(),
        }),
      });
    } catch (err) {
      console.warn('Direct HTTP email dispatch notice:', err);
    } finally {
      onSendMessage({
        name: name.trim(),
        email: email.trim(),
        subject: subject.trim(),
        message: message.trim(),
      });
      setIsSending(false);
      setSubmitted(true);
    }
  };

  const handleCopyEmail = async () => {
    try {
      await navigator.clipboard.writeText(DESTINATION_EMAIL);
      setCopiedEmail(true);
      setTimeout(() => setCopiedEmail(false), 2000);
    } catch {
      // fallback
    }
  };

  const mailtoUrl = `mailto:${DESTINATION_EMAIL}?subject=${encodeURIComponent(
    subject ? `[مدير الحسابات الشامل] ${subject}` : 'رسالة من مدير الحسابات الشامل'
  )}&body=${encodeURIComponent(
    `الاسم: ${name}\nالبريد الإلكتروني: ${email}\n\nالرسالة:\n${message}`
  )}`;

  return (
    <main className="wrap-narrow">
      <nav className="breadcrumb">
        <button type="button" onClick={() => onNavigate({ view: 'home' })}>
          الرئيسية
        </button>{' '}
        › <span>تواصل معنا</span>
      </nav>

      <div className="card">
        <h1 className="card-title">📬 تواصل معنا</h1>

        {/* Email target information card */}
        <div
          style={{
            background: 'var(--ibg)',
            border: '1px solid var(--ibr)',
            borderRadius: '10px',
            padding: '14px 18px',
            marginBottom: '20px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '10px',
          }}
        >
          <div>
            <div style={{ fontSize: '12px', color: 'var(--muted)' }}>
              البريد الإلكتروني المعتمد لاستلام الرسائل:
            </div>
            <a
              href={`mailto:${DESTINATION_EMAIL}`}
              style={{
                fontSize: '15px',
                fontWeight: 700,
                color: 'var(--accent)',
                direction: 'ltr',
                display: 'inline-block',
                marginTop: '2px',
              }}
            >
              {DESTINATION_EMAIL}
            </a>
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              type="button"
              className="btn btn-ghost btn-sm"
              onClick={handleCopyEmail}
            >
              {copiedEmail ? 'تم نسخ البريد ✓' : 'نسخ البريد'}
            </button>
            <a
              href={`mailto:${DESTINATION_EMAIL}`}
              className="btn btn-info btn-sm"
              style={{ textDecoration: 'none' }}
            >
              فتح تطبيق البريد ↗
            </a>
          </div>
        </div>

        <p style={{ fontSize: '14px', lineHeight: 1.8, marginBottom: '22px' }}>
          هل لديك سؤال، اقتراح، أو تريد الإبلاغ عن مشكلة أو استفسار أمني؟ أرسل لنا رسالة من النموذج أدناه وسيتم تسليمها مباشرة إلى البريد الإلكتروني{' '}
          <strong style={{ color: 'var(--heading)', direction: 'ltr', display: 'inline-block' }}>
            {DESTINATION_EMAIL}
          </strong>.
        </p>

        {submitted && (
          <div className="alert alert-success" style={{ marginBottom: '20px' }}>
            <div>
              <p style={{ fontWeight: 700 }}>
                تم إرسال رسالتك بنجاح إلى ({DESTINATION_EMAIL})! ✅
              </p>
              <p style={{ fontSize: '13px', marginTop: '4px' }}>
                شكراً لتواصلك، سنقوم بالرد عليك عبر بريدك الإلكتروني في أقرب وقت.
              </p>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="fgrid">
            <div className="fg">
              <label htmlFor="cn">الاسم الكريم</label>
              <input
                id="cn"
                type="text"
                value={name}
                onChange={e => setName(e.target.value)}
                placeholder="اسمك"
                required
              />
            </div>
            <div className="fg">
              <label htmlFor="ce">بريدك الإلكتروني (للرد عليك)</label>
              <input
                id="ce"
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="example@mail.com"
                required
              />
            </div>
          </div>
          <div className="fg">
            <label htmlFor="cs">الموضوع</label>
            <input
              id="cs"
              type="text"
              value={subject}
              onChange={e => setSubject(e.target.value)}
              placeholder="موضوع رسالتك"
              required
            />
          </div>
          <div className="fg">
            <label htmlFor="cm">نص الرسالة</label>
            <textarea
              id="cm"
              value={message}
              onChange={e => setMessage(e.target.value)}
              placeholder="اكتب رسالتك بالتفصيل هنا..."
              required
            />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <button
              type="submit"
              className="btn btn-primary btn-block"
              disabled={isSending}
            >
              {isSending
                ? `جارٍ الإرسال إلى ${DESTINATION_EMAIL}...`
                : `إرسال الرسالة إلى ${DESTINATION_EMAIL} ✉️`}
            </button>

            {(name || subject || message) && (
              <a
                href={mailtoUrl}
                className="btn btn-ghost btn-block"
                style={{ fontSize: '13px', textAlign: 'center' }}
              >
                أو إرسالها مباشرة من بريدك (Gmail / Outlook) ↗
              </a>
            )}
          </div>
        </form>
      </div>
    </main>
  );
};
