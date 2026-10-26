// Cryptographic utilities using Web Crypto API

// Fallback constant encryption salt/key when running client-side
const APP_ENCRYPTION_SALT = 'manager_fernet_aes_2026_secure_key';

async function deriveKeyLegacy(saltString: string = APP_ENCRYPTION_SALT): Promise<CryptoKey> {
  const enc = new TextEncoder();
  const rawKey = enc.encode(saltString);
  const hash = await crypto.subtle.digest('SHA-256', rawKey);
  return crypto.subtle.importKey('raw', hash, { name: 'AES-GCM' }, false, ['encrypt', 'decrypt']);
}

async function deriveKey(saltString: string = APP_ENCRYPTION_SALT): Promise<CryptoKey> {
  const enc = new TextEncoder();
  const keyMaterial = await crypto.subtle.importKey(
    'raw',
    enc.encode(saltString),
    { name: 'PBKDF2' },
    false,
    ['deriveKey']
  );
  return crypto.subtle.deriveKey(
    {
      name: 'PBKDF2',
      salt: enc.encode('pwm_aes_gcm_salt_2026'),
      iterations: 100000,
      hash: 'SHA-256'
    },
    keyMaterial,
    { name: 'AES-GCM', length: 256 },
    false,
    ['encrypt', 'decrypt']
  );
}

/**
 * Hash user master password using SHA-256 with fixed app salt
 */
export async function hashPassword(plainText: string): Promise<string> {
  if (!plainText) return '';
  try {
    const enc = new TextEncoder();
    const data = enc.encode(plainText + '::' + APP_ENCRYPTION_SALT);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  } catch (e) {
    // Basic fallback if subtle crypto unavailable
    let hash = 0;
    for (let i = 0; i < plainText.length; i++) {
      const char = plainText.charCodeAt(i);
      hash = (hash << 5) - hash + char;
      hash |= 0;
    }
    return 'fallback:' + Math.abs(hash).toString(16);
  }
}

/**
 * Verify user password
 */
export async function verifyPassword(inputPassword: string, storedHash: string): Promise<boolean> {
  const computed = await hashPassword(inputPassword);
  return computed === storedHash;
}

/**
 * Encrypt stored password using AES-GCM
 */
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
  } catch (err) {
    // Fallback obfuscation if Web Crypto not fully supported
    return 'b64:' + btoa(encodeURIComponent(plainText));
  }
}

/**
 * Decrypt stored password
 */
export async function decryptPassword(cipherText: string): Promise<string> {
  if (!cipherText) return '';
  try {
    if (cipherText.startsWith('aes-gcm:')) {
      const parts = cipherText.split(':');
      if (parts.length === 3) {
        const iv = Uint8Array.from(atob(parts[1]), c => c.charCodeAt(0));
        const cipherData = Uint8Array.from(atob(parts[2]), c => c.charCodeAt(0));
        try {
          const key = await deriveKey();
          const decrypted = await crypto.subtle.decrypt({ name: 'AES-GCM', iv }, key, cipherData);
          return new TextDecoder().decode(decrypted);
        } catch {
          const legacyKey = await deriveKeyLegacy();
          const decrypted = await crypto.subtle.decrypt({ name: 'AES-GCM', iv }, legacyKey, cipherData);
          return new TextDecoder().decode(decrypted);
        }
      }
    }
    if (cipherText.startsWith('b64:')) {
      return decodeURIComponent(atob(cipherText.slice(4)));
    }
    return cipherText;
  } catch (err) {
    console.error('Decryption error:', err);
    return '[خطأ في فك التشفير]';
  }
}

export interface PasswordGeneratorOptions {
  length?: number;
  includeUppercase?: boolean;
  includeLowercase?: boolean;
  includeNumbers?: boolean;
  includeSymbols?: boolean;
}

const UPPERCASE_CHARS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
const LOWERCASE_CHARS = 'abcdefghijklmnopqrstuvwxyz';
const NUMBER_CHARS = '0123456789';
const SYMBOL_CHARS = '!@#$%^&*()_+-=[]{}|;:,.<>?';

/**
 * Returns a cryptographically secure random integer in range [0, max - 1]
 */
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

/**
 * Generates a cryptographically strong, random password using Web Crypto API
 */
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

  // Fallback if no sets chosen
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

export interface PasswordStrength {
  score: number; // 1 to 4
  label: string;
  color: string;
  percentage: number;
}

/**
 * Evaluates password strength based on length, complexity, and character entropy
 */
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
