import React from 'react';
import { ARTICLES } from '../data/articles';
import { ViewState } from '../types';
import { AdUnit } from '../components/AdUnit';

interface ArticleViewProps {
  slug: string;
  onNavigate: (view: ViewState) => void;
}

export const ArticleView: React.FC<ArticleViewProps> = ({ slug, onNavigate }) => {
  const article = ARTICLES.find(a => a.slug === slug);

  if (!article) {
    return (
      <main className="wrap">
        <div className="card">
          <p>المقال غير موجود.</p>
          <button
            type="button"
            className="btn btn-ghost"
            style={{ marginTop: '14px' }}
            onClick={() => onNavigate({ view: 'blog' })}
          >
            العودة للمدونة
          </button>
        </div>
      </main>
    );
  }

  const related = ARTICLES.filter(a => a.slug !== slug).slice(0, 3);

  return (
    <main className="wrap-narrow">
      <nav className="breadcrumb" aria-label="مسار التنقل">
        <button type="button" onClick={() => onNavigate({ view: 'home' })}>
          الرئيسية
        </button>{' '}
        ›{' '}
        <button type="button" onClick={() => onNavigate({ view: 'blog' })}>
          المدونة
        </button>{' '}
        › <span>{article.title}</span>
      </nav>

      <AdUnit slot="top" />

      <article className="card">
        <div className="blog-cat" style={{ marginBottom: '10px' }}>
          {article.cat}
        </div>
        <h1
          style={{
            fontSize: '26px',
            color: 'var(--heading)',
            fontWeight: 900,
            lineHeight: 1.3,
            marginBottom: '12px',
          }}
        >
          {article.title}
        </h1>
        <div className="blog-meta" style={{ marginBottom: '22px' }}>
          🕐 {article.readTime} · 📅 {article.date}
        </div>
        <div
          className="article-body"
          dangerouslySetInnerHTML={{ __html: article.body }}
        />
      </article>

      <AdUnit slot="mid" />

      <section style={{ marginTop: '28px' }}>
        <h2 style={{ fontSize: '18px', color: 'var(--heading)', fontWeight: 700, marginBottom: '16px' }}>
          📖 مقالات ذات صلة
        </h2>
        <div className="blog-grid">
          {related.map(a => (
            <div
              key={a.slug}
              className="blog-card"
              onClick={() => onNavigate({ view: 'article', slug: a.slug })}
            >
              <div className="blog-cat">{a.cat}</div>
              <h3 style={{ fontSize: '14px', color: 'var(--heading)', marginBottom: '6px' }}>
                {a.title}
              </h3>
              <span className="blog-link">اقرأ ◀</span>
            </div>
          ))}
        </div>
      </section>

      <AdUnit slot="bottom" />
    </main>
  );
};
