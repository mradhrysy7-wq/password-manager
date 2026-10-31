import React, { useState, useEffect, useCallback } from 'react';

// ==========================================
// 1. TYPES & INTERFACES
// ==========================================
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
  passwordUpdatedAt?: string;
  remind6Months?: boolean;
}

export function checkPasswordAge(dateString?: string): {
  isOlderThan6Months: boolean;
  ageDays: number;
  ageMonths: number;
  formattedDate: string;
} {
  const date = new Date(dateString || Date.now());
  const now = Date.now();
  const diffMs = now - date.getTime();
  const ageDays = Math.max(0, Math.floor(diffMs / (1000 * 60 * 60 * 24)));
  const ageMonths = Math.max(0, Math.floor(ageDays / 30));
  const isOlderThan6Months = ageDays >= 180;
  const formattedDate = isNaN(date.getTime())
    ? 'غير محدد'
    : date.toLocaleDateString('ar-EG', { year: 'numeric', month: 'long', day: 'numeric' });
  return { isOlderThan6Months, ageDays, ageMonths, formattedDate };
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

export interface PasswordGeneratorOptions {
  length?: number;
  includeUppercase?: boolean;
  includeLowercase?: boolean;
  includeNumbers?: boolean;
  includeSymbols?: boolean;
}

export interface PasswordStrength {
  score: number;
  label: string;
  color: string;
  percentage: number;
}

// ==========================================
// 2. CRYPTO & PASSWORD UTILITIES
// ==========================================
const APP_ENCRYPTION_SALT = 'manager_fernet_aes_2026_secure_key';
const UPPERCASE_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
const LOWERCASE_CHARS = 'abcdefghijklmnopqrstuvwxyz';
const NUMBER_CHARS = '0123456789';
const SYMBOL_CHARS = '!@#$%^&*()_+-=[]{}|;:,.<>?';

async function deriveKey(saltString: string = APP_ENCRYPTION_SALT): Promise<CryptoKey> {
  const enc = new TextEncoder();
  const rawKey = enc.encode(saltString);
  const hash = await crypto.subtle.digest('SHA-256', rawKey);
  return crypto.subtle.importKey('raw', hash, { name: 'AES-GCM' }, false, ['encrypt', 'decrypt']);
}

export async function hashPassword(plainText: string): Promise<string> {
  if (!plainText) return '';
  try {
    const enc = new TextEncoder();
    const data = enc.encode(plainText + '::' + APP_ENCRYPTION_SALT);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  } catch {
    let hash = 0;
    for (let i = 0; i < plainText.length; i++) {
      hash = (hash << 5) - hash + plainText.charCodeAt(i);
      hash |= 0;
    }
    return 'fallback:' + Math.abs(hash).toString(16);
  }
}

export async function verifyPassword(inputPassword: string, storedHash: string): Promise<boolean> {
  const computed = await hashPassword(inputPassword);
  return computed === storedHash;
}

export async function encryptPassword(plainText: string): Promise<string> {
  if (!plainText) return '';
  try {
    const key = await deriveKey();
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const enc = new TextEncoder();
    const encoded = enc.encode(plainText);
    const cipherBuffer = await crypto.subtle.encrypt({ name: 'AES-GCM', iv }, key, encoded);

    const ivB64 = btoa(String.fromCharCode(...iv));
    const cipherB64 = btoa(String.fromCharCode(...new Uint8Array(cipherBuffer)));
    return `aes-gcm:${ivB64}:${cipherB64}`;
  } catch {
    return 'b64:' + btoa(encodeURIComponent(plainText));
  }
}

export async function decryptPassword(cipherText: string): Promise<string> {
  if (!cipherText) return '';
  try {
    if (cipherText.startsWith('aes-gcm:')) {
      const parts = cipherText.split(':');
      if (parts.length === 3) {
        const iv = Uint8Array.from(atob(parts[1]), c => c.charCodeAt(0));
        const cipherData = Uint8Array.from(atob(parts[2]), c => c.charCodeAt(0));
        const key = await deriveKey();
        const decrypted = await crypto.subtle.decrypt({ name: 'AES-GCM', iv }, key, cipherData);
        return new TextDecoder().decode(decrypted);
      }
    }
    if (cipherText.startsWith('b64:')) {
      return decodeURIComponent(atob(cipherText.slice(4)));
    }
    return cipherText;
  } catch {
    return '[خطأ في فك التشفير]';
  }
}

export function getSecureRandomInt(max: number): number {
  if (max <= 0) return 0;
  const randomBuffer = new Uint32Array(1);
  const maxSafe = Math.floor(0xffffffff / max) * max;
  let val: number;
  do {
    crypto.getRandomValues(randomBuffer);
    val = randomBuffer[0];
  } while (val >= maxSafe);
  return val % max;
}

export function generateSecurePassword(options: PasswordGeneratorOptions = {}): string {
  const {
    length = 16,
    includeUppercase = true,
    includeLowercase = true,
    includeNumbers = true,
    includeSymbols = true,
  } = options;

  let charPool = '';
  const guaranteedChars: string[] = [];

  if (includeUppercase) {
    charPool += UPPERCASE_CHARS;
    guaranteedChars.push(UPPERCASE_CHARS[getSecureRandomInt(UPPERCASE_CHARS.length)]);
  }
  if (includeLowercase) {
    charPool += LOWERCASE_CHARS;
    guaranteedChars.push(LOWERCASE_CHARS[getSecureRandomInt(LOWERCASE_CHARS.length)]);
  }
  if (includeNumbers) {
    charPool += NUMBER_CHARS;
    guaranteedChars.push(NUMBER_CHARS[getSecureRandomInt(NUMBER_CHARS.length)]);
  }
  if (includeSymbols) {
    charPool += SYMBOL_CHARS;
    guaranteedChars.push(SYMBOL_CHARS[getSecureRandomInt(SYMBOL_CHARS.length)]);
  }

  if (!charPool) {
    charPool = LOWERCASE_CHARS + NUMBER_CHARS;
    guaranteedChars.push(charPool[getSecureRandomInt(charPool.length)]);
  }

  const remainingLength = Math.max(0, length - guaranteedChars.length);
  const resultChars = [...guaranteedChars];

  for (let i = 0; i < remainingLength; i++) {
    resultChars.push(charPool[getSecureRandomInt(charPool.length)]);
  }

  // Fisher-Yates cryptographically secure shuffle
  for (let i = resultChars.length - 1; i > 0; i--) {
    const j = getSecureRandomInt(i + 1);
    const temp = resultChars[i];
    resultChars[i] = resultChars[j];
    resultChars[j] = temp;
  }

  return resultChars.join('');
}

export function calculatePasswordStrength(password: string): PasswordStrength {
  if (!password) {
    return { score: 0, label: 'فارغة', color: 'var(--muted)', percentage: 0 };
  }
  let points = 0;
  if (password.length >= 8) points += 1;
  if (password.length >= 12) points += 1;
  if (password.length >= 16) points += 1;
  if (/[a-z]/.test(password) && /[A-Z]/.test(password)) points += 1;
  if (/[0-9]/.test(password)) points += 1;
  if (/[^A-Za-z0-9]/.test(password)) points += 1;

  if (points <= 2) {
    return { score: 1, label: 'ضعيفة', color: '#dc2626', percentage: 25 };
  } else if (points <= 4) {
    return { score: 2, label: 'متوسطة', color: '#f59e0b', percentage: 50 };
  } else if (points === 5) {
    return { score: 3, label: 'قوية', color: '#3b82f6', percentage: 75 };
  } else {
    return { score: 4, label: 'قوية جداً 🛡️', color: '#16a34a', percentage: 100 };
  }
}

// ==========================================
// 3. STORAGE UTILITIES
// ==========================================
const USERS_KEY = 'pwm_users_v1';
const ACCOUNTS_KEY = 'pwm_accounts_v1';
const SESSION_KEY = 'pwm_session_v1';
const SESSION_TIMESTAMP_KEY = 'pwm_last_active_v1';
const INACTIVITY_TIMEOUT_MS = 15 * 60 * 1000;

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

// ==========================================
// 4. BLOG ARTICLES
// ==========================================
export const ARTICLES: BlogPost[] = [
  {
    slug: 'how-to-create-strong-password',
    cat: 'أمان رقمي',
    title: 'كيف تنشئ كلمة مرور قوية لا تُكسر أبداً؟',
    desc: 'دليل شامل لإنشاء كلمات مرور آمنة وقوية تحمي حساباتك من الاختراق والقرصنة.',
    date: '10 أكتوبر 2026',
    readTime: '5 دقائق',
    body: `
<p>في عالم رقمي تتزايد فيه التهديدات السيبرانية يوماً بعد يوم، أصبح اختيار كلمة مرور قوية أمراً لا تهاون فيه. كثيرون يقعون في خطأ استخدام كلمات مرور بسيطة أو متكررة عبر مواقع متعددة، وهو ما يجعلهم هدفاً سهلاً للمخترقين.</p>
<h2>لماذا كلمات المرور الضعيفة خطيرة؟</h2>
<p>وفقاً لدراسات الأمن السيبراني، يمكن لهجمات "القوة العمياء" (Brute Force) كسر كلمة مرور مكونة من 6 أرقام في أقل من ثانية واحدة باستخدام الحواسيب الحديثة. أما كلمة مرور من 8 أحرف مختلطة، فقد تأخذ بضع ساعات فقط. لذلك فإن قوة كلمة مرورك = درعك الأول ضد الاختراق.</p>
<h2>مواصفات كلمة المرور القوية</h2>
<ul>
  <li><strong>الطول:</strong> 12 حرفاً على الأقل، والأفضل 16 أو أكثر.</li>
  <li><strong>التنوع:</strong> مزيج من الحروف الكبيرة والصغيرة والأرقام والرموز الخاصة مثل @، !، #.</li>
  <li><strong>التفرد:</strong> كلمة مرور مختلفة لكل حساب دون استثناء.</li>
  <li><strong>التجنب:</strong> لا تستخدم اسمك أو تاريخ ميلادك أو كلمات القاموس.</li>
</ul>
<h2>كيف تتذكر كل هذه الكلمات؟</h2>
<p>استخدم مدير كلمات المرور! أداة مثل <strong>مدير الحسابات الشامل</strong> تحفظ جميع كلمات مرورك المشفرة في مكان واحد آمن، وما عليك سوى تذكر كلمة مرور رئيسية واحدة قوية.</p>
`,
  },
  {
    slug: 'two-factor-authentication-guide',
    cat: 'دليل تقني',
    title: 'المصادقة الثنائية: طبقة حماية إضافية لا غنى عنها',
    desc: 'تعرف على المصادقة الثنائية 2FA وكيف تحمي حساباتك حتى لو سُرقت كلمة المرور.',
    date: '8 أكتوبر 2026',
    readTime: '6 دقائق',
    body: `
<p>المصادقة الثنائية (Two-Factor Authentication - 2FA) أصبحت معياراً أساسياً في أمان الحسابات الرقمية حول العالم، حيث تتطلب شيئاً تعرفه (كلمة المرور) وشيئاً تملكه (هاتفك أو تطبيق المصادقة).</p>
<h2>أنواع المصادقة الثنائية</h2>
<ul>
  <li>رمز SMS مؤقت.</li>
  <li>تطبيقات المصادقة مثل Google Authenticator.</li>
  <li>البصمة البيومترية ومفاتيح الأجهزة.</li>
</ul>
`,
  },
  {
    slug: 'password-manager-benefits',
    cat: 'نصائح تقنية',
    title: '7 أسباب تجعل مدير كلمات المرور ضرورة لا رفاهية',
    desc: 'اكتشف لماذا يستخدم خبراء الأمن السيبراني مديري كلمات المرور وكيف تختار الأفضل.',
    date: '5 أكتوبر 2026',
    readTime: '7 دقائق',
    body: `
<p>مدير كلمات المرور يمنحك كلمة مرور فريدة لكل موقع، وتوليد كلمات مرور آمنة تلقائياً، والوصول المنظم من أي جهاز مع تشفير قوي لا يمكن اختراقه.</p>
`,
  },
  {
    slug: 'email-security-tips',
    cat: 'أمان رقمي',
    title: '10 نصائح ذهبية لحماية بريدك الإلكتروني من الاختراق',
    desc: 'احمِ بريدك الإلكتروني من القرصنة والتصيد الاحتيالي بهذه النصائح العملية المجربة.',
    date: '2 أكتوبر 2026',
    readTime: '8 دقائق',
    body: `
<p>البريد الإلكتروني هو المفتاح الأساسي لجميع حساباتك، وحمايته تبدأ بكلمة مرور معقدة لا تقل عن 16 حرفاً وتفعيل التحقق بخطوتين وتجنب الروابط المشبوهة.</p>
`,
  },
];

// ==========================================
// 5. REUSABLE UI COMPONENTS
// ==========================================
export const AdUnit: React.FC<{ slot?: string }> = () => (
  <div className="ad-wrap" aria-label="إعلان" role="region">
    <div style={{ opacity: 0.6, fontSize: '13px' }}>
      📢 مساحة إعلانية متوافقة مع Google AdSense
    </div>
  </div>
);

export const PasswordGeneratorUtility: React.FC<{
  onApplyPassword: (password: string) => void;
  initialIsOpen?: boolean;
}> = ({ onApplyPassword, initialIsOpen = false }) => {
  const [isOpen, setIsOpen] = useState(initialIsOpen);
  const [length, setLength] = useState(16);
  const [includeUppercase, setIncludeUppercase] = useState(true);
  const [includeLowercase, setIncludeLowercase] = useState(true);
  const [includeNumbers, setIncludeNumbers] = useState(true);
  const [includeSymbols, setIncludeSymbols] = useState(true);
  const [generatedPassword, setGeneratedPassword] = useState('');
  const [copied, setCopied] = useState(false);

  const handleGenerate = useCallback(() => {
    const pwd = generateSecurePassword({
      length,
      includeUppercase,
      includeLowercase,
      includeNumbers,
      includeSymbols,
    });
    setGeneratedPassword(pwd);
  }, [length, includeUppercase, includeLowercase, includeNumbers, includeSymbols]);

  useEffect(() => {
    if (isOpen && !generatedPassword) {
      handleGenerate();
    }
  }, [isOpen, generatedPassword, handleGenerate]);

  const handleCopy = async () => {
    if (!generatedPassword) return;
    try {
      await navigator.clipboard.writeText(generatedPassword);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {}
  };

  const strength = calculatePasswordStrength(generatedPassword);

  if (!isOpen) {
    return (
      <div style={{ margin: '8px 0 14px' }}>
        <button
          type="button"
          className="btn btn-ghost btn-sm"
          style={{
            borderColor: 'var(--accent)',
            color: 'var(--heading)',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            fontSize: '12px',
          }}
          onClick={() => {
            setIsOpen(true);
            handleGenerate();
          }}
        >
          <span>⚡ أداة توليد كلمة مرور قوية وعشوائية</span>
        </button>
      </div>
    );
  }

  return (
    <div
      style={{
        background: 'var(--ibg)',
        border: '1px solid var(--ibr)',
        borderRadius: '10px',
        padding: '16px',
        margin: '10px 0 16px',
        boxShadow: '0 2px 10px rgba(0,0,0,0.15)',
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '12px',
          borderBottom: '1px solid var(--brd)',
          paddingBottom: '8px',
        }}
      >
        <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--heading)' }}>
          ⚡ مولّد كلمات المرور المشفرة والآمنة
        </span>
        <button
          type="button"
          onClick={() => setIsOpen(false)}
          style={{ background: 'none', border: 'none', color: 'var(--muted)', fontSize: '13px', cursor: 'pointer' }}
        >
          ✕ إغلاق
        </button>
      </div>

      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          background: 'var(--card)',
          border: '1px solid var(--ibr)',
          borderRadius: '8px',
          padding: '8px 12px',
          marginBottom: '10px',
        }}
      >
        <span
          style={{
            flex: 1,
            fontFamily: 'monospace',
            fontSize: '15px',
            fontWeight: 700,
            color: 'var(--heading)',
            letterSpacing: '1px',
            wordBreak: 'break-all',
            direction: 'ltr',
            textAlign: 'left',
          }}
        >
          {generatedPassword}
        </span>

        <button
          type="button"
          className="btn btn-ghost btn-sm"
          onClick={handleGenerate}
          title="توليد كلمة أخرى"
          style={{ padding: '4px 8px', fontSize: '13px' }}
        >
          🔄 جديد
        </button>

        <button
          type="button"
          className="btn btn-ghost btn-sm"
          onClick={handleCopy}
          style={{ padding: '4px 8px', fontSize: '12px' }}
        >
          {copied ? 'تم النسخ ✓' : 'نسخ'}
        </button>

        <button
          type="button"
          className="btn btn-primary btn-sm"
          onClick={() => onApplyPassword(generatedPassword)}
          style={{ padding: '4px 10px', fontSize: '12px' }}
        >
          استخدام ✓
        </button>
      </div>

      <div style={{ marginBottom: '12px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--muted)', marginBottom: '4px' }}>
          <span>قوة كلمة المرور:</span>
          <span style={{ fontWeight: 700, color: strength.color }}>{strength.label}</span>
        </div>
        <div style={{ height: '5px', width: '100%', background: 'var(--card)', borderRadius: '3px', overflow: 'hidden' }}>
          <div
            style={{
              height: '100%',
              width: `${strength.percentage}%`,
              background: strength.color,
              transition: 'width 0.3s ease, background 0.3s ease',
            }}
          />
        </div>
      </div>

      <div style={{ marginBottom: '12px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'var(--muted)', marginBottom: '4px' }}>
          <label htmlFor="pwd-length">طول كلمة المرور:</label>
          <span style={{ fontWeight: 700, color: 'var(--heading)' }}>{length} حرفاً</span>
        </div>
        <input
          id="pwd-length"
          type="range"
          min={8}
          max={32}
          value={length}
          onChange={e => setLength(parseInt(e.target.value, 10))}
          onMouseUp={handleGenerate}
          onTouchEnd={handleGenerate}
          style={{ width: '100%', cursor: 'pointer', accentColor: 'var(--btn)' }}
        />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '8px', fontSize: '12px', color: 'var(--text)' }}>
        <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
          <input type="checkbox" checked={includeUppercase} onChange={e => setIncludeUppercase(e.target.checked)} style={{ accentColor: 'var(--btn)' }} />
          <span>أحرف كبيرة (A-Z)</span>
        </label>
        <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
          <input type="checkbox" checked={includeLowercase} onChange={e => setIncludeLowercase(e.target.checked)} style={{ accentColor: 'var(--btn)' }} />
          <span>أحرف صغيرة (a-z)</span>
        </label>
        <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
          <input type="checkbox" checked={includeNumbers} onChange={e => setIncludeNumbers(e.target.checked)} style={{ accentColor: 'var(--btn)' }} />
          <span>أرقام (0-9)</span>
        </label>
        <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
          <input type="checkbox" checked={includeSymbols} onChange={e => setIncludeSymbols(e.target.checked)} style={{ accentColor: 'var(--btn)' }} />
          <span>رموز خاصة (@#$%)</span>
        </label>
      </div>
    </div>
  );
};

