export type AccountType = 'تطبيق' | 'بريد' | 'موقع';

export interface User {
  id: string;
  username: string;
  passwordHash: string;
  email?: string;
  createdAt: string;
}

export interface AppAccount {
  id: string;
  userId: string;
  accountType: AccountType;
  appName?: string;
  appUsername?: string;
  email?: string;
  encryptedPassword: string;
  createdAt: string;
}

export interface BlogPost {
  slug: string;
  cat: string;
  title: string;
  desc: string;
  date: string;
  readTime: string;
  body: string;
}

export type ViewState =
  | { view: 'home' }
  | { view: 'auth'; initialTab?: 'login' | 'register' }
  | { view: 'category'; category: AccountType }
  | { view: 'edit'; accountId: string }
  | { view: 'settings' }
  | { view: 'admin' }
  | { view: 'blog' }
  | { view: 'article'; slug: string }
  | { view: 'about' }
  | { view: 'privacy' }
  | { view: 'terms' }
  | { view: 'contact' };

export interface FlashMessage {
  id: string;
  type: 'success' | 'error' | 'info';
  text: string;
}
