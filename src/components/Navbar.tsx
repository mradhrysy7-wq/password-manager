import React from 'react';
import { User, ViewState } from '../types';

interface NavbarProps {
  currentUser: User | null;
  onNavigate: (view: ViewState) => void;
  isLightTheme: boolean;
  onToggleTheme: () => void;
  onLogout: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentUser,
  onNavigate,
  isLightTheme,
  onToggleTheme,
  onLogout,
}) => {
  const isAdmin = currentUser && (currentUser.username.toLowerCase() === 'admin' || currentUser.username.toLowerCase() === 'morad');

  return (
    <nav className="site-nav" role="navigation" aria-label="القائمة الرئيسية">
      <div className="nav-logo" onClick={() => onNavigate({ view: 'home' })}>
        🔐 مدير الحسابات الشامل
      </div>
      <div className="nav-links">
        {currentUser ? (
          <>
            <button
              type="button"
              className="hide-sm"
              onClick={() => onNavigate({ view: 'blog' })}
            >
              ✍️ المدونة
            </button>
            <button
              type="button"
              className="hide-sm"
              onClick={() => onNavigate({ view: 'settings' })}
            >
              ⚙️ الإعدادات
            </button>
            {isAdmin && (
              <button
                type="button"
                className="nav-cta btn btn-sm"
                style={{ background: '#1e3a8a' }}
                onClick={() => onNavigate({ view: 'admin' })}
              >
                👥 المشرف
              </button>
            )}
            <button
              type="button"
              id="themeToggle"
              title="تبديل المظهر"
              onClick={onToggleTheme}
            >
              {isLightTheme ? '🌙' : '☀️'}
            </button>
            <button
              type="button"
              className="btn btn-sm"
              style={{ background: '#450a0a', color: '#f87171' }}
              onClick={onLogout}
            >
              خروج
            </button>
          </>
        ) : (
          <>
            <button
              type="button"
              className="hide-sm"
              onClick={() => onNavigate({ view: 'blog' })}
            >
              ✍️ المدونة
            </button>
            <button
              type="button"
              className="hide-sm"
              onClick={() => onNavigate({ view: 'about' })}
            >
              عن الموقع
            </button>
            <button
              type="button"
              className="hide-sm"
              onClick={() => onNavigate({ view: 'privacy' })}
            >
              الخصوصية
            </button>
            <button
              type="button"
              id="themeToggle"
              title="تبديل المظهر"
              onClick={onToggleTheme}
            >
              {isLightTheme ? '🌙' : '☀️'}
            </button>
            <button
              type="button"
              className="nav-cta btn btn-sm"
              onClick={() => onNavigate({ view: 'auth' })}
            >
              دخول / تسجيل
            </button>
          </>
        )}
      </div>
    </nav>
  );
};
