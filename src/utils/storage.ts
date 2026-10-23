import { User, AppAccount } from '../types';
import { hashPassword, encryptPassword } from './crypto';

const USERS_KEY = 'pwm_users_v1';
const ACCOUNTS_KEY = 'pwm_accounts_v1';
const SESSION_KEY = 'pwm_session_v1';
const SESSION_TIMESTAMP_KEY = 'pwm_last_active_v1';
const INACTIVITY_TIMEOUT_MS = 15 * 60 * 1000; // 15 minutes

export function getUsers(): User[] {
  try {
    const raw = localStorage.getItem(USERS_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function saveUsers(users: User[]): void {
  try {
    localStorage.setItem(USERS_KEY, JSON.stringify(users));
  } catch (e) {
    console.error('Failed to save users', e);
  }
}

export function getAccounts(): AppAccount[] {
  try {
    const raw = localStorage.getItem(ACCOUNTS_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

export function saveAccounts(accounts: AppAccount[]): void {
  try {
    localStorage.setItem(ACCOUNTS_KEY, JSON.stringify(accounts));
  } catch (e) {
    console.error('Failed to save accounts', e);
  }
}

export function getCurrentUser(): User | null {
  try {
    const lastActiveStr = localStorage.getItem(SESSION_TIMESTAMP_KEY);
    if (lastActiveStr) {
      const lastActive = parseInt(lastActiveStr, 10);
      if (Date.now() - lastActive > INACTIVITY_TIMEOUT_MS) {
        clearSession();
        return null;
      }
    }
    const raw = localStorage.getItem(SESSION_KEY);
    if (!raw) return null;
    const sessionUser: User = JSON.parse(raw);
    // Touch session
    touchSession();
    return sessionUser;
  } catch {
    return null;
  }
}

export function setCurrentUser(user: User): void {
  try {
    localStorage.setItem(SESSION_KEY, JSON.stringify(user));
    touchSession();
  } catch (e) {
    console.error('Failed to set current user', e);
  }
}

export function touchSession(): void {
  localStorage.setItem(SESSION_TIMESTAMP_KEY, Date.now().toString());
}

export function clearSession(): void {
  localStorage.removeItem(SESSION_KEY);
  localStorage.removeItem(SESSION_TIMESTAMP_KEY);
}

/**
 * Initializes default user and sample accounts if first visit
 */
export async function seedInitialDataIfNeeded(): Promise<void> {
  const users = getUsers();
  if (users.length === 0) {
    const adminHash = await hashPassword('admin123');
    const defaultAdmin: User = {
      id: 'usr_morad',
      username: 'morad',
      passwordHash: adminHash,
      email: 'morad@example.com',
      createdAt: new Date().toISOString(),
    };
    saveUsers([defaultAdmin]);

    // Sample accounts for demonstration
    const pass1 = await encryptPassword('P@ssw0rd_2026!');
    const pass2 = await encryptPassword('Secur3_Gma!l_99');
    const pass3 = await encryptPassword('Git#Hub_Acc_88');

    const sampleAccounts: AppAccount[] = [
      {
        id: 'acc_1',
        userId: 'usr_morad',
        accountType: 'تطبيق',
        appName: 'تيليجرام (Telegram)',
        appUsername: '@morad_dev',
        email: 'morad@example.com',
        encryptedPassword: pass1,
        createdAt: new Date().toISOString(),
      },
      {
        id: 'acc_2',
        userId: 'usr_morad',
        accountType: 'بريد',
        email: 'work.morad@gmail.com',
        encryptedPassword: pass2,
        createdAt: new Date().toISOString(),
      },
      {
        id: 'acc_3',
        userId: 'usr_morad',
        accountType: 'موقع',
        appName: 'GitHub',
        appUsername: 'mradhrysy7',
        email: 'dev@github.com',
        encryptedPassword: pass3,
        createdAt: new Date().toISOString(),
      },
    ];
    saveAccounts(sampleAccounts);
  }
}
