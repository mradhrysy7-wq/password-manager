import React from 'react';
import { User, AppAccount, ViewState } from '../types';

interface AdminViewProps {
  currentUser: User | null;
  users: User[];
  accounts: AppAccount[];
  onNavigate: (view: ViewState) => void;
}

export const AdminView: React.FC<AdminViewProps> = ({
  currentUser,
  users,
  accounts,
  onNavigate,
}) => {
  const isAdmin = currentUser && (currentUser.username.toLowerCase() === 'admin' || currentUser.username.toLowerCase() === 'morad');

  if (!isAdmin) {
    return (
      <main className="wrap">
        <div className="card">
          <p style={{ color: 'var(--danger)', fontWeight: 700 }}>⛔ غير مسموح. هذه الصفحة مخصصة للمشرفين فقط.</p>
          <button
            type="button"
            className="btn btn-ghost"
            style={{ marginTop: '12px' }}
            onClick={() => onNavigate({ view: 'home' })}
          >
            العودة للرئيسية
          </button>
        </div>
      </main>
    );
  }

  return (
    <main className="wrap">
      <nav className="breadcrumb">
        <button type="button" onClick={() => onNavigate({ view: 'home' })}>
          الرئيسية
        </button>{' '}
        › <span>لوحة المشرف</span>
      </nav>

      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px', flexWrap: 'wrap', gap: '10px' }}>
          <h1 className="card-title" style={{ margin: 0, border: 'none', padding: 0 }}>
            👥 لوحة تحكم المشرف – إدارة المستخدمين
          </h1>
          <span className="badge" style={{ margin: 0 }}>
            إجمالي المسجلين: {users.length}
          </span>
        </div>

        <div className="tbl-wrap">
          <table>
            <thead>
              <tr>
                <th style={{ width: '60px' }}>#</th>
                <th>اسم المستخدم</th>
                <th>البريد</th>
                <th>عدد الحسابات المحفوظة</th>
                <th>تاريخ الإنشاء</th>
              </tr>
            </thead>
            <tbody>
              {users.length === 0 ? (
                <tr>
                  <td colSpan={5} style={{ color: 'var(--muted)', padding: '24px' }}>
                    لا توجد حسابات مسجلة.
                  </td>
                </tr>
              ) : (
                users.map((u, i) => {
                  const userAccountsCount = accounts.filter(a => a.userId === u.id).length;
                  return (
                    <tr key={u.id}>
                      <td style={{ color: 'var(--muted)' }}>{i + 1}</td>
                      <td style={{ fontWeight: 700, color: 'var(--heading)' }}>{u.username}</td>
                      <td>{u.email || '-'}</td>
                      <td>
                        <span style={{ fontWeight: 700, color: userAccountsCount > 0 ? 'var(--accent)' : 'inherit' }}>
                          {userAccountsCount}
                        </span>
                      </td>
                      <td style={{ fontSize: '12px', color: 'var(--muted)' }}>
                        {u.createdAt ? new Date(u.createdAt).toLocaleDateString('ar-EG') : 'حديثاً'}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </main>
  );
};
