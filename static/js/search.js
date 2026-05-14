document.addEventListener('DOMContentLoaded', function() {
  const searchResults = document.querySelector('.search-results');
  if (!searchResults) return;

  const params = new URLSearchParams(window.location.search);
  const query = params.get('q');

  if (!query) return;

  const queryLower = query.toLowerCase();
  const results = document.querySelectorAll('.search-result-item');
  const noResults = document.querySelector('.no-results');
  let matchCount = 0;

  results.forEach(result => {
    const title = result.querySelector('h2').textContent.toLowerCase();
    const excerpt = result.querySelector('.excerpt')?.textContent.toLowerCase() || '';

    if (title.includes(queryLower) || excerpt.includes(queryLower)) {
      result.style.display = 'block';
      matchCount++;
    } else {
      result.style.display = 'none';
    }
  });

  const resultsList = document.querySelector('.search-result-list');
  const resultCount = document.querySelector('.result-count');

  if (matchCount === 0 && resultsList) {
    resultsList.style.display = 'none';
    if (resultCount) resultCount.style.display = 'none';
    if (noResults) {
      noResults.style.display = 'block';
    }
  } else if (resultCount) {
    resultCount.textContent = `Found ${matchCount} result${matchCount !== 1 ? 's' : ''}`;
  }

  // Update page title
  const titleEl = document.querySelector('.search-query');
  if (titleEl) {
    titleEl.textContent = `Results for: ${query}`;
  }
});
