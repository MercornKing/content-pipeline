/* site.js — WorkSmart Reviews
   Architecture: vanilla JS, no framework, no build step.
   AI maintenance notes at bottom of file.
   Depends on: marked.js (CDN), site.css
*/

'use strict';

// ── Site configuration ────────────────────────────────────────────────────────
// AI MAINTENANCE: Edit SITE_CONFIG to add topics, update metadata, change copy.
// To add a new article: add the .md file to /content and add an entry to ARTICLES.

const SITE_CONFIG = {
  name: 'WorkSmart Reviews',
  tagline: 'Honest tool reviews for small business owners and freelancers',
  description: 'Cut through the noise. Find the right tools for your business — reviewed honestly, with real pricing and real weaknesses.',
  affiliateDisclaimer: 'Some links on this site are affiliate links. We may earn a commission at no extra cost to you.',
};

// ── Article registry ──────────────────────────────────────────────────────────
// AI MAINTENANCE: Add new articles here. slug must match the .md filename.
// topics must be one of the keys in TOPICS below.

const ARTICLES = [
  {
    slug: 'best-email-marketing-tools-for-beginners',
    title: 'Best Email Marketing Tools for Beginners',
    topic: 'marketing',
    excerpt: 'Mailchimp, MailerLite, or Brevo? An honest comparison for UK small business owners who just want emails to go out without the faff.',
    date: '2026-05-09',
  },
  {
    slug: 'monday-com-review-for-small-business',
    title: 'Monday.com Review for Small Business',
    topic: 'productivity',
    excerpt: 'Monday.com is everywhere. But is it right for a small team or solo operator — or is the pricing model working against you?',
    date: '2026-05-09',
  },
  {
    slug: 'best-scheduling-tools-for-coaches',
    title: 'Best Scheduling Tools for Coaches',
    topic: 'coaching',
    excerpt: 'Calendly, Acuity, or Tidycal? A straight-talking guide for coaches who want clients to book without the back-and-forth.',
    date: '2026-05-09',
  },
  {
    slug: 'best-accounting-software-for-sole-traders-uk',
    title: 'Best Accounting Software for Sole Traders UK',
    topic: 'finance',
    excerpt: 'Xero, QuickBooks, or FreeAgent? An honest guide to accounting software for UK sole traders — with real pricing and no jargon.',
    date: '2026-05-09',
  },
  {
    slug: 'best-invoicing-software-for-small-business-uk',
    title: 'Best Invoicing Software for Small Business UK',
    topic: 'finance',
    excerpt: 'Stop chasing payments with spreadsheets. The best invoicing tools for UK small businesses — compared on features, price, and ease of use.',
    date: '2026-05-09',
  },
  {
    slug: 'best-project-management-tools-for-freelancers',
    title: 'Best Project Management Tools for Freelancers',
    topic: 'productivity',
    excerpt: 'When it\'s just you managing multiple clients, the right project management tool makes all the difference. Here\'s what actually works.',
    date: '2026-05-09',
  },
  {
    slug: 'canva-pro-review-is-the-upgrade-worth-it',
    title: 'Canva Pro Review: Is the Upgrade Worth It?',
    topic: 'marketing',
    excerpt: 'Canva\'s free plan is genuinely useful. But is Pro worth £10.99 a month for a small business? An honest look at what you actually get.',
    date: '2026-05-09',
  },
  {
    slug: 'freshbooks-vs-quickbooks-for-freelancers',
    title: 'FreshBooks vs QuickBooks for Freelancers',
    topic: 'finance',
    excerpt: 'Two of the most popular accounting tools for freelancers — but they suit very different working styles. Here\'s how to choose.',
    date: '2026-05-09',
  },
  {
    slug: 'monday-vs-asana-for-small-teams',
    title: 'Monday.com vs Asana for Small Teams',
    topic: 'productivity',
    excerpt: 'Both promise to fix your workflow. Monday.com is more flexible; Asana is more focused. Which one is actually right for a small team?',
    date: '2026-05-09',
  },
  {
    slug: 'notion-vs-obsidian-for-note-taking',
    title: 'Notion vs Obsidian for Note-Taking',
    topic: 'productivity',
    excerpt: 'Notion is collaborative and structured. Obsidian is private and powerful. The right choice depends on how your brain works.',
    date: '2026-05-09',
  },
  {
    slug: 'cheaper-alternatives-to-monday-com',
    title: 'Cheaper Alternatives to Monday.com for UK Small Teams',
    topic: 'productivity',
    excerpt: 'Monday.com is polished but pricey. These alternatives deliver the same core features for significantly less — some for free.',
    date: '2026-05-09',
  },
  {
    slug: 'best-time-tracking-apps-for-remote-teams',
    title: 'Best Time Tracking Apps For Remote Teams',
    topic: 'general',
    excerpt: "Best Time Tracking Apps for Remote Teams (2026 UK Guide)",
    date: '2026-05-09',
  },
  {
    slug: 'freshbooks-review-for-sole-traders',
    title: 'Freshbooks Review For Sole Traders',
    topic: 'finance',
    excerpt: "FreshBooks Review for Sole Traders UK (2026)",
    date: '2026-05-09',
  }
];

