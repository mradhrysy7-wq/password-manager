import React, { useState, useEffect, useCallback } from 'react';
import {
  generateSecurePassword,
  calculatePasswordStrength,
  PasswordGeneratorOptions,
} from '../utils/crypto';

interface PasswordGeneratorUtilityProps {
  onApplyPassword: (password: string) => void;
  initialIsOpen?: boolean;
}

export const PasswordGeneratorUtility: React.FC<PasswordGeneratorUtilityProps> = ({
  onApplyPassword,
  initialIsOpen = false,
}) => {
  const [isOpen, setIsOpen] = useState(initialIsOpen);
  const [length, setLength] = useState(16);
  const [includeUppercase, setIncludeUppercase] = useState(true);
  const [includeLowercase, setIncludeLowercase] = useState(true);
  const [includeNumbers, setIncludeNumbers] = useState(true);
  const [includeSymbols, setIncludeSymbols] = useState(true);

  const [generatedPassword, setGeneratedPassword] = useState('');
  const [copied, setCopied] = useState(false);

  const handleGenerate = useCallback(() => {
    const opts: PasswordGeneratorOptions = {
      length,
      includeUppercase,
      includeLowercase,
      includeNumbers,
      includeSymbols,
    };
    const pwd = generateSecurePassword(opts);
    setGeneratedPassword(pwd);
  }, [length, includeUppercase, includeLowercase, includeNumbers, includeSymbols]);

  // Generate on initial open or option change
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
    } catch {
      // fallback
    }
  };

  const handleApply = () => {
    if (!generatedPassword) return;
    onApplyPassword(generatedPassword);
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
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--muted)',
            fontSize: '13px',
            cursor: 'pointer',
          }}
        >
          ✕ إغلاق
        </button>
      </div>

      {/* Generated Password Monospace Box */}
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
          title="نسخ إلى الحافظة"
          style={{ padding: '4px 8px', fontSize: '12px' }}
        >
          {copied ? 'تم النسخ ✓' : 'نسخ'}
        </button>

        <button
          type="button"
          className="btn btn-primary btn-sm"
          onClick={handleApply}
          title="تطبيق على النموذج"
          style={{ padding: '4px 10px', fontSize: '12px' }}
        >
          استخدام ✓
        </button>
      </div>

      {/* Strength indicator */}
      <div style={{ marginBottom: '12px' }}>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            fontSize: '11px',
            color: 'var(--muted)',
            marginBottom: '4px',
          }}
        >
          <span>قوة كلمة المرور:</span>
          <span style={{ fontWeight: 700, color: strength.color }}>{strength.label}</span>
        </div>
        <div
          style={{
            height: '5px',
            width: '100%',
            background: 'var(--card)',
            borderRadius: '3px',
            overflow: 'hidden',
          }}
        >
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

      {/* Length Slider */}
      <div style={{ marginBottom: '12px' }}>
        <div
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            fontSize: '12px',
            color: 'var(--muted)',
            marginBottom: '4px',
          }}
        >
          <label htmlFor="pwd-length">طول كلمة المرور:</label>
          <span style={{ fontWeight: 700, color: 'var(--heading)' }}>{length} حرفاً</span>
        </div>
        <input
          id="pwd-length"
          type="range"
          min={8}
          max={32}
          value={length}
          onChange={e => {
            const val = parseInt(e.target.value, 10);
            setLength(val);
          }}
          onMouseUp={handleGenerate}
          onTouchEnd={handleGenerate}
          style={{
            width: '100%',
            cursor: 'pointer',
            accentColor: 'var(--btn)',
          }}
        />
      </div>

      {/* Options Checkboxes */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
          gap: '8px',
          fontSize: '12px',
          color: 'var(--text)',
        }}
      >
        <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
          <input
            type="checkbox"
            checked={includeUppercase}
            onChange={e => {
              setIncludeUppercase(e.target.checked);
            }}
            style={{ accentColor: 'var(--btn)' }}
          />
          <span>أحرف كبيرة (A-Z)</span>
        </label>

        <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
          <input
            type="checkbox"
            checked={includeLowercase}
            onChange={e => {
              setIncludeLowercase(e.target.checked);
            }}
            style={{ accentColor: 'var(--btn)' }}
          />
          <span>أحرف صغيرة (a-z)</span>
        </label>

        <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
          <input
            type="checkbox"
            checked={includeNumbers}
            onChange={e => {
              setIncludeNumbers(e.target.checked);
            }}
            style={{ accentColor: 'var(--btn)' }}
          />
          <span>أرقام (0-9)</span>
        </label>

        <label style={{ display: 'flex', alignItems: 'center', gap: '6px', cursor: 'pointer' }}>
          <input
            type="checkbox"
            checked={includeSymbols}
            onChange={e => {
              setIncludeSymbols(e.target.checked);
            }}
            style={{ accentColor: 'var(--btn)' }}
          />
          <span>رموز خاصة (@#$%)</span>
        </label>
      </div>

      <div style={{ marginTop: '10px', textAlign: 'left' }}>
        <button
          type="button"
          className="btn btn-ghost btn-sm"
          onClick={handleGenerate}
          style={{ fontSize: '11px', padding: '4px 8px' }}
        >
          🔄 إعادة توليد وفق الخيارات
        </button>
      </div>
    </div>
  );
};