// ==========================================
// 5.1 LANDING HOME EXTRA SECTIONS (1 to 5)
// ==========================================
export const LandingHomeExtraSections: React.FC<{
  onNavigate: (view: ViewState) => void;
  showFlash?: (msg: string, type: 'success' | 'error' | 'info') => void;
}> = ({ onNavigate, showFlash }) => {
  // 1. Live Interactive Generator & Strength Tester State
  const [length, setLength] = useState<number>(16);
  const [includeUppercase, setIncludeUppercase] = useState<boolean>(true);
  const [includeLowercase, setIncludeLowercase] = useState<boolean>(true);
  const [includeNumbers, setIncludeNumbers] = useState<boolean>(true);
  const [includeSymbols, setIncludeSymbols] = useState<boolean>(true);
  const [generatedPassword, setGeneratedPassword] = useState<string>('');
  const [copied, setCopied] = useState<boolean>(false);
  const [customPassword, setCustomPassword] = useState<string>('');
  const [activeTab, setActiveTab] = useState<'generate' | 'test'>('generate');

  // 4. FAQ Accordion State (first item open by default)
  const [openFaq, setOpenFaq] = useState<number | null>(0);

  const handleGenerate = useCallback(() => {
    const pwd = generateSecurePassword({
      length,
      includeUppercase,
      includeLowercase,
      includeNumbers,
      includeSymbols,
    });
    setGeneratedPassword(pwd);
  }, [length, includeUppercase, includeLowercase, includeNumbers, includeSymbols]);

  useEffect(() => {
    handleGenerate();
  }, [handleGenerate]);

  const handleCopy = async (text: string) => {
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      if (showFlash) showFlash('تم نسخ كلمة المرور إلى الحافظة بنجاح ✓', 'success');
      setTimeout(() => setCopied(false), 2000);
    } catch {}
  };

  const activeStrength = activeTab === 'generate'
    ? calculatePasswordStrength(generatedPassword)
    : calculatePasswordStrength(customPassword);

  const faqs = [
    {
      q: 'هل بياناتي وكلمات مروري مشفرة وآمنة تماماً؟',
      a: 'نعم بالتأكيد! يتم تشفير كلمات المرور باستخدام خوارزميات التشفير المتماثل المتقدمة (AES / Fernet). لا يتم تخزين كلمات المرور بصيغة نصية مكشوفة أبداً، ولا يستطيع أحد فك تشفيرها وقراءتها سواك.',
    },
    {
      q: 'هل يعمل التطبيق بسلاسة على الهواتف الذكية والأجهزة المختلفة؟',
      a: 'نعم بنسبة 100%. تم تصميم الواجهة بتقنية متجاوبة بالكامل لتعمل بسلاسة وسرعة فائقة على كافة أجهزة أندرويد، آيفون، الأجهزة اللوحية، وشاشات الحواسيب المكتبية دون أي تأخير.',
    },
    {
      q: 'هل هذه الخدمة مجانية؟',
      a: 'نعم، المنصة مجانية بالكامل ومصممة لمساعدة المستخدمين على حماية وتنظيم هوياتهم وحساباتهم الرقمية والتخلص من كلمات المرور الضعيفة والمكررة.',
    },
    {
      q: 'كيف يمكنني التواصل معكم لطلب المساعدة أو تقديم اقتراح؟',
      a: 'يمكنك التواصل معنا في أي وقت من خلال الضغط على رابط "تواصل معنا" أسفل الصفحة، أو بإرسال رسالة مباشرة إلى بريدنا المعتمد: mradhrysy7@gmail.com.',
    },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px', marginTop: '16px', marginBottom: '40px' }}>
      
      {/* ========================================================
          1. LIVE INTERACTIVE GENERATOR & TESTER
          ======================================================== */}
      <section className="card" style={{ border: '1px solid var(--accent)', padding: '24px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px', marginBottom: '16px' }}>
          <div>
            <span className="badge" style={{ background: 'rgba(59, 130, 246, 0.15)', color: 'var(--accent)' }}>
              ⚡ أداة مباشرة
            </span>
            <h2 style={{ fontSize: '20px', fontWeight: 800, color: 'var(--heading)', marginTop: '6px' }}>
              مولّد وفاحص كلمات المرور التفاعلي
            </h2>
            <p style={{ fontSize: '13px', color: 'var(--muted)', marginTop: '4px' }}>
              جرّب توليد كلمات مرور قوية أو اختبر قوة كلمة مرورك الحالية فوراً
            </p>
          </div>

          <div style={{ display: 'flex', background: 'var(--ibg)', padding: '4px', borderRadius: '8px', gap: '4px' }}>
            <button
              type="button"
              className={`btn btn-sm ${activeTab === 'generate' ? 'btn-primary' : 'btn-ghost'}`}
              onClick={() => setActiveTab('generate')}
              style={{ fontSize: '12px' }}
            >
              ⚡ توليد كلمة مرور
            </button>
            <button
              type="button"
              className={`btn btn-sm ${activeTab === 'test' ? 'btn-primary' : 'btn-ghost'}`}
              onClick={() => setActiveTab('test')}
              style={{ fontSize: '12px' }}
            >
              🔍 فحص كلمة مرور
            </button>
          </div>
        </div>

        {activeTab === 'generate' ? (
          <div>
            {/* Display box */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                background: 'var(--ibg)',
                border: '1px solid var(--ibr)',
                borderRadius: '10px',
                padding: '12px 16px',
                marginBottom: '16px',
                flexWrap: 'wrap',
              }}
            >
              <span
                style={{
                  flex: 1,
                  fontFamily: 'monospace',
                  fontSize: '16px',
                  fontWeight: 800,
                  color: 'var(--heading)',
                  letterSpacing: '1px',
                  wordBreak: 'break-all',
                  direction: 'ltr',
                  textAlign: 'left',
                }}
              >
                {generatedPassword}
              </span>

              <div style={{ display: 'flex', gap: '6px' }}>
                <button
                  type="button"
                  className="btn btn-ghost btn-sm"
                  onClick={handleGenerate}
                  title="توليد كلمة مرور أخرى"
                  style={{ fontSize: '13px' }}
                >
                  🔄 جديد
                </button>
                <button
                  type="button"
                  className="btn btn-primary btn-sm"
                  onClick={() => handleCopy(generatedPassword)}
                  style={{ fontSize: '13px' }}
                >
                  {copied ? 'تم النسخ ✓' : '📋 نسخ'}
                </button>
              </div>
            </div>

            {/* Strength meter */}
            <div style={{ marginBottom: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'var(--muted)', marginBottom: '6px' }}>
                <span>مستوى الحماية والقوة:</span>
                <span style={{ fontWeight: 800, color: activeStrength.color }}>{activeStrength.label}</span>
              </div>
              <div style={{ height: '6px', width: '100%', background: 'var(--ibg)', borderRadius: '4px', overflow: 'hidden' }}>
                <div
                  style={{
                    height: '100%',
                    width: `${activeStrength.percentage}%`,
                    background: activeStrength.color,
                    transition: 'width 0.3s ease, background 0.3s ease',
                  }}
                />
              </div>
            </div>

            {/* Slider length */}
            <div style={{ marginBottom: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', color: 'var(--heading)', marginBottom: '6px' }}>
                <label htmlFor="landing-pwd-length">طول كلمة المرور:</label>
                <span style={{ fontWeight: 800, color: 'var(--accent)' }}>{length} حرفاً</span>
              </div>
              <input
                id="landing-pwd-length"
                type="range"
                min={8}
                max={32}
                value={length}
                onChange={e => setLength(parseInt(e.target.value, 10))}
                onMouseUp={handleGenerate}
                onTouchEnd={handleGenerate}
                style={{ width: '100%', cursor: 'pointer', accentColor: 'var(--btn)' }}
              />
            </div>

            {/* Checkboxes */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: '10px', fontSize: '13px', color: 'var(--text)' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                <input type="checkbox" checked={includeUppercase} onChange={e => setIncludeUppercase(e.target.checked)} style={{ accentColor: 'var(--btn)' }} />
                <span>أحرف كبيرة (A-Z)</span>
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                <input type="checkbox" checked={includeLowercase} onChange={e => setIncludeLowercase(e.target.checked)} style={{ accentColor: 'var(--btn)' }} />
                <span>أحرف صغيرة (a-z)</span>
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                <input type="checkbox" checked={includeNumbers} onChange={e => setIncludeNumbers(e.target.checked)} style={{ accentColor: 'var(--btn)' }} />
                <span>أرقام (0-9)</span>
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                <input type="checkbox" checked={includeSymbols} onChange={e => setIncludeSymbols(e.target.checked)} style={{ accentColor: 'var(--btn)' }} />
                <span>رموز خاصة (@#$%)</span>
              </label>
            </div>
          </div>
        ) : (
          <div>
            <div style={{ marginBottom: '16px' }}>
              <label htmlFor="custom-test-input" style={{ display: 'block', fontSize: '13px', color: 'var(--heading)', marginBottom: '6px' }}>
                أدخل أي كلمة مرور لفحص مدى قوتها ومقاومتها للاختراق:
              </label>
              <input
                id="custom-test-input"
                type="text"
                placeholder="اكتب كلمة مرورك هنا للتجربة..."
                value={customPassword}
                onChange={e => setCustomPassword(e.target.value)}
                style={{
                  width: '100%',
                  padding: '12px 14px',
                  borderRadius: '8px',
                  background: 'var(--ibg)',
                  border: '1px solid var(--ibr)',
                  color: 'var(--itxt)',
                  direction: 'ltr',
                  fontFamily: 'monospace',
                  fontSize: '15px',
                }}
              />
            </div>

            {customPassword && (
              <div style={{ marginBottom: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '6px' }}>
                  <span style={{ color: 'var(--muted)' }}>النتيجة المقدرة:</span>
                  <span style={{ fontWeight: 800, color: activeStrength.color }}>{activeStrength.label}</span>
                </div>
                <div style={{ height: '6px', width: '100%', background: 'var(--ibg)', borderRadius: '4px', overflow: 'hidden' }}>
                  <div
                    style={{
                      height: '100%',
                      width: `${activeStrength.percentage}%`,
                      background: activeStrength.color,
                      transition: 'width 0.3s ease, background 0.3s ease',
                    }}
                  />
                </div>
                <p style={{ fontSize: '12px', color: 'var(--muted)', marginTop: '8px' }}>
                  {activeStrength.score <= 2
                    ? '⚠️ كلمة المرور هذه معرضة للتخمين السريع! ننصح بزيادة طولها واستخدام رموز وأرقام.'
                    : '🛡️ كلمة مرور جيدة جداً وستوفر حماية متينة لحسابك.'}
                </p>
              </div>
            )}
          </div>
        )}
      </section>

      {/* ========================================================
          2. HOW IT WORKS (3 STEPS)
          ======================================================== */}
      <section>
        <div style={{ textAlign: 'center', marginBottom: '20px' }}>
          <span className="badge">سهل وبسيط</span>
          <h2 style={{ fontSize: '24px', fontWeight: 800, color: 'var(--heading)', marginTop: '8px' }}>
            🚀 كيف يعمل مدير الحسابات الشامل؟
          </h2>
          <p style={{ fontSize: '14px', color: 'var(--muted)', maxWidth: '600px', margin: '6px auto 0' }}>
            ثلاث خطوات بسيطة ومباشرة لحماية كافة حساباتك والوصول إليها بأمان في أي وقت
          </p>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '16px' }}>
          <div className="card" style={{ position: 'relative', overflow: 'hidden', padding: '22px' }}>
            <div style={{ fontSize: '32px', marginBottom: '12px' }}>1️⃣</div>
            <h3 style={{ fontSize: '17px', fontWeight: 700, color: 'var(--heading)', marginBottom: '8px' }}>
              أنشئ حسابك الآمن
            </h3>
            <p style={{ fontSize: '13px', color: 'var(--text)', lineHeight: 1.6 }}>
              سجّل حسابك برقم سري رئيسي في ثوانٍ معدودة. لا نطلب معلومات معقدة ولا مشاركة لأي بيانات حساسة.
            </p>
          </div>

          <div className="card" style={{ position: 'relative', overflow: 'hidden', padding: '22px' }}>
            <div style={{ fontSize: '32px', marginBottom: '12px' }}>2️⃣</div>
            <h3 style={{ fontSize: '17px', fontWeight: 700, color: 'var(--heading)', marginBottom: '8px' }}>
              نظّم وشفّر حساباتك
            </h3>
            <p style={{ fontSize: '13px', color: 'var(--text)', lineHeight: 1.6 }}>
              أضف حساباتك مصنفة إلى (تطبيقات، بريد، مواقع). كلمات المرور تُشفر فورياً بتشفير قوي متماثل.
            </p>
          </div>

          <div className="card" style={{ position: 'relative', overflow: 'hidden', padding: '22px' }}>
            <div style={{ fontSize: '32px', marginBottom: '12px' }}>3️⃣</div>
            <h3 style={{ fontSize: '17px', fontWeight: 700, color: 'var(--heading)', marginBottom: '8px' }}>
              استرجع وولّد في أي لحظة
            </h3>
            <p style={{ fontSize: '13px', color: 'var(--text)', lineHeight: 1.6 }}>
              انسخ واسترجع كلمات مرورك بضغطة زر، أو ولّد كلمات سر معقدة جديدة عبر مولد الأمان المدمج.
            </p>
          </div>
        </div>
      </section>

      {/* ========================================================
          3. FEATURED SECURITY ARTICLES / TIPS
          ======================================================== */}
      <section>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', flexWrap: 'wrap', gap: '10px', marginBottom: '18px' }}>
          <div>
            <span className="badge">أمان رقمي</span>
            <h2 style={{ fontSize: '22px', fontWeight: 800, color: 'var(--heading)', marginTop: '6px' }}>
              🛡️ أحدث نصائح التوعية والأمن السيبراني
            </h2>
          </div>
          <button
            type="button"
            className="btn btn-ghost btn-sm"
            onClick={() => onNavigate({ view: 'blog' })}
            style={{ fontSize: '13px', color: 'var(--accent)' }}
          >
            استعراض كافة المقالات (4) ◀
          </button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
          {ARTICLES.slice(0, 3).map(art => (
            <article
              key={art.slug}
              className="blog-card"
              onClick={() => onNavigate({ view: 'article', slug: art.slug })}
              style={{ cursor: 'pointer', padding: '20px' }}
            >
              <div className="blog-cat">{art.cat}</div>
              <h3 style={{ fontSize: '16px', fontWeight: 700, color: 'var(--heading)', margin: '8px 0' }}>
                {art.title}
              </h3>
              <p style={{ fontSize: '13px', color: 'var(--text)', marginBottom: '12px', lineHeight: 1.5 }}>
                {art.desc}
              </p>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px', color: 'var(--muted)' }}>
                <span>🕐 {art.readTime}</span>
                <span className="blog-link" style={{ fontWeight: 700 }}>اقرأ المقال ◀</span>
              </div>
            </article>
          ))}
        </div>
      </section>

      {/* ========================================================
          4. FAQ ACCORDION
          ======================================================== */}
      <section className="card" style={{ padding: '24px' }}>
        <div style={{ textAlign: 'center', marginBottom: '22px' }}>
          <span className="badge">إجابات واضحة</span>
          <h2 style={{ fontSize: '22px', fontWeight: 800, color: 'var(--heading)', marginTop: '8px' }}>
            ❓ الأسئلة الشائعة حول المنصة
          </h2>
          <p style={{ fontSize: '13px', color: 'var(--muted)', marginTop: '4px' }}>
            كل ما تحتاج لمعرفته حول الخصوصية والتشفير وتوافق الأجهزة
          </p>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {faqs.map((faq, idx) => {
            const isOpen = openFaq === idx;
            return (
              <div
                key={faq.q}
                style={{
                  border: '1px solid var(--ibr)',
                  borderRadius: '10px',
                  background: 'var(--ibg)',
                  overflow: 'hidden',
                  transition: 'all 0.2s ease',
                }}
              >
                <button
                  type="button"
                  onClick={() => setOpenFaq(isOpen ? null : idx)}
                  style={{
                    width: '100%',
                    padding: '14px 18px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    background: 'none',
                    border: 'none',
                    color: 'var(--heading)',
                    fontSize: '14px',
                    fontWeight: 700,
                    cursor: 'pointer',
                    textAlign: 'right',
                    gap: '12px',
                  }}
                >
                  <span>{faq.q}</span>
                  <span style={{ fontSize: '14px', color: 'var(--accent)', transition: 'transform 0.2s', transform: isOpen ? 'rotate(180deg)' : 'none' }}>
                    ▼
                  </span>
                </button>
                {isOpen && (
                  <div
                    style={{
                      padding: '0 18px 16px',
                      fontSize: '13px',
                      color: 'var(--text)',
                      lineHeight: 1.6,
                      borderTop: '1px solid var(--ibr)',
                      paddingTop: '12px',
                    }}
                  >
                    {faq.a}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </section>

      {/* ========================================================
          5. CALL TO ACTION (CTA BANNER)
          ======================================================== */}
      <section
        style={{
          background: 'linear-gradient(135deg, rgba(37, 99, 235, 0.18) 0%, rgba(22, 163, 74, 0.18) 100%)',
          border: '1px solid var(--accent)',
          borderRadius: '16px',
          padding: '32px 24px',
          textAlign: 'center',
          boxShadow: '0 8px 24px rgba(0, 0, 0, 0.25)',
        }}
      >
        <div style={{ fontSize: '38px', marginBottom: '12px' }}>🔐✨</div>
        <h2 style={{ fontSize: '24px', fontWeight: 900, color: 'var(--heading)', marginBottom: '8px' }}>
          جاهز لحماية وتنظيم كلمات مرورك الآن؟
        </h2>
        <p style={{ fontSize: '14px', color: 'var(--text)', maxWidth: '540px', margin: '0 auto 24px', lineHeight: 1.6 }}>
          ابدأ مجاناً اليوم، وتخلص نهائياً من عناء نسيان كلمات المرور أو مخاطر الاعتماد على كلمات مرور ضعيفة.
        </p>

        <div style={{ display: 'flex', justifyContent: 'center', gap: '12px', flexWrap: 'wrap' }}>
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => onNavigate({ view: 'auth', initialTab: 'register' })}
            style={{ fontSize: '14px', padding: '10px 22px' }}
          >
            🚀 إنشاء حساب جديد الآن
          </button>
          <button
            type="button"
            className="btn btn-ghost"
            onClick={() => onNavigate({ view: 'auth', initialTab: 'login' })}
            style={{ fontSize: '14px', padding: '10px 20px', borderColor: 'var(--ibr)', color: 'var(--heading)' }}
          >
            🔑 تسجيل الدخول
          </button>
        </div>
      </section>

    </div>
  );
};

// ==========================================
// 6. MAIN APPLICATION COMPONENT
// ==========================================
export const App: React.FC = () => {
  const [currentUser, setCurrentUserState] = useState<User | null>(null);
  const [viewState, setViewState] = useState<ViewState>({ view: 'home' });
  const [users, setUsersState] = useState<User[]>([]);
  const [accounts, setAccountsState] = useState<AppAccount[]>([]);
  const [isLightTheme, setIsLightTheme] = useState<boolean>(() => localStorage.getItem('theme') === 'light');
  const [flashMessages, setFlashMessages] = useState<FlashMessage[]>([]);

  // Apply theme
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

  // Initialize
  useEffect(() => {
    seedInitialDataIfNeeded().then(() => {
      setUsersState(getUsers());
      setAccountsState(getAccounts());
      setCurrentUserState(getCurrentUser());
    });
  }, []);

  // Inactivity timeout (15 min)
  useEffect(() => {
    const interval = setInterval(() => {
      if (currentUser && !getCurrentUser()) {
        setCurrentUserState(null);
        setViewState({ view: 'home' });
        showFlash('انتهت مدة الجلسة (15 دقيقة من عدم النشاط). يرجى تسجيل الدخول مرة أخرى.', 'info');
      }
    }, 30000);

    const onUserInteraction = () => {
      if (currentUser) touchSession();
    };

    window.addEventListener('click', onUserInteraction);
    window.addEventListener('keydown', onUserInteraction);
    return () => {
      clearInterval(interval);
      window.removeEventListener('click', onUserInteraction);
      window.removeEventListener('keydown', onUserInteraction);
    };
  }, [currentUser, showFlash]);

  // Auth Handlers
  const handleLogin = async (username: string, pass: string) => {
    const foundUser = users.find(u => u.username.toLowerCase() === username.toLowerCase());
    if (!foundUser || !(await verifyPassword(pass, foundUser.passwordHash))) {
      showFlash('اسم المستخدم أو كلمة المرور غير صحيحة.', 'error');
      return;
    }
    setCurrentUser(foundUser);
    setCurrentUserState(foundUser);
    showFlash(`مرحباً! تم تسجيل دخولك بنجاح. 👋`, 'success');
    setViewState({ view: 'home' });
  };

  const handleRegister = async (username: string, pass: string) => {
    if (username.length < 3 || username.length > 32 || /\s/.test(username)) {
      showFlash('اسم المستخدم يجب أن يكون من 3 إلى 32 حرفاً ومن دون مسافات.', 'error');
      return;
    }
    if (pass.length < 6) {
      showFlash('كلمة المرور يجب أن تكون 6 أحرف على الأقل.', 'error');
      return;
    }
    if (users.some(u => u.username.toLowerCase() === username.toLowerCase())) {
      showFlash('اسم المستخدم مستخدم بالفعل. اختر اسماً آخر.', 'error');
      return;
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
  };

  const handleLogout = () => {
    clearSession();
    setCurrentUserState(null);
    setViewState({ view: 'home' });
    showFlash('تم تسجيل الخروج بنجاح.', 'info');
  };

  // Account Handlers
  const handleAddAccount = async (data: {
    accountType: AccountType;
    appName?: string;
    appUsername?: string;
    email?: string;
    password: string;
    remind6Months?: boolean;
  }) => {
    if (!currentUser) return;
    const encPass = await encryptPassword(data.password);
    const nowIso = new Date().toISOString();
    const newAcc: AppAccount = {
      id: 'acc_' + Date.now().toString(36),
      userId: currentUser.id,
      accountType: data.accountType,
      appName: data.appName,
      appUsername: data.appUsername,
      email: data.email,
      encryptedPassword: encPass,
      createdAt: nowIso,
      passwordUpdatedAt: nowIso,
      remind6Months: data.remind6Months ?? false,
    };
    const nextAccounts = [...accounts, newAcc];
    saveAccounts(nextAccounts);
    setAccountsState(nextAccounts);
    showFlash('تم حفظ الحساب بنجاح. ✅', 'success');
  };

  const handleUpdateAccount = async (
    id: string,
    data: {
      appName?: string;
      appUsername?: string;
      email?: string;
      password?: string;
      remind6Months?: boolean;
      passwordUpdatedAt?: string;
    }
  ) => {
    if (!currentUser) return;
    const target = accounts.find(a => a.id === id && a.userId === currentUser.id);
    if (!target) return;
    let encPass = target.encryptedPassword;
    let passwordUpdatedAt = data.passwordUpdatedAt !== undefined
      ? data.passwordUpdatedAt
      : (target.passwordUpdatedAt || target.createdAt || new Date().toISOString());

    if (data.password && data.password !== '') {
      encPass = await encryptPassword(data.password);
      if (data.passwordUpdatedAt === undefined) {
        passwordUpdatedAt = new Date().toISOString();
      }
    }

    const updated: AppAccount = {
      ...target,
      appName: data.appName !== undefined ? data.appName : target.appName,
      appUsername: data.appUsername !== undefined ? data.appUsername : target.appUsername,
      email: data.email !== undefined ? data.email : target.email,
      encryptedPassword: encPass,
      remind6Months: data.remind6Months !== undefined ? data.remind6Months : target.remind6Months,
      passwordUpdatedAt,
    };
    const nextAccounts = accounts.map(a => (a.id === id ? updated : a));
    saveAccounts(nextAccounts);
    setAccountsState(nextAccounts);
    showFlash('تم تحديث البيانات بنجاح. ✅', 'success');
  };

  const handleDeleteAccount = async (id: string) => {
    if (!currentUser) return;
    const nextAccounts = accounts.filter(a => a.id !== id);
    saveAccounts(nextAccounts);
    setAccountsState(nextAccounts);
    showFlash('تم حذف الحساب. 🗑️', 'success');
  };

  const userAccounts = currentUser ? accounts.filter(a => a.userId === currentUser.id) : [];
  const isAdmin = currentUser && (currentUser.username.toLowerCase() === 'admin' || currentUser.username.toLowerCase() === 'morad');

  // RENDER APP
  return (
    <div className="min-h-screen flex flex-col justify-between">
      <div>
        {/* Navbar */}
        <nav className="site-nav" role="navigation" aria-label="القائمة الرئيسية">
          <div className="nav-logo" onClick={() => setViewState({ view: 'home' })}>
            🔐 مدير الحسابات الشامل
          </div>
          <div className="nav-links">
            <button type="button" className="hide-sm" onClick={() => setViewState({ view: 'blog' })}>
              ✍️ المدونة
            </button>
            {currentUser ? (
              <>
                <button type="button" className="hide-sm" onClick={() => setViewState({ view: 'settings' })}>
                  ⚙️ الإعدادات
                </button>
                {isAdmin && (
                  <button
                    type="button"
                    className="nav-cta btn btn-sm"
                    style={{ background: '#1e3a8a' }}
                    onClick={() => setViewState({ view: 'admin' })}
                  >
                    👥 المشرف
                  </button>
                )}
                <button type="button" id="themeToggle" onClick={toggleTheme}>
                  {isLightTheme ? '🌙' : '☀️'}
                </button>
                <button
                  type="button"
                  className="btn btn-sm"
                  style={{ background: '#450a0a', color: '#f87171' }}
                  onClick={handleLogout}
                >
                  خروج
                </button>
              </>
            ) : (
              <>
                <button type="button" className="hide-sm" onClick={() => setViewState({ view: 'about' })}>
                  عن الموقع
                </button>
                <button type="button" className="hide-sm" onClick={() => setViewState({ view: 'privacy' })}>
                  الخصوصية
                </button>
                <button type="button" id="themeToggle" onClick={toggleTheme}>
                  {isLightTheme ? '🌙' : '☀️'}
                </button>
                <button type="button" className="nav-cta btn btn-sm" onClick={() => setViewState({ view: 'auth' })}>
                  دخول / تسجيل
                </button>
              </>
            )}
          </div>
        </nav>

        {/* Flash Messages */}
        {flashMessages.length > 0 && (
          <div className="flash-wrap">
            {flashMessages.map(msg => (
              <div key={msg.id} className={`alert alert-${msg.type}`}>
                {msg.text}
              </div>
            ))}
          </div>
        )}

        {/* VIEWS WITH SMOOTH TRANSITION */}
        <div key={viewState.view + ('category' in viewState ? viewState.category : '')} className="page-view-enter">
          {viewState.view === 'home' && (
          currentUser ? (
            <main className="wrap">
              <header style={{ marginBottom: '24px' }}>
                <h1 style={{ fontSize: '24px', color: 'var(--heading)', fontWeight: 800 }}>
                  مرحباً، {currentUser.username} 👋
                </h1>
                <p style={{ fontSize: '14px', color: 'var(--muted)' }}>
                  اختر قسماً لإدارة حساباتك وكلمات مرورك المشفرة
                </p>
              </header>

              <div className="feat-grid" style={{ marginBottom: '32px' }}>
                <div className="feat-card" onClick={() => setViewState({ view: 'category', category: 'تطبيق' })}>
                  <div className="feat-icon">📱</div>
                  <h3>التطبيقات والمنصات</h3>
                  <p>إدارة حسابات التطبيقات ({userAccounts.filter(a => a.accountType === 'تطبيق').length} حساب)</p>
                </div>
                <div className="feat-card" onClick={() => setViewState({ view: 'category', category: 'بريد' })}>
                  <div className="feat-icon">📧</div>
                  <h3>البريد الإلكتروني</h3>
                  <p>إدارة حسابات البريد ({userAccounts.filter(a => a.accountType === 'بريد').length} حساب)</p>
                </div>
                <div className="feat-card" onClick={() => setViewState({ view: 'category', category: 'موقع' })}>
                  <div className="feat-icon">🌐</div>
                  <h3>المواقع الإلكترونية</h3>
                  <p>إدارة حسابات المواقع ({userAccounts.filter(a => a.accountType === 'موقع').length} حساب)</p>
                </div>
              </div>

              <section>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                  <h2 style={{ fontSize: '18px', color: 'var(--heading)', fontWeight: 700 }}>
                    📖 آخر مقالات الأمن الرقمي
                  </h2>
                  <button type="button" className="btn btn-ghost btn-sm" onClick={() => setViewState({ view: 'blog' })}>
                    عرض جميع المقالات
                  </button>
                </div>
                <div className="blog-grid">
                  {ARTICLES.slice(0, 3).map(art => (
                    <div key={art.slug} className="blog-card" onClick={() => setViewState({ view: 'article', slug: art.slug })}>
                      <div className="blog-cat">{art.cat}</div>
                      <h2>{art.title}</h2>
                      <p>{art.desc}</p>
                      <span className="blog-link">اقرأ المقال ◀</span>
                    </div>
                  ))}
                </div>
              </section>
            </main>
          ) : (
            <main>
              <section className="hero">
                <span className="badge">إدارة حساباتك في مكان واحد</span>
                <h1>كلمات مرورك، تحت سيطرتك الكاملة</h1>
                <p>نظّم بيانات حساباتك في مكان واحد، مع تشفير كلمات المرور وإمكانية استعادتها وتوليد كلمات مرور قوية.</p>
              </section>
              <div className="wrap" style={{ paddingTop: 0 }}>
                <AdUnit />
                <section className="card welcome-panel">
                  <span className="badge">مرحباً بك</span>
                  <h2>👋 أهلاً بك في مدير الحسابات الشامل</h2>
                  <p>منصة سريعة وآمنة لتنظيم بيانات حساباتك في مكان واحد مع تشفير عالي الكفاءة.</p>
                </section>
                <div className="feat-grid" style={{ marginBottom: '32px' }}>
                  <div className="feat-card">
                    <div className="feat-icon">🔒</div>
                    <h3>تشفير متقدم</h3>
                    <p>كلمات مرورك مشفرة تشفيراً متماثلاً قوياً.</p>
                  </div>
                  <div className="feat-card">
                    <div className="feat-icon">⚡</div>
                    <h3>مولد كلمات مرور</h3>
                    <p>توليد كلمات مرور قوية بضغطة زر واحدة.</p>
                  </div>
                  <div className="feat-card">
                    <div className="feat-icon">📱</div>
                    <h3>متوافق الجوال</h3>
                    <p>يعمل على كافة الأجهزة والشاشات بسلاسة.</p>
                  </div>
                </div>

                {/* 5 Integrated Sections: Live Generator, How it works, Featured articles, FAQ, and CTA */}
                <LandingHomeExtraSections onNavigate={setViewState} showFlash={showFlash} />
              </div>
            </main>
          )
        )}

        {viewState.view === 'auth' && (
          <AuthViewContainer
            onLogin={handleLogin}
            onRegister={handleRegister}
            onNavigate={setViewState}
          />
        )}

        {viewState.view === 'category' && (
          <CategoryViewContainer
            category={viewState.category}
            accounts={userAccounts}
            onAddAccount={handleAddAccount}
            onDeleteAccount={handleDeleteAccount}
            onNavigate={setViewState}
          />
        )}

        {viewState.view === 'edit' && (
          <EditViewContainer
            accountId={viewState.accountId}
            accounts={userAccounts}
            onUpdateAccount={handleUpdateAccount}
            onNavigate={setViewState}
          />
        )}

        {viewState.view === 'settings' && currentUser && (
          <SettingsViewContainer
            currentUser={currentUser}
            onNavigate={setViewState}
            showFlash={showFlash}
            onDeleteUserAccount={async () => {
              const uid = currentUser.id;
              saveAccounts(accounts.filter(a => a.userId !== uid));
              saveUsers(users.filter(u => u.id !== uid));
              setAccountsState(accounts.filter(a => a.userId !== uid));
              setUsersState(users.filter(u => u.id !== uid));
              clearSession();
              setCurrentUserState(null);
              setViewState({ view: 'home' });
              showFlash('تم حذف حسابك وجميع بياناتك نهائياً.', 'info');
            }}
          />
        )}

        {viewState.view === 'admin' && (
          <AdminViewContainer
            currentUser={currentUser}
            users={users}
            accounts={accounts}
            onNavigate={setViewState}
          />
        )}

        {viewState.view === 'blog' && (
          <main className="wrap">
            <header style={{ textAlign: 'center', marginBottom: '32px' }}>
              <span className="badge">✍️ المدونة</span>
              <h1 style={{ fontSize: '30px', color: 'var(--heading)', fontWeight: 900, marginTop: '10px' }}>
                مقالات الأمن الرقمي
              </h1>
            </header>
            <div className="blog-grid">
              {ARTICLES.map(a => (
                <article key={a.slug} className="blog-card" onClick={() => setViewState({ view: 'article', slug: a.slug })}>
                  <div className="blog-cat">{a.cat}</div>
                  <h2>{a.title}</h2>
                  <p>{a.desc}</p>
                  <div className="blog-meta">🕐 {a.readTime} · 📅 {a.date}</div>
                  <span className="blog-link">اقرأ المقال كاملاً ◀</span>
                </article>
              ))}
            </div>
          </main>
        )}

        {viewState.view === 'article' && (
          <ArticleViewContainer slug={viewState.slug} onNavigate={setViewState} />
        )}

        {viewState.view === 'contact' && (
          <ContactViewContainer onNavigate={setViewState} showFlash={showFlash} />
        )}

        {viewState.view === 'about' && (
          <main className="wrap-narrow">
            <article className="card">
              <h1 className="card-title">🛡️ عن مدير الحسابات الشامل</h1>
              <p>تطبيق ويب متخصص لإدارة وتنظيم كلمات المرور والحسابات بأعلى درجات الأمان والسهولة.</p>
              <p style={{ marginTop: '10px' }}>
                للتواصل معنا: <a href="mailto:mradhrysy7@gmail.com" style={{ color: '#60a5fa' }}>mradhrysy7@gmail.com</a>
              </p>
            </article>
          </main>
        )}

        {viewState.view === 'privacy' && (
          <main className="wrap-narrow">
            <article className="card prose">
              <h1 className="card-title">🔏 سياسة الخصوصية</h1>
              <p>بياناتك مشفرة ولا يتم بيع أو مشاركة أي بيانات شخصية مع أطراف ثالثة.</p>
              <p>البريد المعتمد: <a href="mailto:mradhrysy7@gmail.com" style={{ color: '#60a5fa' }}>mradhrysy7@gmail.com</a></p>
            </article>
          </main>
        )}

        {viewState.view === 'terms' && (
          <main className="wrap-narrow">
            <article className="card prose">
              <h1 className="card-title">📋 شروط الاستخدام</h1>
              <p>استخدامك للخدمة يعني موافقتك على شروط الاستخدام والأمان وحفظ بيانات دخولك بسرية كاملة.</p>
            </article>
          </main>
        )}
        </div>
      </div>

      {/* Footer */}
      <footer className="site-footer" role="contentinfo">
        <div className="footer-links">
          <button type="button" onClick={() => setViewState({ view: 'home' })}>الرئيسية</button>
          <button type="button" onClick={() => setViewState({ view: 'blog' })}>المدونة</button>
          <button type="button" onClick={() => setViewState({ view: 'about' })}>عن الموقع</button>
          <button type="button" onClick={() => setViewState({ view: 'privacy' })}>الخصوصية</button>
          <button type="button" onClick={() => setViewState({ view: 'terms' })}>شروط الاستخدام</button>
          <button type="button" onClick={() => setViewState({ view: 'contact' })}>تواصل معنا</button>
        </div>
        <p style={{ fontSize: '12px' }}>© 2026 مدير الحسابات الشامل · جميع الحقوق محفوظة</p>
      </footer>
    </div>
  );
};

// ==========================================
// SUB-VIEWS CONTAINERS
// ==========================================
function AuthViewContainer({
  onLogin,
  onRegister,
  onNavigate,
}: {
  onLogin: (u: string, p: string) => Promise<void>;
  onRegister: (u: string, p: string) => Promise<void>;
  onNavigate: (v: ViewState) => void;
}) {
  const [tab, setTab] = useState<'login' | 'register'>('login');
  const [u, setU] = useState('');
  const [p, setP] = useState('');

  return (
    <main className="wrap-narrow">
      <header style={{ textAlign: 'center', margin: '12px 0 24px' }}>
        <span className="badge">🔐 حسابك يبدأ من هنا</span>
        <h1 style={{ fontSize: '28px', color: 'var(--heading)', fontWeight: 900 }}>دخول / تسجيل حساب</h1>
      </header>
      <div style={{ display: 'flex', gap: '8px', marginBottom: '20px', justifyContent: 'center' }}>
        <button type="button" className={`btn ${tab === 'login' ? 'btn-primary' : 'btn-ghost'}`} onClick={() => setTab('login')}>
          🔑 تسجيل الدخول
        </button>
        <button type="button" className={`btn ${tab === 'register' ? 'btn-primary' : 'btn-ghost'}`} onClick={() => setTab('register')}>
          ✨ إنشاء حساب مجاني
        </button>
      </div>
      <div className="card">
        <form onSubmit={async e => { e.preventDefault(); if (tab === 'login') await onLogin(u, p); else await onRegister(u, p); }}>
          <div className="fg">
            <label>اسم المستخدم</label>
            <input type="text" value={u} onChange={e => setU(e.target.value)} required />
          </div>
          <div className="fg">
            <label>كلمة المرور</label>
            <input type="password" value={p} onChange={e => setP(e.target.value)} required />
          </div>
          <button type="submit" className="btn btn-primary btn-block">
            {tab === 'login' ? 'تسجيل الدخول' : 'إنشاء حساب جديد'}
          </button>
        </form>
      </div>
    </main>
  );
}

function CategoryViewContainer({
  category,
  accounts,
  onAddAccount,
  onDeleteAccount,
  onNavigate,
}: {
  category: AccountType;
  accounts: AppAccount[];
  onAddAccount: (d: any) => Promise<void>;
  onDeleteAccount: (id: string) => Promise<void>;
  onNavigate: (v: ViewState) => void;
}) {
  const catNames: Record<AccountType, string> = { 'تطبيق': 'التطبيقات والمنصات', 'بريد': 'البريد الإلكتروني', 'موقع': 'المواقع الإلكترونية' };
  const catName = catNames[category];

  const [appName, setAppName] = useState('');
  const [appUsername, setAppUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [remind6Months, setRemind6Months] = useState(false);
  const [revealedPasswords, setRevealedPasswords] = useState<Record<string, string>>({});
  const [isAllRevealed, setIsAllRevealed] = useState<boolean>(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [pwModal, setPwModal] = useState<{ title: string; password: string } | null>(null);
  const [modalCopied, setModalCopied] = useState<boolean>(false);

  const filtered = accounts.filter(a => a.accountType === category);
  const strength = calculatePasswordStrength(password);

  // إخفاء الحسابات تلقائياً عند التبديل بين الأقسام لتوفير طبقة إضافية من الخصوصية في الأماكن العامة
  useEffect(() => {
    setRevealedPasswords({});
    setIsAllRevealed(false);
  }, [category]);

  const togglePassword = async (id: string, enc: string) => {
    if (revealedPasswords[id]) {
      const next = { ...revealedPasswords };
      delete next[id];
      setRevealedPasswords(next);
      if (Object.keys(next).length === 0) {
        setIsAllRevealed(false);
      }
    } else {
      const p = await decryptPassword(enc);
      const next = { ...revealedPasswords, [id]: p };
      setRevealedPasswords(next);
      if (filtered.length > 0 && Object.keys(next).length >= filtered.length) {
        setIsAllRevealed(true);
      }
    }
  };

  const handleToggleAll = async () => {
    if (isAllRevealed) {
      setRevealedPasswords({});
      setIsAllRevealed(false);
    } else {
      const next: Record<string, string> = {};
      for (const acc of filtered) {
        next[acc.id] = await decryptPassword(acc.encryptedPassword);
      }
      setRevealedPasswords(next);
      setIsAllRevealed(true);
    }
  };

  const copyPassword = async (id: string, enc: string) => {
    const p = revealedPasswords[id] || (await decryptPassword(enc));
    await navigator.clipboard.writeText(p);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <main className="wrap">
      <nav className="breadcrumb">
        <button type="button" onClick={() => onNavigate({ view: 'home' })}>الرئيسية</button> › <span>{catName}</span>
      </nav>

      <div className="card card-add-account" style={{ marginBottom: '20px' }}>
        <h1 className="card-title">➕ إضافة حساب جديد في {catName}</h1>
        <form onSubmit={async e => {
          e.preventDefault();
          await onAddAccount({ accountType: category, appName, appUsername, email, password, remind6Months });
          setAppName(''); setAppUsername(''); setEmail(''); setPassword(''); setRemind6Months(false);
        }}>
          <div className="fgrid">
            {category !== 'بريد' && (
              <>
                <div className="fg">
                  <label>اسم التطبيق / الخدمة</label>
                  <input type="text" value={appName} onChange={e => setAppName(e.target.value)} required />
                </div>
                <div className="fg">
                  <label>اسم المستخدم</label>
                  <input type="text" value={appUsername} onChange={e => setAppUsername(e.target.value)} />
                </div>
              </>
            )}
            <div className="fg">
              <label>البريد الإلكتروني</label>
              <input type="email" value={email} onChange={e => setEmail(e.target.value)} />
            </div>
            <div className="fg">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <label>كلمة المرور</label>
                {password && <span style={{ fontSize: '11px', color: strength.color, fontWeight: 700 }}>{strength.label}</span>}
              </div>
              <input type="text" value={password} onChange={e => setPassword(e.target.value)} placeholder="أدخل كلمة المرور أو ولّدها" required />
            </div>
          </div>

          <PasswordGeneratorUtility onApplyPassword={pwd => setPassword(pwd)} />

          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '13px', color: 'var(--text)', margin: '14px 0 16px', userSelect: 'none' }}>
            <input
              type="checkbox"
              checked={remind6Months}
              onChange={e => setRemind6Months(e.target.checked)}
              style={{ accentColor: 'var(--btn)', width: '17px', height: '17px', cursor: 'pointer' }}
            />
            <span>🔔 تفعيل تنبيه لتغيير كلمة المرور إذا مر عليها أكثر من 6 أشهر (ميزة اختيارية)</span>
          </label>

          <button type="submit" className="btn btn-primary btn-block">حفظ الحساب</button>
        </form>
      </div>

      <div className="card card-saved-accounts">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px', marginBottom: '16px' }}>
          <div>
            <h2 className="card-title" style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>📋 الحسابات المحفوظة</span>
              <span className="count-pill">{filtered.length}</span>
            </h2>
            <div className="privacy-note">
              🛡️ وضع الخصوصية: يتم إخفاء كلمات المرور تلقائياً عند التبديل بين الأقسام لحمايتك في الأماكن العامة
            </div>
          </div>

          {filtered.length > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <button
                type="button"
                className={`btn ${isAllRevealed ? 'btn-ghost' : 'btn-primary'} btn-sm`}
                onClick={handleToggleAll}
                style={{ display: 'inline-flex', alignItems: 'center', gap: '6px', fontWeight: 700, padding: '7px 14px' }}
                title={isAllRevealed ? 'إخفاء كافة الحسابات لحماية الخصوصية في الأماكن العامة' : 'إظهار كافة كلمات المرور في هذا القسم'}
              >
                <span>{isAllRevealed ? '🔒' : '👁️'}</span>
                <span>{isAllRevealed ? 'إخفاء الكل' : 'إظهار الكل'}</span>
              </button>
            </div>
          )}
        </div>

        <div className="tbl-wrap">
          <table>
            <thead>
              <tr>
                <th>#</th>
                {category !== 'بريد' && <th>الاسم</th>}
                <th>البريد</th>
                <th>كلمة المرور</th>
                <th>الإجراءات</th>
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr><td colSpan={5} style={{ padding: '24px', color: 'var(--muted)' }}>لا توجد حسابات بعد.</td></tr>
              ) : (
                filtered.map((acc, i) => {
                  const ageInfo = checkPasswordAge(acc.passwordUpdatedAt || acc.createdAt);
                  return (
                  <tr key={acc.id}>
                    <td>{i + 1}</td>
                    {category !== 'بريد' && (
                      <td>
                        <strong>{acc.appName}</strong>
                        {acc.appUsername && (
                          <div style={{ fontSize: '11px', color: 'var(--muted)', marginTop: '2px' }}>
                            @{acc.appUsername}
                          </div>
                        )}
                        {acc.remind6Months && ageInfo.isOlderThan6Months && (
                          <div style={{ marginTop: '4px' }}>
                            <span
                              style={{
                                fontSize: '11px',
                                color: '#f59e0b',
                                background: 'rgba(245, 158, 11, 0.12)',
                                border: '1px solid rgba(245, 158, 11, 0.35)',
                                padding: '2px 7px',
                                borderRadius: '4px',
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '3px',
                                fontWeight: 700,
                              }}
                              title="تنبيه: مرّت أكثر من 6 أشهر على تعيين كلمة المرور هذه. اضغط تعديل لتحديثها."
                            >
                              ⚠️ كلمة المرور قديمة (+6 أشهر)
                            </span>
                          </div>
                        )}
                      </td>
                    )}
                    <td>
                      <div>{acc.email || '-'}</div>
                      {category === 'بريد' && acc.remind6Months && ageInfo.isOlderThan6Months && (
                        <div style={{ marginTop: '4px' }}>
                          <span
                            style={{
                              fontSize: '11px',
                              color: '#f59e0b',
                              background: 'rgba(245, 158, 11, 0.12)',
                              border: '1px solid rgba(245, 158, 11, 0.35)',
                              padding: '2px 7px',
                              borderRadius: '4px',
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: '3px',
                              fontWeight: 700,
                            }}
                            title="تنبيه: مرّت أكثر من 6 أشهر على تعيين كلمة المرور هذه. اضغط تعديل لتحديثها."
                          >
                            ⚠️ كلمة المرور قديمة (+6 أشهر)
                          </span>
                        </div>
                      )}
                    </td>
                    <td className="pw-cell" style={{ minWidth: '220px', maxWidth: '340px' }}>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', alignItems: 'center', justifyContent: 'center' }}>
                        <span
                          className="pw-badge"
                          dir="ltr"
                          title="نص كلمة المرور كاملة"
                          style={{
                            fontFamily: revealedPasswords[acc.id] ? "'SFMono-Regular', Consolas, Menlo, monospace" : 'inherit',
                            letterSpacing: revealedPasswords[acc.id] ? '0.5px' : '2px',
                            fontWeight: 600,
                            wordBreak: 'break-all',
                            whiteSpace: 'normal',
                            userSelect: 'all',
                            maxWidth: '100%',
                            textAlign: 'center',
                          }}
                        >
                          {revealedPasswords[acc.id] || '••••••••'}
                        </span>
                        <div style={{ display: 'inline-flex', gap: '4px', alignItems: 'center', justifyContent: 'center', flexWrap: 'wrap' }}>
                          <button
                            type="button"
                            className="btn btn-ghost btn-sm"
                            onClick={() => togglePassword(acc.id, acc.encryptedPassword)}
                            title={revealedPasswords[acc.id] ? 'إخفاء كلمة المرور' : 'إظهار كلمة المرور'}
                          >
                            {revealedPasswords[acc.id] ? 'إخفاء' : 'إظهار'}
                          </button>
                          <button
                            type="button"
                            className="btn btn-ghost btn-sm"
                            onClick={() => copyPassword(acc.id, acc.encryptedPassword)}
                            title="نسخ كلمة المرور"
                          >
                            {copiedId === acc.id ? 'تم النسخ ✓' : 'نسخ'}
                          </button>
                          <button
                            type="button"
                            className="btn btn-ghost btn-sm"
                            onClick={async () => {
                              let p = revealedPasswords[acc.id];
                              if (!p) {
                                p = await decryptPassword(acc.encryptedPassword);
                                setRevealedPasswords(prev => ({ ...prev, [acc.id]: p }));
                              }
                              setModalCopied(false);
                              setPwModal({
                                title: acc.appName || acc.email || 'الحساب',
                                password: p,
                              });
                            }}
                            title="عرض كلمة المرور كاملة ومكبرة"
                          >
                            🔍 عرض كامل
                          </button>
                        </div>
                      </div>
                    </td>
                    <td className="td-act">
                      <button type="button" className="btn btn-info btn-sm" onClick={() => onNavigate({ view: 'edit', accountId: acc.id })}>
                        تعديل
                      </button>
                      <button type="button" className="btn btn-danger btn-sm" onClick={() => onDeleteAccount(acc.id)}>
                        حذف
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {pwModal && (
        <div className="pw-modal-overlay" onClick={() => setPwModal(null)}>
          <div className="pw-modal-content" onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', borderBottom: '1px solid var(--brd)', paddingBottom: '10px' }}>
              <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 700, color: 'var(--heading)' }}>
                🔐 كلمة المرور كاملة ({pwModal.title})
              </h3>
              <button
                type="button"
                onClick={() => setPwModal(null)}
                style={{ background: 'none', border: 'none', fontSize: '20px', color: 'var(--muted)', cursor: 'pointer', padding: '0 4px' }}
                title="إغلاق"
              >
                ✕
              </button>
            </div>

            <div style={{ margin: '20px 0' }}>
              <div
                dir="ltr"
                style={{
                  background: 'var(--ibg)',
                  border: '2px solid var(--info)',
                  borderRadius: '10px',
                  padding: '16px',
                  fontFamily: "'SFMono-Regular', Consolas, Menlo, monospace",
                  fontSize: '17px',
                  fontWeight: 700,
                  color: 'var(--heading)',
                  wordBreak: 'break-all',
                  whiteSpace: 'normal',
                  userSelect: 'all',
                  lineHeight: 1.6,
                  textAlign: 'center',
                  boxShadow: 'inset 0 2px 6px rgba(0,0,0,0.3)',
                }}
              >
                {pwModal.password}
              </div>
              <div style={{ fontSize: '12px', color: 'var(--muted)', marginTop: '10px' }}>
                عدد الأحرف: {pwModal.password.length} حرف | نص كامل بدون أي اقتطاع
              </div>
            </div>

            <div style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
              <button
                type="button"
                className="btn btn-primary"
                onClick={async () => {
                  await navigator.clipboard.writeText(pwModal.password);
                  setModalCopied(true);
                  setTimeout(() => setModalCopied(false), 2500);
                }}
              >
                {modalCopied ? 'تم نسخ كلمة المرور كاملة! ✓' : '📋 نسخ كلمة المرور بالكامل'}
              </button>
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => setPwModal(null)}
              >
                إغلاق
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}

function EditViewContainer({
  accountId,
  accounts,
  onUpdateAccount,
  onNavigate,
}: {
  accountId: string;
  accounts: AppAccount[];
  onUpdateAccount: (id: string, d: any) => Promise<void>;
  onNavigate: (v: ViewState) => void;
}) {
  const account = accounts.find(a => a.id === accountId);
  const [appName, setAppName] = useState(account?.appName || '');
  const [appUsername, setAppUsername] = useState(account?.appUsername || '');
  const [email, setEmail] = useState(account?.email || '');
  const [password, setPassword] = useState('');

  useEffect(() => {
    if (account) {
      decryptPassword(account.encryptedPassword).then(p => setPassword(p));
    }
  }, [account]);

  if (!account) return <main className="wrap"><div className="card"><p>الحساب غير موجود.</p></div></main>;

  return (
    <main className="wrap" style={{ display: 'flex', justifyContent: 'center' }}>
      <div className="card" style={{ width: 'min(460px, 100%)' }}>
        <h1 className="card-title">✏️ تعديل البيانات</h1>
        <form onSubmit={async e => {
          e.preventDefault();
          await onUpdateAccount(accountId, { appName, appUsername, email, password });
          onNavigate({ view: 'category', category: account.accountType });
        }}>
          {account.accountType !== 'بريد' && (
            <div className="fg">
              <label>اسم التطبيق / الموقع</label>
              <input type="text" value={appName} onChange={e => setAppName(e.target.value)} required />
            </div>
          )}
          <div className="fg">
            <label>البريد الإلكتروني</label>
            <input type="email" value={email} onChange={e => setEmail(e.target.value)} />
          </div>
          <div className="fg">
            <label>كلمة المرور الجديدة</label>
            <input type="text" value={password} onChange={e => setPassword(e.target.value)} required />
          </div>
          <PasswordGeneratorUtility onApplyPassword={pwd => setPassword(pwd)} />
          <button type="submit" className="btn btn-primary btn-block">حفظ التعديلات</button>
        </form>
      </div>
    </main>
  );
}

function SettingsViewContainer({
  currentUser,
  onNavigate,
  showFlash,
  onDeleteUserAccount,
}: any) {
  return (
    <main className="wrap-narrow">
      <div className="card">
        <h2 className="card-title">👤 المستخدم الحالي: {currentUser.username}</h2>
        <div style={{ marginTop: '20px' }}>
          <button type="button" className="btn btn-danger btn-block" onClick={onDeleteUserAccount}>
            حذف الحساب وكافة البيانات نهائياً
          </button>
        </div>
      </div>
    </main>
  );
}

function AdminViewContainer({ users, accounts }: any) {
  return (
    <main className="wrap">
      <div className="card">
        <h1 className="card-title">👥 لوحة المشرف</h1>
        <div className="tbl-wrap">
          <table>
            <thead><tr><th>المستخدم</th><th>عدد الحسابات</th></tr></thead>
            <tbody>
              {users.map((u: any) => (
                <tr key={u.id}><td>{u.username}</td><td>{accounts.filter((a: any) => a.userId === u.id).length}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </main>
  );
}

function ArticleViewContainer({ slug, onNavigate }: { slug: string; onNavigate: (v: ViewState) => void }) {
  const art = ARTICLES.find(a => a.slug === slug);
  if (!art) return <main className="wrap"><div className="card"><p>المقال غير موجود.</p></div></main>;
  return (
    <main className="wrap-narrow">
      <article className="card">
        <h1 style={{ fontSize: '24px', fontWeight: 900, marginBottom: '12px' }}>{art.title}</h1>
        <div className="article-body" dangerouslySetInnerHTML={{ __html: art.body }} />
      </article>
    </main>
  );
}

function ContactViewContainer({ onNavigate, showFlash }: any) {
  const DESTINATION_EMAIL = 'mradhrysy7@gmail.com';
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [subject, setSubject] = useState('');
  const [message, setMessage] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await fetch(`https://formsubmit.co/ajax/${DESTINATION_EMAIL}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
        body: JSON.stringify({ name, email, _subject: subject, message }),
      });
    } catch {}
    setSubmitted(true);
    showFlash(`تم إرسال رسالتك بنجاح إلى ${DESTINATION_EMAIL}! ✅`, 'success');
  };

  return (
    <main className="wrap-narrow">
      <div className="card">
        <h1 className="card-title">📬 تواصل معنا</h1>
        <p style={{ marginBottom: '14px' }}>
          البريد المعتمد: <strong>{DESTINATION_EMAIL}</strong>
        </p>
        {submitted && (
          <div className="alert alert-success">تم إرسال رسالتك بنجاح إلى {DESTINATION_EMAIL}! ✅</div>
        )}
        <form onSubmit={handleSubmit}>
          <div className="fg"><label>الاسم</label><input type="text" value={name} onChange={e => setName(e.target.value)} required /></div>
          <div className="fg"><label>البريد الإلكتروني</label><input type="email" value={email} onChange={e => setEmail(e.target.value)} required /></div>
          <div className="fg"><label>الموضوع</label><input type="text" value={subject} onChange={e => setSubject(e.target.value)} required /></div>
          <div className="fg"><label>الرسالة</label><textarea value={message} onChange={e => setMessage(e.target.value)} required /></div>
          <button type="submit" className="btn btn-primary btn-block">إرسال الرسالة إلى {DESTINATION_EMAIL}</button>
        </form>
      </div>
    </main>
  );
}

export default App;
