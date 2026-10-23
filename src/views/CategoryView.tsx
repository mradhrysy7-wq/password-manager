import React, { useState } from 'react';
import { AccountType, AppAccount, ViewState } from '../types';
import { decryptPassword, calculatePasswordStrength } from '../utils/crypto';
import { PasswordGeneratorUtility } from '../components/PasswordGeneratorUtility';

interface CategoryViewProps {
  category: AccountType;
  accounts: AppAccount[];
  onAddAccount: (data: {
    accountType: AccountType;
    appName?: string;
    appUsername?: string;
    email?: string;
    password: string;
  }) => Promise<void>;
  onDeleteAccount: (accountId: string) => Promise<void>;
  onNavigate: (view: ViewState) => void;
}

export const CategoryView: React.FC<CategoryViewProps> = ({
  category,
  accounts,
  onAddAccount,
  onDeleteAccount,
  onNavigate,
}) => {
  const catNames: Record<AccountType, string> = {
    'تطبيق': 'التطبيقات والمنصات',
    'بريد': 'البريد الإلكتروني',
    'موقع': 'المواقع الإلكترونية',
  };
  const catName = catNames[category];

  // Add form fields
  const [appName, setAppName] = useState('');
  const [appUsername, setAppUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Decrypted passwords cache for toggle
  const [revealedPasswords, setRevealedPasswords] = useState<Record<string, string>>({});
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [deleteCandidateId, setDeleteCandidateId] = useState<string | null>(null);

  const filteredAccounts = accounts.filter(a => a.accountType === category);

  const handleTogglePassword = async (id: string, encrypted: string) => {
    if (revealedPasswords[id]) {
      const next = { ...revealedPasswords };
      delete next[id];
      setRevealedPasswords(next);
    } else {
      const plain = await decryptPassword(encrypted);
      setRevealedPasswords(prev => ({ ...prev, [id]: plain }));
    }
  };

  const handleCopyPassword = async (id: string, encrypted: string) => {
    try {
      const plain = revealedPasswords[id] || (await decryptPassword(encrypted));
      await navigator.clipboard.writeText(plain);
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2000);
    } catch (e) {
      console.error('Clipboard copy failed', e);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!password) return;
    setIsSubmitting(true);
    await onAddAccount({
      accountType: category,
      appName: appName.trim(),
      appUsername: appUsername.trim(),
      email: email.trim(),
      password,
    });
    setAppName('');
    setAppUsername('');
    setEmail('');
    setPassword('');
    setIsSubmitting(false);
  };

  const passwordStrength = calculatePasswordStrength(password);

  return (
    <main className="wrap">
      <nav className="breadcrumb">
        <button type="button" onClick={() => onNavigate({ view: 'home' })}>
          الرئيسية
        </button>{' '}
        › <span>{catName}</span>
      </nav>

      {/* Add Account Card */}
      <div className="card" style={{ marginBottom: '20px' }}>
        <h1 className="card-title">➕ إضافة حساب جديد في {catName}</h1>
        <form onSubmit={handleSubmit}>
          <div className="fgrid">
            {category === 'بريد' ? (
              <>
                <div className="fg">
                  <label>البريد الإلكتروني</label>
                  <input
                    type="email"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    placeholder="example@mail.com"
                    required
                  />
                </div>
                <div className="fg">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '5px' }}>
                    <label style={{ margin: 0 }}>كلمة المرور</label>
                    {password && (
                      <span style={{ fontSize: '11px', fontWeight: 700, color: passwordStrength.color }}>
                        {passwordStrength.label}
                      </span>
                    )}
                  </div>
                  <input
                    type="text"
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    placeholder="أدخل كلمة المرور أو ولّدها أدناه"
                    required
                    autoComplete="off"
                  />
                  {password && (
                    <div style={{ height: '3px', width: '100%', background: 'var(--ibr)', borderRadius: '2px', overflow: 'hidden', marginTop: '4px' }}>
                      <div style={{ height: '100%', width: `${passwordStrength.percentage}%`, background: passwordStrength.color, transition: 'all 0.2s' }} />
                    </div>
                  )}
                </div>
              </>
            ) : category === 'تطبيق' ? (
              <>
                <div className="fg">
                  <label>اسم التطبيق / الخدمة</label>
                  <input
                    type="text"
                    value={appName}
                    onChange={e => setAppName(e.target.value)}
                    placeholder="مثال: تيليجرام"
                    required
                  />
                </div>
                <div className="fg">
                  <label>البريد الإلكتروني</label>
                  <input
                    type="email"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    placeholder="example@mail.com"
                  />
                </div>
                <div className="fg">
                  <label>اسم المستخدم</label>
                  <input
                    type="text"
                    value={appUsername}
                    onChange={e => setAppUsername(e.target.value)}
                    placeholder="اسم المستخدم"
                    required
                  />
                </div>
                <div className="fg">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '5px' }}>
                    <label style={{ margin: 0 }}>كلمة المرور</label>
                    {password && (
                      <span style={{ fontSize: '11px', fontWeight: 700, color: passwordStrength.color }}>
                        {passwordStrength.label}
                      </span>
                    )}
                  </div>
                  <input
                    type="text"
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    placeholder="أدخل كلمة المرور أو ولّدها أدناه"
                    required
                    autoComplete="off"
                  />
                  {password && (
                    <div style={{ height: '3px', width: '100%', background: 'var(--ibr)', borderRadius: '2px', overflow: 'hidden', marginTop: '4px' }}>
                      <div style={{ height: '100%', width: `${passwordStrength.percentage}%`, background: passwordStrength.color, transition: 'all 0.2s' }} />
                    </div>
                  )}
                </div>
              </>
            ) : (
              <>
                <div className="fg">
                  <label>اسم الموقع / الخدمة</label>
                  <input
                    type="text"
                    value={appName}
                    onChange={e => setAppName(e.target.value)}
                    placeholder="مثال: GitHub"
                    required
                  />
                </div>
                <div className="fg">
                  <label>البريد الإلكتروني</label>
                  <input
                    type="email"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    placeholder="example@mail.com"
                  />
                </div>
                <div className="fg">
                  <label>اسم المستخدم</label>
                  <input
                    type="text"
                    value={appUsername}
                    onChange={e => setAppUsername(e.target.value)}
                    placeholder="اسم المستخدم"
                  />
                </div>
                <div className="fg">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '5px' }}>
                    <label style={{ margin: 0 }}>كلمة المرور</label>
                    {password && (
                      <span style={{ fontSize: '11px', fontWeight: 700, color: passwordStrength.color }}>
                        {passwordStrength.label}
                      </span>
                    )}
                  </div>
                  <input
                    type="text"
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    placeholder="أدخل كلمة المرور أو ولّدها أدناه"
                    required
                    autoComplete="off"
                  />
                  {password && (
                    <div style={{ height: '3px', width: '100%', background: 'var(--ibr)', borderRadius: '2px', overflow: 'hidden', marginTop: '4px' }}>
                      <div style={{ height: '100%', width: `${passwordStrength.percentage}%`, background: passwordStrength.color, transition: 'all 0.2s' }} />
                    </div>
                  )}
                </div>
              </>
            )}
          </div>

          {/* Password Generator Utility */}
          <PasswordGeneratorUtility onApplyPassword={pwd => setPassword(pwd)} />

          <button
            type="submit"
            className="btn btn-primary btn-block"
            style={{ marginTop: '8px' }}
            disabled={isSubmitting}
          >
            {isSubmitting ? 'جارٍ الحفظ...' : 'حفظ الحساب'}
          </button>
        </form>
      </div>

      {/* Accounts List Table Card */}
      <div className="card">
        <h2 className="card-title">📋 الحسابات المحفوظة ({filteredAccounts.length})</h2>
        <div className="tbl-wrap">
          <table>
            <thead>
              <tr>
                <th style={{ width: '40px' }}>#</th>
                {category === 'بريد' ? (
                  <>
                    <th>البريد الإلكتروني</th>
                    <th>كلمة المرور</th>
                  </>
                ) : (
                  <>
                    <th>الاسم / الخدمة</th>
                    <th>البريد</th>
                    <th>اسم المستخدم</th>
                    <th>كلمة المرور</th>
                  </>
                )}
                <th style={{ width: '150px' }}>الإجراءات</th>
              </tr>
            </thead>
            <tbody>
              {filteredAccounts.length === 0 ? (
                <tr>
                  <td colSpan={category === 'بريد' ? 4 : 6} style={{ color: 'var(--muted)', padding: '28px' }}>
                    لا توجد حسابات بعد. أضف حسابك الأول من النموذج أعلاه.
                  </td>
                </tr>
              ) : (
                filteredAccounts.map((acc, index) => {
                  const isRevealed = !!revealedPasswords[acc.id];
                  const plainVal = revealedPasswords[acc.id] || '••••••••';
                  return (
                    <tr key={acc.id}>
                      <td style={{ color: 'var(--muted)' }}>{index + 1}</td>
                      {category === 'بريد' ? (
                        <td style={{ fontWeight: 700, color: 'var(--heading)' }}>
                          {acc.email || '-'}
                        </td>
                      ) : (
                        <>
                          <td style={{ fontWeight: 700, color: 'var(--heading)' }}>
                            {acc.appName || '-'}
                          </td>
                          <td>{acc.email || '-'}</td>
                          <td>{acc.appUsername || '-'}</td>
                        </>
                      )}
                      <td>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}>
                          <span
                            style={{
                              fontFamily: isRevealed ? 'monospace' : 'inherit',
                              letterSpacing: isRevealed ? '1px' : '2px',
                              minWidth: '70px',
                            }}
                          >
                            {plainVal}
                          </span>
                          <button
                            type="button"
                            className="btn btn-ghost btn-sm"
                            onClick={() => handleTogglePassword(acc.id, acc.encryptedPassword)}
                            aria-label="إظهار كلمة المرور"
                          >
                            {isRevealed ? 'إخفاء' : 'إظهار'}
                          </button>
                          <button
                            type="button"
                            className="btn btn-ghost btn-sm"
                            onClick={() => handleCopyPassword(acc.id, acc.encryptedPassword)}
                            title="نسخ كلمة المرور"
                          >
                            {copiedId === acc.id ? 'تم النسخ ✓' : 'نسخ'}
                          </button>
                        </div>
                      </td>
                      <td className="td-act">
                        <button
                          type="button"
                          className="btn btn-info btn-sm"
                          onClick={() => onNavigate({ view: 'edit', accountId: acc.id })}
                        >
                          تعديل
                        </button>
                        <button
                          type="button"
                          className="btn btn-danger btn-sm"
                          onClick={() => setDeleteCandidateId(acc.id)}
                        >
                          حذف
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {deleteCandidateId && (
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
          <div className="card" style={{ maxWidth: '400px', width: '100%', textAlign: 'center' }}>
            <h3 style={{ fontSize: '18px', fontWeight: 700, color: 'var(--heading)', marginBottom: '12px' }}>
              تأكيد الحذف
            </h3>
            <p style={{ fontSize: '14px', color: 'var(--text)', marginBottom: '20px' }}>
              هل أنت متأكد من رغبتك في حذف هذا الحساب؟ لا يمكن التراجع عن هذا الإجراء.
            </p>
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
              <button
                type="button"
                className="btn btn-danger btn-sm"
                onClick={async () => {
                  const id = deleteCandidateId;
                  setDeleteCandidateId(null);
                  await onDeleteAccount(id);
                }}
              >
                نعم، احذف الحساب
              </button>
              <button
                type="button"
                className="btn btn-ghost btn-sm"
                onClick={() => setDeleteCandidateId(null)}
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
