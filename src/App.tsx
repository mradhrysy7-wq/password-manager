import React, { useState, useEffect, useCallback } from 'react';
import {
  User,
  AppAccount,
  ViewState,
  AccountType,
  FlashMessage,
} from './types';
import {
  getUsers,
  saveUsers,
  getAccounts,
  saveAccounts,
  getCurrentUser,
  setCurrentUser,
  clearSession,
  touchSession,
  seedInitialDataIfNeeded,
} from './utils/storage';
import { hashPassword, verifyPassword, encryptPassword } from './utils/crypto';

import { Navbar } from './components/Navbar';
import { Footer } from './components/Footer';
import { HomeView } from './views/HomeView';
import { AuthView } from './views/AuthView';
import { CategoryView } from './views/CategoryView';
import { EditView } from './views/EditView';
import { SettingsView } from './views/SettingsView';
import { AdminView } from './views/AdminView';
import { BlogView } from './views/BlogView';
import { ArticleView } from './views/ArticleView';
import { AboutView } from './views/AboutView';
import { PrivacyView } from './views/PrivacyView';
import { TermsView } from './views/TermsView';
import { ContactView } from './views/ContactView';

export const App: React.FC = () => {
  const [currentUser, setCurrentUserState] = useState<User | null>(null);
  const [viewState, setViewState] = useState<ViewState>({ view: 'home' });
  const [users, setUsersState] = useState<User[]>([]);
  const [accounts, setAccountsState] = useState<AppAccount[]>([]);
  const [isLightTheme, setIsLightTheme] = useState<boolean>(() => {
    return localStorage.getItem('theme') === 'light';
  });
  const [flashMessages, setFlashMessages] = useState<FlashMessage[]>([]);

  // Apply theme to document
  useEffect(() => {
    if (isLightTheme) {
      document.body.classList.add('light-theme');
    } else {
      document.body.classList.remove('light-theme');
    }
  }, [isLightTheme]);

  const toggleTheme = () => {
    setIsLightTheme(prev => {
      const next = !prev;
      localStorage.setItem('theme', next ? 'light' : 'dark');
      return next;
    });
  };

  const showFlash = useCallback((text: string, type: 'success' | 'error' | 'info' = 'info') => {
    const id = Date.now().toString() + Math.random().toString();
    setFlashMessages(prev => [...prev, { id, text, type }]);
    setTimeout(() => {
      setFlashMessages(prev => prev.filter(m => m.id !== id));
    }, 4500);
  }, []);

  // Initialize data on mount
  useEffect(() => {
    seedInitialDataIfNeeded().then(() => {
      const u = getUsers();
      setUsersState(u);
      const a = getAccounts();
      setAccountsState(a);
      const sessionUser = getCurrentUser();
      setCurrentUserState(sessionUser);
    });
  }, []);

  // 15-minute inactivity session watchdog (identical to session_guard in Flask)
  useEffect(() => {
    const interval = setInterval(() => {
      if (currentUser) {
        const checked = getCurrentUser();
        if (!checked) {
          setCurrentUserState(null);
          setViewState({ view: 'home' });
          showFlash('انتهت مدة الجلسة (15 دقيقة من عدم النشاط). يرجى تسجيل الدخول مرة أخرى.', 'info');
        }
      }
    }, 30000);

    const onUserInteraction = () => {
      if (currentUser) {
        touchSession();
      }
    };

    window.addEventListener('click', onUserInteraction);
    window.addEventListener('keydown', onUserInteraction);

    return () => {
      clearInterval(interval);
      window.removeEventListener('click', onUserInteraction);
      window.removeEventListener('keydown', onUserInteraction);
    };
  }, [currentUser, showFlash]);

  // Auth: Login
  const handleLogin = async (username: string, pass: string): Promise<{ success: boolean; message: string }> => {
    const foundUser = users.find(u => u.username.toLowerCase() === username.toLowerCase());
    if (!foundUser) {
      showFlash('اسم المستخدم أو كلمة المرور غير صحيحة.', 'error');
      return { success: false, message: 'اسم المستخدم غير موجود.' };
    }

    const matches = await verifyPassword(pass, foundUser.passwordHash);
    if (!matches) {
      showFlash('اسم المستخدم أو كلمة المرور غير صحيحة.', 'error');
      return { success: false, message: 'كلمة المرور غير صحيحة.' };
    }

    setCurrentUser(foundUser);
    setCurrentUserState(foundUser);
    showFlash(`مرحباً! تم تسجيل دخولك بنجاح. 👋`, 'success');
    setViewState({ view: 'home' });
    return { success: true, message: 'تم بنجاح.' };
  };

  // Auth: Register
  const handleRegister = async (username: string, pass: string): Promise<{ success: boolean; message: string }> => {
    if (username.length < 3 || username.length > 32 || /\s/.test(username)) {
      const err = 'اسم المستخدم يجب أن يكون من 3 إلى 32 حرفاً ومن دون مسافات.';
      showFlash(err, 'error');
      return { success: false, message: err };
    }

    if (pass.length < 6) {
      const err = 'كلمة المرور يجب أن تكون 6 أحرف على الأقل.';
      showFlash(err, 'error');
      return { success: false, message: err };
    }

    const exists = users.some(u => u.username.toLowerCase() === username.toLowerCase());
    if (exists) {
      const err = 'اسم المستخدم مستخدم بالفعل. اختر اسماً آخر.';
      showFlash(err, 'error');
      return { success: false, message: err };
    }

    const hashed = await hashPassword(pass);
    const newUser: User = {
      id: 'usr_' + Date.now().toString(36),
      username,
      passwordHash: hashed,
      createdAt: new Date().toISOString(),
    };

    const nextUsers = [...users, newUser];
    saveUsers(nextUsers);
    setUsersState(nextUsers);

    showFlash('🎉 تم إنشاء حسابك بنجاح! يمكنك تسجيل الدخول الآن.', 'success');
    return { success: true, message: 'تم إنشاء الحساب بنجاح.' };
  };

  // Auth: Logout
  const handleLogout = () => {
    clearSession();
    setCurrentUserState(null);
    setViewState({ view: 'home' });
    showFlash('تم تسجيل الخروج بنجاح.', 'info');
  };

  // Accounts: Add
  const handleAddAccount = async (data: {
    accountType: AccountType;
    appName?: string;
    appUsername?: string;
    email?: string;
    password: string;
  }) => {
    if (!currentUser) return;
    const encPass = await encryptPassword(data.password);
    const newAcc: AppAccount = {
      id: 'acc_' + Date.now().toString(36),
      userId: currentUser.id,
      accountType: data.accountType,
      appName: data.appName,
      appUsername: data.appUsername,
      email: data.email,
      encryptedPassword: encPass,
      createdAt: new Date().toISOString(),
    };

    const nextAccounts = [...accounts, newAcc];
    saveAccounts(nextAccounts);
    setAccountsState(nextAccounts);
    showFlash('تم حفظ الحساب بنجاح. ✅', 'success');
  };

  // Accounts: Update
  const handleUpdateAccount = async (
    id: string,
    data: {
      appName?: string;
      appUsername?: string;
      email?: string;
      password?: string;
    }
  ) => {
    if (!currentUser) return;
    const target = accounts.find(a => a.id === id && a.userId === currentUser.id);
    if (!target) return;

    let encPass = target.encryptedPassword;
    if (data.password) {
      encPass = await encryptPassword(data.password);
    }

    const updated: AppAccount = {
      ...target,
      appName: data.appName !== undefined ? data.appName : target.appName,
      appUsername: data.appUsername !== undefined ? data.appUsername : target.appUsername,
      email: data.email !== undefined ? data.email : target.email,
      encryptedPassword: encPass,
    };

    const nextAccounts = accounts.map(a => (a.id === id ? updated : a));
    saveAccounts(nextAccounts);
    setAccountsState(nextAccounts);
    showFlash('تم تحديث البيانات بنجاح. ✅', 'success');
  };

  // Accounts: Delete
  const handleDeleteAccount = async (id: string) => {
    if (!currentUser) return;
    const nextAccounts = accounts.filter(a => a.id !== id);
    saveAccounts(nextAccounts);
    setAccountsState(nextAccounts);
    showFlash('تم حذف الحساب. 🗑️', 'success');
  };

  // Settings: Update username
  const handleUpdateUsername = async (newUsername: string): Promise<{ success: boolean; message: string }> => {
    if (!currentUser) return { success: false, message: 'غير مصرح' };

    if (newUsername.length < 3 || newUsername.length > 32 || /\s/.test(newUsername)) {
      const err = 'اسم المستخدم يجب أن يكون من 3 إلى 32 حرفاً ومن دون مسافات.';
      showFlash(err, 'error');
      return { success: false, message: err };
    }

    const exists = users.some(
      u => u.username.toLowerCase() === newUsername.toLowerCase() && u.id !== currentUser.id
    );
    if (exists) {
      const err = 'اسم المستخدم مستخدم بالفعل. اختر اسماً آخر.';
      showFlash(err, 'error');
      return { success: false, message: err };
    }

    const updatedUser = { ...currentUser, username: newUsername };
    const nextUsers = users.map(u => (u.id === currentUser.id ? updatedUser : u));
    saveUsers(nextUsers);
    setUsersState(nextUsers);
    setCurrentUser(updatedUser);
    setCurrentUserState(updatedUser);
    showFlash('تم تحديث اسم المستخدم بنجاح. ✅', 'success');
    return { success: true, message: 'تم التحديث بنجاح.' };
  };

  // Settings: Update password
  const handleUpdatePassword = async (newPassword: string): Promise<{ success: boolean; message: string }> => {
    if (!currentUser) return { success: false, message: 'غير مصرح' };

    if (newPassword.length < 6) {
      const err = 'كلمة المرور يجب أن تكون 6 أحرف على الأقل.';
      showFlash(err, 'error');
      return { success: false, message: err };
    }

    const hashed = await hashPassword(newPassword);
    const updatedUser = { ...currentUser, passwordHash: hashed };
    const nextUsers = users.map(u => (u.id === currentUser.id ? updatedUser : u));
    saveUsers(nextUsers);
    setUsersState(nextUsers);
    setCurrentUser(updatedUser);
    setCurrentUserState(updatedUser);
    showFlash('تم تحديث كلمة المرور بنجاح. ✅', 'success');
    return { success: true, message: 'تم تحديث كلمة المرور.' };
  };

  // Settings: Delete account & all data
  const handleDeleteUserAccount = async () => {
    if (!currentUser) return;
    const uid = currentUser.id;
    const nextAccounts = accounts.filter(a => a.userId !== uid);
    const nextUsers = users.filter(u => u.id !== uid);

    saveAccounts(nextAccounts);
    saveUsers(nextUsers);
    setAccountsState(nextAccounts);
    setUsersState(nextUsers);
    clearSession();
    setCurrentUserState(null);
    setViewState({ view: 'home' });
    showFlash('تم حذف حسابك وجميع بياناتك نهائياً.', 'info');
  };

  // Contact form
  const handleSendMessage = () => {
    showFlash('تم إرسال رسالتك بنجاح إلى mradhrysy7@gmail.com وسنرد عليك قريباً. ✅', 'success');
  };

  const userAccounts = currentUser ? accounts.filter(a => a.userId === currentUser.id) : [];

  return (
    <div className="min-h-screen flex flex-col justify-between">
      <div>
        <Navbar
          currentUser={currentUser}
          onNavigate={setViewState}
          isLightTheme={isLightTheme}
          onToggleTheme={toggleTheme}
          onLogout={handleLogout}
        />

        {/* Flash Messages wrapper */}
        {flashMessages.length > 0 && (
          <div className="flash-wrap">
            {flashMessages.map(msg => (
              <div key={msg.id} className={`alert alert-${msg.type}`}>
                {msg.text}
              </div>
            ))}
          </div>
        )}

        {/* View Routing */}
        {viewState.view === 'home' && (
          <HomeView
            currentUser={currentUser}
            accounts={userAccounts}
            onNavigate={setViewState}
          />
        )}

        {viewState.view === 'auth' && (
          <AuthView
            onLogin={handleLogin}
            onRegister={handleRegister}
            onNavigate={setViewState}
            initialTab={viewState.initialTab || 'login'}
          />
        )}

        {viewState.view === 'category' && (
          <CategoryView
            category={viewState.category}
            accounts={userAccounts}
            onAddAccount={handleAddAccount}
            onDeleteAccount={handleDeleteAccount}
            onNavigate={setViewState}
          />
        )}

        {viewState.view === 'edit' && (
          <EditView
            accountId={viewState.accountId}
            accounts={userAccounts}
            onUpdateAccount={handleUpdateAccount}
            onNavigate={setViewState}
          />
        )}

        {viewState.view === 'settings' && currentUser && (
          <SettingsView
            currentUser={currentUser}
            onUpdateUsername={handleUpdateUsername}
            onUpdatePassword={handleUpdatePassword}
            onDeleteAccount={handleDeleteUserAccount}
            onNavigate={setViewState}
          />
        )}

        {viewState.view === 'admin' && (
          <AdminView
            currentUser={currentUser}
            users={users}
            accounts={accounts}
            onNavigate={setViewState}
          />
        )}

        {viewState.view === 'blog' && <BlogView onNavigate={setViewState} />}

        {viewState.view === 'article' && (
          <ArticleView slug={viewState.slug} onNavigate={setViewState} />
        )}

        {viewState.view === 'about' && <AboutView onNavigate={setViewState} />}

        {viewState.view === 'privacy' && <PrivacyView onNavigate={setViewState} />}

        {viewState.view === 'terms' && <TermsView onNavigate={setViewState} />}

        {viewState.view === 'contact' && (
          <ContactView onNavigate={setViewState} onSendMessage={handleSendMessage} />
        )}
      </div>

      <Footer onNavigate={setViewState} />
    </div>
  );
};

export default App;