// ── Topic registry ────────────────────────────────────────────────────────────
// AI MAINTENANCE: Add new topics here as the article library grows.

const TOPICS = {
  all:        { label: 'All Articles' },
  marketing:  { label: 'Marketing' },
  productivity: { label: 'Productivity' },
  coaching:   { label: 'Coaching' },
  finance:    { label: 'Finance' },
  hr:         { label: 'HR & Hiring' },
};

// ── State ─────────────────────────────────────────────────────────────────────
let state = {
  view: 'home',        // 'home' | 'article'
  topic: 'all',
  search: '',
  articleSlug: null,
};

// ── DOM refs ──────────────────────────────────────────────────────────────────
const $ = id => document.getElementById(id);

// ── Boot ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  renderTopicTabs();
  renderSidebarTopics();
  handleRouting();
  bindSearch();
  window.addEventListener('popstate', handleRouting);
});

// ── Routing ───────────────────────────────────────────────────────────────────
function handleRouting() {
  const hash = window.location.hash;
  if (hash.startsWith('#article/')) {
    const slug = hash.replace('#article/', '');
    openArticle(slug, false);
  } else {
    showHome();
  }
}

function navigate(hash) {
  window.location.hash = hash;
}

// ── Home view ─────────────────────────────────────────────────────────────────
function showHome() {
  state.view = 'home';
  state.articleSlug = null;
  $('main-content').style.display = 'grid';
  const av = $('article-view');
  av.classList.remove('visible');
  renderArticleGrid();
  window.scrollTo(0, 0);
}

// ── Article grid ──────────────────────────────────────────────────────────────
function renderArticleGrid() {
  const grid = $('article-grid');
  const filtered = getFilteredArticles();

  if (filtered.length === 0) {
    grid.innerHTML = `<div class="empty-state"><p>No articles found${state.search ? ` for "<strong>${escHtml(state.search)}</strong>"` : ''}.</p></div>`;
    return;
  }

  grid.innerHTML = filtered.map(a => {
    const topicLabel = TOPICS[a.topic]?.label || a.topic;
    const titleHl = highlight(a.title, state.search);
    const excerptHl = highlight(a.excerpt, state.search);
    return `
    <article class="article-card" onclick="navigate('#article/${a.slug}')" role="button" tabindex="0"
      onkeydown="if(event.key==='Enter')navigate('#article/${a.slug}')">
      <div class="card-topic">${topicLabel}</div>
      <div class="card-title">${titleHl}</div>
      <div class="card-excerpt">${excerptHl}</div>
      <div class="card-meta">${formatDate(a.date)}</div>
      <div class="card-cta">Read review <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M5 12h14M12 5l7 7-7 7"/></svg></div>
    </article>`;
  }).join('');
}

function getFilteredArticles() {
  return ARTICLES.filter(a => a && a.slug).filter(a => {
    const matchTopic = state.topic === 'all' || a.topic === state.topic;
    const q = state.search.toLowerCase();
    const matchSearch = !q || a.title.toLowerCase().includes(q) || a.excerpt.toLowerCase().includes(q);
    return matchTopic && matchSearch;
  });
}

// ── Article view ──────────────────────────────────────────────────────────────
async function openArticle(slug, pushState = true) {
  const meta = ARTICLES.filter(a => a && a.slug).find(a => a.slug === slug);
  if (!meta) { showHome(); return; }

  state.view = 'article';
  state.articleSlug = slug;

  if (pushState) navigate(`#article/${slug}`);

  $('main-content').style.display = 'none';
  const av = $('article-view');
  av.classList.add('visible');
  av.innerHTML = `
    <button class="article-back" onclick="navigate('#')">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
      Back to all articles
    </button>
    <div class="article-body" id="article-body">
      <p style="color:var(--cream-dim);padding:2rem 0">Loading article…</p>
    </div>
    <aside id="article-sidebar"></aside>`;

  renderArticleSidebar();

  try {
    const res = await fetch(`/articles/${slug}.md`);
    if (!res.ok) throw new Error(res.status);
    let md = await res.text();
    md = stripFrontmatter(md);
    const html = marked.parse(md);
    const body = $('article-body');
    body.innerHTML = `
      <div class="article-meta">
        <span class="topic-tag">${TOPICS[meta.topic]?.label || meta.topic}</span>
        <span class="date">${formatDate(meta.date)}</span>
      </div>
      ${injectInlineAd(html)}`;
  } catch(e) {
    $('article-body').innerHTML = `<p style="color:var(--cream-dim)">Could not load article. <button onclick="navigate('#')" style="background:none;border:none;color:var(--amber);cursor:pointer;font-family:inherit">Go back</button></p>`;
  }

  window.scrollTo(0, 0);
}

