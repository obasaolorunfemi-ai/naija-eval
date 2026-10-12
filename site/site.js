/* Shared by every page: theme switch, reading progress, current section in the bar. */
(() => {
  const root = document.documentElement;
  const btn = document.getElementById('theme');
  const isDark = () => root.dataset.theme ? root.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches;
  const label = () => btn && btn.setAttribute('aria-label', isDark() ? 'Switch to light mode' : 'Switch to dark mode');
  if (btn) {
    label();
    btn.addEventListener('click', () => {
      root.dataset.theme = isDark() ? 'light' : 'dark';
      try { localStorage.setItem('ne-theme', root.dataset.theme); } catch (e) {}
      label();
    });
  }

  /* reading progress */
  const bar = document.getElementById('progress');
  let ticking = false;
  const update = () => {
    const max = document.documentElement.scrollHeight - innerHeight;
    if (bar) bar.style.setProperty('--p', max > 0 ? Math.min(1, scrollY / max) : 0);
    ticking = false;
  };
  addEventListener('scroll', () => { if (!ticking) { ticking = true; requestAnimationFrame(update); } }, { passive: true });
  addEventListener('resize', update);
  update();

  /* highlight the section being read, and keep its link in view on small screens */
  const links = [...document.querySelectorAll('.sections a[href^="#"]')];
  const targets = links.map(a => document.getElementById(a.hash.slice(1))).filter(Boolean);
  if (targets.length && 'IntersectionObserver' in window) {
    const set = id => links.forEach(a => {
      const on = a.hash === '#' + id;
      if (on) {
        a.setAttribute('aria-current', 'location');
        const nav = a.parentElement, l = a.offsetLeft - nav.offsetLeft;
        if (l < nav.scrollLeft || l + a.offsetWidth > nav.scrollLeft + nav.clientWidth) nav.scrollTo({ left: l - 12, behavior: 'smooth' });
      }
      else a.removeAttribute('aria-current');
    });
    const io = new IntersectionObserver(es => {
      const vis = es.filter(e => e.isIntersecting).sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top);
      if (vis[0]) set(vis[0].target.id);
    }, { rootMargin: '-35% 0px -60% 0px' });
    targets.forEach(t => io.observe(t));
  }

  /* in-page links: scroll to the section and move focus there, in every browser and preview */
  const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const samePage = a => {
    const href = a.getAttribute('href') || '';
    const i = href.indexOf('#');
    if (i < 0) return null;
    const path = href.slice(0, i);
    /* same page when the link has no path, points at this page, or points at the report while we are on it */
    const onReport = !!document.getElementById('mt');
    if (path && path !== location.pathname && !((path === '/' || path === 'index.html' || path === '/index.html') && onReport)) return null;
    return document.getElementById(decodeURIComponent(href.slice(i + 1))) || null;
  };
  const go = (target, push) => {
    target.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'start' });
    if (!target.hasAttribute('tabindex')) target.setAttribute('tabindex', '-1');
    target.focus({ preventScroll: true });
    if (push) try { history.pushState(null, '', '#' + target.id); } catch (e) {}
  };
  document.addEventListener('click', e => {
    if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    const a = e.target.closest('a[href*="#"]');
    if (!a) return;
    const target = samePage(a);
    if (!target) return;
    e.preventDefault();
    closeMenu(false);
    go(target, true);
  });

  /* menu */
  const menu = document.getElementById('menu');
  const menuBtn = document.getElementById('menu-btn');
  let lastFocus = null;
  function openMenu() {
    if (!menu) return;
    lastFocus = document.activeElement;
    menu.hidden = false;
    requestAnimationFrame(() => menu.classList.add('open'));
    menuBtn.setAttribute('aria-expanded', 'true');
    menuBtn.setAttribute('aria-label', 'Close menu');
    root.classList.add('menu-open');
    const first = menu.querySelector('.menu-group a');
    if (first) first.focus();
  }
  function closeMenu(restore = true) {
    if (!menu || menu.hidden) return;
    menu.classList.remove('open');
    menuBtn.setAttribute('aria-expanded', 'false');
    menuBtn.setAttribute('aria-label', 'Open menu');
    root.classList.remove('menu-open');
    setTimeout(() => { menu.hidden = true; }, reduceMotion ? 0 : 220);
    if (restore && lastFocus) lastFocus.focus();
  }
  if (menu && menuBtn) {
    menuBtn.addEventListener('click', () => (menu.hidden ? openMenu() : closeMenu()));
    menu.querySelectorAll('[data-close]').forEach(el => el.addEventListener('click', () => closeMenu()));
    menu.querySelectorAll('a').forEach(a => a.addEventListener('click', () => { if (!samePage(a)) closeMenu(false); }));
    document.addEventListener('keydown', e => {
      if (menu.hidden) return;
      if (e.key === 'Escape') { e.preventDefault(); closeMenu(); return; }
      if (e.key === 'Tab') {
        /* keep focus inside the open menu */
        const items = [...menu.querySelectorAll('a, button')];
        const first = items[0], last = items[items.length - 1];
        if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
        else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
      }
    });
    /* mark the current page in the menu */
    menu.querySelectorAll('a').forEach(a => {
      const h = a.getAttribute('href');
      if (h && !h.includes('#') && h === location.pathname) a.setAttribute('aria-current', 'page');
    });
  }

  /* arriving with a #section in the address: land below the sticky bar */
  if (location.hash.length > 1) {
    const t = document.getElementById(decodeURIComponent(location.hash.slice(1)));
    if (t) addEventListener('load', () => go(t, false), { once: true });
  }
})();
