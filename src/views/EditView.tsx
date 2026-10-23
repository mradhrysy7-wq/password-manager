import React, { useState, useEffect } from 'react';
import { AppAccount, ViewState } from '../types';
import { decryptPassword, calculatePasswordStrength } from '../utils/crypto';
import { PasswordGeneratorUtility } from '../components/PasswordGeneratorUtility';

interface EditViewProps {
  accountId: string;
  accounts: AppAccount[];
  onUpdateAccount: (
    id: string,
    data: {
      appName?: string;
      appUsername?: string;
      email?: string;
      password?: string;
    }
  ) => Promise<void>;
  onNavigate: (view: ViewState) => void;
}

export const EditView: React.FC<EditViewProps> = ({
  accountId,
  accounts,
  onUpdateAccount,
  onNavigate,
}) => {
  const account = accounts.find(a => a.id === accountId);

  const [appName, setAppName] = useState('');
  const [appUsername, setAppUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (account) {
      setAppName(account.appName || '');
      setAppUsername(account.appUsername || '');
      setEmail(account.email || '');
      decryptPassword(account.encryptedPassword).then(p => {
        setPassword(p);
      });
    }
  }, [account]);

  if (!account) {
    return (
      <main className="wrap">
        <div className="card">
          <p style={{ color: 'var(--danger)' }}>الحساب غير موجود أو تم حذفه.</p>
          <button
            type="button"
            className="btn btn-ghost"
            style={{ marginTop: '14px' }}
            onClick={() => onNavigate({ view: 'home' })}
          >
            العودة للرئيسية
          </button>
        </div>
      </main>
    );
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!password) return;
    setIsSaving(true);
    await onUpdateAccount(accountId, {
      appName: appName.trim(),
      appUsername: appUsername.trim(),
      email: email.trim(),
      password,
    });
    setIsSaving(false);
    onNavigate({ view: 'category', category: account.accountType });
  };

  return (
    <main className="wrap" style={{ display: 'flex', justifyContent: 'center' }}>
      <div className="card" style={{ width: 'min(460px, 100%)' }}>
        <nav className="breadcrumb">
          <button type="button" onClick={() => onNavigate({ view: 'home' })}>
            الرئيسية
          </button>{' '}
          ›{' '}
          <button
            type="button"
            onClick={() => onNavigate({ view: 'category', category: account.accountType })}
          >
            {account.accountType === 'تطبيق'
              ? 'التطبيقات'
              : account.accountType === 'بريد'
              ? 'البريد'
              : 'المواقع'}
          </button>{' '}
          › <span>تعديل</span>
        </nav>

        <h1 className="card-title">✏️ تعديل البيانات</h1>

        <form onSubmit={handleSubmit}>
          {account.accountType !== 'بريد' ? (
            <>
              <div className="fg">
                <label>اسم التطبيق / الموقع</label>
                <input
                  type="text"
                  value={appName}
                  onChange={e => setAppName(e.target.value)}
                  required
                />
              </div>
              <div className="fg">
                <label>البريد الإلكتروني</label>
                <input
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                />
              </div>
              <div className="fg">
                <label>اسم المستخدم</label>
                <input
                  type="text"
                  value={appUsername}
                  onChange={e => setAppUsername(e.target.value)}
                />
              </div>
            </>
          ) : (
            <div className="fg">
              <label>البريد الإلكتروني</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                required
              />
            </div>
          )}

          <div className="fg">
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '5px' }}>
              <label style={{ margin: 0 }}>كلمة المرور الجديدة</label>
              {password && (
                <span style={{ fontSize: '11px', fontWeight: 700, color: calculatePasswordStrength(password).color }}>
                  {calculatePasswordStrength(password).label}
                </span>
              )}
            </div>
            <input
              type="text"
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="أدخل كلمة المرور الجديدة أو ولّدها أدناه"
              required
              autoComplete="off"
            />
            {password && (
              <div style={{ height: '3px', width: '100%', background: 'var(--ibr)', borderRadius: '2px', overflow: 'hidden', marginTop: '4px' }}>
                <div
                  style={{
                    height: '100%',
                    width: `${calculatePasswordStrength(password).percentage}%`,
                    background: calculatePasswordStrength(password).color,
                    transition: 'all 0.2s',
                  }}
                />
              </div>
            )}
          </div>

          {/* Password Generator Utility */}
          <PasswordGeneratorUtility onApplyPassword={pwd => setPassword(pwd)} />

          <button
            type="submit"
            className="btn btn-primary btn-block"
            disabled={isSaving}
          >
            {isSaving ? 'جارٍ الحفظ...' : 'حفظ التعديلات'}
          </button>
        </form>

        <button
          type="button"
          className="btn btn-ghost btn-block"
          style={{ marginTop: '10px' }}
          onClick={() => onNavigate({ view: 'category', category: account.accountType })}
        >
          إلغاء والعودة
        </button>
      </div>
    </main>
  );
};
