(() => {
  const root = document.documentElement;
  const toggle = document.querySelector('[data-theme-toggle]');
  const syncThemeButton = () => {
    const dark = root.dataset.theme === 'dark';
    if (!toggle) return;
    toggle.setAttribute('aria-label', dark ? '切换到浅色模式' : '切换到深色模式');
    toggle.setAttribute('aria-pressed', String(dark));
    toggle.querySelector('span').textContent = dark ? '浅色' : '深色';
  };
  syncThemeButton();
  toggle?.addEventListener('click', () => {
    root.dataset.theme = root.dataset.theme === 'dark' ? 'light' : 'dark';
    try { localStorage.setItem('quiet-notes-theme', root.dataset.theme); } catch {}
    syncThemeButton();
  });

  const search = document.querySelector('[data-search]');
  const filters = [...document.querySelectorAll('[data-category]')];
  const cards = [...document.querySelectorAll('[data-post]')];
  let category = new URLSearchParams(location.search).get('category') || '全部';
  if (!filters.some(button => button.dataset.category === category)) category = '全部';
  const filterPosts = () => {
    const query = (search?.value || '').trim().toLocaleLowerCase();
    let visible = 0;
    cards.forEach(card => {
      const matches = (category === '全部' || card.dataset.postCategory === category)
        && card.dataset.search.toLocaleLowerCase().includes(query);
      card.hidden = !matches;
      visible += Number(matches);
    });
    filters.forEach(button => {
      button.setAttribute('aria-pressed', String(button.dataset.category === category));
    });
    const count = document.querySelector('[data-result-count]');
    if (count) count.textContent = `${visible} 篇文章`;
    const empty = document.querySelector('[data-empty]');
    if (empty) empty.hidden = visible !== 0;
  };
  search?.addEventListener('input', filterPosts);
  filters.forEach(button => button.addEventListener('click', () => {
    category = button.dataset.category;
    const url = new URL(location.href);
    if (category === '全部') url.searchParams.delete('category');
    else url.searchParams.set('category', category);
    history.replaceState(null, '', url);
    filterPosts();
  }));
  if (cards.length) filterPosts();
  document.querySelector('[data-reset-search]')?.addEventListener('click', () => {
    search.value = '';
    category = '全部';
    history.replaceState(null, '', location.pathname);
    filterPosts();
    search.focus();
  });

  const progress = document.querySelector('[data-reading-progress]');
  if (progress) {
    const updateProgress = () => {
      const distance = document.documentElement.scrollHeight - innerHeight;
      progress.style.transform = `scaleX(${distance > 0 ? Math.min(1, scrollY / distance) : 1})`;
    };
    addEventListener('scroll', updateProgress, {passive: true});
    addEventListener('resize', updateProgress);
    updateProgress();
  }
  const headings = [...document.querySelectorAll('d-article h2[id]')];
  const tocLinks = [...document.querySelectorAll('.toc a')];
  if (headings.length && 'IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => {
      const current = entries.find(entry => entry.isIntersecting);
      if (!current) return;
      tocLinks.forEach(link => {
        if (decodeURIComponent(link.hash.slice(1)) === current.target.id) link.setAttribute('aria-current', 'location');
        else link.removeAttribute('aria-current');
      });
    }, {rootMargin: '-5% 0px -70% 0px'});
    headings.forEach(heading => observer.observe(heading));
  }
})();
