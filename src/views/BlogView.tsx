import React, { useState } from 'react';
import { ARTICLES } from '../data/articles';
import { ViewState } from '../types';
import { AdUnit } from '../components/AdUnit';

interface BlogViewProps {
  onNavigate: (view: ViewState) => void;
}

export const BlogView: React.FC<BlogViewProps> = ({ onNavigate }) => {
  const [searchTerm, setSearchTerm] = useState('');

  const filtered = ARTICLES.filter(
    a =>
      a.title.includes(searchTerm) ||
      a.desc.includes(searchTerm) ||
      a.cat.includes(searchTerm)
  );

  return (
    <main className="wrap">
      <header style={{ textAlign: 'center', marginBottom: '32px' }}>
        <span className="badge">✍️ المدونة</span>
        <h1 style={{ fontSize: '30px', color: 'var(--heading)', fontWeight: 900, marginTop: '10px' }}>
          مقالات الأمن الرقمي
        </h1>
        <p style={{ fontSize: '15px', maxWidth: '560px', margin: '10px auto 18px', lineHeight: 1.7 }}>
          دليلك الشامل لحماية حساباتك وخصوصيتك الرقمية. مقالات موثوقة يكتبها خبراء متخصصون.
        </p>
        <div style={{ maxWidth: '400px', margin: '0 auto' }}>
          <input
            type="search"
            placeholder="ابحث في المقالات..."
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            style={{
              width: '100%',
              padding: '10px 14px',
              borderRadius: '8px',
              border: '1px solid var(--ibr)',
              background: 'var(--ibg)',
              color: 'var(--itxt)',
            }}
          />
        </div>
      </header>

      <AdUnit slot="top" />

      <div className="blog-grid" style={{ marginBottom: '32px' }}>
        {filtered.length === 0 ? (
          <p style={{ gridColumn: '1 / -1', textAlign: 'center', color: 'var(--muted)', padding: '30px' }}>
            لم يتم العثور على مقالات تطابق بحثك.
          </p>
        ) : (
          filtered.map(a => (
            <article
              key={a.slug}
              className="blog-card"
              onClick={() => onNavigate({ view: 'article', slug: a.slug })}
            >
              <div className="blog-cat">{a.cat}</div>
              <h2>{a.title}</h2>
              <p>{a.desc}</p>
              <div className="blog-meta">🕐 {a.readTime} · 📅 {a.date}</div>
              <span className="blog-link">اقرأ المقال كاملاً ◀</span>
            </article>
          ))
        )}
      </div>

      <AdUnit slot="bottom" />
    </main>
  );
};
