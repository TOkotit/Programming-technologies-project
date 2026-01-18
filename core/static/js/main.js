document.addEventListener('DOMContentLoaded', () => {
  const searchInput = document.getElementById('invoice-search');
  const wrapper = document.getElementById('invoices-wrapper');

  if (!searchInput || !wrapper) return;

  let timer = null;
  const delay = 300; // ms debounce

  function fetchAndReplace(q) {
    const url = '/invoices/' + (q ? `?q=${encodeURIComponent(q)}` : '');
    fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
      .then(resp => resp.text())
      .then(html => {
        // parse returned HTML and extract the wrapper content
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        const newWrapper = doc.querySelector('#invoices-wrapper');
        if (newWrapper) {
          wrapper.innerHTML = newWrapper.innerHTML;
        } else {
          // fallback: show "no results"
          wrapper.innerHTML = '<div class="alert alert-info">No results</div>';
        }
        // Re-run any UI init if needed (e.g., tooltips)
      })
      .catch(err => {
        console.error('Search fetch error', err);
      });
  }

  searchInput.addEventListener('input', (e) => {
    const q = e.target.value.trim();
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => {
      fetchAndReplace(q);
    }, delay);
  });

  // handle Enter -> go to page (keeps history/bookmark)
  searchInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      const q = searchInput.value.trim();
      location.href = '/invoices/' + (q ? `?q=${encodeURIComponent(q)}` : '');
    }
  });
});
