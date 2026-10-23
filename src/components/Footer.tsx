import React from 'react';
import { ViewState } from '../types';

interface FooterProps {
  onNavigate: (view: ViewState) => void;
}

export const Footer: React.FC<FooterProps> = ({ onNavigate }) => {
  const year = 2026;

  return (
    <footer className="site-footer" role="contentinfo">
      <div className="footer-links">
        <button type="button" onClick={() => onNavigate({ view: 'home' })}>
          الرئيسية
        </button>
        <button type="button" onClick={() => onNavigate({ view: 'blog' })}>
          المدونة
        </button>
        <button type="button" onClick={() => onNavigate({ view: 'about' })}>
          عن الموقع
        </button>
        <button type="button" onClick={() => onNavigate({ view: 'privacy' })}>
          سياسة الخصوصية
        </button>
        <button type="button" onClick={() => onNavigate({ view: 'terms' })}>
          شروط الاستخدام
        </button>
        <button type="button" onClick={() => onNavigate({ view: 'contact' })}>
          تواصل معنا
        </button>
      </div>
      <p style={{ fontSize: '12px' }}>
        © {year} مدير الحسابات الشامل · جميع الحقوق محفوظة
      </p>
      <p style={{ fontSize: '11px', marginTop: '6px', color: 'var(--muted)' }}>
        هذا الموقع يستخدم Google AdSense الذي قد يستخدم ملفات تعريف الارتباط لعرض إعلانات مخصصة.{' '}
        <button
          type="button"
          onClick={() => onNavigate({ view: 'privacy' })}
          style={{ color: '#60a5fa', textDecoration: 'underline' }}
        >
          سياسة الخصوصية
        </button>
      </p>
    </footer>
  );
};
