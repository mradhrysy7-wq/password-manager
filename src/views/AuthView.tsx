import React, { useState } from 'react';
import { ViewState } from '../types';

interface AuthViewProps {
  onLogin: (username: string, password: string) => Promise<{ success: boolean; message: string }>;
  onRegister: (username: string, password: string) => Promise<{ success: boolean; message: string }>;
  onNavigate: (view: ViewState) => void;
  initialTab?: 'login' | 'register';
}

export const AuthView: React.FC<AuthViewProps> = ({
  onLogin,
  onRegister,
  onNavigate,
  initialTab = 'login',
}) => {
  const [loginUser, setLoginUser] = useState('');
  const [loginPass, setLoginPass] = useState('');
  const [regUser, setRegUser] = useState('');
  const [regPass, setRegPass] = useState('');
  const [activeTab, setActiveTab] = useState<'login' | 'register'>(initialTab);
  const [loading, setLoading] = useState(false);

  const handleLoginSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!loginUser.trim() || !loginPass) return;
    setLoading(true);
    await onLogin(loginUser.trim(), loginPass);
    setLoading(false);
  };

  const handleRegisterSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!regUser.trim() || !regPass) return;
    setLoading(true);
    const res = await onRegister(regUser.trim(), regPass);
    setLoading(false);
    if (res.success) {
      setLoginUser(regUser.trim());
      setRegPass('');
      setActiveTab('login');
    }
  };

  return (
    <main className="wrap-narrow">
      <header style={{ textAlign: 'center', margin: '12px 0 24px' }}>
        <span className="badge">🔐 حسابك يبدأ من هنا</span>
        <h1 style={{ fontSize: '28px', color: 'var(--heading)', fontWeight: 900 }}>
          دخول / تسجيل حساب
        </h1>
        <p style={{ color: 'var(--text)', fontSize: '14px', marginTop: '6px' }}>
          سجّل الدخول إلى حسابك أو أنشئ حساباً جديداً لإدارة كلمات المرور بأمان.
        </p>
      </header>

      {/* Tabs for mobile / desktop convenience */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '20px', justifyContent: 'center' }}>
        <button
          type="button"
          className={`btn ${activeTab === 'login' ? 'btn-primary' : 'btn-ghost'}`}
          onClick={() => setActiveTab('login')}
        >
          🔑 تسجيل الدخول
        </button>
        <button
          type="button"
          className={`btn ${activeTab === 'register' ? 'btn-primary' : 'btn-ghost'}`}
          onClick={() => setActiveTab('register')}
        >
          ✨ إنشاء حساب مجاني
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '20px' }}>
        {activeTab === 'login' && (
          <article className="card" id="login-section">
            <h2 className="card-title">🔑 تسجيل الدخول</h2>
            <form onSubmit={handleLoginSubmit}>
              <div className="fg">
                <label htmlFor="li-username">اسم المستخدم</label>
                <input
                  id="li-username"
                  type="text"
                  value={loginUser}
                  onChange={e => setLoginUser(e.target.value)}
                  placeholder="اسم المستخدم"
                  autoComplete="username"
                  required
                />
              </div>
              <div className="fg">
                <label htmlFor="li-pass">كلمة المرور</label>
                <input
                  id="li-pass"
                  type="password"
                  value={loginPass}
                  onChange={e => setLoginPass(e.target.value)}
                  placeholder="كلمة المرور"
                  autoComplete="current-password"
                  required
                />
              </div>
              <button
                type="submit"
                className="btn btn-primary btn-block"
                disabled={loading}
              >
                {loading ? 'جارٍ تسجيل الدخول...' : 'تسجيل الدخول'}
              </button>
            </form>
          </article>
        )}

        {activeTab === 'register' && (
          <article className="card" id="register-section">
            <h2 className="card-title">✨ إنشاء حساب مجاني</h2>
            <form onSubmit={handleRegisterSubmit}>
              <div className="fg">
                <label htmlFor="re-username">اسم المستخدم</label>
                <input
                  id="re-username"
                  type="text"
                  value={regUser}
                  onChange={e => setRegUser(e.target.value)}
                  placeholder="3 أحرف على الأقل، بدون مسافات"
                  minLength={3}
                  maxLength={32}
                  autoComplete="username"
                  required
                />
              </div>
              <div className="fg">
                <label htmlFor="re-pass">كلمة المرور الرئيسية</label>
                <input
                  id="re-pass"
                  type="password"
                  value={regPass}
                  onChange={e => setRegPass(e.target.value)}
                  placeholder="6 أحرف على الأقل"
                  minLength={6}
                  autoComplete="new-password"
                  required
                />
              </div>
              <button
                type="submit"
                className="btn btn-primary btn-block"
                disabled={loading}
              >
                {loading ? 'جارٍ إنشاء الحساب...' : 'إنشاء حساب مجاني'}
              </button>
            </form>
            <p style={{ textAlign: 'center', marginTop: '12px', fontSize: '12px', color: 'var(--muted)' }}>
              بالتسجيل توافق على{' '}
              <button
                type="button"
                onClick={() => onNavigate({ view: 'terms' })}
                style={{ color: '#60a5fa', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
              >
                شروط الاستخدام
              </button>{' '}
              و{' '}
              <button
                type="button"
                onClick={() => onNavigate({ view: 'privacy' })}
                style={{ color: '#60a5fa', background: 'none', border: 'none', cursor: 'pointer', padding: 0 }}
              >
                سياسة الخصوصية
              </button>
            </p>
          </article>
        )}
      </div>
    </main>
  );
};
