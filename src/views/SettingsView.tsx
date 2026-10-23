import React, { useState } from 'react';
import { User, ViewState } from '../types';

interface SettingsViewProps {
  currentUser: User;
  onUpdateUsername: (newUsername: string) => Promise<{ success: boolean; message: string }>;
  onUpdatePassword: (newPassword: string) => Promise<{ success: boolean; message: string }>;
  onDeleteAccount: () => Promise<void>;
  onNavigate: (view: ViewState) => void;
}

export const SettingsView: React.FC<SettingsViewProps> = ({
  currentUser,
  onUpdateUsername,
  onUpdatePassword,
  onDeleteAccount,
  onNavigate,
}) => {
  const [newUsername, setNewUsername] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [showConfirmDelete, setShowConfirmDelete] = useState(false);
  const [loadingUser, setLoadingUser] = useState(false);
  const [loadingPass, setLoadingPass] = useState(false);

  const handleUsernameSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newUsername.trim()) return;
    setLoadingUser(true);
    const res = await onUpdateUsername(newUsername.trim());
    setLoadingUser(false);
    if (res.success) {
      setNewUsername('');
    }
  };

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPassword) return;
    setLoadingPass(true);
    const res = await onUpdatePassword(newPassword);
    setLoadingPass(false);
    if (res.success) {
      setNewPassword('');
    }
  };

  return (
    <main className="wrap-narrow">
      <nav className="breadcrumb">
        <button type="button" onClick={() => onNavigate({ view: 'home' })}>
          الرئيسية
        </button>{' '}
        › <span>الإعدادات</span>
      </nav>

      <div className="card">
        <h2 className="card-title">👤 تغيير اسم المستخدم</h2>
        <form onSubmit={handleUsernameSubmit} style={{ marginBottom: '28px' }}>
          <div className="fg">
            <label htmlFor="current-username">اسم المستخدم الحالي</label>
            <input
              id="current-username"
              type="text"
              value={currentUser.username}
              disabled
              style={{ opacity: 0.7 }}
            />
          </div>
          <div className="fg">
            <label htmlFor="new-username">اسم المستخدم الجديد</label>
            <input
              id="new-username"
              type="text"
              value={newUsername}
              onChange={e => setNewUsername(e.target.value)}
              minLength={3}
              maxLength={32}
              placeholder="3 إلى 32 حرفاً وبدون مسافات"
              autoComplete="username"
              required
            />
          </div>
          <button
            type="submit"
            className="btn btn-info btn-block"
            disabled={loadingUser}
          >
            {loadingUser ? 'جارٍ التحديث...' : 'تحديث اسم المستخدم'}
          </button>
        </form>

        <h2 className="card-title">🔒 تغيير كلمة المرور الرئيسية</h2>
        <form onSubmit={handlePasswordSubmit}>
          <div className="fg">
            <label htmlFor="np">كلمة المرور الجديدة</label>
            <input
              id="np"
              type="password"
              value={newPassword}
              onChange={e => setNewPassword(e.target.value)}
              placeholder="6 أحرف على الأقل"
              minLength={6}
              autoComplete="new-password"
              required
            />
          </div>
          <button
            type="submit"
            className="btn btn-primary btn-block"
            disabled={loadingPass}
          >
            {loadingPass ? 'جارٍ التحديث...' : 'تحديث كلمة المرور'}
          </button>
        </form>
      </div>

      <div className="card" style={{ borderColor: '#7f1d1d', marginTop: '20px' }}>
        <h2 className="card-title" style={{ color: '#f87171' }}>
          ⚠️ منطقة الخطر – حذف الحساب
        </h2>
        <p style={{ fontSize: '13px', lineHeight: 1.8, marginBottom: '16px' }}>
          حذف الحساب سيمسح جميع بياناتك وكلمات مرورك المخزنة نهائياً بشكل لا يمكن استرجاعه.
        </p>
        <button
          type="button"
          className="btn btn-danger btn-block"
          onClick={() => setShowConfirmDelete(true)}
        >
          حذف حسابي نهائياً
        </button>
      </div>

      {showConfirmDelete && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0,0,0,0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 999,
            padding: '16px',
          }}
        >
          <div className="card" style={{ maxWidth: '420px', width: '100%', textAlign: 'center' }}>
            <h3 style={{ fontSize: '18px', fontWeight: 700, color: '#f87171', marginBottom: '12px' }}>
              ⚠️ تأكيد حذف الحساب نهائياً
            </h3>
            <p style={{ fontSize: '14px', color: 'var(--text)', marginBottom: '20px' }}>
              هل أنت متأكد تماماً من حذف حسابك وكل بياناتك نهائياً؟ سيتم محو جميع كلمات المرور المحفوظة على الفور.
            </p>
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
              <button
                type="button"
                className="btn btn-danger btn-sm"
                onClick={async () => {
                  setShowConfirmDelete(false);
                  await onDeleteAccount();
                }}
              >
                نعم، احذف حسابي وبياناتي
              </button>
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                onClick={() => setShowConfirmDelete(false)}
              >
                إلغاء
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
};