function injectInlineAd(html) {
  // Insert an ad slot roughly halfway through the article
  const mid = Math.floor(html.length / 2);
  const breakPoint = html.indexOf('</p>', mid);
  if (breakPoint === -1) return html;
  const adSlot = `
    <div class="inline-ad">
      <div class="ad-label">Advertisement</div>
      <!-- AD SLOT: inline-article-mid — replace comment with ad tag -->
    </div>`;
  return html.slice(0, breakPoint + 4) + adSlot + html.slice(breakPoint + 4);
}

function renderArticleSidebar() {
  const sb = $('article-sidebar');
  if (!sb) return;
  sb.innerHTML = `
    <div class="sidebar-ad">
      <div class="ad-label">Advertisement</div>
      <!-- AD SLOT: sidebar-article — replace comment with ad tag -->
    </div>
    <div class="sidebar-topics">
      <h3>Browse topics</h3>
      <ul class="topic-list">
        ${Object.entries(TOPICS).filter(([k])=>k!=='all').map(([key, t]) => {
          const count = ARTICLES.filter(a => a && a.slug && a.topic === key).length;
          return count ? `<li>
            <button onclick="navigate('#');setTimeout(()=>setTopic('${key}'),50)">${t.label}</button>
            <span class="topic-count">${count}</span>
          </li>` : '';
        }).join('')}
      </ul>
    </div>`;
}

// ── Topic tabs ────────────────────────────────────────────────────────────────
function renderTopicTabs() {
  const nav = $('topics-inner');
  nav.innerHTML = Object.entries(TOPICS).map(([key, t]) => `
    <button class="topic-btn ${key === state.topic ? 'active' : ''}"
      onclick="setTopic('${key}')">${t.label}</button>
  `).join('');
}

function setTopic(key) {
  state.topic = key;
  document.querySelectorAll('.topic-btn').forEach(b => {
    b.classList.toggle('active', b.textContent === TOPICS[key]?.label);
  });
  if (state.view !== 'home') {
    navigate('#');
  } else {
    renderArticleGrid();
  }
}

// ── Sidebar topics ────────────────────────────────────────────────────────────
function renderSidebarTopics() {
  const sb = $('sidebar');
  if (!sb) return;
  sb.innerHTML = `
    <div class="sidebar-ad">
      <div class="ad-label">Advertisement</div>
      <!-- AD SLOT: sidebar-home — replace comment with ad tag -->
    </div>
    <div class="sidebar-topics">
      <h3>Browse topics</h3>
      <ul class="topic-list">
        ${Object.entries(TOPICS).filter(([k])=>k!=='all').map(([key, t]) => {
          const count = ARTICLES.filter(a => a && a.slug && a.topic === key).length;
          return count ? `<li>
            <button onclick="setTopic('${key}')">${t.label}</button>
            <span class="topic-count">${count}</span>
          </li>` : '';
        }).join('')}
      </ul>
    </div>`;
}

// ── Search ────────────────────────────────────────────────────────────────────
function bindSearch() {
  const input = $('search-input');
  if (!input) return;
  let timer;
  input.addEventListener('input', e => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      state.search = e.target.value.trim();
      if (state.view === 'home') renderArticleGrid();
    }, 200);
  });
}

// ── Utilities ─────────────────────────────────────────────────────────────────
function stripFrontmatter(md) {
  return md.replace(/^---[\s\S]*?---\n?/, '').trim();
}

function formatDate(iso) {
  if (!iso) return '';
  return new Date(iso).toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' });
}

function escHtml(str) {
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

function highlight(text, query) {
  if (!query) return escHtml(text);
  const safe = escHtml(text);
  const safeQ = escHtml(query).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  return safe.replace(new RegExp(`(${safeQ})`, 'gi'), '<mark class="search-highlight">$1</mark>');
}

/* ─────────────────────────────────────────────────────────────────────────────
   AI MAINTENANCE GUIDE
   ────────────────────────────────────────────────────────────────────────────
   This file is the entire site logic. No build tools. No framework. Edit here,
   save, push — done.

   ADDING AN ARTICLE
   1. Add .md file to /content folder (pipeline does this automatically)
   2. Add entry to ARTICLES array at top of this file:
      { slug: 'your-file-name', title: '...', topic: 'marketing', excerpt: '...', date: 'YYYY-MM-DD' }

   ADDING A TOPIC
   1. Add key/label to TOPICS object
   2. Tag articles with the new topic key

   ADDING AD SLOTS
   1. Find the comment "AD SLOT: [name]" in index.html or this file
   2. Replace the HTML comment with your ad network tag

   CHANGING SITE NAME / COPY
   1. Edit SITE_CONFIG at top of this file
   2. Update the <title> and logo text in index.html

   CHANGING COLOURS / FONTS
   1. Edit the :root variables block at top of site.css
   ──────────────────────────────────────────────────────────────────────────── */