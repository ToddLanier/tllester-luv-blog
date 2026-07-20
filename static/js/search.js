document.addEventListener('DOMContentLoaded', async function () {
  const searchResults = document.querySelector('.search-results');
  if (!searchResults) return;

  const listEl = document.querySelector('.search-result-list');
  const noResults = document.querySelector('.no-results');
  const resultCount = document.querySelector('.result-count');
  const queryEl = document.querySelector('.search-query');

  const params = new URLSearchParams(window.location.search);
  const rawQuery = (params.get('q') || '').trim();

  // Lowercase, strip accents, reduce every non-alphanumeric run to a single
  // space. Makes "please touch" match "Please, touch me" and "mixed media"
  // match the slug "mixed-media", and folds "Luciérnagas"/"São" to ASCII.
  const normalize = (s) =>
    (s || '')
      .toString()
      .toLowerCase()
      .normalize('NFKD')
      .replace(/[̀-ͯ]/g, '')
      .replace(/[^a-z0-9]+/g, ' ')
      .trim();

  if (!rawQuery) {
    queryEl.textContent = 'Enter a search term in the box above.';
    return;
  }

  queryEl.textContent = `Results for: ${rawQuery}`;

  const tokens = normalize(rawQuery).split(' ').filter(Boolean);
  if (tokens.length === 0) {
    if (resultCount) resultCount.style.display = 'none';
    if (noResults) noResults.style.display = 'block';
    return;
  }

  let records;
  try {
    const res = await fetch('/index.json', { headers: { Accept: 'application/json' } });
    if (!res.ok) throw new Error('HTTP ' + res.status);
    records = await res.json();
  } catch (err) {
    if (resultCount) resultCount.style.display = 'none';
    if (noResults) {
      const p = noResults.querySelector('p');
      if (p) p.textContent = 'Search is temporarily unavailable. Please try again.';
      noResults.style.display = 'block';
    }
    return;
  }

  const matches = [];
  for (const rec of records) {
    const strong = `${normalize(rec.title)} ${normalize(rec.author)} ${normalize((rec.categories || []).join(' '))}`;
    const blob = `${strong} ${normalize(rec.summary)} ${normalize(rec.content)}`;

    // Every query token must appear somewhere in the record.
    if (!tokens.every((t) => blob.includes(t))) continue;

    // Rank a full title/author/category hit above a body-only hit.
    const rank = tokens.every((t) => strong.includes(t)) ? 0 : 1;
    matches.push({ rec, rank });
  }

  matches.sort((a, b) => a.rank - b.rank);

  if (matches.length === 0) {
    listEl.innerHTML = '';
    if (resultCount) resultCount.style.display = 'none';
    if (noResults) noResults.style.display = 'block';
    return;
  }

  const esc = (s) =>
    (s || '')
      .toString()
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');

  const frag = document.createDocumentFragment();
  for (const { rec } of matches) {
    const art = document.createElement('article');
    art.className = 'search-result-item';

    const meta = [];
    if (rec.date) meta.push(`<span class="date">${esc(rec.date)}</span>`);
    if (rec.author) meta.push(`<span class="author">${esc(rec.author)}</span>`);

    const summary = (rec.summary || '').trim();
    let excerpt = summary || (rec.content || '').trim().slice(0, 160);
    const truncated = !summary && (rec.content || '').trim().length > 160;

    art.innerHTML =
      `<h2><a href="${esc(rec.url)}">${esc(rec.title)}</a></h2>` +
      `<div class="search-result-meta">${meta.join(' <span class="sep">·</span> ')}</div>` +
      `<p class="excerpt">${esc(excerpt)}${truncated ? '…' : ''}</p>`;
    frag.appendChild(art);
  }

  listEl.innerHTML = '';
  listEl.appendChild(frag);

  if (resultCount) {
    resultCount.style.display = '';
    resultCount.textContent = `Found ${matches.length} result${matches.length !== 1 ? 's' : ''}`;
  }
  if (noResults) noResults.style.display = 'none';
});
